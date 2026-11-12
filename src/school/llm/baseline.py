from __future__ import annotations

from school.domain.models import Submission
from school.llm.models import Rubric, RubricFeedbackReport, CriterionFeedback, CriterionStatus, source_lines


class LocalRubricBaseline:
    model_id = "local_baseline"

    def evaluate(self, submission: Submission, rubric: Rubric) -> RubricFeedbackReport:
        lines = source_lines(submission)
        feedbacks = []
        for crit in rubric.criteria:
            if not crit.markers:
                feedbacks.append(CriterionFeedback(
                    crit.criterion_id, CriterionStatus.INSUFFICIENT_EVIDENCE, (),
                    "no markers defined; cannot verify locally.", False))
                continue
            hits = tuple(
                i for i, ln in enumerate(lines, start=1)
                if any(m in ln for m in crit.markers)
            )
            if hits:
                feedbacks.append(CriterionFeedback(
                    crit.criterion_id, CriterionStatus.SATISFIED, hits,
                    f"found marker(s) on line(s) {hits}.", False))
            else:
                feedbacks.append(CriterionFeedback(
                    crit.criterion_id, CriterionStatus.NOT_SATISFIED, (),
                    "no marker found in source.", False))
        return RubricFeedbackReport(
            rubric_id = rubric.rubric_id, rubric_version = rubric.version,
            model_id = self.model_id, criteria = tuple(feedbacks), review_required = False)