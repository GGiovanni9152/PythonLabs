from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Protocol, runtime_checkable


class ModelErrorCode(str, Enum):
    TIMEOUT = "model_timeout"
    UNAVAILABLE = "model_unavailable"
    INVALID_RESPONSE = "model_invalid_response"


class ModelError(Exception):
    def __init__(self, message: str, code: ModelErrorCode) -> None:
        super().__init__(message)
        self.code = code


class ModelTimeoutError(ModelError):
    def __init__(self, m: str = "model timeout") -> None:
        super().__init__(m, ModelErrorCode.TIMEOUT)


class ModelUnavailableError(ModelError):
    def __init__(self, m: str = "model unavailable") -> None:
        super().__init__(m, ModelErrorCode.UNAVAILABLE)


class ModelInvalidResponseError(ModelError):
    def __init__(self, m: str = "invalid model response") -> None:
        super().__init__(m, ModelErrorCode.INVALID_RESPONSE)


@dataclass(frozen=True, slots=True)
class BatchConfig:
    batch_size: int

    def __post_init__(self) -> None:
        if self.batch_size < 1:
            raise ValueError("batch_size must be >= 1")

    @property
    def config_hash(self) -> str:
        return hashlib.sha256(
            json.dumps({"batch_size": self.batch_size}, sort_keys=True).encode()
        ).hexdigest()


@runtime_checkable
class ModelAdapter(Protocol):
    adapter_id: str
    async def infer(self, batch: list[dict[str, Any]]) -> list[dict[str, Any]]: ...


def _default_validate(raw: Any) -> bool:
    return isinstance(raw, list) and all(isinstance(x, dict) for x in raw)


class GuardedModelAdapter:
    def __init__(self, inner: ModelAdapter, concurrency_limit: int = 2,
                 timeout: float = 5.0, batch_config: BatchConfig | None = None,
                 validator: Callable[[Any], bool] | None = None) -> None:
        self._inner = inner
        self._sem = asyncio.Semaphore(concurrency_limit)
        self._timeout = timeout
        self.batch_config = batch_config
        self._validator = validator or _default_validate

    async def infer(self, batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if self.batch_config and len(batch) > self.batch_config.batch_size:
            raise ValueError("batch exceeds configured batch_size")
        async with self._sem:
            try:
                raw = await asyncio.wait_for(self._inner.infer(batch), self._timeout)
            except asyncio.TimeoutError as e:
                raise ModelTimeoutError() from e
            except (ConnectionError, OSError) as e:
                raise ModelUnavailableError() from e
            if not self._validator(raw) or len(raw) != len(batch):
                raise ModelInvalidResponseError()
            return raw


class BatchModelProcessor:
    def __init__(self, guarded: GuardedModelAdapter, batch_config: BatchConfig) -> None:
        self._guarded, self._cfg = guarded, batch_config

    async def process(self, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        bs = self._cfg.batch_size
        chunks = [items[i:i + bs] for i in range(0, len(items), bs)]
        outs = await asyncio.gather(*[self._guarded.infer(c) for c in chunks])
        return [x for out in outs for x in out]


class StubModelAdapter:
    adapter_id = "stub"
    async def infer(self, batch): return [{"verdict": "ok", "confidence": 0.5} for _ in batch]


class SlowModelAdapter:
    adapter_id = "slow"
    def __init__(self, delay: float): self._delay = delay
    async def infer(self, batch):
        await asyncio.sleep(self._delay)
        return [{"verdict": "ok"} for _ in batch]


class UnavailableModelAdapter:
    adapter_id = "down"
    async def infer(self, batch): raise ConnectionError("model down")


class InvalidModelAdapter:
    adapter_id = "bad"
    async def infer(self, batch): return ["not a dict"] * len(batch)


class TrackingAdapter:
    adapter_id = "track"
    def __init__(self, delay: float = 0.0):
        self._delay = delay
        self.active = 0
        self.max_active = 0
        self.batch_sizes: list[int] = []
    async def infer(self, batch):
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        self.batch_sizes.append(len(batch))
        await asyncio.sleep(self._delay)
        self.active -= 1
        return [{"ok": True} for _ in batch]


def make_model_work(guarded: GuardedModelAdapter,
                    feature_fn: Callable[[Any], dict] | None = None):
    fn = feature_fn or (lambda job: {"submission_id": job.submission_id})
    async def work(job) -> dict[str, Any]:
        res = await guarded.infer([fn(job)])
        out: dict[str, Any] = {"model": res[0]}
        if guarded.batch_config:
            out["batch_size"] = guarded.batch_config.batch_size
            out["batch_config_hash"] = guarded.batch_config.config_hash
        return out
    return work