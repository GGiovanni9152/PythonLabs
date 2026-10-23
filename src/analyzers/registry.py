from __future__ import annotations
from src.domain.contracts import Analyzer

class AnalyzerRegistry:
    def __init__(self) -> None:
        self._items: dict[str, Analyzer] = {}

    def register(self, analyzer: Analyzer) -> None:
        self._items[analyzer.analyzer_id] = analyzer

    def get(self, analyzer_id: str) -> Analyzer:
        try:
            return self._items[analyzer_id]
        except KeyError as e:
            raise KeyError(f"unknown analyzer: {analyzer_id}") from e

    def all(self) -> list[Analyzer]:
        return list(self._items.values())