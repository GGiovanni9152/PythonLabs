from __future__ import annotations

import asyncio
from typing import Protocol

from school.jobs.models import AnalysisJob, JobStatus


class JobRepository(Protocol):
    async def save(self, job: AnalysisJob) -> None: ...
    async def get(self, job_id: str) -> AnalysisJob | None: ...
    async def list_by_status(self, status: JobStatus) -> list[AnalysisJob]: ...


class InMemoryJobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, AnalysisJob] = {}
        self._lock = asyncio.Lock()

    async def save(self, job: AnalysisJob) -> None:
        async with self._lock:
            self._jobs[job.job_id] = job

    async def get(self, job_id: str) -> AnalysisJob | None:
        async with self._lock:
            return self._jobs.get(job_id)

    async def list_by_status(self, status: JobStatus) -> list[AnalysisJob]:
        async with self._lock:
            return [j for j in self._jobs.values() if j.status == status]