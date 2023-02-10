import sqlite3
import logging

from threading import Thread
from queue import Queue

logger = logging.getLogger(__name__)


class REQUEST:
    GET = "get"
    SET = "set"
    DELETE = "delete"
    COMMIT = "commit"
    EXISTS = "exists"
    KEYS = "keys"
    EXECUTE = "execute"
    FLUSH_DB = "FLUSH_DB"
    CLOSE = "close"


TABLE_STATEMENT = 'CREATE TABLE IF NOT EXISTS "{}" (k TEXT PRIMARY KEY, v BLOB)'


class Sqlite(Thread):
    def __init__(
        self,
        database: str,
        table_name: str,
        autocommit: bool,
        journal_mode: str,
        synchronous: str,
    ) -> None:
        assert isinstance(database, str), "database must be str"
        assert isinstance(table_name, str), "table_name must be str"
        assert isinstance(autocommit, bool), "autocommit must be bool"
        assert isinstance(journal_mode, str), "journal_mode must be str"
        assert isinstance(synchronous, str), "synchronous must be str"

        super(Sqlite, self).__init__()

        self.database = database
        self.table_name = table_name
        self.autocommit = autocommit
        self.journal_mode = journal_mode
        self.synchronous = synchronous

        self.queue = Queue()
        self.daemon = True

        self.start()

    def run(self):
        connection = self.__connect()

        while True:
            request, key, value, future = self.queue.get()
            logger.debug("Request={}, key={}".format(request, key))

            if request == REQUEST.GET:
                try:
                    query = connection.execute(
                        'SELECT v FROM "{}" WHERE k = ?'.format(self.table_name),
                        (key,),
                    ).fetchone()
                    if query:
                        future.set_result(query[0])
                    else:
                        future.set_result(None)
                except Exception as e:
                    logger.exception("SELECT statment error")
                    future.set_exception(e)
            elif request == REQUEST.SET:
                try:
                    query = connection.execute(
                        'REPLACE INTO "{}" (k, v) VALUES(?,?)'.format(self.table_name),
                        (key, value),
                    )
                    if query.rowcount > 0:
                        future.set_result(True)
                    else:
                        future.set_result(False)
                except Exception as e:
                    logger.exception("REPLACE INTO statment error")
                    future.set_exception(e)
            elif request == REQUEST.DELETE:
                try:
                    query = connection.execute(
                        'DELETE FROM "{}" WHERE k = ?'.format(self.table_name),
                        (key,),
                    )
                    if query.rowcount > 0:
                        future.set_result(True)
                    else:
                        future.set_result(False)
                except Exception as e:
                    logger.exception("DELETE statment error")
                    future.set_exception(e)
            elif request == REQUEST.COMMIT:
                try:
                    connection.commit()
                    future.set_result(True)
                except Exception as e:
                    logger.exception("COMMIT error")
                    future.set_exception(e)
            elif request == REQUEST.EXISTS:
                try:
                    query = connection.execute(
                        'SELECT EXISTS(SELECT k FROM "{}" WHERE k = ?)'.format(
                            self.table_name
                        ),
                        (key,),
                    ).fetchone()

                    if query:
                        future.set_result(bool(query[0]))
                    else:
                        future.set_result(False)
                except Exception as e:
                    logger.exception("SELECT EXISTS statment error")
                    future.set_exception(e)
            elif request == REQUEST.KEYS:
                try:
                    query = connection.execute(
                        'SELECT k FROM "{}" ORDER BY rowid'.format(self.table_name)
                    ).fetchall()
                    if query:
                        future.set_result(query)
                    else:
                        future.set_result(None)
                except Exception as e:
                    logger.exception("SELECT KEYS statment error")
                    future.set_exception(e)
            elif request == REQUEST.FLUSH_DB:
                try:
                    connection.execute('DROP TABLE "{}"'.format(self.table_name))
                    connection.execute(TABLE_STATEMENT.format(self.table_name))
                    future.set_result(True)
                except Exception as e:
                    logger.exception("DROP TABLE statment error")
                    future.set_exception(e)
            elif request == REQUEST.CLOSE:
                try:
                    if value:
                        connection.execute("PRAGMA optimize")
                    connection.close()
                    logger.info("Connection to {} closed".format(self.database))
                    future.set_result(True)
                    break
                except Exception as e:
                    logger.exception("On close error")
                    future.set_exception(e)

    def __connect(self):
        try:
            if self.autocommit:
                connection = sqlite3.connect(
                    self.database, isolation_level=None, check_same_thread=False
                )
            else:
                connection = sqlite3.connect(self.database, check_same_thread=False)
        except Exception as e:
            logger.exception(
                "Error while opening sqlite3 connection for database: {}".format(
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
