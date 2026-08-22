from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CodeChunk:
    id: str
    path: str
    name: str
    kind: str
    start_line: int
    end_line: int
    source: str
    docstring: str = ""
    symbols: list[str] = field(default_factory=list)
    branches: int = 0
    nesting: int = 0
    parameters: int = 0

    def as_metadata(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "kind": self.kind,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "docstring": self.docstring,
            "symbols": ",".join(self.symbols),
            "branches": self.branches,
            "nesting": self.nesting,
            "parameters": self.parameters,
        }


@dataclass
class SearchResult:
    chunk: CodeChunk
    score: float
    distance: float | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "distance": self.distance,
            **self.chunk.as_metadata(),
            "source": self.chunk.source,
        }
