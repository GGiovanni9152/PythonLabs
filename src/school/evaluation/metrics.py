"""Метрики качества для оценки детектора сходства."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen = True, slots = True)
class ClassificationMetrics:
    precision: float
    recall: float
    f1: float
    support: int
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int


@dataclass(frozen = True, slots = True)
class EvaluationReport:
    method_name: str
    threshold: float
    metrics: ClassificationMetrics
    confusion_matrix: tuple[tuple[int, int], tuple[int, int]]
    undefined_ratio: float
    total_pairs: int
    errors: list[dict[str, Any]] = field(default_factory=list)


def compute_metrics(y_true: list[bool], y_pred: list[bool], y_undefined: list[bool],) -> ClassificationMetrics:
    tp = fp = fn = tn = 0
    
    for true, pred, undefined in zip(y_true, y_pred, y_undefined):
        if undefined:
            continue
        
        if pred and true:
            tp += 1

        elif pred and not true:
            fp += 1

        elif not pred and true:
            fn += 1

        else:
            tn += 1
    
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 0.0

    if (precision + recall) > 0:
        f1 = 2 * precision * recall / (precision + recall)
    
    return ClassificationMetrics(
        precision = precision,
        recall = recall,
        f1 = f1,
        support = tp + fn,
        true_positives = tp,
        false_positives = fp,
        false_negatives = fn,
        true_negatives = tn,
    )


def find_optimal_threshold(scores: list[float | None], labels: list[bool], thresholds: list[float] | None = None,) -> tuple[float, float]:
    if thresholds is None:
        thresholds = [i / 100 for i in range(10, 91, 5)] 
    
    best_f1 = 0.0
    best_threshold = 0.5
    
    for threshold in thresholds:
        y_pred = [score >= threshold if score is not None else False for score in scores]
        y_undefined = [score is None for score in scores]
        
        metrics = compute_metrics(labels, y_pred, y_undefined)
        
        if metrics.f1 > best_f1:
            best_f1 = metrics.f1
            best_threshold = threshold
    
    return best_threshold, best_f1


def evaluate_method(
    scores: list[float | None],
    labels: list[bool],
    threshold: float,
    method_name: str,
    error_details: list[dict[str, Any]] | None = None,
) -> EvaluationReport:
    
    y_pred = [score >= threshold if score is not None else False for score in scores]
    y_undefined = [score is None for score in scores]
    
    metrics = compute_metrics(labels, y_pred, y_undefined)
    
    confusion_matrix = (
        (metrics.true_positives, metrics.false_positives),
        (metrics.false_negatives, metrics.true_negatives),
    )

    undefined_ratio = 0.0
    if (y_undefined):
        undefined_ratio = sum(y_undefined) / len(y_undefined)
    
    errors = error_details or []
    
    return EvaluationReport(
        method_name = method_name,
        threshold = threshold,
        metrics = metrics,
        confusion_matrix = confusion_matrix,
        undefined_ratio = undefined_ratio,
        total_pairs = len(scores),
        errors = errors,
    )