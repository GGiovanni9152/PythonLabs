from __future__ import annotations

from src.domain.contracts import AnalysisContext
from src.domain.models import AnalysisReport, Submission

class LengthAnalyzer:
    analyzer_id = "length"
    analyzer_version = "1.0.0"

    @staticmethod
    def _count_non_empty(s: str) -> int:
        return sum(1 for line in s.splitlines() if line.strip())

    def analyze(self, submission: Submission, context: AnalysisContext) -> AnalysisReport:
        n_text = self._count_non_empty(submission.text)
        n_code = self._count_non_empty(submission.code)

        feedback = (
            f"non-empty lines: text={n_text}, code={n_code}, total={n_text + n_code}."
        )
        return AnalysisReport(
            analyzer_id = self.analyzer_id,
            analyzer_version = self.analyzer_version,
            score = None,
            rubric_feedback = feedback,
            similarity = None,
            evidence = (),
            metadata = {"text_lines": n_text, "code_lines": n_code, "total_lines": n_text + n_code},
        )