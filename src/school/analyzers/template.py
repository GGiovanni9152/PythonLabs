from __future__ import annotations

from school.domain.contracts import AnalysisContext
from school.domain.models import AnalysisReport, Submission

class TemplateAnalyzer:
    analyzer_id = "template"
    analyzer_version = "1.0.0"

    def analyze(self, submission: Submission, context: AnalysisContext) -> AnalysisReport:
        if not context.template_text: #если нет темплейта
            return AnalysisReport(
                analyzer_id = self.analyzer_id,
                analyzer_version = self.analyzer_version,
                score = None,
                rubric_feedback = "no template provided for this assignment.",
                similarity = None,
                evidence = (),
            )

        template_lines = [ln for ln in context.template_text.splitlines() if ln.strip()]
        if not template_lines: #если темплейт пустой
            return AnalysisReport(
                analyzer_id = self.analyzer_id,
                analyzer_version = self.analyzer_version,
                score = None,
                rubric_feedback = "template is empty.",
                similarity = None,
                evidence = (),
            )

        template_set = set(template_lines)
        matched: list[int] = []

        def scan(source: str, offset: int) -> None:
            for i, line in enumerate(source.splitlines(), start=1):
                if line in template_set:
                    matched.append(i + offset)

        scan(submission.text, 0)
        text_lines_count = len(submission.text.splitlines())
        scan(submission.code, text_lines_count) #сквозная нумерация

        similarity = len(set(matched)) / len(template_set) if template_set else 0.0
        feedback = (
            f"exact template matches: {len(set(matched))}/{len(template_set)}. "
            f"matching with the allowed template is permitted."
        )

        return AnalysisReport(
            analyzer_id = self.analyzer_id,
            analyzer_version = self.analyzer_version,
            score = None,
            rubric_feedback = feedback,
            similarity = similarity,
            evidence = tuple(sorted(set(matched))),
        )