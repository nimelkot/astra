from __future__ import annotations

from pathlib import Path

from mcp.server import MCPServer

from .core.engine import AstraEngine
from .core.visualization import write_visualization
from .core.watcher import AstraWatcher

mcp = MCPServer("Astra", version="0.1.0")
_watchers: dict[str, AstraWatcher] = {}


def _indexed_engine(path: str) -> AstraEngine:
    """Return an engine with a current graph and vector index."""
    engine = AstraEngine(Path(path))
    engine.index()
    return engine


@mcp.prompt(
    name="astra_codebase_workflow",
    title="Astra Codebase Workflow",
    description="Plan an efficient Astra tool sequence for a codebase task.",
)
def astra_codebase_workflow(path: str, task: str) -> list[dict[str, str]]:
    """Give an MCP client a structured, task-aware Astra orchestration plan."""
    return [
        {
            "role": "user",
            "content": (
                f"Work on the local codebase at {path} for this task: {task}\n\n"
                "Use Astra's existing MCP tools as the source of truth. Follow this protocol:\n"
                "1. Call astra_index_repo once to refresh the incremental graph and vector index.\n"
                "2. Choose only the narrowest next tools for the task: "
                "search/context tools for explanation, "
                "path/callers/impact for dependencies, fragility/tether for risk, "
                "refactor_plan before renames, test_map/affected_tests for test planning, "
                "run_impacted for validation, and visualize for a graph view.\n"
                "3. Interpret returned JSON fields and report missing symbols, truncation, "
                "cycles, untested nodes, "
                "or failed tests explicitly.\n"
                "4. Do not repeat indexing between read-only calls unless source files changed.\n"
                "5. Before edits, review impact, fragility, and refactor_plan. After edits, "
                "refresh the index and run affected tests. Use astra_visualize to render "
                "Astra artifacts; "
                "never generate HTML manually.\n"
                "6. Use returned paths, nodes, snippets, test selections, and report URLs "
                "instead of recreating "
                "Astra's graph, index, test selection, or visualization independently."
            ),
        }
    ]


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
def astra_start_watch(path: str, interval: float = 1.0) -> dict:
    """Start one background index watcher for a workspace and return its status."""
    root = str(Path(path).resolve())
    watcher = _watchers.get(root)
    if watcher is None:
        watcher = AstraWatcher(root, interval=interval)
        _watchers[root] = watcher
    return watcher.start()


@mcp.tool()
def astra_index_status(path: str) -> dict:
    """Return the background watcher status for a workspace."""
    root = str(Path(path).resolve())
    watcher = _watchers.get(root)
    if watcher is None:
        return {"root": root, "running": False, "index_count": 0, "last_error": None}
    return watcher.status()


@mcp.tool()
def astra_stop_watch(path: str) -> dict:
    """Stop the background index watcher for a workspace."""
    root = str(Path(path).resolve())
    watcher = _watchers.pop(root, None)
    if watcher is None:
        return {"root": root, "running": False, "index_count": 0, "last_error": None}
    return watcher.stop()


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
