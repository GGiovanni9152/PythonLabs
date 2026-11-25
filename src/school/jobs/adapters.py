from __future__ import annotations

import asyncio
from concurrent.futures import Executor
from dataclasses import asdict
from typing import Any

from school.jobs.models import AnalysisJob


class SlowAdapter:
    analyzer_id = "slow"

    def __init__(self, delay: float = 0.0, fail: bool = False, hang: bool = False,
                 result: dict[str, Any] | None = None) -> None:
        self._delay, self._fail, self._hang = delay, fail, hang
        self._result = result or {"score": 0.5}

    async def analyze(self, job: AnalysisJob) -> dict[str, Any]:
        if self._hang:
            await asyncio.sleep(3600)
        if self._delay:
            await asyncio.sleep(self._delay)
        if self._fail:
            raise RuntimeError(f"simulated failure {job.submission_id}")
        return self._result


def _analyze_sync(analyzer, submission, context) -> dict[str, Any]:
    return asdict(analyzer.analyze(submission, context))


class SyncAnalyzerAdapter:
    def __init__(self, analyzer, submissions: dict, contexts: dict, pool: Executor) -> None:
        self._analyzer, self._subs, self._ctx, self._pool = analyzer, submissions, contexts, pool

    async def analyze(self, job: AnalysisJob) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self._pool, _analyze_sync,
            self._analyzer, self._subs[job.submission_id], self._ctx[job.submission_id])