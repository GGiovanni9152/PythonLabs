from school.ai.config import ModeConfig
from school.ai.feature_extractor import BasicFeatureExtractor
from school.ai.feedback_builder import BasicFeedbackBuilder
from school.ai.stub_model import StubModel
from school.services.analysis import AnalysisService
from school.validation.validator import parse_submission

RAW = (
    '{"schema_version":1,"submission_id":"sub-001","student_id":"s-1",'
    '"assignment_id":"a-1","submitted_at":"2026-09-01T10:00:00+03:00",'
    '"text":"Hello","code":"print(1)","template_id":"t-1",'
    '"ai_declaration":{"used":false,"verified_by_student":true,"tool":null,"purpose":null}}'
)

def test_stub_model_deterministic():
    m = StubModel()
    assert m.predict({"x": 1}) == m.predict({"x": 2})

def test_feature_extractor_does_not_use_ai_declaration_as_label():
    s = parse_submission(RAW)
    feats = BasicFeatureExtractor().extract(s)

    assert "ai_declaration" not in feats
    assert "used" not in feats


def test_feedback_builder_produces_string():
    s = parse_submission(RAW)
    fb = BasicFeedbackBuilder().build({"verdict": "ok"}, s)

    assert isinstance(fb, str) and s.submission_id in fb


def test_mode_config_hash_stable():
    c1 = ModeConfig(mode = "ml", feature_schema_version = "v1")
    c2 = ModeConfig(mode = "ml", feature_schema_version = "v1")
    assert c1.config_hash == c2.config_hash

    c3 = ModeConfig(mode = "llm", template_version = "p1")
    assert c3.config_hash != c1.config_hash


def test_analysis_service_ai_branch(registry, assignment):
    cfg = ModeConfig(mode = "ml", feature_schema_version = "v1")
    svc = AnalysisService(
        registry = registry,
        assignments = {"a-1": assignment},
        templates = {},
        mode_config = cfg,
    )
    s = parse_submission(RAW)
    out = svc.run_ai(s)
    
    assert out["mode"] == "ml"
    assert out["config_hash"] == cfg.config_hash
    assert out["raw_prediction"]["deterministic"] is True