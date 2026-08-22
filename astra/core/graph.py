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

    def shortest_path(self, source: str, target: str, max_hops: int = 12) -> dict[str, Any] | None:
        source_matches = self._matching_nodes(source)
        target_matches = self._matching_nodes(target)
        if not source_matches or not target_matches:
            return None

        undirected = self.graph.to_undirected(as_view=True)
        best_path: list[str] | None = None
        for source_node in source_matches:
            for target_node in target_matches:
                if source_node == target_node:
                    candidate = [source_node]
                else:
                    try:
                        candidate = nx.shortest_path(undirected, source_node, target_node)
                    except nx.NetworkXNoPath:
                        continue
                if best_path is None or len(candidate) < len(best_path):
                    best_path = candidate

        if best_path is None:
            return None

        hops = len(best_path) - 1
        if hops > max_hops:
            return None

        nodes: list[dict[str, Any]] = []
        for node_id in best_path:
            data = self.graph.nodes[node_id]
            nodes.append(
                {"id": node_id, "name": data.get("name", node_id), "kind": data.get("kind")}
            )

        edges: list[dict[str, str]] = []
        for left, right in zip(best_path, best_path[1:]):
            if self.graph.has_edge(left, right):
                edge = self.graph.edges[left, right]
                edges.append({"from": left, "to": right, "kind": edge.get("kind", "related")})
            elif self.graph.has_edge(right, left):
                edge = self.graph.edges[right, left]
                edges.append({"from": right, "to": left, "kind": edge.get("kind", "related")})
            else:
                edges.append({"from": left, "to": right, "kind": "related"})

        return {"hops": hops, "nodes": nodes, "edges": edges}

    def _matching_nodes(self, symbol: str) -> list[str]:
        value = symbol.strip()
        return [
            node
            for node, data in self.graph.nodes(data=True)
            if node == value or data.get("name") == value or node.endswith(f":{value}")
        ]

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(nx.node_link_data(self.graph), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "StructuralGraph":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(nx.node_link_graph(data, directed=True))
