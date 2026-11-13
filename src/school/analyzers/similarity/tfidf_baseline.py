from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from school.domain.contracts import SimilarityAnalyzer
from school.domain.models import CorpusEntry, Pair, SimilarityReport
from school.analyzers.similarity.token_utils import extract_tokens


class TfidfBaselineAnalyzer:
    analyzer_id = "tfidf_baseline"
    analyzer_version = "1.0.0"
    
    def __init__(self):
        self._vectorizer = TfidfVectorizer(
            analyzer = 'word',
            ngram_range = (3, 3),
            token_pattern = r'\S+',
            lowercase = False,
        )
        self._is_fitted = False
    
    def fit(self, entries: list[CorpusEntry]) -> None:
        codes = [' '.join(extract_tokens(e.code)) for e in entries]
        codes = [c for c in codes if c.strip()]
        if codes:
            self._vectorizer.fit(codes)
            self._is_fitted = True
    
    def _transform(self, code: str):
        if not self._is_fitted:
            raise RuntimeError("analyzer not fitted, fit() first")
        tokens = extract_tokens(code)
        text = ' '.join(tokens)
        if not text.strip():
            return None
        return self._vectorizer.transform([text])
    
    def analyze_pair(
        self,
        pair: Pair,
        entries: dict[str, CorpusEntry],
        template_code: str | None = None,
        *, 
        config=None
    ) -> SimilarityReport:
        if config is not None:
            template_code = config.template_for(pair.assignment_id) or template_code
        
        entry_a = entries[pair.submission_id_a]
        entry_b = entries[pair.submission_id_b]
        
        vec_a = self._transform(entry_a.code)
        vec_b = self._transform(entry_b.code)
        
        if vec_a is None or vec_b is None:
            meta = {"reason": "empty_or_invalid_code"}
            if config is not None:
                meta["config_hash"] = config.config_hash
                meta["template_version"] = config.version

            return SimilarityReport(
                analyzer_id = self.analyzer_id,
                analyzer_version = self.analyzer_version,
                submission_id_a = pair.submission_id_a,
                submission_id_b = pair.submission_id_b,
                score = None,
                evidence = (),
                template_overlap = 0.0,
                metadata = meta,
            )
        
        score = float(cosine_similarity(vec_a, vec_b)[0, 0])
        
        template_overlap = 0.0
        if template_code:
            template_tokens = set(extract_tokens(template_code))
            tokens_a = set(extract_tokens(entry_a.code))
            tokens_b = set(extract_tokens(entry_b.code))

            overlap_a = 0.0
            overlap_b = 0.0

            if (tokens_a):
                overlap_a = len(tokens_a & template_tokens) / len(tokens_a)

            if (tokens_b):
                overlap_b = len(tokens_b & template_tokens) / len(tokens_b)

            template_overlap = (overlap_a + overlap_b) / 2

        meta = {"method": "tfidf_cosine"}
        if config is not None:
            meta["config_hash"] = config.config_hash
            meta["template_version"] = config.version
        
        
        return SimilarityReport(
            analyzer_id = self.analyzer_id,
            analyzer_version = self.analyzer_version,
            submission_id_a = pair.submission_id_a,
            submission_id_b = pair.submission_id_b,
            score = score,
            evidence = (),
            template_overlap = template_overlap,
            metadata = meta,
        )