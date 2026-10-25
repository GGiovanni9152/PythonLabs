from __future__ import annotations

from typing import Iterable

from school.domain.contracts import SubmissionSource

class InMemorySource:
    def __init__(self, items: Iterable[str]) -> None:
        self._items = list(items)

    def iter_raw(self) -> Iterable[str]:
        return iter(self._items)