from pathlib import Path

from school.sources.corpus_source import CorpusSource
from school.analyzers.similarity.tfidf_baseline import TfidfBaselineAnalyzer
from school.services.similarity import SimilarityService


def main():
    corpus_dir = Path("data/corpus")
    
    train_entries_list = list(CorpusSource(corpus_dir / "corpus_train.jsonl").iter_entries())
    test_entries_list = list(CorpusSource(corpus_dir / "corpus_test.jsonl").iter_entries())
    
    train_pairs = list(CorpusSource(corpus_dir / "pairs_train.jsonl").iter_pairs())
    test_pairs = list(CorpusSource(corpus_dir / "pairs_test.jsonl").iter_pairs())
    
    train_entries = {e.submission_id: e for e in train_entries_list}
    test_entries = {e.submission_id: e for e in test_entries_list}
    
    analyzer = TfidfBaselineAnalyzer()
    
    print("обучение векторизатора")
    print(f"{len(train_entries)} записей")
    analyzer.fit(train_entries_list)
    
    service = SimilarityService(analyzer)
    print("оценка на train")
    train_reports = service.compare_pairs(train_pairs, train_entries)
    
    all_entries = {**train_entries, **test_entries}
    
    print("оценка на test")
    test_reports = service.compare_pairs(test_pairs, all_entries)

    print(f"train reports: {len(train_reports)}")
    print(f"test reports: {len(test_reports)}")
    
    if test_reports:
        r = test_reports[0]
        print(f"example: {r.submission_id_a} x {r.submission_id_b} score:{r.score}")


if __name__ == "__main__":
    main()