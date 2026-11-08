import pytest
import numpy as np

from school.ai.pair_features import PairFeatureExtractor, PairFeatures
from school.ai.llm_retrieval import LLMRetrievalAnalyzer
from school.analyzers.similarity.tfidf_baseline import TfidfBaselineAnalyzer
from school.domain.models import CorpusEntry, Pair, DerivationRelation


def _make_entry(submission_id: str, code: str, family_id: str = "fam-1") -> CorpusEntry:
    return CorpusEntry(
        submission_id = submission_id,
        student_id = f"student-{submission_id}",
        assignment_id = "a-1",
        family_id = family_id,
        code = code,
        text = "Test",
        derivation_relation = DerivationRelation.EXACT_COPY,
        template_only = False,
    )


def _make_pair(entry_a: CorpusEntry, entry_b: CorpusEntry) -> Pair:
    return Pair(
        submission_id_a = entry_a.submission_id,
        submission_id_b = entry_b.submission_id,
        assignment_id = entry_a.assignment_id,
        student_id_a = entry_a.student_id,
        student_id_b = entry_b.student_id,
        family_id_a = entry_a.family_id,
        family_id_b = entry_b.family_id,
        derivation_relation = DerivationRelation.EXACT_COPY,
        template_only = False,
    )


def test_pair_feature_extractor_creates_features():
    code_a = 'def solve():\n    x = int(input())\n    print(x * 2)'
    code_b = 'def solve():\n    x = int(input())\n    print(x * 2)'
    
    entry_a = _make_entry("sub-001", code_a)
    entry_b = _make_entry("sub-002", code_b, family_id="fam-2")
    pair = _make_pair(entry_a, entry_b)
    
    tfidf = TfidfBaselineAnalyzer()
    tfidf.fit([entry_a, entry_b])
    
    extractor = PairFeatureExtractor(tfidf)
    entries = {entry_a.submission_id: entry_a, entry_b.submission_id: entry_b}
    features = extractor.extract(pair, entries)
    
    assert isinstance(features, PairFeatures)
    assert features.cosine_similarity == 1.0
    assert features.jaccard_similarity == 1.0
    assert features.token_count_diff == 0
    assert len(features.feature_vector) > 0


def test_pair_features_include_difference_vector():
    code_a = 'def solve():\n    x = 1'
    code_b = 'def solve():\n    x = 2'
    
    entry_a = _make_entry("sub-001", code_a)
    entry_b = _make_entry("sub-002", code_b, family_id="fam-2")
    pair = _make_pair(entry_a, entry_b)
    
    tfidf = TfidfBaselineAnalyzer()
    tfidf.fit([entry_a, entry_b])
    
    extractor = PairFeatureExtractor(tfidf)
    entries = {entry_a.submission_id: entry_a, entry_b.submission_id: entry_b}
    features = extractor.extract(pair, entries)

    assert len(features.feature_vector) > 0


def test_llm_retrieval_finds_candidates():
    code_a = 'def solve():\n    x = int(input())\n    print(x * 2)'
    code_b = 'def solve():\n    y = int(input())\n    print(y * 2)'
    code_c = 'def process():\n    items = input().split()\n    print(len(items))'
    
    entry_a = _make_entry("sub-001", code_a)
    entry_b = _make_entry("sub-002", code_b, family_id="fam-2")
    entry_c = _make_entry("sub-003", code_c, family_id="fam-3")
    
    pair = _make_pair(entry_a, entry_b)
    
    tfidf = TfidfBaselineAnalyzer()
    tfidf.fit([entry_a, entry_b, entry_c])
    
    analyzer = LLMRetrievalAnalyzer(tfidf, top_k=2)
    entries = {
        entry_a.submission_id: entry_a,
        entry_b.submission_id: entry_b,
        entry_c.submission_id: entry_c,
    }
    
    report = analyzer.analyze_pair(pair, entries)
    
    assert report.analyzer_id == "llm_retrieval"
    assert report.metadata["num_candidates_found"] <= 2
    assert "feedback" in report.metadata


