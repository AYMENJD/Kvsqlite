import sqlite3
import logging

from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from sys import version_info
from time import time

logger = logging.getLogger(__name__)


class REQUEST:
    GET = "GET"
    SET = "SET"
    SETEX = "SETEX"
    DELETE = "DELETE"
    COMMIT = "COMMIT"
    EXISTS = "EXISTS"
    TTL = "TTL"
    EXPIRE = "EXPIRE"
    RENAME = "RENAME"
    KEYS = "KEYS"
    CLEAN_EX = "CLEAN_EX"
    FLUSH_DB = "FLUSH_DB"
    CLOSE = "CLOSE"


class Sqlite:
    def __init__(
        self,
        database: str,
        table_name: str,
        autocommit: bool,
        journal_mode: str,
        synchronous: str,
        encoder,
        workers: int,
    ) -> None:
        assert isinstance(database, str), "database must be str"
        assert isinstance(table_name, str), "table_name must be str"
        assert isinstance(autocommit, bool), "autocommit must be bool"
        assert isinstance(journal_mode, str), "journal_mode must be str"
        assert isinstance(synchronous, str), "synchronous must be str"

        self.database = database
        self.table_name = table_name
        self.autocommit = autocommit
        self.journal_mode = journal_mode
        self.synchronous = synchronous
        self.__encoder = encoder
        self.__workers = ThreadPoolExecutor(workers, "kvsqlite")
        self.__lock = Lock()

        self.is_running = True

        self.__table_statement = 'CREATE TABLE IF NOT EXISTS "{}" (k VARCHAR(4096) PRIMARY KEY, v BLOB, expire_time INTEGER DEFAULT NULL)'.format(
            self.table_name
        )
        self.__get_statement = 'SELECT v FROM "{}" WHERE k = ? AND (expire_time IS NULL OR expire_time > ?)'.format(
            self.table_name
        )
        self.__set_statement = (
            'REPLACE INTO "{}" (k, v, expire_time) VALUES(?,?,NULL)'.format(
                self.table_name
            )
        )
        self.__setex_statement = (
            'REPLACE INTO "{}" (k, v, expire_time) VALUES(?,?,?)'.format(
                self.table_name
            )
        )
        self.__delete_statement = 'DELETE FROM "{}" WHERE k = ?'.format(self.table_name)
        self.__exists_statement = 'SELECT k FROM "{}" WHERE k = ?'.format(
            self.table_name
        )
        self.__ttl_statement = (
            'SELECT expire_time FROM "{}" WHERE k = ? AND expire_time > ?'.format(
                self.table_name
            )
        )
        self.__expire_statement = 'UPDATE "{}" SET expire_time = ? WHERE k = ?'.format(
            self.table_name
        )
        self.__rename_statement = 'UPDATE OR IGNORE "{}" SET k = ? WHERE k = ?'.format(
            self.table_name
        )
        self.__keys_statement = (
            'SELECT k FROM "{}" WHERE k LIKE ? ORDER BY rowid'.format(self.table_name)
        )
        self.__cleanex_statement = 'DELETE FROM "{}" WHERE expire_time IS NOT NULL AND expire_time <= ?'.format(
            self.table_name
        )
        self.__flush_db_statement = 'DROP TABLE "{}"'.format(self.table_name)

        self.__connection: sqlite3.Connection = self.__connect()

    def request(self, request, key: str = None, value=None):
        return self.__workers.submit(self.procces_request, request, key, value)

    def procces_request(self, request, key: str = None, value=None):
        if not self.is_running:
            raise RuntimeError("Database is closed")

        logger.debug("Request={}, key={}".format(request, key))

        if request == REQUEST.GET:
            return self.__get(key)
        elif request == REQUEST.SET:
            return self.__set(key, value)
        elif request == REQUEST.SETEX:
            return self.__setex(key, value)
        elif request == REQUEST.DELETE:
            return self.__delete(key)
        elif request == REQUEST.COMMIT:
            return self.__commit()
        elif request == REQUEST.EXISTS:
            return self.__exists(key)
        elif request == REQUEST.TTL:
            return self.__ttl(key)
        elif request == REQUEST.EXPIRE:
            return self.__expire(key, value)
        elif request == REQUEST.RENAME:
            return self.__rename(key, value)
        elif request == REQUEST.KEYS:
            return self.__keys(value)
        elif request == REQUEST.CLEAN_EX:
            return self.__clean_ex()
        elif request == REQUEST.FLUSH_DB:
            return self.__flush_db()
        elif request == REQUEST.CLOSE:
            return self.__close(value)
        else:
            raise ValueError("Unknown request {}".format(request))

    def __connect(self):
        try:
            if self.autocommit:
                connection = sqlite3.connect(
                    self.database, isolation_level=None, check_same_thread=False
                )
            else:
                connection = sqlite3.connect(self.database, check_same_thread=False)

            # connection.row_factory = sqlite3.Row
            logger.info("Connected to {}".format(self.database))
        except Exception as e:
            logger.exception(
                "Error while opening sqlite3 for database: {}".format(self.database)
            )
            raise e

        try:
            connection.execute("PRAGMA journal_mode = {}".format(self.journal_mode))
            connection.execute("PRAGMA synchronous = {}".format(self.synchronous))
        except Exception as e:
            logger.exception("Error while executing PRAGMA statement")
            raise e

        try:
            self.__check_table(connection)
        except Exception as e:
            logger.exception("Error while checking table")
            raise e

        return connection

    def __get(self, key: str):
        try:
            query = self.__connection.execute(
                self.__get_statement,
                (key, time()),
            ).fetchone()
            if query:
                return self.__encoder.decode(query[0])
            else:
                return None
        except Exception as e:
            logger.exception("GET command exception")
            raise e

    def __set(self, key: str, value):
        with self.__lock:
            try:
                query = self.__connection.execute(
                    self.__set_statement,
                    (key, self.__encoder.encode(value)),
                )
                if query.rowcount > 0:
                    return True
                else:
                    return False
            except Exception as e:
                logger.exception("SET command exception")
                raise e

    def __setex(self, key: str, value):
        with self.__lock:
            try:
                query = self.__connection.execute(
                    self.__setex_statement,
                    (key, self.__encoder.encode(value[0]), time() + value[1]),
                )
                if query.rowcount > 0:
                    return True
                else:
                    return False
            except Exception as e:
                logger.exception("SETEX command exception")
                raise e

    def __delete(self, key: str):
        with self.__lock:
            try:
                query = self.__connection.execute(
                    self.__delete_statement,
                    (key,),
                )
                if query.rowcount > 0:
                    return True
                else:
                    return False
            except Exception as e:
                logger.exception("DELETE command exception")
                raise e

    def __commit(self):
        with self.__lock:
            try:
                self.__connection.commit()
                return True
            except Exception as e:
                logger.exception("COMMIT command exception")
                raise e

    def __exists(self, key: str):
        try:
            query = self.__connection.execute(
                self.__exists_statement,
                (key,),
            ).fetchone()

            if query:
                return True
            else:
                return False
        except Exception as e:
            logger.exception("EXISTS command exception")
            raise e

    def __ttl(self, key: str):
        try:
            query = self.__connection.execute(
                self.__ttl_statement,
                (key, time()),
            ).fetchone()

            if query:
                return query[0] - time()
            else:
                return 0
        except Exception as e:
            logger.exception("TTL command exception")
            raise e

    def __expire(self, key: str, ttl: int):
        with self.__lock:
            try:
                query = self.__connection.execute(
                    self.__expire_statement,
                    (time() + ttl, key),
                )

                if query.rowcount > 0:
                    return True
                else:
                    return False
            except Exception as e:
                logger.exception("EXPIRE command exception")
                raise e

    def __rename(self, key: str, new_key: str):
        try:
            query = self.__connection.execute(
                self.__rename_statement,
                (new_key, key),
            )

            if query.rowcount > 0:
                return True
            else:
                return False
        except Exception as e:
            logger.exception("RENAME command exception")
            raise e

    def __keys(self, like: str):
        try:
            query = self.__connection.execute(
                self.__keys_statement,
                (like,),
            ).fetchall()
            if query:
                return query
            else:
                return None
        except Exception as e:
            logger.exception("KEYS command exception")
            raise e

    def __clean_ex(self):
        with self.__lock:
            try:
                query = self.__connection.execute(
                    self.__cleanex_statement,
                    (time(),),
                )

                return query.rowcount
            except Exception as e:
                logger.exception("CLEAN_EX command exception")
                raise e

    def __flush_db(self):
        with self.__lock:
            try:
                self.__connection.execute(self.__flush_db_statement)
                self.__connection.execute(self.__table_statement)
                return True
            except Exception as e:
                logger.exception("FLUSH_DB command exception")
                raise e

    def __close(self, optimize: bool):
        with self.__lock:
            try:
                if optimize:
                    self.__connection.execute("PRAGMA optimize")
                self.__connection.close()
                logger.info("Connection to {} closed".format(self.database))

                if version_info.minor > 8:
                    self.__workers.shutdown(False, cancel_futures=True)
                else:
                    self.__workers.shutdown(False)

                self.is_running = False
                return True
            except Exception as e:
                logger.exception("CLOSE command exception")
                raise e

    def __check_table(self, connection: sqlite3.Connection):
        try:
            table_exists = (
                connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
                    (self.table_name,),
                ).fetchone()
                is not None
            )

            if table_exists:
                query = connection.execute(
                    "PRAGMA table_info({})".format((self.table_name))
                )
                columns = [row[1] for row in query.fetchall()]

                if "expire_time" not in columns:
                    connection.execute(
                        "ALTER TABLE '{}' ADD COLUMN expire_time INTEGER DEFAULT NULL".format(
                            self.table_name
                        )
                    )
            else:
                connection.execute(self.__table_statement)

        except Exception:
            logger.exception("Check table error")
