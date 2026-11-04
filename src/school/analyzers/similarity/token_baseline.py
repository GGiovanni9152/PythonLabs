from __future__ import annotations

from school.domain.contracts import SimilarityAnalyzer
from school.domain.models import CorpusEntry, Pair, SimilarityReport
from school.analyzers.similarity.token_utils import extract_tokens, ngrams, jaccard_similarity, extract_template_tokens

class TokenBaselineAnalyzer:
    analyzer_id = "token_baseline"
    analyzer_version = "1.0.0"
    
    def analyze_pair(self, pair: Pair, entries: dict[str, CorpusEntry], template_code: str | None = None) -> SimilarityReport:
        entry_a = entries[pair.submission_id_a]
        entry_b = entries[pair.submission_id_b]
        
        tokens_a = extract_tokens(entry_a.code)
        tokens_b = extract_tokens(entry_b.code)
        
        if not tokens_a and not tokens_b:
            return SimilarityReport(
                analyzer_id = self.analyzer_id,
                analyzer_version = self.analyzer_version,
                submission_id_a = pair.submission_id_a,
                submission_id_b = pair.submission_id_b,
                score = None,
                evidence = (),
                template_overlap = 0.0,
                metadata = {"reason": "empty_or_invalid_code"},
            )
        
        ngrams_a = ngrams(tokens_a, n = 3)
        ngrams_b = ngrams(tokens_b, n = 3)
        
        score = jaccard_similarity(ngrams_a, ngrams_b)
        
        template_overlap = 0.0
        if template_code:
            template_tokens = extract_template_tokens(template_code)
            tokens_a_set = set(tokens_a)
            tokens_b_set = set(tokens_b)
            
            overlap_a = len(tokens_a_set & template_tokens) / len(tokens_a_set) if tokens_a_set else 0.0
            overlap_b = len(tokens_b_set & template_tokens) / len(tokens_b_set) if tokens_b_set else 0.0
            template_overlap = (overlap_a + overlap_b) / 2
        
        evidence = self._find_matching_lines(entry_a.code, entry_b.code)
        
        return SimilarityReport(
            analyzer_id = self.analyzer_id,
            analyzer_version = self.analyzer_version,
            submission_id_a = pair.submission_id_a,
            submission_id_b = pair.submission_id_b,
            score = score,
            evidence = evidence,
            template_overlap = template_overlap,
            metadata = {
                "tokens_a": len(tokens_a),
                "tokens_b": len(tokens_b),
                "ngrams_a": len(ngrams_a),
                "ngrams_b": len(ngrams_b),
            },
        )
    
    def _find_matching_lines(self, code_a: str, code_b: str) -> tuple[tuple[int, int], ...]:
        lines_a = code_a.splitlines()
        lines_b = code_b.splitlines()
        
        evidence = []
        for i, line_a in enumerate(lines_a, start=1):
            for j, line_b in enumerate(lines_b, start=1):
                if line_a.strip() == line_b.strip() and line_a.strip():
                    evidence.append((i, j))
        
        return tuple(evidence)