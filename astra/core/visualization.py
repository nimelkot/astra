from __future__ import annotations

import json
from html import escape
from pathlib import Path

# ruff: noqa: E501


VIS_NETWORK_URL = "https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"


class VisualizationError(FileNotFoundError):
    """Raised when generated Astra artifacts are not available."""


def _load_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VisualizationError(f"Astra artifact not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise VisualizationError(f"Invalid Astra artifact: {path}") from exc


def build_visualization(root: str | Path) -> str:
    """Build an interactive HTML report from a target's generated Astra artifacts."""
    target = Path(root).resolve()
    graph = _load_json(target / ".astra_graph.json")
    chunks = _load_json(target / ".astra_vectors" / "chunks.json")
    graph_data = {
        "nodes": [
            {
                "id": node.get("id"),
                "label": node.get("name", node.get("id", "")),
                "group": node.get("kind", "module"),
                "title": escape(
                    f"{node.get('path', '')}:{node.get('start_line', '')}-{node.get('end_line', '')}"
                ),
            }
            for node in graph.get("nodes", [])
        ],
        "edges": [
            {"from": link["source"], "to": link["target"], "label": link.get("kind", "")}
            for link in graph.get("links", [])
        ],
    }
    chunk_data = [
        {
            "id": chunk.get("id"),
            "label": chunk.get("name", ""),
            "path": chunk.get("path", ""),
            "kind": chunk.get("kind", "file"),
            "lines": f"{chunk.get('start_line', '')}-{chunk.get('end_line', '')}",
            "source": chunk.get("source", ""),
        }
        for chunk in chunks
    ]
    graph_json = json.dumps(graph_data, ensure_ascii=True).replace("</", "<\\/")
    chunks_json = json.dumps(chunk_data, ensure_ascii=True).replace("</", "<\\/")
    title = escape(f"Astra visualization - {target.name}")
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<script src="{VIS_NETWORK_URL}"></script>
<style>
:root {{ color-scheme: dark; --bg:#161826; --surface:#232532; --text:#e9e9ed; --muted:#9698ab; --accent:#9184d9; --line:#3f424d; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--text); font:14px/1.5 Inter, ui-sans-serif, system-ui, sans-serif; }}
header {{ padding:28px 32px 20px; border-bottom:1px solid var(--line); }}
h1 {{ margin:0 0 4px; font-size:24px; font-weight:500; }}
.path {{ color:var(--muted); font-family:ui-monospace, SFMono-Regular, Consolas, monospace; font-size:12px; overflow-wrap:anywhere; }}
nav {{ display:flex; gap:8px; padding:16px 32px 0; }}
button {{ border:1px solid var(--line); border-radius:6px; padding:8px 12px; color:var(--text); background:transparent; cursor:pointer; }}
button.active, button:hover {{ border-color:var(--accent); color:var(--accent); }}
main {{ padding:16px 32px 32px; }}
.panel {{ display:none; }}
.panel.active {{ display:block; }}
#graph {{ height:680px; border:1px solid var(--line); border-radius:8px; background:#1b1d2c; }}
.toolbar {{ display:flex; gap:12px; align-items:center; margin-bottom:12px; }}
input {{ width:min(520px, 100%); padding:9px 11px; border:1px solid var(--line); border-radius:6px; color:var(--text); background:var(--surface); }}
#chunks {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:10px; }}
.chunk {{ min-height:150px; padding:14px; border:1px solid var(--line); border-radius:8px; background:var(--surface); cursor:pointer; }}
.chunk:hover {{ border-color:var(--accent); }}
.chunk h3 {{ margin:0 0 5px; font-size:14px; font-weight:500; color:var(--accent); overflow-wrap:anywhere; }}
.chunk .meta {{ color:var(--muted); font-size:12px; }}
pre {{ display:none; margin:10px 0 0; max-height:240px; overflow:auto; white-space:pre-wrap; color:#cfd3e5; font:12px/1.45 ui-monospace, SFMono-Regular, Consolas, monospace; }}
.chunk.open pre {{ display:block; }}
.empty {{ padding:24px 0; color:var(--muted); }}
</style>
</head>
<body>
<header><h1>Astra visualization</h1><div class="path">{escape(str(target))}</div></header>
<nav><button class="tab active" data-panel="structure">Structural graph</button><button class="tab" data-panel="vectors">Vector chunks</button></nav>
<main>
<section id="structure" class="panel active"><div id="graph"></div></section>
<section id="vectors" class="panel"><div class="toolbar"><input id="filter" type="search" placeholder="Filter files, symbols, or source..."><span id="count"></span></div><div id="chunks"></div></section>
</main>
<script>
const graphData = {graph_json};
const chunks = {chunks_json};
const palette = {{ module:'#9698ab', class:'#b5abfc', function:'#9184d9', method:'#d2cefd', file:'#75798c' }};
const graphEl = document.getElementById('graph');
if (window.vis && graphData.nodes.length) {{
  new vis.Network(graphEl, {{ nodes:new vis.DataSet(graphData.nodes.map(n => ({{...n, color:palette[n.group] || palette.file, font:{{color:'#e9e9ed'}}, shape:'dot' }}))), edges:new vis.DataSet(graphData.edges.map(e => ({{...e, arrows:'to', color:'#5d5294', font:{{color:'#9698ab', size:10, align:'middle'}}}}))) }}, {{ physics:{{ stabilization:{{ iterations:180 }} }}, interaction:{{ hover:true }}, nodes:{{ size:13 }}, edges:{{ smooth:true }} }});
}} else {{ graphEl.innerHTML = '<div class="empty">No structural graph nodes found, or the visualization library could not load.</div>'; }}
const chunksEl = document.getElementById('chunks');
const countEl = document.getElementById('count');
function renderChunks() {{
  const query = document.getElementById('filter').value.toLowerCase();
  const matches = chunks.filter(c => `${{c.path}} ${{c.label}} ${{c.source}}`.toLowerCase().includes(query));
  countEl.textContent = `${{matches.length}} of ${{chunks.length}} chunks`;
  chunksEl.innerHTML = matches.map((c, i) => `<article class="chunk" data-index="${{chunks.indexOf(c)}}"><h3>${{escapeHtml(c.label)}}</h3><div class="meta">${{escapeHtml(c.kind)}} · ${{escapeHtml(c.path)}} · lines ${{escapeHtml(c.lines)}}</div><pre>${{escapeHtml(c.source)}}</pre></article>`).join('') || '<div class="empty">No matching chunks.</div>';
}}
function escapeHtml(value) {{ return String(value).replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c])); }}
document.getElementById('filter').addEventListener('input', renderChunks);
chunksEl.addEventListener('click', event => event.target.closest('.chunk')?.classList.toggle('open'));
document.querySelectorAll('.tab').forEach(tab => tab.addEventListener('click', () => {{ document.querySelectorAll('.tab').forEach(t => t.classList.remove('active')); document.querySelectorAll('.panel').forEach(p => p.classList.remove('active')); tab.classList.add('active'); document.getElementById(tab.dataset.panel).classList.add('active'); }}));
renderChunks();
</script>
</body>
</html>'''


def write_visualization(root: str | Path, output: str | Path | None = None) -> Path:
    target = Path(root).resolve()
    destination = Path(output).resolve() if output else target / ".astra_visualization.html"
    destination.write_text(build_visualization(target), encoding="utf-8")
    return destination
