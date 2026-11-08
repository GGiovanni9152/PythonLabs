from school.evaluation.metrics import compute_metrics, find_optimal_threshold


def test_compute_metrics_perfect_classification():
    y_true = [True, True, False, False]
    y_pred = [True, True, False, False]
    y_undefined = [False, False, False, False]
    
    metrics = compute_metrics(y_true, y_pred, y_undefined)
    
    assert metrics.precision == 1.0
    assert metrics.recall == 1.0
    assert metrics.f1 == 1.0
    assert metrics.true_positives == 2
    assert metrics.true_negatives == 2


def test_compute_metrics_with_undefined():
    y_true = [True, True, False]
    y_pred = [True, False, False]
    y_undefined = [False, True, False]
    
    metrics = compute_metrics(y_true, y_pred, y_undefined)
    
    assert metrics.true_positives == 1
    assert metrics.true_negatives == 1
    assert metrics.false_positives == 0
    assert metrics.false_negatives == 0


def test_find_optimal_threshold():
    scores = [0.9, 0.8, 0.3, 0.2]
    labels = [True, True, False, False]
    
    threshold, f1 = find_optimal_threshold(scores, labels)
    
    assert 0.3 <= threshold <= 0.8
    assert f1 == 1.0


def test_find_optimal_threshold_with_none():
    scores = [0.9, None, 0.3, 0.2]
    labels = [True, True, False, False]
    
    threshold, f1 = find_optimal_threshold(scores, labels)
    
    assert threshold is not None
    assert f1 > 0.0