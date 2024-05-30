
Welcome to Kvsqlite
===================

**Kvsqlite** is easy, sample and powerful key-value database backed by sqlite3.

Features
--------

- Fast and easy-to-use database.
- Simultaneously **asynchronous** or **synchronous** calls.
- Store any data supported by `pickle <https://docs.python.org/3/library/pickle.html>`_

Installation
------------
.. code-block:: bash

   pip install kvsqlite


From github (dev version)

.. code-block:: bash

   pip install git+https://github.com/AYMENJD/Kvsqlite


Usage
-----

.. code-block:: python

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
         else:
               print("Key not found", result)

         await db.close()

   asyncio.run(main())

Tests
-----

**Kvsqlite** tests available at ``test/``, which you can run it by:

.. code-block:: bash

   python3 -m pytest test/ -v

.. note::

   Make sure that ``pytest`` and ``pytest-asyncio`` is installed.

Benchmarking
------------

**Kvsqlite** benchmarking available at ``benchmark/``, which you can run it by:

.. code-block:: bash

   python3 benchmark/benchmark_kvsqlite.py --query-count 100000


.. note::

   Make sure that ``psutil`` is installed.
