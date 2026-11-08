from __future__ import annotations

from pathlib import Path
from typing import Any

from school.sources.corpus_source import CorpusSource
from school.analyzers.similarity.token_baseline import TokenBaselineAnalyzer
from school.analyzers.similarity.tfidf_baseline import TfidfBaselineAnalyzer
from school.services.similarity import SimilarityService
from school.evaluation.metrics import find_optimal_threshold, evaluate_method, EvaluationReport
from school.domain.models import DerivationRelation


def load_data(corpus_dir: Path):
    train_entries = list(CorpusSource(corpus_dir / "corpus_train.jsonl").iter_entries())
    test_entries = list(CorpusSource(corpus_dir / "corpus_test.jsonl").iter_entries())
    train_pairs = list(CorpusSource(corpus_dir / "pairs_train.jsonl").iter_pairs())
    test_pairs = list(CorpusSource(corpus_dir / "pairs_test.jsonl").iter_pairs())
    
    train_dict = {e.submission_id: e for e in train_entries}
    test_dict = {e.submission_id: e for e in test_entries}
    all_entries = {**train_dict, **test_dict}
    
    return train_entries, test_entries, train_pairs, test_pairs, all_entries


def get_labels(pairs, entries):
    labels = []
    for pair in pairs:
        entry_a = entries[pair.submission_id_a]
        entry_b = entries[pair.submission_id_b]
        
        is_similar = (
            entry_a.derivation_relation != DerivationRelation.INDEPENDENT and
            entry_b.derivation_relation != DerivationRelation.INDEPENDENT
        )
        labels.append(is_similar)
    
    return labels


def run_method_evaluation(
    analyzer,
    train_pairs,
    test_pairs,
    train_entries,
    test_entries,
    all_entries,
    method_name: str,
) -> tuple[EvaluationReport, EvaluationReport]:
    train_dict = {e.submission_id: e for e in train_entries}
    test_dict = {e.submission_id: e for e in test_entries}
    
    train_service = SimilarityService(analyzer)
    train_reports = train_service.compare_pairs(train_pairs, train_dict)
    train_scores = [r.score for r in train_reports]
    train_labels = get_labels(train_pairs, train_dict)
    
    threshold, best_f1 = find_optimal_threshold(train_scores, train_labels)
    print(f"{method_name}: оптимальный порог = {threshold:.2f}, f1 = {best_f1:.3f}")
    
    train_report = evaluate_method(train_scores, train_labels, threshold, f"{method_name} (train)")
    
    test_service = SimilarityService(analyzer)
    test_reports = test_service.compare_pairs(test_pairs, all_entries)
    test_scores = [r.score for r in test_reports]
    test_labels = get_labels(test_pairs, all_entries)
    
    test_report = evaluate_method(test_scores, test_labels, threshold, f"{method_name} (test)")
    
    return train_report, test_report


def analyze_errors(test_reports, test_pairs, entries, method_name: str) -> list[dict[str, Any]]:
    errors = []
    
    for report, pair in zip(test_reports, test_pairs):
        entry_a = entries[pair.submission_id_a]
        entry_b = entries[pair.submission_id_b]
        
        is_similar = (
            entry_a.derivation_relation != DerivationRelation.INDEPENDENT and
            entry_b.derivation_relation != DerivationRelation.INDEPENDENT
        )
        
        threshold = 0.5
        predicted = report.score >= threshold if report.score is not None else None
        
        #FP
        if predicted and not is_similar:
            errors.append({
                "type": "false_positive",
                "submission_a": pair.submission_id_a,
                "submission_b": pair.submission_id_b,
                "score": report.score,
                "derivation_a": entry_a.derivation_relation.value,
                "derivation_b": entry_b.derivation_relation.value,
                "template_overlap": report.template_overlap,
            })
        
        #FN
        elif not predicted and is_similar and report.score is not None:
            errors.append({
                "type": "false_negative",
                "submission_a": pair.submission_id_a,
                "submission_b": pair.submission_id_b,
                "score": report.score,
                "derivation_a": entry_a.derivation_relation.value,
                "derivation_b": entry_b.derivation_relation.value,
                "template_overlap": report.template_overlap,
            })
        
        #неопределённый результат
        elif report.score is None:
            errors.append({
                "type": "undefined",
                "submission_a": pair.submission_id_a,
                "submission_b": pair.submission_id_b,
                "derivation_a": entry_a.derivation_relation.value,
                "derivation_b": entry_b.derivation_relation.value,
            })
    
    return errors


def print_report(report: EvaluationReport):
    print(f"method: {report.method_name}")
    print(f"threshold: {report.threshold:.2f}")
    print(f"num pairs: {report.total_pairs}")
    print(f"undefined: {report.undefined_ratio:.1%}")
    print(f"\confusion_matrix:")
    print(f"  TP={report.metrics.true_positives:3d}  FP={report.metrics.false_positives:3d}")
    print(f"  FN={report.metrics.false_negatives:3d}  TN={report.metrics.true_negatives:3d}")
    print(f"\metrics:")
    print(f"  precision: {report.metrics.precision:.3f}")
    print(f"  recall:    {report.metrics.recall:.3f}")
    print(f"  f1:        {report.metrics.f1:.3f}")
    print(f"  support:   {report.metrics.support}")
    
    if report.errors:
        print(f"\errors ({len(report.errors)}):")
        for i, error in enumerate(report.errors[:5], start=1):
            print(f"  {i}. {error['type']}: {error['submission_a']} vs {error['submission_b']}, score={error.get('score', 'N/A')}")


