import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest

from school.jobs.adapters import SlowAdapter
from school.jobs.errors import QueueFullError
from school.jobs.executor import JobExecutor
from school.jobs.models import AnalysisJob, JobStatus
from school.jobs.repository import InMemoryJobRepository


def job(i = 0):
    return AnalysisJob.create(f"sub-{i}", "hash", "slow", "cfg")


def test_success():
    async def main():
        repo = InMemoryJobRepository()
        ex = JobExecutor(repo, SlowAdapter(delay=0.01).analyze)
        j = await ex.submit(job())
        await ex.join()
        assert (await repo.get(j.job_id)).status == JobStatus.COMPLETED
    asyncio.run(main())


def test_failed():
    async def main():
        repo = InMemoryJobRepository()
        ex = JobExecutor(repo, SlowAdapter(fail=True).analyze)
        j = await ex.submit(job())
        await ex.join()
        assert (await repo.get(j.job_id)).status == JobStatus.FAILED
    asyncio.run(main())


def test_timeout():
    async def main():
        repo = InMemoryJobRepository()
        ex = JobExecutor(repo, SlowAdapter(hang=True).analyze, default_timeout=0.1)
        j = await ex.submit(job())
        await ex.join()
        assert (await repo.get(j.job_id)).status == JobStatus.TIMEOUT
    asyncio.run(main())


def test_cancel_running():
    async def main():
        repo = InMemoryJobRepository()
        ex = JobExecutor(repo, SlowAdapter(delay=0.5).analyze)
        j = await ex.submit(job())
        await asyncio.sleep(0.05)
        await ex.cancel(j.job_id)
        assert (await repo.get(j.job_id)).status == JobStatus.CANCELLED
    asyncio.run(main())


def test_cancel_pending():
    async def main():
        repo = InMemoryJobRepository()
        ex = JobExecutor(repo, SlowAdapter(hang=True).analyze, concurrency_limit=1)
        a = await ex.submit(job(1)) 
        b = await ex.submit(job(2))  
        await ex.cancel(b.job_id)
        assert (await repo.get(b.job_id)).status == JobStatus.CANCELLED
        await ex.cancel(a.job_id)
    asyncio.run(main())


def test_queue_full_submission_preserved():
    async def main():
        repo = InMemoryJobRepository()
        ex = JobExecutor(repo, SlowAdapter(hang=True).analyze, concurrency_limit=1, queue_limit=2)
        await ex.submit(job(1)) 
        await ex.submit(job(2))          
        await ex.submit(job(3))              
        with pytest.raises(QueueFullError):
            await ex.submit(job(4))
        assert await repo.get(job(4).job_id) is None 
    asyncio.run(main())


def test_concurrency_limit():
    async def main():
        repo = InMemoryJobRepository()
        ex = JobExecutor(repo, SlowAdapter(delay=0.1).analyze, concurrency_limit=2)
        for i in range(6):
            await ex.submit(job(i))
        await asyncio.sleep(0.05)
        assert len(await repo.list_by_status(JobStatus.RUNNING)) <= 2
        await ex.join()
    asyncio.run(main())