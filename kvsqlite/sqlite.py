import logging
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from sys import version_info
from threading import Lock, local
from time import time
from uuid import uuid4

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = 1
_BUSY_TIMEOUT_MS = 5000
_JOURNAL_MODES = frozenset(("WAL", "DELETE", "TRUNCATE", "PERSIST", "MEMORY", "OFF"))
_SYNCHRONOUS = frozenset(("OFF", "NORMAL", "FULL", "EXTRA"))


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


def _quote_ident(name):
    return '"' + name.replace('"', '""') + '"'


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
        if journal_mode.upper() not in _JOURNAL_MODES:
            raise ValueError("invalid journal_mode {}".format(journal_mode))
        if synchronous.upper() not in _SYNCHRONOUS:
            raise ValueError("invalid synchronous {}".format(synchronous))

        self.database = database
        self.table_name = table_name
        self.autocommit = autocommit
        self.journal_mode = journal_mode
        self.synchronous = synchronous
        self.__encoder = encoder
        self.__workers = ThreadPoolExecutor(workers, "kvsqlite")
        self.__lock = Lock()
        self.__local = local()
        self.__connections = []
        self.__shared = None
        self.__keepalive = None
        self.__dsn, self.__uri = self.__resolve_dsn(database)
        self.is_running = True

        quoted = _quote_ident(self.table_name)
        expire_index = _quote_ident("idx_{}_expire".format(self.table_name))

        self.__table_statement = (
            "CREATE TABLE IF NOT EXISTS {} (k VARCHAR(4096) PRIMARY KEY, "
            "v BLOB, expire_time INTEGER DEFAULT NULL) WITHOUT ROWID".format(quoted)
        )
        self.__expire_index_statement = (
            "CREATE INDEX IF NOT EXISTS {} ON {} (expire_time) "
            "WHERE expire_time IS NOT NULL".format(expire_index, quoted)
        )
        self.__get_statement = (
            "SELECT v FROM {} WHERE k = ? AND "
            "(expire_time IS NULL OR expire_time > ?) LIMIT 1".format(quoted)
        )
        self.__set_statement = (
            "REPLACE INTO {} (k, v, expire_time) VALUES(?,?,NULL)".format(quoted)
        )
        self.__setex_statement = (
            "REPLACE INTO {} (k, v, expire_time) VALUES(?,?,?)".format(quoted)
        )
        self.__delete_statement = "DELETE FROM {} WHERE k = ?".format(quoted)
        self.__exists_statement = (
            "SELECT EXISTS (SELECT 1 FROM {} WHERE k = ? AND "
            "(expire_time IS NULL OR expire_time > ?) LIMIT 1)".format(quoted)
        )
        self.__ttl_statement = (
            "SELECT expire_time FROM {} WHERE k = ? AND expire_time > ? LIMIT 1".format(
                quoted
            )
        )
        self.__expire_statement = "UPDATE {} SET expire_time = ? WHERE k = ?".format(
            quoted
        )
        self.__rename_statement = "UPDATE OR IGNORE {} SET k = ? WHERE k = ?".format(
            quoted
        )
        self.__keys_statement = (
            "SELECT k FROM {} WHERE k LIKE ? AND "
            "(expire_time IS NULL OR expire_time > ?)".format(quoted)
        )
        self.__cleanex_statement = (
            "DELETE FROM {} WHERE expire_time IS NOT NULL AND expire_time <= ?".format(
                quoted
            )
        )
        self.__flush_db_statement = "DROP TABLE IF EXISTS {}".format(quoted)
        self.__table_info_statement = "PRAGMA table_info({})".format(quoted)

        bootstrap = self.__open_connection()
        self.__migrate(bootstrap)
        self.__connections.append(bootstrap)
        if self.autocommit:
            self.__keepalive = bootstrap
        else:
            self.__shared = bootstrap

    def request(self, request, key: str = None, value=None):
        return self.__workers.submit(self.procces_request, request, key, value)

    def procces_request(self, request, key: str = None, value=None):
        if not self.is_running:
            raise RuntimeError("Database is closed")

        logger.debug("Request=%s, key=%s", request, key)

        if self.__shared is not None or request in (
            REQUEST.CLOSE,
            REQUEST.FLUSH_DB,
        ):
            with self.__lock:
                if not self.is_running and request != REQUEST.CLOSE:
                    raise RuntimeError("Database is closed")
                return self.__dispatch(request, key, value)
        return self.__dispatch(request, key, value)

    def __dispatch(self, request, key, value):
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

    def __resolve_dsn(self, database):
        if database == ":memory:":
            return (
                "file:kvsqlite_{}?mode=memory&cache=shared".format(uuid4().hex),
                True,
            )
        if database.startswith("file:"):
            return database, True
        return database, False

    def __open_connection(self):
        try:
            kwargs = {
                "check_same_thread": False,
                "timeout": _BUSY_TIMEOUT_MS / 1000.0,
                "uri": self.__uri,
            }
            if self.autocommit:
                kwargs["isolation_level"] = None
            connection = sqlite3.connect(self.__dsn, **kwargs)
            logger.info("Connected to {}".format(self.database))
        except Exception as e:
            logger.exception(
                "Error while opening sqlite3 for database: {}".format(self.database)
            )
            raise e

        try:
            connection.execute("PRAGMA journal_mode = {}".format(self.journal_mode))
            connection.execute("PRAGMA synchronous = {}".format(self.synchronous))
            connection.execute("PRAGMA busy_timeout = {}".format(_BUSY_TIMEOUT_MS))
            connection.execute("PRAGMA temp_store = MEMORY")
        except Exception as e:
            logger.exception("Error while executing PRAGMA statement")
            connection.close()
            raise e

        return connection

    def __conn(self):
        if self.__shared is not None:
            return self.__shared
        conn = getattr(self.__local, "conn", None)
        if conn is None:
            conn = self.__open_connection()
            with self.__lock:
                if not self.is_running:
                    conn.close()
                    raise RuntimeError("Database is closed")
                self.__local.conn = conn
                self.__connections.append(conn)
        return conn

    def __migrate(self, connection):
        try:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version >= CURRENT_SCHEMA_VERSION:
                return
            self.__migrate_to_v1(connection)
            connection.execute(
                "PRAGMA user_version = {}".format(CURRENT_SCHEMA_VERSION)
            )
        except Exception:
            logger.exception("Error while checking table")
            raise

    def __migrate_to_v1(self, connection):
        table_exists = (
            connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name = ?",
                (self.table_name,),
            ).fetchone()
            is not None
        )

        if table_exists:
            columns = [
                row[1]
                for row in connection.execute(self.__table_info_statement).fetchall()
            ]
            if "expire_time" not in columns:
                connection.execute(
                    "ALTER TABLE {} ADD COLUMN expire_time INTEGER DEFAULT NULL".format(
                        _quote_ident(self.table_name)
                    )
                )
        else:
            connection.execute(self.__table_statement)

        connection.execute(self.__expire_index_statement)

    def __get(self, key: str):
        try:
            query = (
                self.__conn()
                .execute(
                    self.__get_statement,
                    (key, time()),
                )
                .fetchone()
            )
            if query:
                return self.__encoder.decode(query[0])
            else:
                return None
        except Exception as e:
            logger.exception("GET command exception")
            raise e

    def __set(self, key: str, value):
        try:
            query = self.__conn().execute(
                self.__set_statement,
                (key, self.__encoder.encode(value)),
            )
            return query.rowcount > 0
        except Exception as e:
            logger.exception("SET command exception")
            raise e

    def __setex(self, key: str, value):
        try:
            query = self.__conn().execute(
                self.__setex_statement,
                (key, self.__encoder.encode(value[0]), time() + value[1]),
            )
            return query.rowcount > 0
        except Exception as e:
            logger.exception("SETEX command exception")
            raise e

    def __delete(self, key: str):
        try:
            query = self.__conn().execute(
                self.__delete_statement,
                (key,),
            )
            return query.rowcount > 0
        except Exception as e:
            logger.exception("DELETE command exception")
            raise e

    def __commit(self):
        try:
            self.__conn().commit()
            return True
        except Exception as e:
            logger.exception("COMMIT command exception")
            raise e

    def __exists(self, key: str):
        try:
            query = (
                self.__conn()
                .execute(
                    self.__exists_statement,
                    (key, time()),
                )
                .fetchone()
            )
            return bool(query[0])
        except Exception as e:
            logger.exception("EXISTS command exception")
            raise e

    def __ttl(self, key: str):
        try:
            query = (
                self.__conn()
                .execute(
                    self.__ttl_statement,
                    (key, time()),
                )
                .fetchone()
            )
            if query:
                return query[0] - time()
            else:
                return 0
        except Exception as e:
            logger.exception("TTL command exception")
            raise e

    def __expire(self, key: str, ttl: int):
        try:
            query = self.__conn().execute(
                self.__expire_statement,
                (time() + ttl, key),
            )
            return query.rowcount > 0
        except Exception as e:
            logger.exception("EXPIRE command exception")
            raise e

    def __rename(self, key: str, new_key: str):
        try:
            query = self.__conn().execute(
                self.__rename_statement,
                (new_key, key),
            )
            return query.rowcount > 0
        except Exception as e:
            logger.exception("RENAME command exception")
            raise e

    def __keys(self, like: str):
        try:
            query = (
                self.__conn()
                .execute(
                    self.__keys_statement,
                    (like, time()),
                )
                .fetchall()
            )
            if query:
                return query
            else:
                return None
        except Exception as e:
            logger.exception("KEYS command exception")
            raise e

    def __clean_ex(self):
        try:
            query = self.__conn().execute(
                self.__cleanex_statement,
                (time(),),
            )
            return query.rowcount
        except Exception as e:
            logger.exception("CLEAN_EX command exception")
            raise e

    def __flush_db(self):
        try:
            conn = self.__conn()
            conn.execute(self.__flush_db_statement)
            conn.execute(self.__table_statement)
            conn.execute(self.__expire_index_statement)
            return True
        except Exception as e:
            logger.exception("FLUSH_DB command exception")
            raise e

    def __close(self, optimize: bool):
        try:
            self.is_running = False
            conns = list(self.__connections)
            if optimize and conns:
                try:
                    conns[0].execute("PRAGMA optimize")
                except Exception:
                    logger.exception("PRAGMA optimize failed")
            for connection in conns:
                try:
                    connection.close()
                except Exception:
                    logger.exception("Error closing sqlite3 connection")
            self.__connections = []
            self.__shared = None
            self.__keepalive = None
            logger.info("Connection to {} closed".format(self.database))

            if (version_info.major, version_info.minor) >= (3, 9):
                self.__workers.shutdown(False, cancel_futures=True)
            else:
                self.__workers.shutdown(False)
            return True
        except Exception as e:
            logger.exception("CLOSE command exception")
            raise e
