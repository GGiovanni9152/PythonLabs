"""Тесты на корректность разделения корпуса."""
from pathlib import Path

from school.sources.corpus_source import CorpusSource


def test_no_family_leakage():
    corpus_dir = Path("data/corpus")
    
    train_source = CorpusSource(corpus_dir / "corpus_train.jsonl")
    test_source = CorpusSource(corpus_dir / "corpus_test.jsonl")
    
    train_families = set(e.family_id for e in train_source.iter_entries())
    test_families = set(e.family_id for e in test_source.iter_entries())
    
    overlap = train_families & test_families
    assert not overlap, f"утечка: {overlap}"



def test_template_pairs_exist():
    corpus_dir = Path("data/corpus")
    
    train_source = CorpusSource(corpus_dir / "pairs_train.jsonl")
    test_source = CorpusSource(corpus_dir / "pairs_test.jsonl")
    
    all_pairs = list(train_source.iter_pairs()) + list(test_source.iter_pairs())
    template_pairs = [p for p in all_pairs if p.template_only]
    
    assert len(template_pairs) > 0, f"нет пар с template_only"