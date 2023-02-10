import asyncio
import logging

from pickle import dumps, loads, HIGHEST_PROTOCOL
from concurrent.futures import Future
from sqlite3 import Binary
from .sqlite import Sqlite, REQUEST


class PickleEncoder:
    """Encoder which uses pickle to serialize/deserialize the object"""

    def __init__(self) -> None:
        pass

    def encode(self, obj):
        return Binary(dumps(obj, protocol=HIGHEST_PROTOCOL))

    def decode(self, obj):
        return loads(bytes(obj))


class StringEncoder:
    """This encoder can be used instead of :class:`PickleEncoder`. This encoder accpets :py:class:`str` only"""

    def __init__(self) -> None:
        pass

    def encode(self, text):
        assert isinstance(text, str), "text is not str"
        return Binary(text.encode("utf-8"))

    def decode(self, text):
        assert isinstance(text, str), "text is not str"
        return text


logger = logging.getLogger(__name__)


class Client:
    def __init__(
        self,
        database: str,
        table_name: str = "kvsqlite",
        autocommit: bool = True,
        journal_mode: str = "WAL",
        synchronous: str = "NORMAL",
        default_encoder=PickleEncoder,
        loop: asyncio.AbstractEventLoop = None,
    ):
        """Kvsqlite client

        Args:
            database (``str``):
                Sqlite3 database path.

            table_name (``str``, *optional*):
                Table name to use, will be created if not exists. Defaults to ``kvsqlite``.

            autocommit (``bool``, *optional*):
                Whether `autocommit` database changes or not. Defaults to ``True``.

            journal_mode (``str``, *optional*):
                See https://www.sqlite.org/pragma.html#pragma_journal_mode. Defaults to ``WAL``.

            synchronous (``str``, *optional*):
                See https://www.sqlite.org/pragma.html#pragma_synchronous. Defaults to ``NORMAL``.

            default_encoder (``Callable``, *optional*):
                The encoder class which deal with the data sent/received by sqlite3. Defaults to :class:`PickleEncoder`.

            loop (:py:class:`~asyncio.AbstractEventLoop`, *optional*):
                Event loop. Defaults to ``None``.
        """
        assert isinstance(database, str), "database must be str"
        assert isinstance(table_name, str), "table_name must be str"
        assert isinstance(autocommit, bool), "autocommit must be bool"
        assert isinstance(journal_mode, str), "journal_mode must be str"
        assert isinstance(synchronous, str), "synchronous must be str"
        assert callable(default_encoder), "default_encoder must be callable"
        assert hasattr(
            default_encoder, "encode"
        ), "{} must have an 'encode' function".format(default_encoder.__name__)
        assert hasattr(
            default_encoder, "decode"
        ), "{} must have an 'decode' function".format(default_encoder.__name__)

        self.database = database
        self.table_name = table_name
        self.autocommit = autocommit
        self.journal_mode = journal_mode
        self.synchronous = synchronous
        self.__encoder = default_encoder()
        self.loop = (
            loop
            if isinstance(loop, asyncio.AbstractEventLoop)
            else asyncio.get_event_loop()
        )

        self.__sqlite = Sqlite(
            self.database,
            self.table_name,
            self.autocommit,
            self.journal_mode,
            self.synchronous,
        )

        logger.debug("Using {} as encoder".format(default_encoder.__name__))
        logger.info("Connected to {}".format(self.database))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            await self.close()
        except Exception:
            pass

    async def get(self, key: str):
        """Get the value of `key`

        Args:
            key (``str``):
                The key to get.
        """
        assert isinstance(key, str), "key must be str"

        future = await self.__invoke(request=REQUEST.GET, key=key)

        if future:
            return self.__encoder.decode(future)

    async def set(self, key: str, value):
        """Get the value of `key`

        Args:
            key (``str``):
                The key.

            value (``Any``):
                The value to set for `key`.
        """
        assert isinstance(key, str), "key must be str"
        value_encoded = self.__encoder.encode(value)

        future = self.__invoke(request=REQUEST.SET, key=key, value=value_encoded)
        return await future

    async def delete(self, key: str):
        """Delete `key` from database

        Args:
            key (``str``):
                The key to get.
        """
        assert isinstance(key, str), "key must be str"

        future = self.__invoke(request=REQUEST.DELETE, key=key)
        return await future

    async def commit(self):
        """Commit the current changes

        Returns:
            :py:class:`bool`: ``True`` on success.
        """
        future = self.__invoke(request=REQUEST.COMMIT)
        return await future

    async def exists(self, key: str):
        """Check if `key` already exists in database

        Args:
            key (``str``):
                The key to search for.

        Returns:
            :py:class:`bool`: ``True`` if found, otherwise ``False``.
        """
        assert isinstance(key, str), "key must be str"

        future = self.__invoke(request=REQUEST.EXISTS, key=key)
        return await future

    async def keys(self):
        """Return list of keys in database"""
        future = self.__invoke(request=REQUEST.KEYS)
        return await future

    async def flush(self):
        """Flush the current database"""

        future = self.__invoke(request=REQUEST.FLUSH_DB)
        return await future

    async def close(self, optimize_database: bool = True):
        """Close database

        Args:
            optimize_database (``bool``, **optional**):
                Whether optimize database before closing or not. Defaults to ``True``.
        """
        assert isinstance(optimize_database, bool), "optimize_database must be bool"

        future = self.__invoke(request=REQUEST.CLOSE, value=optimize_database)
        return await future

    def __invoke(self, request, key=None, value=None):
        assert self.__sqlite.is_alive(), "Database is closed"

        future = Future()
        self.__sqlite.queue.put_nowait((request, key, value, future))
        return asyncio.wrap_future(future, loop=self.loop)
