import json
from pathlib import Path

from school.domain.models import CorpusEntry, Pair, DerivationRelation
from school.analyzers.similarity.config import SimilarityConfig
from school.analyzers.similarity.token_baseline import TokenBaselineAnalyzer

CODE_A = "def solve():\n    # TODO: implement\n    pass\n    x = 1\n    print(x)"
CODE_B = "def solve():\n    # TODO: implement\n    pass\n    y = 2\n    print(y)"

def entry(sid, code):
    return CorpusEntry(sid, f"st-{sid}", "a-1", "f1", code, "", DerivationRelation.EXACT_COPY, False)

def load_cfg(p):
    d = json.loads(Path(p).read_text(encoding="utf-8"))
    return SimilarityConfig(version=d["version"], templates=d["templates"])

def main():
    a, b = entry("s1", CODE_A), entry("s2", CODE_B)
    pair = Pair("s1", "s2", "a-1", "st-s1", "st-s2", "f1", "f1", DerivationRelation.EXACT_COPY, False)
    entries = {"s1": a, "s2": b}
    analyzer = TokenBaselineAnalyzer()

    for path in ["configs/similarity_v1.json", "configs/similarity_v2.json"]:
        cfg = load_cfg(path)
        r = analyzer.analyze_pair(pair, entries, config=cfg)
        print(f"\nconfig={path} version={cfg.version}")
        print(f"  config_hash={r.metadata['config_hash'][:12]}...")
        print(f"  score={r.score:.3f} template_overlap={r.template_overlap:.3f}")

if __name__ == "__main__":
    main()