import asyncio
import pytest
import random
import string
import kvsqlite

pytest_plugins = ("pytest_asyncio",)


def random_string(length):
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


@pytest.mark.asyncio
async def test_key_value():
    keys = []
    values = []

    for _ in range(100):
        keys.append(random_string(random.randint(1, 20)))

    for _ in range(100):
        values.append(random_string(random.randint(1, 20)))

    async with kvsqlite.Client("test_kvsqlite.sqlite") as db:
        queries_n = 100000
        queries = []
        for _ in range(queries_n):
            op = random.randint(0, 2)
            key = random.choice(keys)
            value = random.choice(values)
            if op == 0:
                q = db.get(key)
            elif op == 1:
                q = db.delete(key)
            elif op == 2:
                q = db.set(key, value)
            queries.append((op, q))

        for op, query in queries:
            result = await query
            if op == 2:
                assert result
            elif op == 1:
                assert isinstance(result, bool)

        await db.flush()


@pytest.mark.asyncio
async def test_in_memory_key_value():
    keys = []
    values = []

    for _ in range(100):
        keys.append(random_string(random.randint(1, 20)))

    for _ in range(100):
        values.append(random_string(random.randint(1, 20)))

    async with kvsqlite.Client(":memory:") as db:
        queries_n = 100000
        queries = []
        for _ in range(queries_n):
            op = random.randint(0, 2)
            key = random.choice(keys)
            value = random.choice(values)
            if op == 0:
                q = db.get(key=key)
            elif op == 1:
                q = db.delete(key=key)
            elif op == 2:
                q = db.set(key=key, value=value)
            queries.append((op, q))

        for op, query in queries:
            result = await query
            if op == 2:
                assert result == True
            elif op == 1:
                assert isinstance(result, bool) == True

        await db.flush()


@pytest.mark.asyncio
async def test_concurrent_get():

    async with kvsqlite.Client("test_kvsqlite.sqlite", workers=5) as db:
        keys = []

        for _ in range(100):
            key = random_string(random.randint(1, 20))
            keys.append(key)
            await db.set(key=key, value=random_string(random.randint(1, 20)))

        futures = await asyncio.gather(
            *[db.get(random.choice(keys)) for _ in range(100000)]
        )

        for result in futures:
            assert isinstance(result, str) == True

        await db.flush()


@pytest.mark.asyncio
async def test_in_memory_concurrent_get():

    async with kvsqlite.Client(":memory:") as db:
        keys = []

        for _ in range(100):
            key = random_string(random.randint(1, 20))
            keys.append(key)
            await db.set(key=key, value=random_string(random.randint(1, 20)))

        futures = await asyncio.gather(
            *[db.get(random.choice(keys)) for _ in range(100000)]
        )

        for result in futures:
            assert isinstance(result, str) == True

        await db.flush()


@pytest.mark.asyncio
async def test_concurrent_set():

    async with kvsqlite.Client("test_kvsqlite.sqlite", workers=5) as db:

        futures = await asyncio.gather(
            *[
                db.set(
                    random_string(random.randint(1, 20)),
                    random_string(random.randint(1, 20)),
                )
                for _ in range(100000)
            ]
        )

        for result in futures:
            assert result == True

        await db.flush()


@pytest.mark.asyncio
async def test_in_memory_concurrent_set():

    async with kvsqlite.Client(":memory:") as db:

        futures = await asyncio.gather(
            *[
                db.set(
                    random_string(random.randint(1, 20)),
                    random_string(random.randint(1, 20)),
                )
                for _ in range(100000)
            ]
        )

        for result in futures:
            assert result == True

        await db.flush()


@pytest.mark.asyncio
async def test_key_exists():

    async with kvsqlite.Client("test_kvsqlite.sqlite") as db:
        keys = []

        for _ in range(10000):
            key = random_string(random.randint(1, 20))
            keys.append(key)
            assert (
                await db.set(key=key, value=random_string(random.randint(1, 20)))
                == True
            )

        for key in keys:
            result = await db.exists(key)
            assert result == True
