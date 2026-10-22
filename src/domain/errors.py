from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SubmissionError(Exception):
    code: str
    field: str | None
    message: str

    def __str__(self) -> str: 
        field_part = f" field={self.field!r}" if self.field else ""
        return f"[{self.code}]{field_part} {self.message}"