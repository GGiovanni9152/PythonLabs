from __future__ import annotations

from typing import Any

from school.ai.config import ModeConfig
from school.ai.feature_extractor import BasicFeatureExtractor
from school.ai.feedback_builder import BasicFeedbackBuilder
from school.ai.stub_model import StubModel
from school.analyzers.registry import AnalyzerRegistry
from school.domain.contracts import AnalysisContext, Analyzer, FeatureExtractor, FeedbackBuilder, Model
from school.domain.models import AnalysisReport, Assignment, Submission


class AnalysisService:
    def __init__(
        self,
        registry: AnalyzerRegistry,
        assignments: dict[str, Assignment],
        templates: dict[str, str],
        mode_config: ModeConfig,
        feature_extractor: FeatureExtractor | None = None,
        feedback_builder: FeedbackBuilder | None = None,
        model: Model | None = None,
    ) -> None:
        self._registry = registry
        self._assignments = assignments
        self._templates = templates
        self._mode = mode_config
        self._features = feature_extractor or BasicFeatureExtractor()
        self._feedback = feedback_builder or BasicFeedbackBuilder()
        self._model = model or StubModel()

    def _context_for(self, assignment: Assignment) -> AnalysisContext:
        template_text = self._templates.get(assignment.template_id) if assignment.template_id else None
        return AnalysisContext(
            assignment = assignment,
            template_text = template_text,
            config_hash = self._mode.config_hash,
        )

    def run(self, analyzer_id: str, submission: Submission) -> AnalysisReport:
        analyzer = self._registry.get(analyzer_id)
        assignment = self._assignments[submission.assignment_id]
        context = self._context_for(assignment)

        return analyzer.analyze(submission, context)

    def run_ai(self, submission: Submission) -> dict[str, Any]:
        features = self._features.extract(submission)
        raw = self._model.predict(features)
        feedback = self._feedback.build(raw, submission)
        
        return {
            "mode": self._mode.mode,
            "config_hash": self._mode.config_hash,
            "features": features,
            "raw_prediction": raw,
            "feedback": feedback,
        }