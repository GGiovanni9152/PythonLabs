from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterator

from school.domain.models import CorpusEntry, Pair, DerivationRelation

class CorpusSource:  
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
    
    def iter_entries(self) -> Iterator[CorpusEntry]:
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                # строка в enum
                data["derivation_relation"] = DerivationRelation(data["derivation_relation"]) 
                yield CorpusEntry(**data)
    
    def iter_pairs(self) -> Iterator[Pair]:
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                data["derivation_relation"] = DerivationRelation(data["derivation_relation"])
                yield Pair(**data)