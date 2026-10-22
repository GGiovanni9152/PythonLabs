from __future__ import annotations

from typing import Any, Iterable, Protocol, runtime_checkable
from src.domain.models import Assignment, Submission, AnalysisReport

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class AnalysisContext:
    assignment: Assignment
    template_text: str | None
    config_hash: str

@runtime_checkable
class Analyzer(Protocol):
    @property
    def analyzer_id(self) -> str: ...

    @property
    def analyzer_version(self) -> str: ...

    def analyze(self, submission: Submission, context: AnalysisContext) -> AnalysisReport: ...

@runtime_checkable
class SubmissionSource(Protocol):
    def iter_raw(self) -> Iterable[str]: ...

@dataclass(frozen=True, slots=True)
class AcceptResult:
    status: str 
    submission: Submission
    existing: Submission | None = None