# Kvsqlite [![version](https://img.shields.io/pypi/v/Kvsqlite?style=flat&logo=pypi)](https://pypi.org/project/Kvsqlite) [![Downloads](https://static.pepy.tech/personalized-badge/Kvsqlite?period=month&units=none&left_color=grey&right_color=brightgreen&left_text=Downloads)](https://pepy.tech/project/Kvsqlite)
Easy, Sample and powerful key-value database backed by sqlite3.

### Features

- Fast and easy-to-use database
- Simultaneously **asynchronous** or **synchronous** calls
- Store any data supported by [**pickle**](https://docs.python.org/3/library/pickle.html)

### Requirements

- Python3.8+

### Installation

```bash
pip install kvsqlite
```
From github (dev version)
```bash
pip install git+https://github.com/AYMENJD/Kvsqlite
```

### Documentation

[Kvsqlite](https://github.com/AYMENJD/Kvsqlite) documentation available at [kvsqlite.rtfd.io](https://kvsqlite.rtfd.io/).

### Usage

```python
from kvsqlite import Client # For sync version do: from kvsqlite.sync import Client
import asyncio

async def main():
    async with Client("kv.sqlite") as db:

        key = "123-456-789"
        result = await db.set(key, "Hello world. Bye!")

        if await db.exists(key):
            get_key = await db.get(key)

            print(get_key) # Hello world. Bye!

            await db.delete(key)

            await db.setex(key, "This key has a lifetime of 60 seconds", 60)

            print(await db.get(key))
        else:
            print("Key not found", result)


asyncio.run(main())
```
