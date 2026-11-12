from __future__ import annotations

import random
import statistics
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from school.analyzers.similarity.token_baseline import TokenBaselineAnalyzer
from school.analyzers.similarity.tfidf_baseline import TfidfBaselineAnalyzer
from school.domain.models import CorpusEntry, Pair, DerivationRelation
from school.services.similarity import SimilarityService


SEED = 42
NUM_RUNS = 3
SIZES = [100, 1000, 5000] #50000]


@dataclass(frozen=True, slots=True)
class ProfileResult:
    num_entries: int
    num_pairs: int
    method: str
    wall_time_seconds: float
    peak_memory_bytes: int
    run_id: int


def generate_synthetic_data(num_entries: int, seed: int = SEED) -> tuple[list[CorpusEntry], list[Pair]]:
    random.seed(seed)
    entries = []

    code_templates = [
        'def solve():\n    x = int(input())\n    print(x * {mult})',
        'def process():\n    items = input().split()\n    total = sum(int(x) for x in items)\n    print(total * {mult})',
        'def calculate():\n    a, b = map(int, input().split())\n    print(a + b * {mult})',
        'def transform():\n    text = input()\n    result = text.strip().upper()\n    print(result * {mult})',
        'def analyze():\n    data = input().split()\n    print(len(data) * {mult})',
    ]

    for i in range(num_entries):
        template = random.choice(code_templates)
        mult = random.randint(1, 10)
        entries.append(CorpusEntry(
            submission_id = f"load-sub-{i:05d}",
            student_id = f"load-student-{i:05d}",
            assignment_id = f"load-a-{i % 5}",
            family_id = f"load-fam-{i % 20}",
            code = template.format(mult=mult),
            text = f"load test submission {i}",
            derivation_relation = DerivationRelation.EXACT_COPY,
            template_only = False,
        ))

    by_assignment: dict[str, list[CorpusEntry]] = {}
    for e in entries:
        by_assignment.setdefault(e.assignment_id, []).append(e)

    pairs = []
    for group in by_assignment.values():
        for i in range(len(group)):
            for j in range(1, 3):
                a = group[i]
                b = group[(i + j) % len(group)]
                if a.submission_id == b.submission_id:
                    continue
                pairs.append(Pair(
                    submission_id_a = a.submission_id,
                    submission_id_b = b.submission_id,
                    assignment_id = a.assignment_id,
                    student_id_a = a.student_id,
                    student_id_b = b.student_id,
                    family_id_a = a.family_id,
                    family_id_b = b.family_id,
                    derivation_relation = DerivationRelation.EXACT_COPY,
                    template_only = False,
                ))

    return entries, pairs


def profile_single_run(
    entries: list[CorpusEntry],
    pairs: list[Pair],
    method: str,
    run_id: int,
) -> ProfileResult:

    tracemalloc.start()
    entries_dict = {e.submission_id: e for e in entries}
    
    if method == "token":
        analyzer = TokenBaselineAnalyzer()
    elif method == "tfidf":
        analyzer = TfidfBaselineAnalyzer()
        analyzer.fit(entries)
    else:
        raise ValueError(f"unknown method: {method}")
    
    service = SimilarityService(analyzer)
    
    start_time = time.perf_counter()
    
    reports = service.compare_pairs(pairs, entries_dict)
    
    end_time = time.perf_counter()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return ProfileResult(
        num_entries = len(entries),
        num_pairs = len(pairs),
        method = method,
        wall_time_seconds = end_time - start_time,
        peak_memory_bytes = peak,
        run_id = run_id,
    )


def aggregate_results(results: list[ProfileResult]) -> dict[str, Any]:
    times = [r.wall_time_seconds for r in results]
    memories = [r.peak_memory_bytes for r in results]
    
    return {
        "num_entries": results[0].num_entries,
        "num_pairs": results[0].num_pairs,
        "method": results[0].method,
        "num_runs": len(results),
        "wall_time_median": statistics.median(times),
        "wall_time_mean": statistics.mean(times),
        "wall_time_min": min(times),
        "wall_time_max": max(times),
        "peak_memory_median": statistics.median(memories),
        "peak_memory_mean": statistics.mean(memories),
        "peak_memory_min": min(memories),
        "peak_memory_max": max(memories),
    }


def print_results_table(all_results: list[dict[str, Any]]) -> None:

    print(f"seed: {SEED}")
    print(f"num runs: {NUM_RUNS}")
    print(f"methods: token (Jaccard), tfidf (TF-IDF + cosine)")
    
    print(f"{'Записей':<10} {'Пар':<10} {'Метод':<10} {'Time Median':<15} {'Time Mean':<15} {'Memory Median':<18} {'Memory Mean':<18}")
    print("-" * 100)
    
    for result in all_results:
        time_median = f"{result['wall_time_median']:.4f}s"
        time_mean = f"{result['wall_time_mean']:.4f}s"
        mem_median = f"{result['peak_memory_median'] / 1024 / 1024:.2f} mb"
        mem_mean = f"{result['peak_memory_mean'] / 1024 / 1024:.2f} mb"
        
        print(f"{result['num_entries']:<10} {result['num_pairs']:<10} {result['method']:<10} {time_median:<15} {time_mean:<15} {mem_median:<18} {mem_mean:<18}")


def main():
    print("Профилирование анализаторов сходства")
    print(f"seed: {SEED}, num_runs: {NUM_RUNS}")
    print(f"sizes: {SIZES}")
    
    all_results = []
    
    for num_entries in SIZES:
        print(f"generating: {num_entries}")
        
        entries, pairs = generate_synthetic_data(num_entries, seed=SEED)
        print(f"generated: {len(entries)} entries, {len(pairs)} pairs")
        
        for method in ["token", "tfidf"]:
            print(f"\method: {method}")
            run_results = []
            
            for run_id in range(NUM_RUNS):
                print(f"{run_id + 1}/{NUM_RUNS}", end=" ", flush=True)
                
                result = profile_single_run(entries, pairs, method, run_id)
                run_results.append(result)
                
                print(f"time={result.wall_time_seconds:.4f}s, memory={result.peak_memory_bytes / 1024 / 1024:.2f} mb")
            
            aggregated = aggregate_results(run_results)
            all_results.append(aggregated)
    
    print_results_table(all_results)
    
    import json
    output_path = Path("out/profile_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "seed": SEED,
            "num_runs": NUM_RUNS,
            "sizes": SIZES,
            "results": all_results,
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nresults in {output_path}")


if __name__ == "__main__":
    main()