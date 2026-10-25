from __future__ import annotations

from typing import Any, Iterable, Protocol, runtime_checkable
from school.domain.models import Assignment, Submission, AnalysisReport

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

@runtime_checkable
class SubmissionRepository(Protocol):
    def accept(self, submission: Submission) -> "AcceptResult": ...
    def get(self, submission_id: str) -> Submission | None: ...
    def get_by_hash(self, content_hash: str) -> Submission | None: ...
    def __len__(self) -> int: ...

@runtime_checkable
class FeatureExtractor(Protocol):
    def extract(self, submission: Submission) -> dict[str, Any]: ...

@runtime_checkable
class FeedbackBuilder(Protocol):
    def build(self, raw: dict[str, Any], submission: Submission) -> str: ...

@runtime_checkable
class Model(Protocol):
    def predict(self, features: dict[str, Any]) -> dict[str, Any]: ...