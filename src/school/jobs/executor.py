from __future__ import annotations

import asyncio
import contextlib
from typing import Any, Awaitable, Callable

from school.jobs.errors import JobNotFoundError, QueueFullError
from school.jobs.models import AnalysisJob, JobStatus, TERMINAL
from school.jobs.repository import JobRepository
from school.jobs.model_adapter import ModelError


class JobExecutor:
    def __init__(self, repository: JobRepository,
                 work: Callable[[AnalysisJob], Awaitable[dict[str, Any]]],
                 concurrency_limit: int = 4, queue_limit: int = 100,
                 default_timeout: float = 30.0) -> None:
        self._repo, self._work = repository, work
        self._sem = asyncio.Semaphore(concurrency_limit)
        self._queue_limit, self._default_timeout = queue_limit, default_timeout
        self._tasks: dict[str, asyncio.Task] = {}

    async def submit(self, job: AnalysisJob, timeout: float | None = None) -> AnalysisJob:
        pending = await self._repo.list_by_status(JobStatus.PENDING)
        if len(pending) >= self._queue_limit:
            raise QueueFullError(f"queue full ({self._queue_limit}); submission preserved")
        await self._repo.save(job)
        self._tasks[job.job_id] = asyncio.create_task(self._run(job, timeout or self._default_timeout))
        await asyncio.sleep(0) #чтобы успела стартануть
        return job

    async def cancel(self, job_id: str) -> AnalysisJob:
        job = await self._repo.get(job_id)
        if job is None:
            raise JobNotFoundError(job_id)
        if job.status in TERMINAL:
            return job
        task = self._tasks.get(job_id)
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        cur = await self._repo.get(job_id) #если не успела стартануть
        if cur is not None and cur.status not in TERMINAL:
            await self._repo.save(cur.with_status(JobStatus.CANCELLED, error="cancelled"))
        return await self._repo.get(job_id)

    async def join(self) -> None:
        await asyncio.gather(*list(self._tasks.values()), return_exceptions=True)

    async def _run(self, job: AnalysisJob, timeout: float) -> None:
        cur = await self._repo.get(job.job_id)
        if cur is not None and cur.status == JobStatus.CANCELLED: #если отменилось до старта
            return
        try:
            async with self._sem:
                running = job.with_status(JobStatus.RUNNING)
                await self._repo.save(running)
                result = await asyncio.wait_for(self._work(running), timeout)
                await self._repo.save(running.with_status(JobStatus.COMPLETED, result=result))

        except asyncio.CancelledError:
            cur = await self._repo.get(job.job_id)
            await self._repo.save(cur.with_status(JobStatus.CANCELLED, error="cancelled", error_code="cancelled"))
            raise
        except asyncio.TimeoutError:
            cur = await self._repo.get(job.job_id)
            await self._repo.save(cur.with_status(JobStatus.TIMEOUT, error="timeout", error_code="job_timeout"))
        except ModelError as e:
            cur = await self._repo.get(job.job_id)
            await self._repo.save(cur.with_status(JobStatus.FAILED, error=str(e), error_code=e.code.value))
        except Exception as e:
            cur = await self._repo.get(job.job_id)
            await self._repo.save(cur.with_status(JobStatus.FAILED, error=str(e), error_code="internal_error"))

    async def shutdown(self) -> None:
        tasks = list(self._tasks.values())
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()
        for status in (JobStatus.PENDING, JobStatus.RUNNING):
            for j in await self._repo.list_by_status(status):
                await self._repo.save(j.with_status(JobStatus.CANCELLED, error="shutdown", error_code="shutdown"))