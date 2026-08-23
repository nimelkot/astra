import json
import time
from pathlib import Path

from astra.core.engine import AstraEngine
from astra.core.visualization import write_visualization
from astra.core.watcher import AstraWatcher


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
    path = AstraEngine(tmp_path).path("checkout", "calculate_total")
    assert path is not None
    assert path["hops"] == 1
    assert path["edges"][0]["kind"] == "calls"
    assert path["nodes"][0]["path"] == "app.py"
    assert path["nodes"][0]["start_line"] == 4


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
    assert result["chunks"] == 4
    assert AstraEngine(tmp_path).search("authenticate token")


def test_typescript_callers_are_linked(tmp_path: Path) -> None:
    (tmp_path / "service.ts").write_text(
        "export function calculateTotal(items) {\n"
        "  return items.length;\n"
        "}\n"
        "\n"
        "export function checkout(items) {\n"
        "  return calculateTotal(items);\n"
        "}\n",
        encoding="utf-8",
    )

    result = AstraEngine(tmp_path).index()

    assert result["files"] == 1
    assert result["chunks"] == 3
    callers = AstraEngine(tmp_path).callers("calculateTotal")
    assert any(item["name"] == "checkout" for item in callers)


def test_markdown_json_yaml_and_markup_are_structured(tmp_path: Path) -> None:
    (tmp_path / "guide.md").write_text(
        "# Overview\n"
        "See [Config](config.yaml).\n"
        "\n"
        "## API\n"
        "Details here.\n",
        encoding="utf-8",
    )
    (tmp_path / "config.yaml").write_text("service:\n  timeout: 30\n", encoding="utf-8")
    (tmp_path / "schema.json").write_text('{"service": {"name": "astra"}}', encoding="utf-8")
    (tmp_path / "index.html").write_text(
        '<main id="dashboard"><section name="summary"></section></main>', encoding="utf-8"
    )
    (tmp_path / "diagram.xml").write_text(
        '<root><node id="alpha"/></root>',
        encoding="utf-8",
    )

    result = AstraEngine(tmp_path).index()

    assert result["files"] == 5
    assert result["chunks"] >= 11
    assert AstraEngine(tmp_path).search("overview")
    assert AstraEngine(tmp_path).search("timeout")
    assert AstraEngine(tmp_path).search("dashboard")


def test_bson_file_is_handled_without_crashing(tmp_path: Path) -> None:
    (tmp_path / "sample.bson").write_bytes(b"\x16\x00\x00\x00\x02x\x00\x02\x00\x00\x00y\x00\x00")

    result = AstraEngine(tmp_path).index()

    assert result["files"] == 1
    assert result["chunks"] >= 1


def test_sql_structure_and_dependencies_are_extracted(tmp_path: Path) -> None:
    (tmp_path / "schema.sql").write_text(
        "CREATE TABLE users (id INT);\n"
        "CREATE VIEW active_users AS SELECT * FROM users;\n",
        encoding="utf-8",
    )

    result = AstraEngine(tmp_path).index()

    assert result["files"] == 1
    assert result["chunks"] == 3
    callers = AstraEngine(tmp_path).callers("users")
    assert any(item["name"] == "active_users" for item in callers)
    path = AstraEngine(tmp_path).path("users", "active_users")
    assert path is not None
    assert path["hops"] == 1
    assert path["edges"][0]["kind"] == "depends_on"


def test_shell_function_files_are_structured(tmp_path: Path) -> None:
    (tmp_path / "deploy.sh").write_text(
        "prepare() {\n"
        "  echo ready\n"
        "}\n"
        "\n"
        "run() {\n"
        "  prepare\n"
        "}\n",
        encoding="utf-8",
    )

    result = AstraEngine(tmp_path).index()

    assert result["files"] == 1
    assert result["chunks"] == 3
    assert AstraEngine(tmp_path).search("prepare")


