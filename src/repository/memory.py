from __future__ import annotations

from src.domain.contracts import AcceptResult
from src.domain.models import Submission

class InMemorySubmissionRepository:
    def __init__(self) -> None:
        self._by_id: dict[str, Submission] = {}
        self._by_hash: dict[str, Submission] = {}

    def accept(self, submission: Submission) -> AcceptResult:
        h = submission.content_hash()
        existing = self._by_id.get(submission.submission_id)

        if existing is None:
            self._by_id[submission.submission_id] = submission
            self._by_hash.setdefault(h, submission)
            return AcceptResult(status="accepted", submission=submission)
        
        if existing.content_hash() == h:
            return AcceptResult(status="duplicate", submission=existing, existing=existing)

        return AcceptResult(status="conflict", submission=existing, existing=existing)

    def get(self, submission_id: str) -> Submission | None:
        return self._by_id.get(submission_id)

    def get_by_hash(self, content_hash: str) -> Submission | None:
        return self._by_hash.get(content_hash)

    def __len__(self) -> int:
        return len(self._by_id)
