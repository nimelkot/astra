from __future__ import annotations

from pathlib import Path

from .embeddings import VectorIndex
from .graph import StructuralGraph
from .models import CodeChunk, SearchResult
from .parser import CodeParser


class AstraEngine:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.graph_path = self.root / ".astra_graph.json"
        self.vector_path = self.root / ".astra_vectors"
        self.parser = CodeParser()
        self.graph = (
            StructuralGraph.load(self.graph_path) if self.graph_path.exists() else StructuralGraph()
        )
        self.vectors = VectorIndex(self.vector_path)

    def index(self) -> dict[str, int | str]:
        chunks: list[CodeChunk] = []
        references: list[dict[str, str]] = []
        for path in self.parser.discover(self.root):
            file_chunks, file_refs = self.parser.parse_file(path, self.root)
            chunks.extend(file_chunks)
            references.extend(file_refs)
        self.graph = StructuralGraph()
        self.graph.add_chunks(chunks, references)
        self.graph.save(self.graph_path)
        count = self.vectors.index(chunks)
        return {
            "root": str(self.root),
            "files": len({chunk.path for chunk in chunks}),
            "chunks": count,
            "graph": str(self.graph_path),
            "vectors": str(self.vector_path),
        }

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        return self.vectors.search(query, limit)

    def callers(self, target: str, limit: int = 50) -> list[dict]:
        return self.graph.callers(target, limit)

    def hybrid_context(self, query: str, limit: int = 5, expansion: int = 5) -> dict:
        results = self.search(query, limit)
        related: list[dict] = []
        seen: set[str] = set()
        for result in results:
            for item in self.callers(result.chunk.name, expansion):
                if item["id"] not in seen:
                    related.append(item)
                    seen.add(item["id"])
        return {"matches": [result.as_dict() for result in results], "related": related}
