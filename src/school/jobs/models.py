from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


TERMINAL = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.TIMEOUT}


@dataclass(frozen = True, slots = True)
class AnalysisJob:
    job_id: str
    submission_id: str
    submission_hash: str
    analyzer_id: str
    config_hash: str
    status: JobStatus = JobStatus.PENDING
    attempt_no: int = 1
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    error_code: str | None = None
    result: dict[str, Any] | None = None

    @staticmethod
    def create(submission_id: str, submission_hash: str, analyzer_id: str, config_hash: str) -> "AnalysisJob":
        return AnalysisJob(str(uuid.uuid4()), submission_id, submission_hash, analyzer_id, config_hash)

    def with_status(self, status: JobStatus, **kw) -> "AnalysisJob":
        now = datetime.now(timezone.utc)
        upd: dict[str, Any] = {"status": status, **kw}
        if status == JobStatus.RUNNING and self.started_at is None:
            upd["started_at"] = now
        if status in TERMINAL:
            upd["finished_at"] = now
        return replace(self, **upd)