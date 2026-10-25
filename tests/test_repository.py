from school.repository.memory import InMemorySubmissionRepository
from school.validation.validator import parse_submission


RAW = (
    '{"schema_version":1,"submission_id":"sub-001","student_id":"s-1",'
    '"assignment_id":"a-1","submitted_at":"2026-09-01T10:00:00+03:00",'
    '"text":"Hello","code":"","template_id":null,'
    '"ai_declaration":{"used":false,"verified_by_student":true,"tool":null,"purpose":null}}'
)
RAW_DIFFERENT_TEXT = RAW.replace('"text":"Hello"', '"text":"World"')


def test_accept_new():
    repo = InMemorySubmissionRepository()
    s = parse_submission(RAW)
    r = repo.accept(s)

    assert r.status == "accepted"
    assert len(repo) == 1


def test_duplicate_same_hash():
    repo = InMemorySubmissionRepository()
    s1 = parse_submission(RAW)
    s2 = parse_submission(RAW)
    repo.accept(s1)
    r = repo.accept(s2)

    assert r.status == "duplicate"
    assert len(repo) == 1


def test_conflict_same_id_different_content():
    repo = InMemorySubmissionRepository()
    s1 = parse_submission(RAW)
    s2 = parse_submission(RAW_DIFFERENT_TEXT)

    assert s1.submission_id == s2.submission_id
    assert s1.content_hash() != s2.content_hash()

    repo.accept(s1)
    r = repo.accept(s2)

    assert r.status == "conflict"
    assert len(repo) == 1
    assert repo.get(s1.submission_id).text == "Hello"