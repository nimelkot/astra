from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from .core.engine import AstraEngine
from .core.visualization import VisualizationError, write_visualization

app = typer.Typer(help="Hybrid structural and semantic codebase intelligence.")
console = Console()


def _engine(path: Path) -> AstraEngine:
    if not path.exists():
        raise typer.BadParameter(f"Path does not exist: {path}")
    return AstraEngine(path)


@app.command()
def index(path: Path = typer.Argument(Path("."), exists=True, file_okay=False)) -> None:
    """Index project files under PATH."""
    result = _engine(path).index()
    console.print_json(json.dumps(result))


@app.command()
def search(
    query: str,
    path: Path = typer.Option(Path("."), "--path", "-p"),
    limit: int = typer.Option(10, min=1, max=100),
) -> None:
    """Find code chunks matching a conceptual query."""
    table = Table("Score", "Kind", "Path", "Symbol", "Lines")
    for result in _engine(path).search(query, limit):
        table.add_row(
            f"{result.score:.3f}",
            result.chunk.kind,
            result.chunk.path,
            result.chunk.name,
            f"{result.chunk.start_line}-{result.chunk.end_line}",
        )
    console.print(table)


@app.command()
def query(
    type_: str = typer.Argument(..., metavar="TYPE"),
    target: str = typer.Argument(...),
    path: Path = typer.Option(Path("."), "--path", "-p"),
) -> None:
    """Run structural queries, currently: callers FUNCTION."""
    engine = _engine(path)
    if type_.lower() != "callers":
        raise typer.BadParameter("TYPE must be callers")
    console.print_json(json.dumps(engine.callers(target)))


@app.command("path")
def shortest_path(
    source: str = typer.Argument(..., help="Start symbol, node id, or declaration name."),
    target: str = typer.Argument(..., help="End symbol, node id, or declaration name."),
    path: Path = typer.Option(Path("."), "--path", "-p"),
    max_hops: int = typer.Option(12, "--max-hops", min=1, max=100),
) -> None:
    """Find the shortest structural path between two symbols."""
    result = _engine(path).path(source, target, max_hops)
    if result is None:
        console.print("No structural path found.")
        raise typer.Exit(code=1)

    nodes = result["nodes"]
    edges = result["edges"]

    def _symbol_label(node: dict) -> str:
        if node.get("kind") in {"function", "method"}:
            return f"{node['name']}()"
        return str(node["name"])

    def _location_label(node: dict) -> str:
        path_value = node.get("path")
        line_value = node.get("start_line")
        if path_value and isinstance(line_value, int):
            return f"{path_value}:{line_value}"
        if path_value:
            return str(path_value)
        return str(node["id"])

    console.print(_symbol_label(nodes[0]))
    console.print(_location_label(nodes[0]))

    fragments = [_symbol_label(nodes[0])]
    for index, (next_node, edge) in enumerate(zip(nodes[1:], edges)):
        current_node = nodes[index]
        relation = edge["kind"]
        if edge["from"] == current_node["id"] and edge["to"] == next_node["id"]:
            fragments.append(f" --{relation}--> {_symbol_label(next_node)}")
        else:
            fragments.append(f" <--{relation}-- {_symbol_label(next_node)}")

        console.print(f"↳ {_symbol_label(next_node)}")
        console.print(_location_label(next_node))

    console.print("")
    console.print(f"Shortest path ({result['hops']} hops):")
    console.print("  " + "".join(fragments))


@app.command()
def dipper(
    query: str = typer.Argument(..., help="Concept, symbol, or identifier to scoop around."),
    path: Path = typer.Option(Path("."), "--path", "-p"),
    limit: int = typer.Option(5, min=1, max=50),
    parent_depth: int = typer.Option(1, min=0, max=8),
    child_depth: int = typer.Option(1, min=0, max=8),
    max_nodes: int = typer.Option(80, min=5, max=500),
    max_source_chars: int = typer.Option(280, min=40, max=2000),
) -> None:
    """Extract a dependency-complete local subgraph for token-efficient LLM context."""
    result = _engine(path).dipper(
        query,
        limit=limit,
        parent_depth=parent_depth,
        child_depth=child_depth,
        max_nodes=max_nodes,
        max_source_chars=max_source_chars,
    )
    console.print_json(json.dumps(result))


@app.command()
def tether(
    path: Path = typer.Option(Path("."), "--path", "-p"),
    cycle_limit: int = typer.Option(20, min=1, max=200),
    fanout_threshold: int = typer.Option(12, min=1, max=500),
) -> None:
    """Run structural health checks and report graph anomalies."""
    result = _engine(path).tether(cycle_limit=cycle_limit, fanout_threshold=fanout_threshold)
    console.print_json(json.dumps(result))


@app.command()
def fragility(
    path: Path = typer.Option(Path("."), "--path", "-p"),
    limit: int = typer.Option(10, min=1, max=100),
    threshold: float = typer.Option(75.0, min=0, max=100),
) -> None:
    """Rank fragile functions and classes using graph and AST metrics."""
    result = _engine(path).fragility_hotspots(limit=limit, threshold=threshold)
    console.print_json(json.dumps(result))


@app.command()
def visualize(
    path: Path = typer.Argument(Path("."), exists=True, file_okay=False),
    output: Path | None = typer.Option(None, "--output", "-o"),
) -> None:
    """Render generated graph and vector artifacts as a local HTML report."""
    try:
        destination = write_visualization(path, output)
    except VisualizationError as exc:
        raise typer.BadParameter(str(exc)) from exc
    console.print(f"Visualization written to {destination}")


if __name__ == "__main__":
    app()
