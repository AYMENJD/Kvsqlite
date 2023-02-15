import sqlite3
import logging

from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from sys import version_info

logger = logging.getLogger(__name__)


class REQUEST:
    GET = "GET"
    SET = "SET"
    DELETE = "DELETE"
    COMMIT = "COMMIT"
    EXISTS = "EXISTS"
    RENAME = "RENAME"
    KEYS = "KEYS"
    FLUSH_DB = "FLUSH_DB"
    CLOSE = "CLOSE"


TABLE_STATEMENT = (
    'CREATE TABLE IF NOT EXISTS "{}" (k VARCHAR(4096) PRIMARY KEY, v BLOB)'
)


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
        self.__connection: sqlite3.Connection = self.__connect()
        self.__lock = Lock()

        self.is_running = True

    def request(self, request, key: str = None, value=None):
        return self.__workers.submit(self.procces_request, request, key, value)

    def procces_request(self, request, key: str = None, value=None):
        if not self.is_running:
            raise RuntimeError("Database is closed")

        logger.debug("Request={}, key={}".format(request, key))

        # TODO: Simplify request handlers

        if request == REQUEST.GET:
            try:
                query = self.__connection.execute(
                    'SELECT v FROM "{}" WHERE k = ?'.format(self.table_name),
                    (key,),
                ).fetchone()
                if query:
                    return self.__encoder.decode(query[0])
                else:
                    return None
            except Exception as e:
                logger.exception("SELECT statment error")
                raise e
        elif request == REQUEST.SET:
            with self.__lock:
                try:
                    query = self.__connection.execute(
                        'REPLACE INTO "{}" (k, v) VALUES(?,?)'.format(self.table_name),
                        (key, self.__encoder.encode(value)),
                    )
                    if query.rowcount > 0:
                        return True
                    else:
                        return False
                except Exception as e:
                    logger.exception("REPLACE INTO statment error")
                    raise e
        elif request == REQUEST.DELETE:
            with self.__lock:
                try:
                    query = self.__connection.execute(
                        'DELETE FROM "{}" WHERE k = ?'.format(self.table_name),
                        (key,),
                    )
                    if query.rowcount > 0:
                        return True
                    else:
                        return False
                except Exception as e:
                    logger.exception("DELETE statment error")
                    raise e
        elif request == REQUEST.COMMIT:
            try:
                self.__connection.commit()
                return True
            except Exception as e:
                logger.exception("COMMIT error")
                raise e
        elif request == REQUEST.EXISTS:
            try:
                query = self.__connection.execute(
                    'SELECT k FROM "{}" WHERE k = ?'.format(self.table_name),
                    (key,),
                ).fetchone()

                if query:
                    return True
                else:
                    return False
            except Exception as e:
                logger.exception("EXISTS error")
                raise e
        elif request == REQUEST.RENAME:
            try:
                query = self.__connection.execute(
                    'UPDATE OR IGNORE "{}" SET k = ? WHERE k = ?'.format(
                        self.table_name
                    ),
                    (value, key),
                )

                if query.rowcount > 0:
                    return True
                else:
                    return False
            except Exception as e:
                logger.exception("RENAME KEY error")
                raise e
        elif request == REQUEST.KEYS:
            try:
                query = self.__connection.execute(
                    'SELECT k FROM "{}" WHERE k LIKE ? ORDER BY rowid'.format(
                        self.table_name
                    ),
                    (value,),
                ).fetchall()
                if query:
                    return query
                else:
                    return None
            except Exception as e:
                logger.exception("SELECT KEYS statment error")
                raise e
        elif request == REQUEST.FLUSH_DB:
            with self.__lock:
                try:
                    self.__connection.execute('DROP TABLE "{}"'.format(self.table_name))
                    self.__connection.execute(TABLE_STATEMENT.format(self.table_name))
                    return True
                except Exception as e:
                    logger.exception("DROP TABLE statment error")
                    raise e
        elif request == REQUEST.CLOSE:
            with self.__lock:
                try:
                    if value:
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
                    logger.exception("On close error")
                    raise e

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
                "Error while opening sqlite3 self.__connection for database: {}".format(
                    self.database
                )
            )
            raise e

        try:
            connection.execute("PRAGMA journal_mode = {}".format(self.journal_mode))
            connection.execute("PRAGMA synchronous = {}".format(self.synchronous))
        except Exception as e:
            logger.exception("Error while executing PRAGMA statement")
            raise e

        try:
            connection.execute(TABLE_STATEMENT.format(self.table_name))
        except Exception as e:
            logger.exception("Error while executing CREATE TABLE statement")
            raise e

        return connection
