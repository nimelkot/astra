from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import networkx as nx

from .models import CodeChunk


class StructuralGraph:
    def __init__(self, graph: nx.DiGraph | None = None) -> None:
        self.graph = graph or nx.DiGraph()

    def add_chunks(self, chunks: list[CodeChunk], references: list[dict[str, str]]) -> None:
        for chunk in chunks:
            self.graph.add_node(chunk.id, **chunk.as_metadata())
            if chunk.kind != "module":
                self.graph.add_edge(f"{chunk.path}:module", chunk.id, kind="defines")
        ids_by_name = {
            data.get("name"): node
            for node, data in self.graph.nodes(data=True)
            if data.get("kind") != "module"
        }
        for reference in references:
            target = ids_by_name.get(reference["target"])
            if target and reference["source"] in self.graph:
                self.graph.add_edge(reference["source"], target, kind=reference["kind"])

    def callers(self, target: str, limit: int = 50) -> list[dict[str, Any]]:
        matches = [
            node
            for node, data in self.graph.nodes(data=True)
            if node == target or data.get("name") == target or node.endswith(f":{target}")
        ]
        found: list[dict[str, Any]] = []
        for node in matches:
            for caller in self.graph.predecessors(node):
                edge = self.graph.edges[caller, node]
                if edge.get("kind") in {"calls", "depends_on"}:
                    found.append(
                        {"id": caller, **self.graph.nodes[caller], "relationship": edge.get("kind")}
                    )
        return found[:limit]

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(nx.node_link_data(self.graph), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "StructuralGraph":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(nx.node_link_graph(data, directed=True))
