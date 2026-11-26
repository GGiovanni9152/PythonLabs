import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from school.jobs.adapters import SyncAnalyzerAdapter
from school.jobs.executor import JobExecutor
from school.jobs.models import AnalysisJob, JobStatus
from school.jobs.repository import InMemoryJobRepository


class CpuAnalyzer:
    analyzer_id = "cpu"
    analyzer_version = "1.0.0"

    def __init__(self, n: int = 2_000_000):
        self._n = n

    def analyze(self, submission, context):
        s = sum(i * i for i in range(self._n))
        return {"score": s % 1.0}


def job(i=0):
    return AnalysisJob.create(f"sub-{i}", "hash", "cpu", "cfg")


def test_sync_analyzer_completes():
    async def main():
        repo = InMemoryJobRepository()
        subs = {"sub-0": object()}
        ctx = {"sub-0": object()}
        with ThreadPoolExecutor(1) as pool:
            adapter = SyncAnalyzerAdapter(CpuAnalyzer(), subs, ctx, pool)
            ex = JobExecutor(repo, adapter.analyze)
            j = await ex.submit(job())
            await ex.join()
            assert (await repo.get(j.job_id)).status == JobStatus.COMPLETED
    asyncio.run(main())


def test_event_loop_not_blocked():
    async def main():
        repo = InMemoryJobRepository()
        subs = {"sub-0": object()}
        ctx = {"sub-0": object()}
        ticks = 0

        async def heartbeat():
            nonlocal ticks
            for _ in range(30):
                ticks += 1
                await asyncio.sleep(0.01)

        with ThreadPoolExecutor(1) as pool:
            adapter = SyncAnalyzerAdapter(CpuAnalyzer(5_000_000), subs, ctx, pool)
            ex = JobExecutor(repo, adapter.analyze)
            await ex.submit(job())
            await heartbeat() 
            await ex.join()
        assert ticks > 0
    asyncio.run(main())


def test_cancel_running_sync_job():
    async def main():
        repo = InMemoryJobRepository()
        subs = {"sub-0": object()}
        ctx = {"sub-0": object()}
        with ThreadPoolExecutor(1) as pool:
            adapter = SyncAnalyzerAdapter(CpuAnalyzer(50_000_000), subs, ctx, pool)
            ex = JobExecutor(repo, adapter.analyze)
            j = await ex.submit(job())
            await asyncio.sleep(0.05)
            await ex.cancel(j.job_id)
            assert (await repo.get(j.job_id)).status == JobStatus.CANCELLED
    asyncio.run(main())