import argparse
import asyncio
import random
import string
import kvsqlite
import time
import os
import psutil

parser = argparse.ArgumentParser(description="Benchmark kvsqlite")
parser.add_argument(
    "--query-count",
    type=int,
    help="Number of queryies to benchmark (Defaults to 100000)",
    default=100000,
)
parser.add_argument(
    "--db-path",
    type=str,
    help="Databse path (Defaults to benchmark_kvsqlite.sqlite)",
    default="benchmark_kvsqlite.sqlite",
)
args = parser.parse_args()

if args.query_count < 1:
    raise ValueError("--query-count must be greater than 1")


def random_string(length):
    return "".join(random.choice(string.ascii_letters) for _ in range(length))


PINK = "\033[95m"
GREEN = "\033[92m"
WARNING = "\033[93m"
ENDC = "\033[0m"


async def benchmark_set(db, keys):
    print(PINK, "================Benchmark set================", ENDC)
    timeing = 0
    start = time.perf_counter()
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    print(
        WARNING,
        "-> Started with memory usage:",
        ENDC,
        start_memory,
    )
    for k, v in keys:
        latncey_start = time.perf_counter()
        await db.set(k, v)
        timeing += time.perf_counter() - latncey_start
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    took = time.perf_counter() - start
    print(
        WARNING,
        "-> {} query took:{} {}".format(args.query_count, ENDC, took),
    )
    print(
        WARNING,
        "-> QRS:",
        ENDC,
        int(args.query_count / took),
    )
    print(
        WARNING,
        "-> Average latancey:",
        ENDC,
        timeing / args.query_count,
    )
    print(
        WARNING,
        "-> Current memory usage:{} {} ({}+{}{})".format(
            ENDC, end_memory, GREEN, (end_memory - start_memory), ENDC
        ),
        ENDC,
    )
    print(GREEN, "================Benchmark end================", ENDC)
    print()


async def benchmark_setex(db, keys):
    print(PINK, "================Benchmark setex================", ENDC)
    timeing = 0
    start = time.perf_counter()
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    print(
        WARNING,
        "-> Started with memory usage:",
        ENDC,
        start_memory,
    )
    for k, v in keys:
        latncey_start = time.perf_counter()
        await db.setex(k, v, 60)
        timeing += time.perf_counter() - latncey_start
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    took = time.perf_counter() - start
    print(
        WARNING,
        "-> {} query took:{} {}".format(args.query_count, ENDC, took),
    )
    print(
        WARNING,
        "-> QRS:",
        ENDC,
        int(args.query_count / took),
    )
    print(
        WARNING,
        "-> Average latancey:",
        ENDC,
        timeing / args.query_count,
    )
    print(
        WARNING,
        "-> Current memory usage:{} {} ({}+{}{})".format(
            ENDC, end_memory, GREEN, (end_memory - start_memory), ENDC
        ),
        ENDC,
    )
    print(GREEN, "================Benchmark end================", ENDC)
    print()


async def benchmark_get(db, keys):
    print(PINK, "================Benchmark get================", ENDC)
    timeing = 0
    start = time.perf_counter()
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    print(
        WARNING,
        "-> Started with memory usage:",
        ENDC,
        start_memory,
    )
    for k, v in keys:
        latncey_start = time.perf_counter()
        await db.get(k)
        timeing += time.perf_counter() - latncey_start
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    took = time.perf_counter() - start
    print(
        WARNING,
        "-> {} query took:{} {}".format(args.query_count, ENDC, took),
    )
    print(
        WARNING,
        "-> QRS:",
        ENDC,
        int(args.query_count / took),
    )
    print(
        WARNING,
        "-> Average latancey:",
        ENDC,
        timeing / args.query_count,
    )
    print(
        WARNING,
        "-> Current memory usage:{} {} ({}+{}{})".format(
            ENDC, end_memory, GREEN, (end_memory - start_memory), ENDC
        ),
        ENDC,
    )
    print(GREEN, "================Benchmark end================", ENDC)
    print()


