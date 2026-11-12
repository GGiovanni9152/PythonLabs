from pathlib import Path

from school.domain.models import CorpusEntry, Pair, DerivationRelation
from school.analyzers.similarity.token_baseline import TokenBaselineAnalyzer
from school.services.similarity import SimilarityService

CODE = "def solve():\n    x = int(input())\n    print(x)"


def entry(sid, student, code=CODE, fam="f1", assign="a1"):
    return CorpusEntry(sid, student, assign, fam, code, "", DerivationRelation.EXACT_COPY, False)


def pair(a, b):
    return Pair(a.submission_id, b.submission_id, a.assignment_id,
                a.student_id, b.student_id, a.family_id, b.family_id,
                DerivationRelation.EXACT_COPY, False)


def test_self_match_excluded_by_service():
    e = entry("s1", "st1")
    p = Pair("s1", "s1", "a1", "st1", "st1", "f1", "f1", DerivationRelation.EXACT_COPY, False)
    svc = SimilarityService(TokenBaselineAnalyzer())
    assert svc.compare_pairs([p], {"s1": e}) == []


def test_same_student_not_in_cross_reports():
    a, b = entry("s1", "st1"), entry("s2", "st1")
    svc = SimilarityService(TokenBaselineAnalyzer())
    assert svc.compare_pairs([pair(a, b)], {"s1": a, "s2": b}) == []


def test_repeat_versions_tracked_separately():
    a, b = entry("s1", "st1"), entry("s2", "st1")
    svc = SimilarityService(TokenBaselineAnalyzer())
    repeats = svc.repeat_version_pairs([pair(a, b)])
    assert len(repeats) == 1
    assert repeats[0].submission_id_a == "s1"


def test_cross_student_compared():
    a, b = entry("s1", "st1"), entry("s2", "st2", fam="f2")
    svc = SimilarityService(TokenBaselineAnalyzer())
    reports = svc.compare_pairs([pair(a, b)], {"s1": a, "s2": b})
    assert len(reports) == 1 and reports[0].score == 1.0


def test_corpus_reproducible(tmp_path):
    from scripts.generate_corpus import generate_corpus
    generate_corpus(tmp_path / "a", seed=42)
    generate_corpus(tmp_path / "b", seed=42)
    for f in ["corpus_train.jsonl", "corpus_test.jsonl", "pairs_train.jsonl", "pairs_test.jsonl"]:
        assert (tmp_path / "a" / f).read_text() == (tmp_path / "b" / f).read_text(), f


def test_saved_llm_experiment_reproducible():
    from scripts.llm_evaluation import build_cases
    from school.llm.models import load_rubric
    from school.llm.service import LLMRubricService
    from school.llm.metrics import compute_llm_metrics

    rubric = load_rubric("data/rubric.json")

    def run():
        outs, manual = [], []
        for name, client, subm, expected in build_cases():
            outs.append(LLMRubricService(client).run(subm, rubric))
            manual.append(expected)
        return compute_llm_metrics(outs, manual)

    assert run() == run()