def test_dart_matlab_and_visual_basic_are_structured(tmp_path: Path) -> None:
    (tmp_path / "worker.dart").write_text(
        "class Worker {\n"
        "  int compute(int x) {\n"
        "    return x + 1;\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    (tmp_path / "signal.m").write_text(
        "function y = smoothSignal(x)\n"
        "y = x;\n",
        encoding="utf-8",
    )
    (tmp_path / "module.vb").write_text(
        "Public Function ComputeTotal(x As Integer) As Integer\n"
        "    ComputeTotal = x + 1\n"
        "End Function\n",
        encoding="utf-8",
    )

    result = AstraEngine(tmp_path).index()

    assert result["files"] == 3
    assert result["chunks"] >= 6
    assert AstraEngine(tmp_path).search("smooth signal")
    assert AstraEngine(tmp_path).search("compute total")


def test_python_nodes_with_non_list_body_do_not_crash(tmp_path: Path) -> None:
    (tmp_path / "edge_case.py").write_text(
        "def outer(value):\n"
        "    callback = lambda x: process(x)\n"
        "\n"
        "    def inner():\n"
        "        return value\n"
        "\n"
        "    return callback(inner())\n",
        encoding="utf-8",
    )

    result = AstraEngine(tmp_path).index()

    assert result["files"] == 1
    assert result["chunks"] == 3
    assert AstraEngine(tmp_path).search("outer")


