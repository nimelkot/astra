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
    """Index Python files under PATH."""
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
