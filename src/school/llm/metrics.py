from __future__ import annotations

from dataclasses import dataclass
from school.llm.validator import ValidationOutcome


@dataclass(frozen=True, slots=True)
class LLMMetrics:
    total: int
    structural_valid_ratio: float
    coverage_ratio: float
    citations_ratio: float
    manual_agreement_ratio: float


def compute_llm_metrics(outcomes: list[ValidationOutcome],
                        manual_labels: list[bool]) -> LLMMetrics:
    n = len(outcomes)
    if n == 0:
        return LLMMetrics(0, 0.0, 0.0, 0.0, 0.0)
    
    sv = sum(o.structural_valid for o in outcomes) / n
    cov = sum(o.coverage_ok for o in outcomes) / n
    cit = sum(o.citations_ok for o in outcomes) / n
    agree = sum(o.is_valid == m for o, m in zip(outcomes, manual_labels)) / n
    
    return LLMMetrics(n, sv, cov, cit, agree)