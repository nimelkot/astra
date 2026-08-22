from __future__ import annotations

from pathlib import Path

from mcp.server import MCPServer

from .core.engine import AstraEngine
from .core.visualization import write_visualization

mcp = MCPServer("Astra", version="0.1.0")


@mcp.tool()
def astra_index_repo(path: str) -> dict:
    """Index a local repository into Astra's graph and vector store."""
    return AstraEngine(Path(path)).index()


@mcp.tool()
def astra_semantic_search(path: str, query: str, limit: int = 10) -> list[dict]:
    """Search indexed code chunks by conceptual intent."""
    return [result.as_dict() for result in AstraEngine(Path(path)).search(query, limit)]


@mcp.tool()
def astra_get_callers(path: str, target: str, limit: int = 50) -> list[dict]:
    """Find exact callers of a function or method using the structural graph."""
    return AstraEngine(Path(path)).callers(target, limit)


@mcp.tool()
def astra_hybrid_context(path: str, query: str, limit: int = 5, expansion: int = 5) -> dict:
    """Combine semantic matches with structural expansion."""
    return AstraEngine(Path(path)).hybrid_context(query, limit, expansion)


@mcp.tool()
def astra_path(path: str, source: str, target: str, max_hops: int = 12) -> dict | None:
    """Find the shortest structural path between two symbols."""
    return AstraEngine(Path(path)).path(source, target, max_hops)


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
    """Extract a localized dependency-complete subgraph for LLM context."""
    return AstraEngine(Path(path)).dipper(
        query,
        limit=limit,
        parent_depth=parent_depth,
        child_depth=child_depth,
        max_nodes=max_nodes,
        max_source_chars=max_source_chars,
    )


@mcp.tool()
def astra_tether(path: str, cycle_limit: int = 20, fanout_threshold: int = 12) -> dict:
    """Run graph health checks and flag structural anomalies."""
    return AstraEngine(Path(path)).tether(
        cycle_limit=cycle_limit,
        fanout_threshold=fanout_threshold,
    )


@mcp.tool()
def astra_visualize(path: str, output: str | None = None) -> dict:
    """Generate a local HTML visualization and return its path and file URL."""
    report = write_visualization(Path(path), output)
    return {"path": str(report), "url": report.as_uri()}


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
