from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class AIDeclarationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    used: bool
    verified_by_student: bool
    tool: str | None = None
    purpose: str | None = None

    @model_validator(mode="after")
    def _check_used_requires_tool_and_purpose(self) -> "AIDeclarationModel":
        if self.used:
            if not self.tool or not self.tool.strip():
                raise ValueError("tool is required when used=True")
            
            if not self.purpose or not self.purpose.strip():
                raise ValueError("purpose is required when used=True")
            
        return self

class SubmissionModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        strict=True,
    )

    schema_version: int = Field(..., eq=1)
    submission_id: str
    student_id: str
    assignment_id: str
    submitted_at: str
    text: str
    code: str
    template_id: str | None = None
    ai_declaration: AIDeclarationModel

    @field_validator("submission_id", "student_id", "assignment_id")
    @classmethod
    def _non_empty(cls, v: str, info) -> str:
        if not v.strip():
            raise ValueError(f"{info.field_name} is empty")
        return v

    @field_validator("template_id")
    @classmethod
    def _template_id_non_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("template_id must not be empty")
        return v

    @field_validator("submitted_at")
    @classmethod
    def _submitted_at_has_tz(cls, v: str) -> str:
        try:
            dt = datetime.fromisoformat(v)
        except (TypeError, ValueError) as e:
            raise ValueError(f"submitted_at is not ISO 8601: {e}") from e
        
        if dt.tzinfo is None:
            raise ValueError("submitted_at must include a timezone")
        return v

    @model_validator(mode="after")
    def _text_or_code_non_empty(self) -> "SubmissionModel":
        if not self.text.strip() and not self.code.strip():
            raise ValueError("at least one of text/code must be non-empty")
        return self