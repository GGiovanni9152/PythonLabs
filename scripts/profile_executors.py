import asyncio
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

N = 3_000_000
JOBS = 8
RUNS = 3


def cpu_work(n: int) -> int:
    return sum(i * i for i in range(n))


async def bench(pool) -> float:
    loop = asyncio.get_running_loop()
    t0 = time.perf_counter()
    await asyncio.gather(*[loop.run_in_executor(pool, cpu_work, N) for _ in range(JOBS)])
    return time.perf_counter() - t0


def main():
    for kind, pool_cls in [("thread", ThreadPoolExecutor), ("process", ProcessPoolExecutor)]:
        times = []
        for _ in range(RUNS):
            with pool_cls(max_workers=4) as pool:
                times.append(asyncio.run(bench(pool)))
        print(f"{kind}: median={statistics.median(times):.3f}s mean={statistics.mean(times):.3f}s")


if __name__ == "__main__":
    main()