def test_visualization_contains_both_artifacts(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def hello():\n    return 'world'\n", encoding="utf-8")
    AstraEngine(tmp_path).index()

    output = write_visualization(tmp_path)

    html = output.read_text(encoding="utf-8")
    assert "Structural graph" in html
    assert "Vector chunks" in html
    assert 'id="astra-mark"' in html
    assert "data:image/png;base64," in html
    assert "hello" in html
    assert "Hotspots only" in html
    assert "Community view" in html
    assert "Star nodes only" in html
    assert "shape:n.isStar ? 'star'" in html
    assert "IBM Plex Sans" in html
    assert "sourceCommunity" in html
    assert "m6 15 6-6 6 6" in html
    assert "M12 5v14M5 12h14" in html
    assert "M9 4H4v5" in html
    assert "border-radius:50% !important" in html


def test_path_returns_none_when_missing_symbol(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def hello():\n    return 'world'\n", encoding="utf-8")
    engine = AstraEngine(tmp_path)
    engine.index()

    assert engine.path("hello", "does_not_exist") is None


def test_dipper_returns_local_context_scoop(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "def calculate_total(items):\n"
        "    return sum(items)\n"
        "\n"
        "def checkout(items):\n"
        "    return calculate_total(items)\n",
        encoding="utf-8",
    )
    engine = AstraEngine(tmp_path)
    engine.index()

    scoop = engine.dipper("calculate_total", limit=3, parent_depth=1, child_depth=1)

    assert scoop["summary"]["nodes"] >= 2
    assert any(node["name"] == "calculate_total" for node in scoop["nodes"])
    assert any(edge["kind"] in {"calls", "defines"} for edge in scoop["edges"])
    assert any(snippet["name"] == "calculate_total" for snippet in scoop["snippets"])


def test_tether_reports_cycles(tmp_path: Path) -> None:
    (tmp_path / "loop.py").write_text(
        "def a():\n"
        "    return b()\n"
        "\n"
        "def b():\n"
        "    return a()\n",
        encoding="utf-8",
    )
    engine = AstraEngine(tmp_path)
    engine.index()

    report = engine.tether(cycle_limit=10)

    assert report["summary"]["cycles"] >= 1
    assert report["status"] == "warn"
    assert any(item["type"] == "cycle_detected" for item in report["anomalies"])


def test_fragility_hotspots_combine_graph_and_ast_metrics(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "def stable(value):\n"
        "    return value\n"
        "\n"
        "def fragile(a, b, c):\n"
        "    if a:\n"
        "        for value in b:\n"
        "            if value > c:\n"
        "                return stable(value)\n"
        "    return stable(c)\n",
        encoding="utf-8",
    )
    engine = AstraEngine(tmp_path)
    engine.index()

    report = engine.fragility_hotspots(limit=10)

    fragile = next(item for item in report["hotspots"] if item["name"] == "fragile")
    assert fragile["branches"] == 3
    assert fragile["parameters"] == 3
    assert fragile["score"] >= 0
    assert report["formula"]


def test_star_nodes_rank_shared_dependencies_and_assign_communities(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "def shared():\n    return 1\n\n"
        "def first():\n    return shared()\n\n"
        "def second():\n    return shared()\n",
        encoding="utf-8",
    )
    engine = AstraEngine(tmp_path)
    engine.index()

    report = engine.star_nodes(limit=3, threshold=50)
    communities = engine.graph.communities()

    assert report["stars"][0]["name"] == "shared"
    assert report["stars"][0]["is_star"] is True
    assert report["stars"][0]["incoming"] == 2
    assert all(node_id in communities for node_id in engine.graph.graph.nodes)


def test_impact_and_refactor_plan_are_graph_aware(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "def total(value):\n"
        "    return value\n"
        "\n"
        "def checkout(value):\n"
        "    return total(value)\n",
        encoding="utf-8",
    )
    engine = AstraEngine(tmp_path)
    engine.index()

    impact = engine.blast_radius("total")
    plan = engine.refactor_plan("total", "sum_total")

    assert impact["found"] is True
    assert any(node["name"] == "checkout" for node in impact["nodes"])
    assert plan["apply"] is False
    assert any(change["path"] == "app.py" for change in plan["changes"])
    assert any("sum_total" in change["after"] for change in plan["changes"])


def test_test_map_and_affected_tests_use_graph_reachability(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text(
        "def total(value):\n"
        "    return value\n",
        encoding="utf-8",
    )
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text(
        "from app import total\n\n"
        "def test_total():\n"
        "    assert total(2) == 2\n",
        encoding="utf-8",
    )
    engine = AstraEngine(tmp_path)
    engine.index()

    mapping = engine.test_map()
    affected = engine.affected_tests(["app.py"])

    source = next(item for item in mapping["sources"] if item["name"] == "total")
    assert source["tested"] is True
    assert affected["test_files"] == ["tests/test_app.py"]
    assert affected["uncovered_changed_nodes"] == []


def test_run_impacted_executes_selected_tests(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("def total(value):\n    return value\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_app.py").write_text(
        "from app import total\n\n"
        "def test_total():\n"
        "    assert total(2) == 2\n",
        encoding="utf-8",
    )
    engine = AstraEngine(tmp_path)
    engine.index()

    result = engine.run_impacted(["app.py"])

    assert result["status"] == "passed"
    assert result["returncode"] == 0


def test_watcher_reindexes_changed_files(tmp_path: Path) -> None:
    source_file = tmp_path / "app.py"
    source_file.write_text("def greet():\n    return 'hi'\n", encoding="utf-8")
    watcher = AstraWatcher(tmp_path, interval=0.25)

    try:
        status = watcher.start()
        assert status["running"] is True
        initial_count = status["index_count"]
        source_file.write_text("def greet(name):\n    return f'hi {name}'\n", encoding="utf-8")
        deadline = time.monotonic() + 5
        while watcher.status()["index_count"] <= initial_count and time.monotonic() < deadline:
            time.sleep(0.05)
        assert watcher.status()["index_count"] > initial_count
    finally:
        watcher.stop()


def test_index_cache_tracks_file_hash_changes(tmp_path: Path) -> None:
    source_file = tmp_path / "app.py"
    source_file.write_text("def greet():\n    return 'hi'\n", encoding="utf-8")
    engine = AstraEngine(tmp_path)

    first = engine.index()
    assert first["files"] == 1

    cache_path = tmp_path / ".astra_index_cache.json"
    assert cache_path.exists()
    first_cache = json.loads(cache_path.read_text(encoding="utf-8"))
    first_hash = first_cache["files"]["app.py"]["hash"]

    second = engine.index()
    assert second["chunks"] == first["chunks"]
    second_cache = json.loads(cache_path.read_text(encoding="utf-8"))
    assert second_cache["files"]["app.py"]["hash"] == first_hash

    source_file.write_text("def greet(name):\n    return f'hi {name}'\n", encoding="utf-8")
    engine.index()
    third_cache = json.loads(cache_path.read_text(encoding="utf-8"))
    assert third_cache["files"]["app.py"]["hash"] != first_hash
