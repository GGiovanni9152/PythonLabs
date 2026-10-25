import pytest

from school.domain.errors import SubmissionError
from school.validation.validator import parse_submission


def test_valid_submission():
    raw = (
        '{"schema_version":1,"submission_id":"sub-001","student_id":"s-1",'
        '"assignment_id":"a-1","submitted_at":"2026-09-01T10:00:00+03:00",'
        '"text":"Hello","code":"","template_id":null,'
        '"ai_declaration":{"used":false,"verified_by_student":true,"tool":null,"purpose":null}}'
    )
    s = parse_submission(raw)

    assert s.submission_id == "sub-001"
    assert s.schema_version == 1


def test_invalid_json_is_format_error():
    with pytest.raises(SubmissionError) as ei:
        parse_submission("{not json")

    assert ei.value.code == "format_error"


def test_unknown_field_is_schema_error():
    raw = (
        '{"schema_version":1,"submission_id":"sub-001","student_id":"s-1",'
        '"assignment_id":"a-1","submitted_at":"2026-09-01T10:00:00+03:00",'
        '"text":"Hello","code":"","studnet_id":"typo","template_id":null,'
        '"ai_declaration":{"used":false,"verified_by_student":true,"tool":null,"purpose":null}}'
    )

    with pytest.raises(SubmissionError) as ei:
        parse_submission(raw)

    assert ei.value.code == "schema_error"
    assert ei.value.field == "studnet_id"


def test_empty_student_id_is_schema_error():
    raw = (
        '{"schema_version":1,"submission_id":"sub-001","student_id":"   ",'
        '"assignment_id":"a-1","submitted_at":"2026-09-01T10:00:00+03:00",'
        '"text":"Hello","code":"","template_id":null,'
        '"ai_declaration":{"used":false,"verified_by_student":true,"tool":null,"purpose":null}}'
    )

    with pytest.raises(SubmissionError) as ei:
        parse_submission(raw)

    assert ei.value.code == "schema_error"
    assert ei.value.field == "student_id"


def test_missing_timezone_is_schema_error():
    raw = (
        '{"schema_version":1,"submission_id":"sub-001","student_id":"s-1",'
        '"assignment_id":"a-1","submitted_at":"2026-09-01T10:00:00",'
        '"text":"Hello","code":"","template_id":null,'
        '"ai_declaration":{"used":false,"verified_by_student":true,"tool":null,"purpose":null}}'
    )

    with pytest.raises(SubmissionError) as ei:
        parse_submission(raw)

    assert ei.value.code == "schema_error"
    assert ei.value.field == "submitted_at"


def test_bool_schema_version_rejected():
    raw = (
        '{"schema_version":true,"submission_id":"sub-001","student_id":"s-1",'
        '"assignment_id":"a-1","submitted_at":"2026-09-01T10:00:00+03:00",'
        '"text":"Hello","code":"","template_id":null,'
        '"ai_declaration":{"used":false,"verified_by_student":true,"tool":null,"purpose":null}}'
    )

    with pytest.raises(SubmissionError) as ei:
        parse_submission(raw)

    assert ei.value.code == "schema_error"
    assert ei.value.field == "schema_version"


def test_ai_declaration_used_requires_tool_and_purpose():
    raw = (
        '{"schema_version":1,"submission_id":"sub-001","student_id":"s-1",'
        '"assignment_id":"a-1","submitted_at":"2026-09-01T10:00:00+03:00",'
        '"text":"Hello","code":"","template_id":null,'
        '"ai_declaration":{"used":true,"verified_by_student":true,"tool":null,"purpose":null}}'
    )

    with pytest.raises(SubmissionError) as ei:
        parse_submission(raw)

    assert ei.value.code == "schema_error"
    assert ei.value.field == "ai_declaration"


def test_original_text_preserved():
    raw = (
        '{"schema_version":1,"submission_id":"sub-001","student_id":"s-1",'
        '"assignment_id":"a-1","submitted_at":"2026-09-01T10:00:00+03:00",'
        '"text":"  Hello  \\n","code":"","template_id":null,'
        '"ai_declaration":{"used":false,"verified_by_student":true,"tool":null,"purpose":null}}'
    )

    s = parse_submission(raw)
    
    assert s.text == "  Hello  \n"