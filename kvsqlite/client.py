import asyncio
import logging

from typing import Any, List, Tuple, Union
from .sqlite import Sqlite, REQUEST
from .encoders import PickleEncoder
from .base import BaseClient

logger = logging.getLogger(__name__)


class Client(BaseClient):
    def __init__(
        self,
        database: str,
        table_name: str = "kvsqlite",
        autocommit: bool = True,
        journal_mode: str = "WAL",
        synchronous: str = "NORMAL",
        default_encoder=PickleEncoder,
        workers: int = 2,
        loop: asyncio.AbstractEventLoop = None,
    ):
        """Kvsqlite asynchronous client

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
                The encoder class which deal with the data sent/received by sqlite3. Defaults to :class:`kvsqlite.PickleEncoder`.

            workers (``int``, *optional*):
                The number of workers which process sqlite queries. Defaults to ``2``.

            loop (:py:class:`~asyncio.AbstractEventLoop`, *optional*):
                Event loop. Defaults to ``None``.
        """
        assert isinstance(database, str), "database must be str"
        assert isinstance(table_name, str), "table_name must be str"
        assert isinstance(autocommit, bool), "autocommit must be bool"
        assert isinstance(journal_mode, str), "journal_mode must be str"
        assert isinstance(synchronous, str), "synchronous must be str"
        assert callable(default_encoder), "default_encoder must be callable"
        assert isinstance(workers, int), "workers must be int"
        assert workers > 0, "workers must be greater than 0"

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
        self.workers = workers
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
            self.__encoder,
            self.workers,
        )

        logger.debug("Using {} as encoder".format(default_encoder.__name__))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            await self.close()
        except Exception:
            logger.exception("Error on __aexit__")

    async def get(self, key: str) -> Any:
        assert isinstance(key, str), "key must be str"

        return await self.__invoke(request=REQUEST.GET, key=key)

    async def set(self, key: str, value) -> bool:
        assert isinstance(key, str), "key must be str"

        future = self.__invoke(request=REQUEST.SET, key=key, value=value)
        return await future

    async def setex(self, key: str, ttl: int, value) -> bool:
        assert isinstance(key, str), "key must be str"
        assert ttl >= 1, "ttl must be greater than 1"

        future = self.__invoke(request=REQUEST.SETEX, key=key, value=[value, ttl])
        return await future

    async def delete(self, key: str) -> bool:
        assert isinstance(key, str), "key must be str"

        future = self.__invoke(request=REQUEST.DELETE, key=key)
        return await future

    async def commit(self) -> bool:
        future = self.__invoke(request=REQUEST.COMMIT)
        return await future

    async def exists(self, key: str) -> bool:
        assert isinstance(key, str), "key must be str"

        future = self.__invoke(request=REQUEST.EXISTS, key=key)
        return await future

    async def ttl(self, key: str) -> float:
        assert isinstance(key, str), "key must be str"

        future = self.__invoke(request=REQUEST.TTL, key=key)
        return await future

    async def expire(self, key: str, ttl: int) -> bool:
        assert isinstance(key, str), "key must be str"
        assert ttl >= 1, "ttl must be greater than 1"

        future = self.__invoke(request=REQUEST.EXPIRE, key=key, value=ttl)
        return await future

    async def rename(self, key: str, new_key: str) -> bool:
        assert isinstance(key, str), "key must be str"
        assert isinstance(new_key, str), "new_key must be str"

        future = self.__invoke(request=REQUEST.RENAME, key=key, value=new_key)
        return await future

    async def keys(self, like: str = "%") -> Union[List[Tuple[str]], None]:
        assert isinstance(like, str), "like must be str"

        future = self.__invoke(request=REQUEST.KEYS, value=like)
        return await future

    async def cleanex(self) -> int:
        future = self.__invoke(request=REQUEST.CLEAN_EX)
        return await future

    async def flush(self) -> bool:
        future = self.__invoke(request=REQUEST.FLUSH_DB)
        return await future

    async def close(self, optimize_database: bool = True) -> bool:
        assert isinstance(optimize_database, bool), "optimize_database must be bool"

        future = self.__invoke(request=REQUEST.CLOSE, value=optimize_database)
        return await future

    def __invoke(self, request, key=None, value=None):
        assert self.__sqlite.is_running, "Database is closed"

        future = self.__sqlite.request(request, key, value)
        return asyncio.wrap_future(future, loop=self.loop)
