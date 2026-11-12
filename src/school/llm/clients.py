from __future__ import annotations

from dataclasses import asdict
from typing import Any, Protocol, runtime_checkable

from school.domain.models import Submission
from school.llm.models import Rubric
from school.llm.baseline import LocalRubricBaseline


@runtime_checkable
class LLMClient(Protocol):
    model_id: str
    def generate(self, prompt: str, submission: Submission, rubric: Rubric) -> Any: ...


class StubLLMClient:
    model_id = "stub_llm"

    def __init__(self) -> None:
        self._baseline = LocalRubricBaseline()

    def generate(self, prompt: str, submission: Submission, rubric: Rubric) -> Any:
        report = self._baseline.evaluate(submission, rubric)
        return {
            "criteria": [
                {
                    "criterion_id": c.criterion_id,
                    "status": c.status.value,
                    "evidence": list(c.evidence),
                    "explanation": c.explanation,
                    "review_required": c.review_required,
                }
                for c in report.criteria
            ]
        }


class ScriptedLLMClient:
    model_id = "scripted_llm"

    def __init__(self, raw: Any) -> None:
        self._raw = raw

    def generate(self, prompt: str, submission: Submission, rubric: Rubric) -> Any:
        return self._raw