import pytest

from scripts.profile_similarity import (
    generate_synthetic_data,
    profile_single_run,
    aggregate_results,
    ProfileResult,
)


def test_generate_synthetic_data_correct_size():
    entries, pairs = generate_synthetic_data(100, seed=42)
    
    assert len(entries) == 100
    assert len(pairs) > 0
    assert all(e.submission_id.startswith("load-sub-") for e in entries)


def test_generate_synthetic_data_is_reproducible():
    entries1, pairs1 = generate_synthetic_data(100, seed=42)
    entries2, pairs2 = generate_synthetic_data(100, seed=42)
    
    assert len(entries1) == len(entries2)
    assert len(pairs1) == len(pairs2)
    
    for e1, e2 in zip(entries1, entries2):
        assert e1.code == e2.code


def test_profile_single_run_returns_result():
    entries, pairs = generate_synthetic_data(50, seed=42)
    
    result = profile_single_run(entries, pairs, "token", run_id=0)
    
    assert isinstance(result, ProfileResult)
    assert result.num_entries == 50
    assert result.method == "token"
    assert result.wall_time_seconds > 0
    assert result.peak_memory_bytes > 0


def test_aggregate_results_computes_statistics():
    results = [
        ProfileResult(100, 200, "token", 1.0, 1000, 0),
        ProfileResult(100, 200, "token", 2.0, 2000, 1),
        ProfileResult(100, 200, "token", 3.0, 3000, 2),
    ]
    
    aggregated = aggregate_results(results)
    
    assert aggregated["wall_time_median"] == 2.0
    assert aggregated["wall_time_mean"] == 2.0
    assert aggregated["peak_memory_median"] == 2000
    assert aggregated["peak_memory_mean"] == 2000
    assert aggregated["num_runs"] == 3


def test_profile_tfidf_method():
    entries, pairs = generate_synthetic_data(50, seed=42)
    
    result = profile_single_run(entries, pairs, "tfidf", run_id=0)
    
    assert result.method == "tfidf"
    assert result.wall_time_seconds > 0
    assert result.peak_memory_bytes > 0