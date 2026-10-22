from __future__ import annotations

from typing import Any
from src.domain.models import Submission


class BasicFeedbackBuilder:
    def build(self, raw: dict[str, Any], submission: Submission) -> str:
        verdict = raw.get("verdict", "ok")
        return f"automated feedback: verdict={verdict} for submission {submission.submission_id}."