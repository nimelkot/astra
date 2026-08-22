from __future__ import annotations

import re
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

    def path(self, source: str, target: str, max_hops: int = 12) -> dict | None:
        return self.graph.shortest_path(source, target, max_hops)

    def dipper(
        self,
        query: str,
        limit: int = 5,
        parent_depth: int = 1,
        child_depth: int = 1,
        max_nodes: int = 80,
        max_source_chars: int = 280,
    ) -> dict:
        seed_ids: list[str] = []
        seed_ids.extend(self.graph.resolve_nodes(query, limit=limit))

        for result in self.search(query, limit):
            if result.chunk.id not in seed_ids:
                seed_ids.append(result.chunk.id)
            if len(seed_ids) >= limit:
                break

        neighborhood = self.graph.neighborhood(
            seed_ids,
            parent_depth=parent_depth,
            child_depth=child_depth,
            max_nodes=max_nodes,
        )
        nodes = neighborhood["nodes"]
        edges = neighborhood["edges"]

        chunks_by_id = {chunk.id: chunk for chunk in self.vectors.chunks}
        snippets: list[dict[str, str | int]] = []
        for node in nodes:
            chunk = chunks_by_id.get(node["id"])
            if chunk is None:
                continue
            source = re.sub(r"\s+", " ", chunk.source).strip()
            snippets.append(
                {
                    "id": chunk.id,
                    "path": chunk.path,
                    "name": chunk.name,
                    "kind": chunk.kind,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "source": source[:max_source_chars],
                }
            )

        return {
            "query": query,
            "seeds": seed_ids,
            "summary": {
                "nodes": len(nodes),
                "edges": len(edges),
                "snippets": len(snippets),
                "parent_depth": parent_depth,
                "child_depth": child_depth,
            },
            "nodes": nodes,
            "edges": edges,
            "snippets": snippets,
        }

    def tether(self, cycle_limit: int = 20, fanout_threshold: int = 12) -> dict:
        report = self.graph.health_report(
            cycle_limit=cycle_limit,
            fanout_threshold=fanout_threshold,
        )
        report["root"] = str(self.root)
        return report

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
