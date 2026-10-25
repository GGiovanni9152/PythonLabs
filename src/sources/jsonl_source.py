from __future__ import annotations
from pathlib import Path
from typing import Iterable
from src.domain.contracts import SubmissionSource

class JSONLSource:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def iter_raw(self) -> Iterable[str]:
        with self._open() as f:
            for line in f:
                stripped = line.rstrip("\n")
                if stripped == "":
                    continue
                yield stripped

    def _open(self): 
        return open(self._path, "r", encoding="utf-8")