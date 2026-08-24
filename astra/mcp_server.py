from __future__ import annotations

from pathlib import Path

from mcp.server import MCPServer

from .core.engine import AstraEngine
from .core.visualization import write_visualization
from .core.watcher import AstraWatcher

MCP_INSTRUCTIONS = (
    "Astra provides indexed code intelligence for the connected local workspace. "
    "Use this routing protocol and reuse Astra's returned JSON, source locations, test "
    "selections, and report URLs.\n"
    "1. Sync: call astra_index_repo once at the start of a task, or call astra_start_watch "
    "once for a long editing session. All analysis tools perform an incremental hash-based "
    "refresh automatically, so do not repeat astra_index_repo between read-only calls. "
    "Use astra_index_status to check a watcher and astra_stop_watch when the session ends.\n"
    "2. Discover: use astra_semantic_search for concepts, astra_get_callers for direct callers, "
    "astra_hybrid_context for semantic matches plus callers, and astra_dipper for a compact "
    "dependency-complete context package. These read-only discovery calls may be parallelized "
    "after sync when they are independent.\n"
    "3. Understand structure: use astra_path for a relationship between two symbols and "
    "astra_impact for the recursive upstream blast radius and affected files. Use "
    "astra_tether for cycles, orphan declarations, and high fan-out; use "
    "astra_get_fragility_hotspots for centrality, AST complexity, and instability scores, "
    "and astra_star_nodes for highly depended-on declarations.\n"
    "4. Change safely: call astra_refactor_plan before a rename or structural edit. It is "
    "read-only, returns an ordered preview, and must be reviewed before the host edits files.\n"
    "5. Test deliberately: use astra_test_map to find untested declarations, "
    "astra_affected_tests for changed paths, astra_gen_test_scaffold for a reviewed pytest "
    "stub, and astra_run_impacted after edits. Interpret status, returncode, and output; "
    "never claim success from test selection alone. Use astra_validate_change as the "
    "high-level testing orchestrator: plan for analysis only, targeted for selected tests, "
    "scaffold for reviewed pytest stubs, and full only when explicitly requested.\n"
    "6. Render: use astra_visualize for the current knowledge graph, vector chunks, Dipper, "
    "and Tether views. It renders Astra artifacts; never generate equivalent HTML manually.\n"
    "7. For every result, report missing symbols, empty selections, truncation, cycles, "
    "untested nodes, fragility thresholds, watcher errors, and failed tests explicitly. "
    "Do not recreate Astra's index, graph, test selection, or visualization independently."
)

mcp = MCPServer("Astra", version="0.1.0", instructions=MCP_INSTRUCTIONS)
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


def _register_tool_prompts() -> None:
    tool_prompts = {
        "astra_index_repo": "Refresh the local graph and vector index before analysis.",
        "astra_semantic_search": "Find code by concept, identifier, or source meaning.",
        "astra_get_callers": "Find direct callers of a function or method.",
        "astra_hybrid_context": "Combine semantic matches with structural callers.",
        "astra_path": "Find the shortest structural path between symbols.",
        "astra_dipper": "Scoop compact dependency-complete context for an LLM.",
        "astra_tether": "Check cycles, orphan declarations, and high fan-out.",
        "astra_get_fragility_hotspots": "Rank declarations by graph and AST risk.",
        "astra_star_nodes": "Rank highly depended-on declarations by incoming links and PageRank.",
        "astra_impact": "Calculate the upstream blast radius of a declaration.",
        "astra_refactor_plan": "Preview a graph-ordered structural rename.",
        "astra_test_map": "Map source declarations to tests that reach them.",
        "astra_affected_tests": "Select tests affected by changed paths.",
        "astra_gen_test_scaffold": "Generate a read-only pytest scaffold for a target.",
        "astra_run_impacted": "Run the graph-selected impacted tests.",
        "astra_validate_change": (
            "Orchestrate impact, risk, test selection, scaffolding, and validation."
        ),
        "astra_start_watch": "Start continuous background indexing for a workspace.",
        "astra_index_status": "Check continuous indexing status.",
        "astra_stop_watch": "Stop continuous background indexing.",
        "astra_visualize": "Render the current Astra graph and vector artifacts.",
    }

    def make_tool_prompt(tool_name: str) -> object:
        def tool_prompt(path: str, task: str) -> list[dict[str, str]]:
            return [
                {
                    "role": "user",
                    "content": (
                        f"Use the MCP tool {tool_name} for the local workspace at {path}.\n"
                        f"Task: {task}\n\n"
                        f"Purpose: {tool_prompts[tool_name]}\n"
                        "Call the named tool with the appropriate arguments, interpret its "
                        "structured result, and report missing data, warnings, failures, or "
                        "limitations. This prompt "
                        "call; it does not execute the tool itself."
                    ),
                }
            ]

        tool_prompt.__name__ = f"{tool_name}_prompt"
        return tool_prompt

    for tool_name, description in tool_prompts.items():
        tool_prompt = make_tool_prompt(tool_name)
        mcp.prompt(
            name=f"{tool_name}_prompt",
            title=f"{tool_name} Workflow",
            description=f"{description} Use the {tool_name} MCP tool.",
        )(tool_prompt)


_register_tool_prompts()


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
def astra_star_nodes(path: str, limit: int = 20, threshold: float = 60.0) -> dict:
    """Rank important declarations using incoming dependencies and PageRank."""
    return _indexed_engine(path).star_nodes(limit=limit, threshold=threshold)


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
def astra_validate_change(
    path: str,
    changed_paths: list[str] | None = None,
    target: str | None = None,
    mode: str = "targeted",
    timeout: int = 120,
) -> dict:
    """Orchestrate impact, risk, test selection, scaffolding, and validation."""
    return _indexed_engine(path).validate_change(changed_paths, target, mode, timeout)


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