def main():
    corpus_dir = Path("data/corpus")
    
    train_entries, test_entries, train_pairs, test_pairs, all_entries = load_data(corpus_dir)
    print(f"train: {len(train_entries)} записей, {len(train_pairs)} пар")
    print(f"test: {len(test_entries)} записей, {len(test_pairs)} пар")
    
    print("оценка token baseline")
    token_analyzer = TokenBaselineAnalyzer()
    token_train_report, token_test_report = run_method_evaluation(
        token_analyzer, train_pairs, test_pairs, train_entries, test_entries, all_entries,
        "Token Baseline"
    )
    
    token_test_service = SimilarityService(token_analyzer)
    token_test_reports = token_test_service.compare_pairs(test_pairs, all_entries)

    token_errors = analyze_errors(token_test_reports, test_pairs, all_entries, "Token Baseline")

    token_test_report = evaluate_method(
        [r.score for r in token_test_reports],
        get_labels(test_pairs, all_entries),
        token_test_report.threshold,
        "token baseline (test)",
        error_details=token_errors,
    )
    
    print_report(token_train_report)
    print_report(token_test_report)
    
    print("оценка TF-IDF baseline")
    tfidf_analyzer = TfidfBaselineAnalyzer()
    tfidf_analyzer.fit(train_entries)
    
    tfidf_train_report, tfidf_test_report = run_method_evaluation(
        tfidf_analyzer, train_pairs, test_pairs, train_entries, test_entries, all_entries,
        "TF-IDF baseline"
    )
    
    tfidf_test_service = SimilarityService(tfidf_analyzer)
    tfidf_test_reports = tfidf_test_service.compare_pairs(test_pairs, all_entries)

    tfidf_errors = analyze_errors(tfidf_test_reports, test_pairs, all_entries, "TF-IDF baseline")

    tfidf_test_report = evaluate_method(
        [r.score for r in tfidf_test_reports],
        get_labels(test_pairs, all_entries),
        tfidf_test_report.threshold,
        "TF-IDF baseline (test)",
        error_details=tfidf_errors,
    )
    
    print_report(tfidf_train_report)
    print_report(tfidf_test_report)

    print("сравнение методов")
    print(f"{'method':<20} {'precision':<10} {'recall':<10} {'f1':<10} {'undefined':<10}")
    print(f"{'token baseline':<20} {token_test_report.metrics.precision:<10.3f} {token_test_report.metrics.recall:<10.3f} {token_test_report.metrics.f1:<10.3f} {token_test_report.undefined_ratio:<10.1%}")
    print(f"{'TF-IDF baseline':<20} {tfidf_test_report.metrics.precision:<10.3f} {tfidf_test_report.metrics.recall:<10.3f} {tfidf_test_report.metrics.f1:<10.3f} {tfidf_test_report.undefined_ratio:<10.1%}")
    
    print("errors:")
    
    template_errors = [e for e in token_errors if e["type"] == "false_positive" and e["template_overlap"] > 0.5]
    if template_errors:
        print("\nFP из-за общего шаблона:")
        err = template_errors[0]
        print(f"   pairs: {err['submission_a']} vs {err['submission_b']}")
        print(f"   score: {err['score']:.3f}, Template overlap: {err['template_overlap']:.3f}")
        print(f"   derivation: {err['derivation_a']} / {err['derivation_b']}")
        print(f"   reason: высокое сходство из-за общих строк шаблона")
    else:
        print("\nFP из-за общего шаблона: не найдено")
    
    rename_errors = [e for e in token_errors if e["type"] == "false_negative" and ("rename" in e.get("derivation_a", "") or "rename" in e.get("derivation_b", ""))]
    if rename_errors:
        print("\nFN: переименование переменных:")
        err = rename_errors[0]
        print(f"   pairs: {err['submission_a']} vs {err['submission_b']}")
        print(f"   score: {err['score']:.3f}")
        print(f"   derivation: {err['derivation_a']} / {err['derivation_b']}")
        print(f"   reason: переименование снизило Jaccard similarity")
    else:
        print("\nFN переименование: не найдено")
    
    undefined_errors = [e for e in token_errors if e["type"] == "undefined"]
    if undefined_errors:
        print("\nundefined:")
        err = undefined_errors[0]
        print(f"   pairs: {err['submission_a']} vs {err['submission_b']}")
        print(f"   derivation: {err['derivation_a']} / {err['derivation_b']}")
        print(f"   reason: пустой или некорректный код")

    else:
        print("\nnundefined: не найдено")

    if not (template_errors or rename_errors or undefined_errors):
        print("\nmain errors:")
        for i, err in enumerate(token_errors[:3], start=1):
            print(f"{i}. {err['type']}: {err['submission_a']} vs {err['submission_b']}, score={err.get('score', 'N/A')}")


if __name__ == "__main__":
    main()