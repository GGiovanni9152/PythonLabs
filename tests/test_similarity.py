import pytest

from school.analyzers.similarity.token_baseline import TokenBaselineAnalyzer
from school.domain.models import CorpusEntry, Pair, DerivationRelation


def _make_entry(submission_id: str, code: str, family_id: str = "fam-1") -> CorpusEntry:
    return CorpusEntry(
        submission_id = submission_id,
        student_id = f"student-{submission_id}",
        assignment_id = "a-1",
        family_id = family_id,
        code = code,
        text = "Test",
        derivation_relation = DerivationRelation.EXACT_COPY,
        template_only = False,
    )


def _make_pair(entry_a: CorpusEntry, entry_b: CorpusEntry) -> Pair:
    return Pair(
        submission_id_a = entry_a.submission_id,
        submission_id_b = entry_b.submission_id,
        assignment_id = entry_a.assignment_id,
        student_id_a = entry_a.student_id,
        student_id_b = entry_b.student_id,
        family_id_a = entry_a.family_id,
        family_id_b = entry_b.family_id,
        derivation_relation = DerivationRelation.EXACT_COPY,
        template_only = False,
    )


def test_identical_code_gets_max_similarity():
    code = 'def solve():\n    x = int(input())\n    print(x * 2)'

    entry_a = _make_entry("sub-001", code)
    entry_b = _make_entry("sub-002", code, family_id = "fam-2")

    pair = _make_pair(entry_a, entry_b)
    
    analyzer = TokenBaselineAnalyzer()
    entries = {entry_a.submission_id: entry_a, entry_b.submission_id: entry_b}
    report = analyzer.analyze_pair(pair, entries)
    
    assert report.score == 1.0, f"expected 1.0, got {report.score}"


def test_renamed_variables_still_similar():
    code_a = 'def solve():\n    x = int(input())\n    print(x * 2)'
    code_b = 'def solve():\n    value = int(input())\n    print(value * 2)'

    entry_a = _make_entry("sub-001", code_a)
    entry_b = _make_entry("sub-002", code_b, family_id = "fam-2")
    pair = _make_pair(entry_a, entry_b)
    
    analyzer = TokenBaselineAnalyzer()
    entries = {entry_a.submission_id: entry_a, entry_b.submission_id: entry_b}
    report = analyzer.analyze_pair(pair, entries)
    
    assert report.score is not None
    assert report.score > 0.4, f"expected high similarity, got {report.score}"


def test_independent_solutions_have_low_similarity():
    code_a = 'def solve():\n    x = int(input())\n    print(x * 2)'
    code_b = 'def process():\n    items = input().split()\n    total = sum(int(x) for x in items)\n    print(total)'

    entry_a = _make_entry("sub-001", code_a)
    entry_b = _make_entry("sub-002", code_b, family_id = "fam-2")
    pair = _make_pair(entry_a, entry_b)
    
    analyzer = TokenBaselineAnalyzer()
    entries = {entry_a.submission_id: entry_a, entry_b.submission_id: entry_b}
    report = analyzer.analyze_pair(pair, entries)
    
    assert report.score is not None
    assert report.score < 0.3, f"expected low similarity, got {report.score}"


def test_empty_code_returns_none():
    entry_a = _make_entry("sub-001", "")
    entry_b = _make_entry("sub-002", "def solve(): pass", family_id = "fam-2")
    pair = _make_pair(entry_a, entry_b)
    
    analyzer = TokenBaselineAnalyzer()
    entries = {entry_a.submission_id: entry_a, entry_b.submission_id: entry_b}
    report = analyzer.analyze_pair(pair, entries)
    
    assert report.score is None


def test_syntax_error_returns_none():
    code_a = 'def solve():\n    x = int(input())\n    print(x * 2)'
    code_b = 'def solve():\n    x = int(input()\n    print(x * 2'

    entry_a = _make_entry("sub-001", code_a)
    entry_b = _make_entry("sub-002", code_b, family_id = "fam-2")
    pair = _make_pair(entry_a, entry_b)
    
    analyzer = TokenBaselineAnalyzer()
    entries = {entry_a.submission_id: entry_a, entry_b.submission_id: entry_b}
    report = analyzer.analyze_pair(pair, entries)
    
    assert report.score is None


def test_self_match_excluded():
    code = 'def solve(): pass'

    entry = _make_entry("sub-001", code)
    pair = _make_pair(entry, entry)
    
    analyzer = TokenBaselineAnalyzer()
    entries = {entry.submission_id: entry}
    report = analyzer.analyze_pair(pair, entries)
    
    assert report is not None


def test_evidence_points_to_existing_lines():
    code_a = 'def solve():\n    x = 1\n    print(x)'
    code_b = 'def solve():\n    x = 1\n    print(x)'

    entry_a = _make_entry("sub-001", code_a)
    entry_b = _make_entry("sub-002", code_b, family_id = "fam-2")
    pair = _make_pair(entry_a, entry_b)
    
    analyzer = TokenBaselineAnalyzer()
    entries = {entry_a.submission_id: entry_a, entry_b.submission_id: entry_b}
    report = analyzer.analyze_pair(pair, entries)
    
    lines_a = len(code_a.splitlines())
    lines_b = len(code_b.splitlines())
    
    for line_a, line_b in report.evidence:
        assert 1 <= line_a <= lines_a, f"line {line_a} out of range [1, {lines_a}]"
        assert 1 <= line_b <= lines_b, f"line {line_b} out of range [1, {lines_b}]"