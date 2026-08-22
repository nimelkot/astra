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