async def benchmark_exists(db, keys):
    print(PINK, "================Benchmark exists=============", ENDC)
    timeing = 0
    start = time.perf_counter()
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    print(
        WARNING,
        "-> Started with memory usage:",
        ENDC,
        start_memory,
    )
    for k, v in keys:
        latncey_start = time.perf_counter()
        await db.exists(k)
        timeing += time.perf_counter() - latncey_start
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    took = time.perf_counter() - start
    print(
        WARNING,
        "-> {} query took:{} {}".format(args.query_count, ENDC, took),
    )
    print(
        WARNING,
        "-> QRS:",
        ENDC,
        int(args.query_count / took),
    )
    print(
        WARNING,
        "-> Average latancey:",
        ENDC,
        timeing / args.query_count,
    )
    print(
        WARNING,
        "-> Current memory usage:{} {} ({}+{}{})".format(
            ENDC, end_memory, GREEN, (end_memory - start_memory), ENDC
        ),
        ENDC,
    )
    print(GREEN, "================Benchmark end================", ENDC)
    print()


async def benchmark_ttl(db, keys):
    print(PINK, "================Benchmark ttl=============", ENDC)
    timeing = 0
    start = time.perf_counter()
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    print(
        WARNING,
        "-> Started with memory usage:",
        ENDC,
        start_memory,
    )
    for k, v in keys:
        latncey_start = time.perf_counter()
        await db.ttl(k)
        timeing += time.perf_counter() - latncey_start
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    took = time.perf_counter() - start
    print(
        WARNING,
        "-> {} query took:{} {}".format(args.query_count, ENDC, took),
    )
    print(
        WARNING,
        "-> QRS:",
        ENDC,
        int(args.query_count / took),
    )
    print(
        WARNING,
        "-> Average latancey:",
        ENDC,
        timeing / args.query_count,
    )
    print(
        WARNING,
        "-> Current memory usage:{} {} ({}+{}{})".format(
            ENDC, end_memory, GREEN, (end_memory - start_memory), ENDC
        ),
        ENDC,
    )
    print(GREEN, "================Benchmark end================", ENDC)
    print()


async def benchmark_expire(db, keys):
    print(PINK, "================Benchmark expire=============", ENDC)
    timeing = 0
    start = time.perf_counter()
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    print(
        WARNING,
        "-> Started with memory usage:",
        ENDC,
        start_memory,
    )
    for k, v in keys:
        latncey_start = time.perf_counter()
        await db.expire(k, 30)
        timeing += time.perf_counter() - latncey_start
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    took = time.perf_counter() - start
    print(
        WARNING,
        "-> {} query took:{} {}".format(args.query_count, ENDC, took),
    )
    print(
        WARNING,
        "-> QRS:",
        ENDC,
        int(args.query_count / took),
    )
    print(
        WARNING,
        "-> Average latancey:",
        ENDC,
        timeing / args.query_count,
    )
    print(
        WARNING,
        "-> Current memory usage:{} {} ({}+{}{})".format(
            ENDC, end_memory, GREEN, (end_memory - start_memory), ENDC
        ),
        ENDC,
    )
    print(GREEN, "================Benchmark end================", ENDC)
    print()


async def benchmark_delete(db, keys):
    print(PINK, "================Benchmark delete=============", ENDC)
    timeing = 0
    start = time.perf_counter()
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    print(
        WARNING,
        "-> Started with memory usage:",
        ENDC,
        start_memory,
    )
    for k, v in keys:
        latncey_start = time.perf_counter()
        await db.delete(k)
        timeing += time.perf_counter() - latncey_start
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    took = time.perf_counter() - start
    print(
        WARNING,
        "-> {} query took:{} {}".format(args.query_count, ENDC, took),
    )
    print(
        WARNING,
        "-> QRS:",
        ENDC,
        int(args.query_count / took),
    )
    print(
        WARNING,
        "-> Average latancey:",
        ENDC,
        timeing / args.query_count,
    )
    print(
        WARNING,
        "-> Current memory usage:{} {} ({}+{}{})".format(
            ENDC, end_memory, GREEN, (end_memory - start_memory), ENDC
        ),
        ENDC,
    )
    print(GREEN, "================Benchmark end================", ENDC)
    print()


