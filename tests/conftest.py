from __future__ import annotations
import pytest

from school.ai.config import ModeConfig
from school.analyzers.length import LengthAnalyzer
from school.analyzers.registry import AnalyzerRegistry
from school.analyzers.template import TemplateAnalyzer
from school.domain.models import Assignment
from school.repository.memory import InMemorySubmissionRepository
from school.sources.memory_source import InMemorySource

VALID = (
    '{"schema_version":1,"submission_id":"sub-001","student_id":"s-1",'
    '"assignment_id":"a-1","submitted_at":"2026-09-01T10:00:00+03:00",'
    '"text":"Hello\\nWorld","code":"print(1)","template_id":"t-1",'
    '"ai_declaration":{"used":false,"verified_by_student":true,"tool":null,"purpose":null}}'
)

@pytest.fixture
def repo():
    return InMemorySubmissionRepository()

@pytest.fixture
def source():
    return InMemorySource([VALID])

@pytest.fixture
def registry() -> AnalyzerRegistry:
    r = AnalyzerRegistry()
    r.register(LengthAnalyzer())
    r.register(TemplateAnalyzer())

    return r

@pytest.fixture
def assignment() -> Assignment:
    return Assignment(
        assignment_id = "a-1", 
        title = "A1",
        template_id = "t-1", 
        allowed_templates = ("t-1",)
        )

@pytest.fixture
def mode_config() -> ModeConfig:
    return ModeConfig(mode = "ml", feature_schema_version = "v1")