import asyncio

from school.jobs.executor import JobExecutor
from school.jobs.models import AnalysisJob, JobStatus
from school.jobs.repository import InMemoryJobRepository
from school.jobs.adapters import SlowAdapter


def job(i=0):
    return AnalysisJob.create(f"sub-{i}", "h", "a", "c")


def test_shutdown_no_orphan_tasks():
    async def main():
        repo = InMemoryJobRepository()
        ex = JobExecutor(repo, SlowAdapter(hang=True).analyze, concurrency_limit=2)
        for i in range(5):
            await ex.submit(job(i))
        await asyncio.sleep(0.05)
        await ex.shutdown()
        assert ex._tasks == {}
        assert await repo.list_by_status(JobStatus.RUNNING) == []
        assert await repo.list_by_status(JobStatus.PENDING) == []
    asyncio.run(main())


def test_collect_errors_one_failure_keeps_others():
    async def main():
        repo = InMemoryJobRepository()

        async def work(j):
            if j.submission_id == "sub-1":
                raise RuntimeError("boom")
            return {"ok": True}

        ex = JobExecutor(repo, work)
        ids = [ (await ex.submit(job(i))).job_id for i in range(3) ]
        await ex.join()
        statuses = {i: (await repo.get(ids[i])).status for i in range(3)}
        assert statuses[1] == JobStatus.FAILED
        assert statuses[0] == JobStatus.COMPLETED
        assert statuses[2] == JobStatus.COMPLETED
    asyncio.run(main())


def test_executor_concurrency_tracking():
    async def main():
        repo = InMemoryJobRepository()
        active = 0
        max_active = 0

        async def work(j):
            nonlocal active, max_active
            active += 1
            max_active = max(max_active, active)
            await asyncio.sleep(0.05)
            active -= 1
            return {}

        ex = JobExecutor(repo, work, concurrency_limit=2)
        for i in range(6):
            await ex.submit(job(i))
        await ex.join()
        assert max_active <= 2
    asyncio.run(main())