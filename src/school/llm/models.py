from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class CriterionStatus(str, Enum):
    SATISFIED = "satisfied"
    NOT_SATISFIED = "not_satisfied"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


@dataclass(frozen=True, slots=True)
class RubricCriterion:
    criterion_id: str
    description: str
    markers: tuple[str, ...] = ()
    required: bool = True


@dataclass(frozen=True, slots=True)
class Rubric:
    rubric_id: str
    version: str
    criteria: tuple[RubricCriterion, ...]

    def required_ids(self) -> set[str]:
        return {c.criterion_id for c in self.criteria if c.required}

    def get(self, criterion_id: str) -> RubricCriterion | None:
        for c in self.criteria:
            if c.criterion_id == criterion_id:
                return c
        return None


@dataclass(frozen=True, slots=True)
class CriterionFeedback:
    criterion_id: str
    status: CriterionStatus
    evidence: tuple[int, ...]
    explanation: str
    review_required: bool = False


@dataclass(frozen=True, slots=True)
class RubricFeedbackReport:
    rubric_id: str
    rubric_version: str
    model_id: str
    criteria: tuple[CriterionFeedback, ...]
    review_required: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


def load_rubric(path: str | Path) -> Rubric:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    criteria = tuple(
        RubricCriterion(
            criterion_id = c["criterion_id"],
            description = c.get("description", ""),
            markers = tuple(c.get("markers", ())),
            required = bool(c.get("required", True)),
        )
        for c in data["criteria"]
    )
    return Rubric(rubric_id = data["rubric_id"], version = data["version"], criteria = criteria)


def source_lines(submission) -> list[str]:
    return submission.text.splitlines() + submission.code.splitlines()