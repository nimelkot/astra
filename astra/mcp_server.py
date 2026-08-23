from __future__ import annotations

from pathlib import Path

from mcp.server import MCPServer

from .core.engine import AstraEngine
from .core.visualization import write_visualization

mcp = MCPServer("Astra", version="0.1.0")


def _indexed_engine(path: str) -> AstraEngine:
    """Return an engine with a current graph and vector index."""
    engine = AstraEngine(Path(path))
    engine.index()
    return engine


@mcp.tool()
def astra_index_repo(path: str) -> dict:
    """Index or refresh a local repository before using other Astra tools."""
    return AstraEngine(Path(path)).index()


@mcp.tool()
def astra_semantic_search(path: str, query: str, limit: int = 10) -> list[dict]:
    """Search indexed chunks; automatically index first when artifacts are missing."""
    return [result.as_dict() for result in _indexed_engine(path).search(query, limit)]


@mcp.tool()
def astra_get_callers(path: str, target: str, limit: int = 50) -> list[dict]:
    """Find callers from the graph, indexing first when artifacts are missing."""
    return _indexed_engine(path).callers(target, limit)


@mcp.tool()
def astra_hybrid_context(path: str, query: str, limit: int = 5, expansion: int = 5) -> dict:
    """Index if needed, then combine semantic matches with structural expansion."""
    return _indexed_engine(path).hybrid_context(query, limit, expansion)


@mcp.tool()
def astra_path(path: str, source: str, target: str, max_hops: int = 12) -> dict | None:
    """Find a graph path, indexing first when this workspace has no graph artifact."""
    return _indexed_engine(path).path(source, target, max_hops)


@mcp.tool()
def astra_dipper(
    path: str,
    query: str,
    limit: int = 5,
    parent_depth: int = 1,
    child_depth: int = 1,
    max_nodes: int = 80,
    max_source_chars: int = 280,
) -> dict:
    """Index if needed, then extract dependency-complete context around a query."""
    return _indexed_engine(path).dipper(
        query,
        limit=limit,
        parent_depth=parent_depth,
        child_depth=child_depth,
        max_nodes=max_nodes,
        max_source_chars=max_source_chars,
    )


@mcp.tool()
def astra_tether(path: str, cycle_limit: int = 20, fanout_threshold: int = 12) -> dict:
    """Index if needed, then flag cycles, orphans, and high fan-out nodes."""
    return _indexed_engine(path).tether(
        cycle_limit=cycle_limit,
        fanout_threshold=fanout_threshold,
    )


@mcp.tool()
def astra_get_fragility_hotspots(
    path: str, limit: int = 10, threshold: float = 75.0
) -> dict:
    """Index if needed, then rank fragile functions/classes using graph and AST metrics."""
    return _indexed_engine(path).fragility_hotspots(limit=limit, threshold=threshold)


@mcp.tool()
def astra_impact(path: str, target: str, max_nodes: int = 200) -> dict:
    """Index if needed, then report declarations/files in a target's upstream blast radius."""
    return _indexed_engine(path).blast_radius(target, max_nodes=max_nodes)


@mcp.tool()
def astra_refactor_plan(path: str, target: str, replacement: str) -> dict:
    """Index if needed, then preview a graph-ordered rename without editing files."""
    return _indexed_engine(path).refactor_plan(target, replacement)


@mcp.tool()
def astra_test_map(path: str, limit: int = 1000) -> dict:
    """Map source declarations to tests that reach them through the graph."""
    return _indexed_engine(path).test_map(limit)


@mcp.tool()
def astra_affected_tests(path: str, changed_paths: list[str], limit: int = 100) -> dict:
    """Select indexed test files affected by a set of changed paths."""
    return _indexed_engine(path).affected_tests(changed_paths, limit)


@mcp.tool()
def astra_gen_test_scaffold(path: str, target: str) -> dict:
    """Generate a read-only pytest scaffold with target context and dependency hints."""
    return _indexed_engine(path).test_scaffold(target)


@mcp.tool()
def astra_run_impacted(path: str, changed_paths: list[str], timeout: int = 120) -> dict:
    """Select and run impacted tests with a bounded local pytest subprocess."""
    return _indexed_engine(path).run_impacted(changed_paths, timeout)


@mcp.tool()
def astra_visualize(path: str, output: str | None = None) -> dict:
    """Index if needed, then render Astra artifacts; never generate the HTML manually."""
    _indexed_engine(path)
    report = write_visualization(Path(path), output)
    return {"path": str(report), "url": report.as_uri()}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
