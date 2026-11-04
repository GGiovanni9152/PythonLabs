from __future__ import annotations

import json
import random
from dataclasses import asdict
from pathlib import Path

from school.domain.models import CorpusEntry, Pair, DerivationRelation

FAMILIES = {
    "fam-001": {
        "assignment_id": "a-1",
        "original_code": 'def solve():\n    x = int(input())\n    print(x * 2)',
        "template_code": 'def solve():\n    # TODO: implement\n    pass',
    },

    "fam-002": {
        "assignment_id": "a-1",
        "original_code": 'def solve():\n    n = int(input())\n    result = n + 1\n    print(result)',
        "template_code": 'def solve():\n    # TODO: implement\n    pass',
    },

    "fam-003": {
        "assignment_id": "a-1",
        "original_code": 'def solve():\n    data = input()\n    value = int(data)\n    output = value * 2\n    print(output)',
        "template_code": 'def solve():\n    # TODO: implement\n    pass',
    },

    "fam-004": {
        "assignment_id": "a-2",
        "original_code": 'def process():\n    items = input().split()\n    total = sum(int(x) for x in items)\n    print(total)',
        "template_code": 'def process():\n    # TODO: implement\n    pass',
    },

    "fam-005": {
        "assignment_id": "a-2",
        "original_code": 'def process():\n    numbers = [int(x) for x in input().split()]\n    result = sum(numbers)\n    print(result)',
        "template_code": 'def process():\n    # TODO: implement\n    pass',
    },

    "fam-006": {
        "assignment_id": "a-2",
        "original_code": 'def calc():\n    a, b = map(int, input().split())\n    print(a + b)',
        "template_code": 'def calc():\n    # TODO\n    pass',
    },

    "fam-007": {
        "assignment_id": "a-3",
        "original_code": 'def main():\n    s = input()\n    print(s.upper())',
        "template_code": 'def main():\n    # TODO\n    pass',
    },

    "fam-008": {
        "assignment_id": "a-3",
        "original_code": 'def transform():\n    text = input()\n    result = text.strip()\n    print(result)',
        "template_code": 'def transform():\n    # TODO\n    pass',
    },
}


def generate_variants(family_id: str, family_data: dict, start_id: int) -> tuple[list[CorpusEntry], int]:
    entries = []
    current_id = start_id
    assignment_id = family_data["assignment_id"]
    original_code = family_data["original_code"]
    template_code = family_data["template_code"]
    
    entries.append(CorpusEntry(
        submission_id = f"sub-{current_id:03d}",
        student_id = f"student-{current_id:03d}",
        assignment_id = assignment_id,
        family_id = family_id,
        code = original_code,
        text = "Решение задачи",
        derivation_relation = DerivationRelation.EXACT_COPY ,
        template_only = False,
    ))
    current_id += 1

    #точная копия
    entries.append(CorpusEntry(
        submission_id = f"sub-{current_id:03d}",
        student_id = f"student-{current_id:03d}",
        assignment_id = assignment_id,
        family_id = family_id,
        code = original_code,
        text = "Решение задачи",
        derivation_relation = DerivationRelation.EXACT_COPY,
        template_only = False,
    ))
    current_id += 1
    
    #другое форматирование
    formatted_code = original_code.replace("    ", "  ")
    entries.append(CorpusEntry(
        submission_id = f"sub-{current_id:03d}",
        student_id = f"student-{current_id:03d}",
        assignment_id = assignment_id,
        family_id = family_id,
        code = formatted_code,
        text = "Решение задачи",
        derivation_relation = DerivationRelation.FORMATTING_CHANGE,
        template_only = False,
    ))
    current_id += 1
    
    #переименование переменных
    renamed_code = original_code.replace("x", "value").replace("n", "num").replace("data", "input_data")
    entries.append(CorpusEntry(
        submission_id = f"sub-{current_id:03d}",
        student_id = f"student-{current_id:03d}",
        assignment_id = assignment_id,
        family_id = family_id,
        code = renamed_code,
        text = "Решение задачи",
        derivation_relation = DerivationRelation.RENAME,
        template_only = False,
    ))
    current_id += 1
    
    #другое решение
    independent_code = original_code.replace("def solve():", "def solution():").replace("print", "return")
    entries.append(CorpusEntry(
        submission_id = f"sub-{current_id:03d}",
        student_id = f"student-{current_id:03d}",
        assignment_id = assignment_id,
        family_id = f"family-indep-{assignment_id}",
        code = independent_code,
        text = "Моё решение",
        derivation_relation = DerivationRelation.INDEPENDENT,
        template_only = False,
    ))
    current_id += 1
    
    #только шаблон
    entries.append(CorpusEntry(
        submission_id = f"sub-{current_id:03d}",
        student_id = f"student-{current_id:03d}",
        assignment_id = assignment_id,
        family_id = family_id,
        code = template_code,
        text = "Шаблон",
        derivation_relation = DerivationRelation.COMMON_TEMPLATE,
        template_only = True,
    ))
    current_id += 1
    
    return entries, current_id


