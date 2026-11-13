from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SimilarityConfig:
    version: str
    templates: dict[str, str] = field(default_factory=dict)

    def template_for(self, assignment_id: str) -> str | None:
        return self.templates.get(assignment_id)

    @property
    def config_hash(self) -> str:
        payload = {"version": self.version, "templates": self.templates}
        raw = json.dumps(payload, sort_keys = True, ensure_ascii = False)

        return hashlib.sha256(raw.encode("utf-8")).hexdigest()