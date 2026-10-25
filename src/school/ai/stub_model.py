from __future__ import annotations
from typing import Any

class StubModel:
    def predict(self, features: dict[str, Any]) -> dict[str, Any]:
        return {
            "verdict": "ok",
            "confidence": 0.5,
            "deterministic": True,
        }