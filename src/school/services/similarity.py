from __future__ import annotations

from typing import Iterable

from school.domain.contracts import SimilarityAnalyzer
from school.domain.models import CorpusEntry, Pair, SimilarityReport


class SimilarityService:
    def __init__(self, analyzer: SimilarityAnalyzer):
        self._analyzer = analyzer
    
    def compare_pairs(
        self,
        pairs: Iterable[Pair],
        entries: dict[str, CorpusEntry],
        template_code: str | None = None,
    ) -> list[SimilarityReport]:

        reports = []
        for pair in pairs:
            #один и тот же студент
            if pair.student_id_a == pair.student_id_b:
                continue

            #без сравнений одинаковых решений
            if pair.submission_id_a == pair.submission_id_b:
                continue
            
            if pair.submission_id_a not in entries or pair.submission_id_b not in entries:
                continue
            
            report = self._analyzer.analyze_pair(pair, entries, template_code)
            reports.append(report)
        
        return reports