async def benchmark_concurrent_set(db, keys):
    print(PINK, "================Benchmark concurrent set=====", ENDC)

    futures = asyncio.gather(*[db.set(k, v) for k, v in keys])
    start = time.perf_counter()
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    print(
        WARNING,
        "-> Started with memory usage:",
        ENDC,
        start_memory,
    )
    await futures
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    took = time.perf_counter() - start
    print(
        WARNING,
        "-> {} query took:{} {}".format(args.query_count, ENDC, took),
    )
    print(
        WARNING,
        "-> QRS:",
        ENDC,
        int(args.query_count / took),
    )
    print(
        WARNING,
        "-> Current memory usage:{} {} ({}+{}{})".format(
            ENDC, end_memory, GREEN, (end_memory - start_memory), ENDC
        ),
        ENDC,
    )
    print(GREEN, "================Benchmark end================", ENDC)
    print()


async def benchmark_concurrent_get(db, keys):
    print(PINK, "================Benchmark concurrent get=====", ENDC)

    futures = asyncio.gather(*[db.get(k) for k, v in keys])
    start = time.perf_counter()
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    print(
        WARNING,
        "-> Started with memory usage:",
        ENDC,
        start_memory,
    )
    await futures
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    took = time.perf_counter() - start
    print(
        WARNING,
        "-> {} query took:{} {}".format(args.query_count, ENDC, took),
    )
    print(
        WARNING,
        "-> QRS:",
        ENDC,
        int(args.query_count / took),
    )
    print(
        WARNING,
        "-> Current memory usage:{} {} ({}+{}{})".format(
            ENDC, end_memory, GREEN, (end_memory - start_memory), ENDC
        ),
        ENDC,
    )
    print(GREEN, "================Benchmark end================", ENDC)
    print()


async def benchmark_no_auto_commit_set(db, keys):
    print(PINK, "========Benchmark set no autocommit==========", ENDC)
    timeing = 0
    start = time.perf_counter()
    start_memory = psutil.Process(os.getpid()).memory_info().rss
    print(
        WARNING,
        "-> Started with memory usage:",
        ENDC,
        start_memory,
    )
    for k, v in keys:
        latncey_start = time.perf_counter()
        await db.set(k, v)
        timeing += time.perf_counter() - latncey_start
    await db.commit()
    end_memory = psutil.Process(os.getpid()).memory_info().rss
    took = time.perf_counter() - start
    print(
        WARNING,
        "-> {} query took:{} {}".format(args.query_count, ENDC, took),
    )
    print(
        WARNING,
        "-> QRS:",
        ENDC,
        int(args.query_count / took),
    )
    print(
        WARNING,
        "-> Average latancey:",
        ENDC,
        timeing / args.query_count,
    )
    print(
        WARNING,
        "-> Current memory usage:{} {} ({}+{}{})".format(
            ENDC, end_memory, GREEN, (end_memory - start_memory), ENDC
        ),
        ENDC,
    )
    print(GREEN, "================Benchmark end================", ENDC)
    print()


async def main():

    keys = []
    for _ in range(args.query_count):
        keys.append(
            (
                random_string(random.randint(1, 20)),
                random_string(random.randint(1, 20)),
            )
        )

    async with kvsqlite.Client(args.db_path) as db:
        print(WARNING, args.query_count, "Query benchmark", ENDC)
        await benchmark_set(db, keys)
        await benchmark_get(db, keys)
        await benchmark_exists(db, keys)
        await benchmark_delete(db, keys)

        await db.flush()

    async with kvsqlite.Client(args.db_path) as db:
        await benchmark_setex(db, keys)
        await benchmark_get(db, keys)
        await benchmark_ttl(db, keys)
        await benchmark_expire(db, keys)

        await db.flush()

    async with kvsqlite.Client(args.db_path, autocommit=False) as db:
        await benchmark_no_auto_commit_set(db, keys)
        await db.flush()

    async with kvsqlite.Client(args.db_path, workers=5) as db:
        print(
            WARNING,
            args.query_count,
            "Query benchmark with",
            db.workers,
            "workers",
            ENDC,
        )
        await benchmark_concurrent_set(db, keys)
        await benchmark_concurrent_get(db, keys)

        await db.flush()


asyncio.run(main())
