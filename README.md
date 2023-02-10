# Kvsqlite [![version](https://img.shields.io/pypi/v/Kvsqlite?style=flat&logo=pypi)](https://pypi.org/project/Kvsqlite) [![downloads](https://static.pepy.tech/personalized-badge/Kvsqlite?period=total&units=none&left_color=black&right_color=orange&left_text=Downloads)](https://pepy.tech/project/Kvsqlite)
Easy, Sample and powerful key-value database backed by sqlite3.

### Requirements

- Python3.8+

### Installation

```bash
pip install kvsqlite
```
From github (dev version)
```bash
pip install git+https://github.com/AYEMNJD/Kvsqlite
```

### Usage

```python
import kvsqlite, asyncio

async def main():
    async with kvsqlite.Client("kv.sqlite") as db:

        key = "123-456-789"
        result = await db.set(key, "Hello world. Bye!")

        if await db.exists(key):
            get_key = await db.get(key)

            print(get_key) # Hello world. Bye!

            await db.delete(key)
        else:
            print("Key not found", result)

        await db.close()

asyncio.run(main())
```

Check all available methods at https://kvsqlite.rtfd.io/en/latest/API.html.