def test_llm_retrieval_excludes_self_and_pair():
    code_a = 'def solve():\n    x = 1'
    code_b = 'def solve():\n    x = 2'
    code_c = 'def solve():\n    x = 3'
    
    entry_a = _make_entry("sub-001", code_a)
    entry_b = _make_entry("sub-002", code_b, family_id="fam-2")
    entry_c = _make_entry("sub-003", code_c, family_id="fam-3")
    
    pair = _make_pair(entry_a, entry_b)
    
    tfidf = TfidfBaselineAnalyzer()
    tfidf.fit([entry_a, entry_b, entry_c])
    
    analyzer = LLMRetrievalAnalyzer(tfidf, top_k=5)
    entries = {
        entry_a.submission_id: entry_a,
        entry_b.submission_id: entry_b,
        entry_c.submission_id: entry_c,
    }
    
    report = analyzer.analyze_pair(pair, entries)
    
    assert report.metadata["num_candidates_found"] == 1
    assert "feedback" in report.metadata
    assert "llm retrieval" in report.metadata["feedback"]


def test_llm_retrieval_includes_template_in_prompt():
    code_a = 'def solve():\n    x = 1'
    code_b = 'def solve():\n    x = 2'
    
    entry_a = _make_entry("sub-001", code_a)
    entry_b = _make_entry("sub-002", code_b, family_id="fam-2")
    pair = _make_pair(entry_a, entry_b)
    
    tfidf = TfidfBaselineAnalyzer()
    tfidf.fit([entry_a, entry_b])
    
    analyzer = LLMRetrievalAnalyzer(tfidf, top_k=1)
    entries = {entry_a.submission_id: entry_a, entry_b.submission_id: entry_b}
    
    template_code = 'def solve():\n    pass'
    report = analyzer.analyze_pair(pair, entries, template_code=template_code)
    
    assert report.metadata["has_template"] is True

def test_retrieval_excludes_different_assignment():
    code_a = 'def solve():\n    x = 1'
    code_b = 'def solve():\n    x = 2'
    code_c = 'def process():\n    items = input()'
    
    entry_a = CorpusEntry(
        submission_id="sub-001",
        student_id="student-001",
        assignment_id="a-1",
        family_id="fam-1",
        code=code_a,
        text="Test",
        derivation_relation=DerivationRelation.EXACT_COPY,
        template_only=False,
    )
    entry_b = CorpusEntry(
        submission_id="sub-002",
        student_id="student-002",
        assignment_id="a-1",
        family_id="fam-2",
        code=code_b,
        text="Test",
        derivation_relation=DerivationRelation.EXACT_COPY,
        template_only=False,
    )
    entry_c = CorpusEntry(
        submission_id="sub-003",
        student_id="student-003",
        assignment_id="a-2",
        family_id="fam-3",
        code=code_c,
        text="Test",
        derivation_relation=DerivationRelation.INDEPENDENT,
        template_only=False,
    )
    
    pair = Pair(
        submission_id_a=entry_a.submission_id,
        submission_id_b=entry_b.submission_id,
        assignment_id="a-1",
        student_id_a=entry_a.student_id,
        student_id_b=entry_b.student_id,
        family_id_a=entry_a.family_id,
        family_id_b=entry_b.family_id,
        derivation_relation=DerivationRelation.EXACT_COPY,
        template_only=False,
    )
    
    tfidf = TfidfBaselineAnalyzer()
    tfidf.fit([entry_a, entry_b, entry_c])
    
    analyzer = LLMRetrievalAnalyzer(tfidf, top_k=5)
    entries = {
        entry_a.submission_id: entry_a,
        entry_b.submission_id: entry_b,
        entry_c.submission_id: entry_c,
    }
    
    report = analyzer.analyze_pair(pair, entries)

    assert report.metadata["num_candidates_found"] == 0, f"ожидалось 0 кандидатов, найдено {report.metadata['num_candidates_found']}"
    assert "feedback" in report.metadata