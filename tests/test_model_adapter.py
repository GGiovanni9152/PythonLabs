import asyncio

import pytest

from school.jobs.executor import JobExecutor
from school.jobs.model_adapter import (
    BatchConfig, BatchModelProcessor, GuardedModelAdapter,
    StubModelAdapter, SlowModelAdapter, UnavailableModelAdapter, InvalidModelAdapter,
    TrackingAdapter, ModelTimeoutError, ModelUnavailableError, ModelInvalidResponseError,
    make_model_work,
)
from school.jobs.models import AnalysisJob, JobStatus
from school.jobs.repository import InMemoryJobRepository


def job(i=0):
    return AnalysisJob.create(f"sub-{i}", "h", "a", "c")


def test_model_concurrency_limit():
    async def main():
        track = TrackingAdapter(delay=0.05)
        guarded = GuardedModelAdapter(track, concurrency_limit=2)
        proc = BatchModelProcessor(guarded, BatchConfig(2))
        await proc.process([{"i": i} for i in range(12)])
        assert track.max_active <= 2
    asyncio.run(main())


def test_batch_size_fixed():
    async def main():
        track = TrackingAdapter()
        guarded = GuardedModelAdapter(track)
        proc = BatchModelProcessor(guarded, BatchConfig(4))
        await proc.process([{"i": i} for i in range(10)])
        assert track.batch_sizes == [4, 4, 2]
    asyncio.run(main())


def test_error_codes_distinct():
    async def main():
        with pytest.raises(ModelTimeoutError):
            await GuardedModelAdapter(SlowModelAdapter(1.0), timeout=0.05).infer([{}])
        with pytest.raises(ModelUnavailableError):
            await GuardedModelAdapter(UnavailableModelAdapter()).infer([{}])
        with pytest.raises(ModelInvalidResponseError):
            await GuardedModelAdapter(InvalidModelAdapter()).infer([{}])
    asyncio.run(main())


@pytest.mark.parametrize("adapter,code", [
    (SlowModelAdapter(1.0), "model_timeout"),
    (UnavailableModelAdapter(), "model_unavailable"),
    (InvalidModelAdapter(), "model_invalid_response"),
])
def test_job_error_code(adapter, code):
    async def main():
        repo = InMemoryJobRepository()
        guarded = GuardedModelAdapter(adapter, timeout=0.05)
        ex = JobExecutor(repo, make_model_work(guarded))
        j = await ex.submit(job())
        await ex.join()
        got = await repo.get(j.job_id)
        assert got.status == JobStatus.FAILED
        assert got.error_code == code
    asyncio.run(main())


def test_swap_stub_does_not_change_management():
    async def main():
        for inner in (StubModelAdapter(), TrackingAdapter()):
            repo = InMemoryJobRepository()
            guarded = GuardedModelAdapter(inner, batch_config=BatchConfig(4))
            ex = JobExecutor(repo, make_model_work(guarded))
            j = await ex.submit(job())
            await ex.join()
            got = await repo.get(j.job_id)
            assert got.status == JobStatus.COMPLETED
            assert got.result["batch_size"] == 4
    asyncio.run(main())