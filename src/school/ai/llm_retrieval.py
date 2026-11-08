from __future__ import annotations

from typing import Any

from sklearn.metrics.pairwise import cosine_similarity

from school.domain.contracts import SimilarityAnalyzer
from school.domain.models import CorpusEntry, Pair, SimilarityReport
from school.analyzers.similarity.tfidf_baseline import TfidfBaselineAnalyzer
from school.analyzers.similarity.token_utils import extract_tokens
from school.ai.stub_model import StubModel


class LLMRetrievalAnalyzer:
    analyzer_id = "llm_retrieval"
    analyzer_version = "1.0.0"
    
    def __init__(self, tfidf_analyzer: TfidfBaselineAnalyzer, top_k: int = 3):
        if not tfidf_analyzer._is_fitted:
            raise RuntimeError(
                "TfidfBaselineAnalyzer must be fitted before use. "
            )
        self._tfidf = tfidf_analyzer
        self._top_k = top_k
        self._model = StubModel()
    
    def analyze_pair(
        self,
        pair: Pair,
        entries: dict[str, CorpusEntry],
        template_code: str | None = None,
    ) -> SimilarityReport:

        entry_a = entries.get(pair.submission_id_a)
        entry_b = entries.get(pair.submission_id_b)
        
        if entry_a is None or entry_b is None:
            return SimilarityReport(
                analyzer_id = self.analyzer_id,
                analyzer_version=  self.analyzer_version,
                submission_id_a = pair.submission_id_a,
                submission_id_b = pair.submission_id_b,
                score = None,
                evidence = (),
                template_overlap = 0.0,
                metadata = {
                    "method": "llm_retrieval",
                    "error": "missing_entry",
                    "feedback": "one or both submissions not found in corpus.",
                },
            )
        
        candidates = self._find_similar_candidates(
            entry_a, entries,
            exclude_ids={pair.submission_id_a, pair.submission_id_b},
        )
        
        prompt = self._build_prompt(entry_a, entry_b, candidates, template_code)
        
        features: dict[str, Any] = {
            "prompt": prompt,
            "num_candidates": len(candidates),
            "has_template": template_code is not None,
            "submission_id_a": pair.submission_id_a,
            "submission_id_b": pair.submission_id_b,
        }
        
        raw_prediction = self._model.predict(features)
        
        feedback = self._generate_feedback(entry_a, entry_b, candidates, template_code, raw_prediction)
        
        return SimilarityReport(
            analyzer_id = self.analyzer_id,
            analyzer_version = self.analyzer_version,
            submission_id_a = pair.submission_id_a,
            submission_id_b = pair.submission_id_b,
            score = None,
            evidence = (),
            template_overlap = 0.0,
            metadata = {
                "method": "llm_retrieval",
                "top_k": self._top_k,
                "num_candidates_found": len(candidates),
                "has_template": template_code is not None,
                "feedback": feedback,
                "model_verdict": raw_prediction.get("verdict"),
                "model_confidence": raw_prediction.get("confidence"),
            },
        )
    
    def _find_similar_candidates(
        self,
        query_entry: CorpusEntry,
        entries: dict[str, CorpusEntry],
        exclude_ids: set[str],
    ) -> list[tuple[float, CorpusEntry]]:
        
        query_vec = self._tfidf._transform(query_entry.code)
        if query_vec is None:
            return []
        
        scored_candidates: list[tuple[float, CorpusEntry]] = []
        for entry_id, entry in entries.items():
            if entry_id in exclude_ids:
                continue

            if entry.assignment_id != query_entry.assignment_id:
                continue
            
            entry_vec = self._tfidf._transform(entry.code)
            if entry_vec is not None:
                sim = float(cosine_similarity(query_vec, entry_vec)[0, 0])
                scored_candidates.append((sim, entry))
        
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        return scored_candidates[:self._top_k]
    
    def _build_prompt(
        self,
        entry_a: CorpusEntry,
        entry_b: CorpusEntry,
        candidates: list[tuple[float, CorpusEntry]],
        template_code: str | None,
    ) -> str:
        lines: list[str] = []
        lines.append("анализ сходства кода")
        lines.append("")
        lines.append(f"сдача A (student_id={entry_a.student_id}):")
        lines.append("```python")
        lines.append(entry_a.code)
        lines.append("```")
        lines.append("")
        lines.append(f"сдача B (student_id={entry_b.student_id}):")
        lines.append("```python")
        lines.append(entry_b.code)
        lines.append("```")
        lines.append("")
        
        if candidates:
            lines.append(f"похожие работы других студентов (top-{len(candidates)}):")
            for i, (sim, candidate) in enumerate(candidates, start=1):
                lines.append(f"\n{i}. student_id={candidate.student_id} (similarity={sim:.3f}):")
                lines.append("```python")
                lines.append(candidate.code)
                lines.append("```")
        else:
            lines.append("похожих работ других студентов не найдено.")
        
        lines.append("")
        
        if template_code:
            lines.append("разрешённый шаблон задания:")
            lines.append("```python")
            lines.append(template_code)
            lines.append("```")
        else:
            lines.append("шаблон задания не предоставлен.")
        
        lines.append("")
        lines.append(
            "опиши, что общего и чем отличаются сдачи A и B. "
            "Учти, что совпадение с разрешённым шаблоном не является нарушением."
        )
        
        return "\n".join(lines)
    
    def _generate_feedback(
        self,
        entry_a: CorpusEntry,
        entry_b: CorpusEntry,
        candidates: list[tuple[float, CorpusEntry]],
        template_code: str | None,
        raw_prediction: dict[str, Any],
    ) -> str:

        verdict = raw_prediction.get("verdict", "unknown")
        confidence = raw_prediction.get("confidence", 0.0)
        
        parts: list[str] = []
        parts.append(f"llm retrieval verdict={verdict}, confidence={confidence:.2f}")
        parts.append(f"найдено {len(candidates)} похожих кандидатов.")
        
        tokens_a = set(extract_tokens(entry_a.code))
        tokens_b = set(extract_tokens(entry_b.code))
        
        if not tokens_a and not tokens_b:
            parts.append("обе сдачи содержат некорректный или пустой код.")

        elif not tokens_a:
            parts.append(f"сдача A ({entry_a.submission_id}) содержит некорректный код.")

        elif not tokens_b:
            parts.append(f"сдача B ({entry_b.submission_id}) содержит некорректный код.")

        else:
            common = tokens_a & tokens_b
            unique_a = tokens_a - tokens_b
            unique_b = tokens_b - tokens_a
            parts.append(
                f"общие токены: {len(common)}, "
                f"уникальные для A: {len(unique_a)}, "
                f"уникальные для B: {len(unique_b)}."
            )
        
        if template_code:
            template_tokens = set(extract_tokens(template_code))

            overlap_a = len(tokens_a & template_tokens)
            overlap_b = len(tokens_b & template_tokens)

            parts.append(
                f"cовпадение с шаблоном: A={overlap_a} токенов, B={overlap_b} токенов "
                f"(совпадение с шаблоном разрешено)."
            )
        
        return " ".join(parts)