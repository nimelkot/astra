from pathlib import Path

from astra.core.engine import AstraEngine
from astra.core.visualization import write_visualization


def test_index_search_and_callers(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "def calculate_total(items):\n"
        "    return sum(items)\n"
        "\n"
        "def checkout(items):\n"
        "    return calculate_total(items)\n",
        encoding="utf-8",
    )
    result = AstraEngine(tmp_path).index()
    assert result["files"] == 1
    assert result["chunks"] == 3
    assert AstraEngine(tmp_path).search("calculate total")
    callers = AstraEngine(tmp_path).callers("calculate_total")
    assert any(item["name"] == "checkout" for item in callers)


def test_invalid_python_is_skipped(tmp_path: Path) -> None:
    (tmp_path / "broken.py").write_text("def broken(:\n", encoding="utf-8")
    assert AstraEngine(tmp_path).index()["chunks"] == 0


def test_nested_text_files_are_indexed(tmp_path: Path) -> None:
    nested = tmp_path / "frontend" / "src"
    nested.mkdir(parents=True)
    (nested / "app.ts").write_text("export function authenticateToken() {}", encoding="utf-8")
    (tmp_path / "settings.json").write_text('{"retry_limit": 3}', encoding="utf-8")

    result = AstraEngine(tmp_path).index()

    assert result["files"] == 2
    assert result["chunks"] == 2
    assert AstraEngine(tmp_path).search("authenticate token")


def test_visualization_contains_both_artifacts(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def hello():\n    return 'world'\n", encoding="utf-8")
    AstraEngine(tmp_path).index()

    output = write_visualization(tmp_path)

    html = output.read_text(encoding="utf-8")
    assert "Structural graph" in html
    assert "Vector chunks" in html
    assert "astra-mark" in html
    assert "hello" in html