def generate_pairs(entries: list[CorpusEntry]) -> list[Pair]:
    pairs = []
    
    by_family: dict[str, list[CorpusEntry]] = {}
    for entry in entries:
        by_family.setdefault(entry.family_id, []).append(entry)
    
    for family_id, family_entries in by_family.items():
        if len(family_entries) < 2:
            continue
        
        original = family_entries[0]
        
        for entry in family_entries[1:]:
            if entry.template_only:
                pairs.append(Pair(
                    submission_id_a = original.submission_id,
                    submission_id_b = entry.submission_id,
                    assignment_id = original.assignment_id,
                    student_id_a = original.student_id,
                    student_id_b = entry.student_id,
                    family_id_a = original.family_id,
                    family_id_b = entry.family_id,
                    derivation_relation = DerivationRelation.COMMON_TEMPLATE,
                    template_only = True,
                ))
            else:
                pairs.append(Pair(
                    submission_id_a = original.submission_id,
                    submission_id_b = entry.submission_id,
                    assignment_id = original.assignment_id,
                    student_id_a = original.student_id,
                    student_id_b = entry.student_id,
                    family_id_a = original.family_id,
                    family_id_b = entry.family_id,
                    derivation_relation = entry.derivation_relation,
                    template_only = False,
                ))
    
    return pairs


def split_by_family(
    entries: list[CorpusEntry],
    pairs: list[Pair],
    test_ratio: float = 0.3,
    seed: int = 42,
) -> tuple[list[CorpusEntry], list[CorpusEntry], list[Pair], list[Pair]]:
    random.seed(seed)
    
    family_ids = list(set(e.family_id for e in entries))
    random.shuffle(family_ids)
    
    split_idx = int(len(family_ids) * (1 - test_ratio))
    train_families = set(family_ids[:split_idx])
    test_families = set(family_ids[split_idx:])
    
    train_entries = [e for e in entries if e.family_id in train_families]
    test_entries = [e for e in entries if e.family_id in test_families]
    
    train_pairs = [
        p for p in pairs
        if p.family_id_a in train_families and p.family_id_b in train_families
    ]
    test_pairs = [
        p for p in pairs
        if p.family_id_a in test_families and p.family_id_b in test_families
    ]
    
    return train_entries, test_entries, train_pairs, test_pairs

def save_jsonl(path: Path, items: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(asdict(item)) + "\n")


def generate_corpus(output_dir: Path, seed: int = 42) -> None:
    random.seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_entries = []
    current_id = 1
    
    for family_id, family_data in FAMILIES.items():
        entries, current_id = generate_variants(family_id, family_data, current_id)
        all_entries.extend(entries)
    
    all_pairs = generate_pairs(all_entries)
    
    train_entries, test_entries, train_pairs, test_pairs = split_by_family(
        all_entries, all_pairs, test_ratio=0.3, seed=seed
    )
    
    save_jsonl(output_dir / "corpus_train.jsonl", train_entries)
    save_jsonl(output_dir / "corpus_test.jsonl", test_entries)
    save_jsonl(output_dir / "pairs_train.jsonl", train_pairs)
    save_jsonl(output_dir / "pairs_test.jsonl", test_pairs)
    
    print(f"всего записей: {len(all_entries)}")
    print(f"train: {len(train_entries)}")
    print(f"test: {len(test_entries)}")

    print(f"всего пар: {len(all_pairs)}")
    print(f"train: {len(train_pairs)}")
    print(f"test: {len(test_pairs)}")

    template_pairs = [p for p in all_pairs if p.template_only]
    print(f"шаблонных пар: {len(template_pairs)}")
    
    train_families = set(e.family_id for e in train_entries)
    test_families = set(e.family_id for e in test_entries)

    if train_families & test_families:
        print(f"утечка")

if __name__ == "__main__":
    generate_corpus(Path("data/corpus"), seed = 42)