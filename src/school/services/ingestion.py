from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from school.domain.contracts import AcceptResult, SubmissionRepository, SubmissionSource
from school.domain.errors import SubmissionError
from school.domain.models import Assignment, Manifest, ManifestEntry, Submission
from school.validation.validator import parse_submission


@dataclass(frozen=True, slots=True)
class IngestionOutcome:
    accepted: list[Submission]
    duplicates: list[Submission]
    conflicts: list[AcceptResult]
    errors: list[SubmissionError]


class IngestionService:
    def __init__(self, repository: SubmissionRepository) -> None:
        self._repo = repository

    def ingest(self, source: SubmissionSource) -> IngestionOutcome:
        accepted: list[Submission] = []
        duplicates: list[Submission] = []
        conflicts: list[AcceptResult] = []
        errors: list[SubmissionError] = []

        for raw in source.iter_raw():
            try:
                submission = parse_submission(raw)
            except SubmissionError as e: #на случай кривого json
                errors.append(e)
                continue

            result = self._repo.accept(submission)

            if result.status == "accepted":
                accepted.append(result.submission)

            elif result.status == "duplicate":
                duplicates.append(result.submission)

            else:
                conflicts.append(result)

        return IngestionOutcome(
            accepted = accepted, 
            duplicates = duplicates,
            conflicts = conflicts, 
            errors = errors,
        )


def load_assignments(path: str | Path) -> dict[str, Assignment]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out: dict[str, Assignment] = {}

    for item in data: #загрузка заданий
        a = Assignment(
            assignment_id = item["assignment_id"],
            title = item.get("title", ""),
            template_id = item.get("template_id"),
            allowed_templates = tuple(item.get("allowed_templates", ())),
        )
        out[a.assignment_id] = a

    return out


def build_manifest(submissions: Iterable[Submission], corpus_version: str, processing_version: str) -> Manifest:
    entries = tuple(
        ManifestEntry
                    (
                        submission_id = s.submission_id,
                        content_hash = s.content_hash(),
                        processing_version = processing_version
                    )          
        for s in submissions
    )
    
    return Manifest(corpus_version = corpus_version, entries = entries)