from __future__ import annotations

import json

from pydantic import ValidationError

from src.domain.errors import SubmissionError
from src.domain.models import AIDeclaration, Submission
from src.validation.pydantic_models import SubmissionModel

def _to_domain(model: SubmissionModel) -> Submission:
    ai = model.ai_declaration
    return Submission(
        schema_version=model.schema_version,
        submission_id=model.submission_id,
        student_id=model.student_id,
        assignment_id=model.assignment_id,
        submitted_at=model.submitted_at,
        text=model.text,                  
        code=model.code,
        template_id=model.template_id,
        ai_declaration=AIDeclaration(
            used=ai.used,
            verified_by_student=ai.verified_by_student,
            tool=ai.tool,
            purpose=ai.purpose,
        ),
    )

def parse_submission(raw: str) -> Submission:
    try: 
        data = json.loads(raw)
    except json.JSONDecodeError as e: #кривой json
        raise SubmissionError("format_error", None, f"invalid JSON: {e}") from e
    
    if not isinstance(data, dict):
        raise SubmissionError("format_error", None, "top-level value must be an object")

    try: #проверка схемы
        model = SubmissionModel.model_validate(data)
    except ValidationError as e:
        first = e.errors()[0]
        field = ".".join(str(p) for p in first["loc"]) or None
        raise SubmissionError("schema_error", field, first["msg"]) from e

    return _to_domain(model)

    