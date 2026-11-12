from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from school.domain.models import Submission
from school.llm.models import Rubric, RubricFeedbackReport, CriterionFeedback, CriterionStatus, source_lines


@dataclass(frozen=True, slots=True)
class ValidationOutcome:
    structural_valid: bool
    coverage_ok: bool
    citations_ok: bool
    issues: tuple[str, ...]
    report: RubricFeedbackReport | None

    @property
    def is_valid(self) -> bool:
        return self.structural_valid and self.coverage_ok and self.citations_ok


def validate_feedback(raw: Any, submission: Submission, rubric: Rubric,
                      model_id: str) -> ValidationOutcome:
    issues: list[str] = []

    if not isinstance(raw, dict) or not isinstance(raw.get("criteria"), list):
        return ValidationOutcome(False, False, False, ("not_an_object_or_missing_criteria",), None)

    seen: dict[str, CriterionStatus] = {}
    feedbacks: list[CriterionFeedback] = []
    structural = True
    for item in raw["criteria"]:
        if not isinstance(item, dict):
            structural = False
            issues.append("criterion_not_object")
            continue
        
        cid = item.get("criterion_id")
        status = item.get("status")
        evidence = item.get("evidence")
        explanation = item.get("explanation")
        review = item.get("review_required")

        if not isinstance(cid, str):
            structural = False
            issues.append("bad_criterion_id")
            continue
        
        if status not in {s.value for s in CriterionStatus}:
            structural = False 
            issues.append(f"bad_status:{cid}")
            continue
        
        if not isinstance(evidence, list) or any(isinstance(e, bool) or not isinstance(e, int) for e in evidence):
            structural = False
            issues.append(f"bad_evidence:{cid}")
            continue
        
        if not isinstance(explanation, str):
            structural = False
            issues.append(f"bad_explanation:{cid}")
            continue
        
        if not isinstance(review, bool):
            structural = False
            issues.append(f"bad_review_required:{cid}")
            continue
        
        st = CriterionStatus(status)

        if cid in seen and seen[cid] != st:
            structural = False
            issues.append(f"conflict:{cid}")

        seen[cid] = st
        feedbacks.append(CriterionFeedback(cid, st, tuple(evidence), explanation, review))

    if not structural:
        return ValidationOutcome(False, False, False, tuple(issues), None)

    present = {c.criterion_id for c in feedbacks}
    coverage_ok = rubric.required_ids() <= present

    if not coverage_ok:
        issues.append("missing_required_criteria")

    lines = source_lines(submission)
    citations_ok = True

    for c in feedbacks:
        crit = rubric.get(c.criterion_id)
        if crit is None:
            citations_ok = False
            issues.append(f"unknown_criterion:{c.criterion_id}")
            continue
        
        if c.status == CriterionStatus.SATISFIED:
            if not c.evidence:
                citations_ok = False
                issues.append(f"satisfied_without_evidence:{c.criterion_id}")
                continue
            
            in_range = all(1 <= i <= len(lines) for i in c.evidence)
            confirmed = any(any(m in lines[i-1] for m in crit.markers) for i in c.evidence if 1 <= i <= len(lines))

            if not in_range or not confirmed:
                citations_ok = False
                issues.append(f"unconfirmed_citation:{c.criterion_id}")
        else:
            if c.evidence:
                citations_ok = False
                issues.append(f"evidence_on_non_satisfied:{c.criterion_id}")

    review_required = any(c.review_required for c in feedbacks) or not coverage_ok or not citations_ok
    report = RubricFeedbackReport(
        rubric_id = rubric.rubric_id, rubric_version = rubric.version, model_id = model_id,
        criteria = tuple(feedbacks), review_required = review_required)
    
    return ValidationOutcome(True, coverage_ok, citations_ok, tuple(issues), report)