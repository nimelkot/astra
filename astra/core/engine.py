from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import networkx as nx

from .embeddings import VectorIndex
from .graph import StructuralGraph
from .models import CodeChunk, SearchResult
from .parser import CodeParser


class AstraEngine:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.graph_path = self.root / ".astra_graph.json"
        self.vector_path = self.root / ".astra_vectors"
        self.cache_path = self.root / ".astra_index_cache.json"
        self.parser = CodeParser()
        self.graph = (
            StructuralGraph.load(self.graph_path) if self.graph_path.exists() else StructuralGraph()
        )
        self.vectors = VectorIndex(self.vector_path)

    def index(self) -> dict[str, int | str]:
        cache = self._load_cache()
        cached_files: dict[str, dict] = cache.get("files", {})
        chunks: list[CodeChunk] = []
        references: list[dict[str, str]] = []
        changed_paths: set[str] = set()
        discovered = self.parser.discover(self.root)
        current_paths = {path.relative_to(self.root).as_posix() for path in discovered}
        removed_paths = set(cached_files) - current_paths
        next_cache_files: dict[str, dict] = {}

        for path in discovered:
            relative = path.relative_to(self.root).as_posix()
            file_hash = self._file_hash(path)
            cached = cached_files.get(relative)
            if cached and cached.get("hash") == file_hash:
                file_chunks = [CodeChunk(**item) for item in cached.get("chunks", [])]
                file_refs = [dict(item) for item in cached.get("references", [])]
            else:
                changed_paths.add(relative)
                file_chunks, file_refs = self.parser.parse_file(path, self.root)
            next_cache_files[relative] = {
                "hash": file_hash,
                "chunks": [chunk.__dict__ for chunk in file_chunks],
                "references": file_refs,
            }
            chunks.extend(file_chunks)
            references.extend(file_refs)

        self.graph = StructuralGraph()
        self.graph.add_chunks(chunks, references)
        self.graph.save(self.graph_path)
        self._save_cache({"version": 2, "files": next_cache_files})
        count = self.vectors.index(
            chunks,
            changed_paths=changed_paths,
            removed_paths=removed_paths,
        )
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

    def fragility_hotspots(self, limit: int = 10, threshold: float = 75.0) -> dict:
        report = self.graph.fragility_hotspots(limit=limit, threshold=threshold)
        report["root"] = str(self.root)
        return report

    def star_nodes(self, limit: int = 20, threshold: float = 60.0) -> dict:
        report = self.graph.star_nodes(limit=limit, threshold=threshold)
        report["root"] = str(self.root)
        return report

    def blast_radius(self, target: str, max_nodes: int = 200) -> dict:
        report = self.graph.blast_radius(target, max_nodes=max_nodes)
        report["root"] = str(self.root)
        return report

    def refactor_plan(self, target: str, replacement: str) -> dict:
        order_report = self.graph.refactor_order(target)
        if not order_report["found"]:
            return {"target": target, "replacement": replacement, **order_report}

        identifier = re.compile(rf"\b{re.escape(target)}\b")
        chunks_by_id = {chunk.id: chunk for chunk in self.vectors.chunks}
        changes: list[dict] = []
        for node_id in order_report["order"]:
            chunk = chunks_by_id.get(node_id)
            if chunk is None:
                continue
            matches = list(identifier.finditer(chunk.source))
            if matches:
                changes.append(
                    {
                        "id": chunk.id,
                        "path": chunk.path,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "kind": chunk.kind,
                        "name": chunk.name,
                        "occurrences": len(matches),
                        "before": chunk.source,
                        "after": identifier.sub(replacement, chunk.source),
                    }
                )
        return {
            "root": str(self.root),
            "target": target,
            "replacement": replacement,
            "order": order_report["order"],
            "cycles": order_report["cycles"],
            "changes": changes,
            "apply": False,
        }

    def test_map(self, limit: int = 1000) -> dict:
        tests = {
            node
            for node, data in self.graph.graph.nodes(data=True)
            if self._is_test_node(node, data)
        }
        sources = {
            node
            for node, data in self.graph.graph.nodes(data=True)
            if data.get("kind") != "module" and node not in tests
        }
        items = []
        for source in sorted(sources):
            reaching = sorted(test for test in tests if self._can_reach(test, source))
            data = self.graph.graph.nodes[source]
            items.append(
                {
                    "id": source,
                    "name": data.get("name", source),
                    "path": data.get("path"),
                    "start_line": data.get("start_line"),
                    "tests": reaching,
                    "tested": bool(reaching),
                }
            )
            if len(items) >= limit:
                break
        return {
            "root": str(self.root),
            "sources": items,
            "untested": sum(not item["tested"] for item in items),
        }

    def affected_tests(self, changed_paths: list[str], limit: int = 100) -> dict:
        normalized = {Path(path).as_posix() for path in changed_paths}
        changed_nodes = [
            node
            for node, data in self.graph.graph.nodes(data=True)
            if data.get("path") in normalized and data.get("kind") != "module"
        ]
        test_nodes = {
            node
            for node, data in self.graph.graph.nodes(data=True)
            if self._is_test_node(node, data)
        }
        affected = sorted(
            test
            for test in test_nodes
            if any(self._can_reach(test, node) for node in changed_nodes)
        )[:limit]
        files = sorted({self.graph.graph.nodes[node].get("path") for node in affected})
        return {
            "root": str(self.root),
            "changed_paths": sorted(normalized),
            "changed_nodes": changed_nodes,
            "tests": affected,
            "test_files": files,
            "uncovered_changed_nodes": [
                node
                for node in changed_nodes
                if not any(self._can_reach(test, node) for test in test_nodes)
            ],
        }

    def test_scaffold(self, target: str) -> dict:
        nodes = self.graph.resolve_nodes(target)
        if not nodes:
            return {"root": str(self.root), "target": target, "found": False, "scaffold": ""}
        node = nodes[0]
        data = self.graph.graph.nodes[node]
        callers = self.graph.callers(target, limit=8)
        scaffold = (
            "import pytest\n\n\n"
            f"def test_{data.get('name', 'target')}_behavior():\n"
            f"    # Target: {data.get('path')}:{data.get('start_line')}\n"
            "    # Dependencies/callers to consider: "
            f"{', '.join(item.get('name', '') for item in callers) or 'none'}\n"
            "    # TODO: Arrange real fixtures and mocks.\n"
            "    pytest.fail(\"Implement assertions for the target behavior\")\n"
        )
        return {
            "root": str(self.root),
            "target": target,
            "found": True,
            "target_node": node,
            "scaffold": scaffold,
        }

    def run_impacted(self, changed_paths: list[str], timeout: int = 120) -> dict:
        selection = self.affected_tests(changed_paths)
        command = [sys.executable, "-m", "pytest", *selection["test_files"]]
        if not selection["test_files"]:
            return {
                **selection,
                "command": command,
                "status": "no_tests",
                "returncode": 0,
                "output": "",
            }
        try:
            completed = subprocess.run(
                command,
                cwd=self.root,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                **selection,
                "command": command,
                "status": "timeout",
                "returncode": None,
                "output": str(exc),
            }
        return {
            **selection,
            "command": command,
            "status": "passed" if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "output": (completed.stdout + completed.stderr)[-12000:],
        }

    def _is_test_node(self, node: str, data: dict) -> bool:
        path = str(data.get("path", "")).lower()
        name = str(data.get("name", "")).lower()
        test_path = "test" in Path(path).parts or Path(path).name.startswith("test_")
        return test_path and (name.startswith("test_") or name.startswith("test"))

    def _can_reach(self, source: str, target: str) -> bool:
        relationship = self.graph.graph.edge_subgraph(
            [
                (left, right)
                for left, right, data in self.graph.graph.edges(data=True)
                if data.get("kind") in {"calls", "depends_on"}
            ]
        )
        return source == target or (
            source in relationship
            and target in relationship
            and nx.has_path(relationship, source, target)
        )

    def _load_cache(self) -> dict:
        if not self.cache_path.exists():
            return {"version": 2, "files": {}}
        try:
            data = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"version": 2, "files": {}}
        if data.get("version") != 2 or not isinstance(data.get("files"), dict):
            return {"version": 2, "files": {}}
        return data

    def _save_cache(self, cache: dict) -> None:
        self.cache_path.write_text(json.dumps(cache, indent=2), encoding="utf-8")

    def _file_hash(self, path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(8192), b""):
                digest.update(chunk)
        return digest.hexdigest()

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
