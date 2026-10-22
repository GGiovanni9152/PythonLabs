from __future__ import annotations

from typing import Any
from src.domain.models import Submission

class BasicFeatureExtractor:
    def extract(self, submission: Submission) -> dict[str, Any]:
        text_lines = [ln for ln in submission.text.splitlines() if ln.strip()]
        code_lines = [ln for ln in submission.code.splitlines() if ln.strip()]
        return {
            "text_len": len(submission.text),
            "code_len": len(submission.code),
            "text_non_empty": len(text_lines),
            "code_non_empty": len(code_lines),
            "template_id": submission.template_id,
            "assignment_id": submission.assignment_id
        }