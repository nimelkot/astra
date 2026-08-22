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
        source_matches = self.resolve_nodes(source)
        target_matches = self.resolve_nodes(target)
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
                {
                    "id": node_id,
                    "name": data.get("name", node_id),
                    "kind": data.get("kind"),
                    "path": data.get("path"),
                    "start_line": data.get("start_line"),
                    "end_line": data.get("end_line"),
                }
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

    def resolve_nodes(self, symbol: str, limit: int = 25) -> list[str]:
        value = symbol.strip()
        matches = [
            node
            for node, data in self.graph.nodes(data=True)
            if node == value or data.get("name") == value or node.endswith(f":{value}")
        ]
        return matches[:limit]

    def neighborhood(
        self,
        seeds: list[str],
        parent_depth: int = 1,
        child_depth: int = 1,
        max_nodes: int = 80,
    ) -> dict[str, Any]:
        if not seeds:
            return {"nodes": [], "edges": []}

        node_ids: set[str] = set()
        for seed in seeds:
            if seed in self.graph:
                node_ids.add(seed)
                node_ids.update(
                    self._walk(
                        seed,
                        direction="up",
                        depth=parent_depth,
                        max_nodes=max_nodes,
                    )
                )
                node_ids.update(
                    self._walk(seed, direction="down", depth=child_depth, max_nodes=max_nodes)
                )
            if len(node_ids) >= max_nodes:
                break
        node_ids = set(list(node_ids)[:max_nodes])

        nodes: list[dict[str, Any]] = []
        for node_id in node_ids:
            data = self.graph.nodes[node_id]
            nodes.append(
                {
                    "id": node_id,
                    "name": data.get("name", node_id),
                    "kind": data.get("kind"),
                    "path": data.get("path"),
                    "start_line": data.get("start_line"),
                    "end_line": data.get("end_line"),
                }
            )

        edges: list[dict[str, str]] = []
        for left, right, data in self.graph.edges(data=True):
            if left in node_ids and right in node_ids:
                edges.append({"from": left, "to": right, "kind": data.get("kind", "related")})

        return {"nodes": nodes, "edges": edges}

    def health_report(self, cycle_limit: int = 20, fanout_threshold: int = 12) -> dict[str, Any]:
        relationship_edges = {
            (u, v)
            for u, v, data in self.graph.edges(data=True)
            if data.get("kind") in {"calls", "depends_on"}
        }
        relationship_graph = nx.DiGraph()
        relationship_graph.add_nodes_from(self.graph.nodes())
        relationship_graph.add_edges_from(relationship_edges)

        cycles_raw = list(nx.simple_cycles(relationship_graph))[:cycle_limit]
        cycles = [{"length": len(cycle), "nodes": cycle} for cycle in cycles_raw]

        orphan_nodes: list[dict[str, Any]] = []
        high_fanout: list[dict[str, Any]] = []
        for node_id, data in self.graph.nodes(data=True):
            kind = data.get("kind")
            if kind == "module":
                continue
            incoming_rel = 0
            outgoing_rel = 0
            for parent, child, edge_data in self.graph.in_edges(node_id, data=True):
                if edge_data.get("kind") in {"calls", "depends_on"}:
                    incoming_rel += 1
            for parent, child, edge_data in self.graph.out_edges(node_id, data=True):
                if edge_data.get("kind") in {"calls", "depends_on"}:
                    outgoing_rel += 1
            if incoming_rel == 0 and outgoing_rel == 0:
                orphan_nodes.append(
                    {"id": node_id, "name": data.get("name", node_id), "kind": kind}
                )
            if outgoing_rel >= fanout_threshold:
                high_fanout.append(
                    {
                        "id": node_id,
                        "name": data.get("name", node_id),
                        "kind": kind,
                        "outgoing_relationships": outgoing_rel,
                    }
                )

        anomalies: list[dict[str, Any]] = []
        if cycles:
            anomalies.append(
                {
                    "severity": "warn",
                    "type": "cycle_detected",
                    "message": "Circular call/dependency chains detected.",
                    "count": len(cycles),
                }
            )
        if orphan_nodes:
            anomalies.append(
                {
                    "severity": "info",
                    "type": "orphan_nodes",
                    "message": (
                        "Declarations without incoming or outgoing structural relationships."
                    ),
                    "count": len(orphan_nodes),
                }
            )
        if high_fanout:
            anomalies.append(
                {
                    "severity": "info",
                    "type": "high_fanout",
                    "message": "Declarations with unusually high outward structural coupling.",
                    "count": len(high_fanout),
                }
            )

        status = "pass" if not cycles else "warn"
        return {
            "status": status,
            "summary": {
                "nodes": self.graph.number_of_nodes(),
                "edges": self.graph.number_of_edges(),
                "relationship_edges": len(relationship_edges),
                "cycles": len(cycles),
                "orphans": len(orphan_nodes),
                "high_fanout": len(high_fanout),
            },
            "anomalies": anomalies,
            "details": {
                "cycles": cycles,
                "orphans": orphan_nodes,
                "high_fanout": high_fanout,
            },
        }

    def _walk(self, seed: str, direction: str, depth: int, max_nodes: int) -> set[str]:
        if depth <= 0:
            return set()
        visited = {seed}
        frontier = {seed}
        collected: set[str] = set()
        for _ in range(depth):
            next_frontier: set[str] = set()
            for node in frontier:
                neighbors = (
                    self.graph.predecessors(node)
                    if direction == "up"
                    else self.graph.successors(node)
                )
                for neighbor in neighbors:
                    if neighbor in visited:
                        continue
                    visited.add(neighbor)
                    collected.add(neighbor)
                    next_frontier.add(neighbor)
                    if len(collected) >= max_nodes:
                        return collected
            frontier = next_frontier
            if not frontier:
                break
        return collected

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(nx.node_link_data(self.graph), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "StructuralGraph":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(nx.node_link_graph(data, directed=True))
