from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True, slots=True)
class ModeConfig:
    mode: Literal["ml", "llm"]
    template_version: str | None = None
    feature_schema_version: str | None = None

    @property
    def config_hash(self) -> str:
        payload = {
            "mode": self.mode,
            "template_version": self.template_version,
            "feature_schema_version": self.feature_schema_version,
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()