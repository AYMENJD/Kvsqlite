import asyncio
import inspect
import sqlite3
from contextlib import asynccontextmanager

import kvsqlite
import pytest
from kvsqlite.encoders import StringEncoder
from kvsqlite.sync import Client as SyncClient


async def call(value):
    if inspect.isawaitable(value):
        return await value
    return value


@asynccontextmanager
async def open_db(kind, path=":memory:", **kwargs):
    if kind == "async":
        async with kvsqlite.Client(path, **kwargs) as db:
            yield db
    else:
        with SyncClient(path, **kwargs) as db:
            yield db


@pytest.fixture(params=["async", "sync"])
def kind(request):
    return request.param


class TestKV:
    async def test_set_get_delete(self, kind):
        async with open_db(kind) as db:
            assert await call(db.set("a", {"n": 1})) is True
            assert await call(db.get("a")) == {"n": 1}
            assert await call(db.exists("a")) is True
            assert await call(db.delete("a")) is True
            assert await call(db.get("a")) is None
            assert await call(db.exists("a")) is False
            assert await call(db.delete("missing")) is False

    async def test_overwrite(self, kind):
        async with open_db(kind) as db:
            await call(db.set("k", "first"))
            await call(db.set("k", "second"))
            assert await call(db.get("k")) == "second"

    async def test_keys_rename_flush(self, kind):
        async with open_db(kind) as db:
            await call(db.set("user:1", 1))
            await call(db.set("user:2", 2))
            await call(db.set("other", 3))
            keys = sorted(row[0] for row in await call(db.keys("user:%")))
            assert keys == ["user:1", "user:2"]
            assert await call(db.rename("user:1", "user:9")) is True
            assert await call(db.get("user:9")) == 1
            assert await call(db.get("user:1")) is None
            assert await call(db.flush()) is True
            assert await call(db.keys()) is None

    async def test_setex_ttl(self, kind):
        async with open_db(kind) as db:
            assert await call(db.setex("tmp", 30, "v")) is True
            ttl = await call(db.ttl("tmp"))
            assert 0 < ttl <= 30
            assert await call(db.get("tmp")) == "v"
            assert await call(db.expire("tmp", 60)) is True
            assert await call(db.ttl("tmp")) > 30

    async def test_expired_keys_are_invisible(self, kind):
        async with open_db(kind) as db:
            await call(db.setex("gone", 1, "x"))
            await asyncio.sleep(1.05)
            assert await call(db.get("gone")) is None
            assert await call(db.exists("gone")) is False
            assert await call(db.ttl("gone")) == 0
            assert await call(db.keys()) is None
            assert await call(db.cleanex()) >= 1


class TestConcurrency:
    async def test_concurrent_get(self):
        async with kvsqlite.Client(":memory:", workers=4) as db:
            for i in range(50):
                await db.set("k%d" % i, "v%d" % i)
            results = await asyncio.gather(
                *[db.get("k%d" % (i % 50)) for i in range(400)],
                return_exceptions=True,
            )
        assert [r for r in results if isinstance(r, Exception)] == []
        assert results == ["v%d" % (i % 50) for i in range(400)]

    async def test_concurrent_set(self):
        async with kvsqlite.Client(":memory:", workers=4) as db:
            results = await asyncio.gather(
                *[db.set("k%d" % i, i) for i in range(200)],
                return_exceptions=True,
            )
            assert [r for r in results if isinstance(r, Exception)] == []
            assert all(r is True for r in results)
            assert await db.get("k0") == 0
            assert await db.get("k199") == 199


class TestIsolation:
    async def test_memory_clients_do_not_share_data(self):
        async with kvsqlite.Client(":memory:") as a:
            async with kvsqlite.Client(":memory:") as b:
                await a.set("k", "a")
                await b.set("k", "b")
                assert await a.get("k") == "a"
                assert await b.get("k") == "b"

    async def test_reopen_persists(self, tmp_path):
        path = str(tmp_path / "kv.sqlite")
        async with kvsqlite.Client(path) as db:
            await db.set("k", "v")
        async with kvsqlite.Client(path) as db:
            assert await db.get("k") == "v"

    async def test_autocommit_false_survives_reopen(self, tmp_path):
        path = str(tmp_path / "kv.sqlite")
        async with kvsqlite.Client(path, autocommit=False) as db:
            assert await db.set("k", "v") is True
            assert await db.commit() is True
        async with kvsqlite.Client(path) as db:
            assert await db.get("k") == "v"


class TestCompat:
    async def test_legacy_file_without_expire_column(self, tmp_path):
        path = str(tmp_path / "old.sqlite")
        conn = sqlite3.connect(path)
        conn.execute(
            "CREATE TABLE kvsqlite (k VARCHAR(4096) PRIMARY KEY, v BLOB) WITHOUT ROWID"
        )
        conn.execute(
            "INSERT INTO kvsqlite (k, v) VALUES (?, ?)",
            ("old", kvsqlite.PickleEncoder().encode("kept")),
        )
        conn.commit()
        conn.close()

        async with kvsqlite.Client(path) as db:
            assert await db.get("old") == "kept"
            assert await db.setex("n", 60, "x") is True
            assert await db.get("n") == "x"

    async def test_string_encoder(self, kind):
        async with open_db(kind, default_encoder=StringEncoder) as db:
            assert await call(db.set("k", "hello")) is True
            assert await call(db.get("k")) == "hello"

    async def test_init_without_running_loop(self, tmp_path):
        db = kvsqlite.Client(str(tmp_path / "kv.sqlite"))
        assert db.loop is None
        assert await db.set("k", 1) is True
        assert db.loop is not None
        assert await db.get("k") == 1
        await db.close()

    async def test_explicit_loop(self, tmp_path):
        loop = asyncio.get_running_loop()
        db = kvsqlite.Client(str(tmp_path / "kv.sqlite"), loop=loop)
        assert db.loop is loop
        try:
            assert await db.set("k", 1) is True
            assert await db.get("k") == 1
        finally:
            await db.close()

    def test_bad_pragma(self):
        with pytest.raises(ValueError):
            kvsqlite.Client(":memory:", journal_mode="NOPE")
        with pytest.raises(ValueError):
            kvsqlite.Client(":memory:", synchronous="NOPE")
