import pytest

from school.domain.models import Assignment, Submission
from school.services.analysis import AnalysisService
from school.validation.validator import parse_submission


RAW = (
    '{"schema_version":1,"submission_id":"sub-001","student_id":"s-1",'
    '"assignment_id":"a-1","submitted_at":"2026-09-01T10:00:00+03:00",'
    '"text":"Hello\\nWorld","code":"print(1)","template_id":"t-1",'
    '"ai_declaration":{"used":false,"verified_by_student":true,"tool":null,"purpose":null}}'
)


def test_analysis_runs_length(registry, assignment, mode_config):
    svc = AnalysisService(
        registry = registry,
        assignments = {"a-1": assignment},
        templates = {"t-1": "Hello\n"},
        mode_config = mode_config,
    )
    s = parse_submission(RAW)
    r = svc.run("length", s)

    assert r.analyzer_id == "length"
    assert r.score is None


def test_analysis_runs_template(registry, assignment, mode_config):
    svc = AnalysisService(
        registry = registry,
        assignments = {"a-1": assignment},
        templates = {"t-1": "Hello\n"},
        mode_config = mode_config,
    )
    s = parse_submission(RAW)
    r = svc.run("template", s)

    assert r.analyzer_id == "template"
    assert 1 in r.evidence


def test_analysis_unknown_analyzer_raises(registry, assignment, mode_config):
    svc = AnalysisService(
        registry = registry,
        assignments = {"a-1": assignment},
        templates = {},
        mode_config = mode_config,
    )
    s = parse_submission(RAW)
    with pytest.raises(KeyError):
        svc.run("nonexistent", s)


def test_analysis_error_propagates(registry, assignment, mode_config):
    class Broken:
        analyzer_id = "broken"
        analyzer_version = "0"
        def analyze(self, submission, context):
            raise RuntimeError("boom")

    registry.register(Broken())
    svc = AnalysisService(
        registry = registry,
        assignments = {"a-1": assignment},
        templates = {},
        mode_config = mode_config,
    )
    s = parse_submission(RAW)
    with pytest.raises(RuntimeError):
        svc.run("broken", s)