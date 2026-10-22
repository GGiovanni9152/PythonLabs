from __future__ import annotations

import hashlib
import json

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass(frozen=True, slots=True)
class AIDeclaration:
    used: bool
    tool: str | None
    purpose: str | None
    verified_by_student: bool

    @classmethod
    def from_raw(cls, raw: dict) -> "AIDeclaration":
        """Создание из словаря без валидации (валидацию делает pydantic)."""
        return cls(
            used = raw["used"],
            verified_by_student = raw["verified_by_student"],
            tool = raw.get("tool"),
            purpose = raw.get("purpose"),
        )



@dataclass(frozen=True, slots=True)
class Submission:
    schema_version: int
    submission_id: str
    student_id: str
    assignment_id: str
    submitted_at: str
    text: str
    code: str
    template_id: str | None
    ai_declaration: AIDeclaration

    def content_hash(self) -> str:
        canon = json.dumps(
            {
                "schema_version": self.schema_version,
                "submission_id": self.submission_id,
                "student_id": self.student_id,
                "assignment_id": self.assignment_id,
                "submitted_at": self.submitted_at,
                "text": self.text,
                "code": self.code,
                "template_id": self.template_id,
                "ai_declaration": {
                    "used": self.ai_declaration.used,
                    "verified_by_student": self.ai_declaration.verified_by_student,
                    "tool": self.ai_declaration.tool,
                    "purpose": self.ai_declaration.purpose,
                },
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canon.encode("utf-8")).hexdigest()

@dataclass(frozen=True, slots=True)
class Assignment:
    assignment_id: str
    title: str
    template_id: str | None
    allowed_templates: tuple[str, ...] = field(default_factory=tuple)

@dataclass(frozen=True, slots=True)
class AnalysisReport:
    analyzer_id: str
    analyzer_version: str
    score: float | None
    rubric_feedback: str
    similarity: float | None = None
    evidence: tuple[int, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)
    