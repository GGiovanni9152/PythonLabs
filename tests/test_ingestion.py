from school.repository.memory import InMemorySubmissionRepository
from school.services.ingestion import IngestionService
from school.sources.memory_source import InMemorySource


VALID = (
    '{"schema_version":1,"submission_id":"sub-001","student_id":"s-1",'
    '"assignment_id":"a-1","submitted_at":"2026-09-01T10:00:00+03:00",'
    '"text":"Hello","code":"","template_id":null,'
    '"ai_declaration":{"used":false,"verified_by_student":true,"tool":null,"purpose":null}}'
)

BROKEN = "{not json"
DUPLICATE = VALID
CONFLICT = VALID.replace('"text":"Hello"', '"text":"World"')

def test_ingestion_accepts_valid():
    repo = InMemorySubmissionRepository()
    svc = IngestionService(repo)
    out = svc.ingest(InMemorySource([VALID]))

    assert len(out.accepted) == 1
    assert out.errors == []
    assert len(repo) == 1


def test_ingestion_handles_broken_json():
    repo = InMemorySubmissionRepository()
    svc = IngestionService(repo)
    out = svc.ingest(InMemorySource([BROKEN, VALID]))

    assert len(out.errors) == 1
    assert out.errors[0].code == "format_error"
    assert len(out.accepted) == 1


def test_ingestion_duplicate_does_not_grow_repo():
    repo = InMemorySubmissionRepository()
    svc = IngestionService(repo)
    svc.ingest(InMemorySource([VALID, DUPLICATE]))

    assert len(repo) == 1


def test_ingestion_conflict_does_not_overwrite():
    repo = InMemorySubmissionRepository()
    svc = IngestionService(repo)
    svc.ingest(InMemorySource([VALID, CONFLICT]))
    
    assert len(repo) == 1
    assert repo.get("sub-001").text == "Hello"