import argparse
import asyncio
import os
import time

import kvsqlite

try:
    import psutil
except ImportError:
    psutil = None

ENCODERS = {
    "pickle": kvsqlite.PickleEncoder,
    "marshal": kvsqlite.MarshalEncoder,
    "string": kvsqlite.StringEncoder,
}


def parse_args():
    p = argparse.ArgumentParser(description="Benchmark kvsqlite")
    p.add_argument(
        "--query-count",
        type=int,
        default=100000,
        help="Operations per case (default 100000)",
    )
    p.add_argument(
        "--db-path",
        default="benchmark_kvsqlite.sqlite",
        help="Database path (default benchmark_kvsqlite.sqlite)",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Worker threads for the concurrent cases (default 5)",
    )
    p.add_argument(
        "--encoder",
        choices=["all"] + sorted(ENCODERS),
        default="all",
        help="Encoder to bench (default all)",
    )
    args = p.parse_args()
    if args.query_count < 1:
        raise ValueError("--query-count must be >= 1")
    if args.workers < 1:
        raise ValueError("--workers must be >= 1")
    return args


def rss():
    if psutil is None:
        return None
    return psutil.Process(os.getpid()).memory_info().rss


def pairs(n):
    return [("k%08d" % i, "v%08d" % i) for i in range(n)]


def fmt_header():
    return "%-20s %8s %8s %8s %8s %8s" % ("op", "n", "s", "qps", "µs", "rss")


def fmt_row(name, n, dt, mem0, mem1):
    qps = int(n / dt) if dt else 0
    lat = (dt / n) * 1e6 if n else 0
    if mem0 is None or mem1 is None:
        mem = "-"
    else:
        mem = "%+.1fM" % ((mem1 - mem0) / (1024.0 * 1024.0))
    return "%-20s %8d %8.3f %8d %8.1f %8s" % (name, n, dt, qps, lat, mem)


async def timed(name, n, body):
    mem0 = rss()
    t0 = time.perf_counter()
    await body()
    dt = time.perf_counter() - t0
    print(fmt_row(name, n, dt, mem0, rss()))


async def seq(db, items, op):
    for k, v in items:
        await op(db, k, v)


async def conc(items, factory):
    await asyncio.gather(*[factory(k, v) for k, v in items])


def unlink(path):
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(path + suffix)
        except OSError:
            pass


async def run_suite(path, n, workers, encoder, items):
    kw = {"default_encoder": encoder}
    print()
    print("encoder %s" % encoder.__name__)
    print(fmt_header())

    async with kvsqlite.Client(path, **kw) as db:
        await timed("set", n, lambda: seq(db, items, lambda d, k, v: d.set(k, v)))
        await timed("get", n, lambda: seq(db, items, lambda d, k, v: d.get(k)))
        await timed("exists", n, lambda: seq(db, items, lambda d, k, v: d.exists(k)))
        await timed("delete", n, lambda: seq(db, items, lambda d, k, v: d.delete(k)))
        await db.flush()

    async with kvsqlite.Client(path, **kw) as db:
        await timed(
            "setex",
            n,
            lambda: seq(db, items, lambda d, k, v: d.setex(k, 60, v)),
        )
        await timed("get(setex)", n, lambda: seq(db, items, lambda d, k, v: d.get(k)))
        await timed("ttl", n, lambda: seq(db, items, lambda d, k, v: d.ttl(k)))
        await timed(
            "expire", n, lambda: seq(db, items, lambda d, k, v: d.expire(k, 30))
        )
        await db.flush()

    async with kvsqlite.Client(path, autocommit=False, **kw) as db:

        async def batched():
            await seq(db, items, lambda d, k, v: d.set(k, v))
            await db.commit()

        await timed("set (no autocommit)", n, batched)
        await db.flush()

    async with kvsqlite.Client(path, workers=workers, **kw) as db:
        await timed(
            "set concurrent",
            n,
            lambda: conc(items, lambda k, v: db.set(k, v)),
        )
        await timed(
            "get concurrent",
            n,
            lambda: conc(items, lambda k, v: db.get(k)),
        )
        await db.flush()


async def main():
    args = parse_args()
    items = pairs(args.query_count)
    n = args.query_count
    unlink(args.db_path)

    if args.encoder == "all":
        selected = [ENCODERS[name] for name in sorted(ENCODERS)]
    else:
        selected = [ENCODERS[args.encoder]]

    print(
        "kvsqlite %s  n=%d  workers=%d  db=%s"
        % (kvsqlite.VERSION, n, args.workers, args.db_path)
    )

    for encoder in selected:
        await run_suite(args.db_path, n, args.workers, encoder, items)
        unlink(args.db_path)


if __name__ == "__main__":
    asyncio.run(main())
