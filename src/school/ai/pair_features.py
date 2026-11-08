from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from school.domain.models import CorpusEntry, Pair
from school.analyzers.similarity.token_utils import extract_tokens, ngrams, jaccard_similarity
from school.analyzers.similarity.tfidf_baseline import TfidfBaselineAnalyzer


@dataclass(frozen=True)
class PairFeatures:
    submission_id_a: str
    submission_id_b: str
    cosine_similarity: float
    jaccard_similarity: float | None
    token_count_diff: int
    template_overlap_a: float
    template_overlap_b: float
    feature_vector: np.ndarray
    metadata: dict[str, Any] = field(default_factory=dict)


class PairFeatureExtractor:  
    def __init__(self, tfidf_analyzer: TfidfBaselineAnalyzer):
        self._tfidf = tfidf_analyzer
    
    def extract(
        self,
        pair: Pair,
        entries: dict[str, CorpusEntry],
        template_code: str | None = None,
    ) -> PairFeatures:

        entry_a = entries[pair.submission_id_a]
        entry_b = entries[pair.submission_id_b]
        
        vec_a = self._tfidf._transform(entry_a.code)
        vec_b = self._tfidf._transform(entry_b.code)
        
        if vec_a is not None and vec_b is not None:
            cosine_sim = float(cosine_similarity(vec_a, vec_b)[0, 0])
        else:
            cosine_sim = 0.0
        
        tokens_a = extract_tokens(entry_a.code)
        tokens_b = extract_tokens(entry_b.code)

        ngrams_a = ngrams(tokens_a, n = 3)
        ngrams_b = ngrams(tokens_b, n = 3)

        jaccard_sim = jaccard_similarity(ngrams_a, ngrams_b)
        
        token_count_diff = abs(len(tokens_a) - len(tokens_b))
        
        template_overlap_a = 0.0
        template_overlap_b = 0.0

        if template_code:
            template_tokens = set(extract_tokens(template_code))

            tokens_a_set = set(tokens_a)
            tokens_b_set = set(tokens_b)

            template_overlap_a = 0.0
            template_overlap_b = 0.0

            if (tokens_a_set):
                template_overlap_a = len(tokens_a_set & template_tokens) / len(tokens_a_set)

            if (tokens_b_set):
                template_overlap_b = len(tokens_b_set & template_tokens) / len(tokens_b_set)
            
        
        if vec_a is not None and vec_b is not None:
            vec_a_dense = vec_a.toarray().flatten()
            vec_b_dense = vec_b.toarray().flatten()

            vec_diff = vec_a_dense - vec_b_dense
            feature_vector = np.concatenate([vec_a_dense, vec_b_dense, vec_diff])
        
        else:
            feature_vector = np.array([])
        
        return PairFeatures(
            submission_id_a = pair.submission_id_a,
            submission_id_b = pair.submission_id_b,
            cosine_similarity = cosine_sim,
            jaccard_similarity = jaccard_sim,
            token_count_diff = token_count_diff,
            template_overlap_a = template_overlap_a,
            template_overlap_b = template_overlap_b,
            feature_vector = feature_vector,
            metadata = {
                "tokens_a": len(tokens_a),
                "tokens_b": len(tokens_b),
            },
        )