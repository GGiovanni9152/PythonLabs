from school.domain.models import CorpusEntry, Pair, DerivationRelation
from school.analyzers.similarity.config import SimilarityConfig
from school.analyzers.similarity.token_baseline import TokenBaselineAnalyzer

TEMPLATE = "def solve():\n    # TODO: implement\n    pass"
CODE_A = TEMPLATE + "\n    x = 1\n    print(x)"
CODE_B = TEMPLATE + "\n    y = 2\n    print(y)"

def _pair_entries():
    a = CorpusEntry("s1", "st1", "a-1", "f1", CODE_A, "", DerivationRelation.EXACT_COPY, False)
    b = CorpusEntry("s2", "st2", "a-1", "f2", CODE_B, "", DerivationRelation.EXACT_COPY, False)
    
    p = Pair("s1", "s2", "a-1", "st1", "st2", "f1", "f2", DerivationRelation.EXACT_COPY, False)
    return p, {"s1": a, "s2": b}

def test_adding_template_changes_config_hash_and_report():
    p, entries = _pair_entries()
    analyzer = TokenBaselineAnalyzer()

    cfg1 = SimilarityConfig(version="1", templates={})
    cfg2 = SimilarityConfig(version="2", templates={"a-1": TEMPLATE})

    r1 = analyzer.analyze_pair(p, entries, config=cfg1)
    r2 = analyzer.analyze_pair(p, entries, config=cfg2)

    assert cfg1.config_hash != cfg2.config_hash
    assert r1.metadata["template_version"] == "1"
    assert r2.metadata["template_version"] == "2"
    assert r1.template_overlap == 0.0
    assert r2.template_overlap > 0.0