import pytest
from school.analyzers.length import LengthAnalyzer
from school.analyzers.template import TemplateAnalyzer
from school.domain.contracts import AnalysisContext
from school.domain.models import Assignment, Submission
from school.validation.validator import parse_submission


def _submission(text: str, code: str) -> Submission:
    raw = (
        '{"schema_version":1,"submission_id":"sub-001","student_id":"s-1",'
        '"assignment_id":"a-1","submitted_at":"2026-09-01T10:00:00+03:00",'
        f'"text":{_js(text)},"code":{_js(code)},"template_id":"t-1",'
        '"ai_declaration":{"used":false,"verified_by_student":true,"tool":null,"purpose":null}}'
    )
    return parse_submission(raw)


def _js(s: str) -> str:
    import json
    return json.dumps(s)


@pytest.fixture
def ctx_template() -> AnalysisContext:
    return AnalysisContext(
        assignment = Assignment("a-1", "A1", "t-1"),
        template_text = "Hello\nWorld\n",
        config_hash = "cfg",
    )


@pytest.fixture
def ctx_no_template() -> AnalysisContext:
    return AnalysisContext(
        assignment = Assignment("a-1", "A1", None),
        template_text = None,
        config_hash = "cfg",
    )


def test_length_counts_non_empty_lines(ctx_no_template):
    s = _submission("Hello\n\nWorld\n", "print(1)\n# comment\n")
    r = LengthAnalyzer().analyze(s, ctx_no_template)

    assert r.score is None
    assert r.metadata["text_lines"] == 2
    assert r.metadata["code_lines"] == 2
    assert r.analyzer_id == "length"
    assert r.analyzer_version


def test_template_finds_exact_lines(ctx_template):
    s = _submission("Hello\nFoo\nWorld\n", "")
    r = TemplateAnalyzer().analyze(s, ctx_template)

    assert set(r.evidence) == {1, 3}
    assert r.similarity is not None and 0 < r.similarity <= 1.0
    assert "permitted" in r.rubric_feedback.lower()


def test_template_evidence_within_source_bounds(ctx_template):
    s = _submission("Hello\n", "")
    r = TemplateAnalyzer().analyze(s, ctx_template)
    total_lines = len(s.text.splitlines()) + len(s.code.splitlines())

    for n in r.evidence:
        assert 1 <= n <= total_lines


def test_template_no_template(ctx_no_template):
    s = _submission("Hello", "")
    r = TemplateAnalyzer().analyze(s, ctx_no_template)

    assert r.evidence == ()
    assert r.similarity is None


def test_submission_object_is_immutable(ctx_no_template):
    s = _submission("Hello", "x=1")
    original_text = s.text
    original_code = s.code
    LengthAnalyzer().analyze(s, ctx_no_template)
    TemplateAnalyzer().analyze(s, ctx_no_template)

    assert s.text == original_text
    assert s.code == original_code