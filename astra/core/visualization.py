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
            {
                "id": index,
                "from": link["source"],
                "to": link["target"],
                "label": link.get("kind", ""),
            }
            for index, link in enumerate(graph.get("edges", graph.get("links", [])))
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
.brand {{ display:flex; align-items:center; gap:12px; margin-bottom:8px; color:var(--text); font-size:30px; font-weight:500; letter-spacing:-1px; }}
.brand svg {{ width:38px; height:38px; flex:none; }}
.path {{ color:var(--muted); font-family:ui-monospace, SFMono-Regular, Consolas, monospace; font-size:12px; overflow-wrap:anywhere; }}
nav {{ display:flex; gap:8px; padding:16px 32px 0; }}
button {{ border:1px solid var(--line); border-radius:6px; padding:8px 12px; color:var(--text); background:transparent; cursor:pointer; }}
button.active, button:hover {{ border-color:var(--accent); color:var(--accent); }}
main {{ padding:16px 32px 32px; }}
.panel {{ display:none; }}
.panel.active {{ display:block; }}
#graph {{ height:680px; border:1px solid var(--line); border-radius:8px; background:#1b1d2c; }}
.graph-toolbar {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:12px; }}
.graph-toolbar input {{ flex:1 1 280px; }}
.legend {{ display:flex; flex-wrap:wrap; gap:6px; }}
.legend button {{ display:inline-flex; align-items:center; gap:6px; padding:6px 9px; font-size:12px; }}
.legend .swatch {{ width:9px; height:9px; border-radius:50%; flex:none; }}
.legend button.off {{ opacity:.4; }}
.edge-info {{ min-height:42px; margin-top:10px; padding:10px 12px; border:1px solid var(--line); border-radius:6px; color:var(--muted); background:var(--surface); overflow-wrap:anywhere; }}
.vis-network .vis-button {{ position:relative; width:28px; height:28px; border:1px solid var(--line); border-radius:6px; background-color:var(--surface); background-image:none !important; box-shadow:none !important; filter:none !important; color:var(--accent); opacity:.92; }}
.vis-network .vis-button::after {{ position:absolute; inset:0; display:grid; place-items:center; font-size:18px; line-height:1; }}
.vis-network .vis-button.vis-up::after {{ content:'^'; }}
.vis-network .vis-button.vis-down::after {{ content:'v'; }}
.vis-network .vis-button.vis-left::after {{ content:'<'; }}
.vis-network .vis-button.vis-right::after {{ content:'>'; }}
.vis-network .vis-button.vis-zoomIn::after {{ content:'+'; }}
.vis-network .vis-button.vis-zoomOut::after {{ content:'-'; }}
.vis-network .vis-button.vis-zoomExtends::after {{ content:'[]'; font-size:12px; }}
.vis-network .vis-button:hover {{ border-color:var(--accent); background-color:#2b2741; }}
.vis-network .vis-button:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; }}
.toolbar {{ display:flex; gap:12px; align-items:center; margin-bottom:12px; }}
input {{ width:min(520px, 100%); padding:9px 11px; border:1px solid var(--line); border-radius:6px; color:var(--text); background:var(--surface); }}
#chunks {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:10px; }}
.chunk {{ min-height:150px; padding:14px; border:1px solid var(--line); border-radius:8px; background:var(--surface); cursor:pointer; }}
.chunk:hover {{ border-color:var(--accent); }}
.chunk h3 {{ margin:0 0 5px; font-size:14px; font-weight:500; color:var(--accent); overflow-wrap:anywhere; }}
.chunk .meta {{ color:var(--muted); font-size:12px; overflow-wrap:anywhere; word-break:break-word; }}
pre {{ display:none; margin:10px 0 0; max-height:240px; overflow:auto; white-space:pre-wrap; color:#cfd3e5; font:12px/1.45 ui-monospace, SFMono-Regular, Consolas, monospace; }}
.chunk.open pre {{ display:block; }}
.empty {{ padding:24px 0; color:var(--muted); }}
</style>
</head>
<body>
<header><div class="brand" aria-label="Astra"><svg id="astra-mark" viewBox="0 0 64 64" role="img" aria-label="Astra constellation mark"><g fill="none" stroke="#9184d9" stroke-linecap="round" stroke-width="1.4" opacity=".72"><path d="M18 13 32 30 46 19 32 30 11 38 32 30 52 46 32 30 26 53 32 30"/></g><circle cx="32" cy="30" r="5" fill="#9184d9"/><g fill="#e9e9ed"><circle cx="18" cy="13" r="2.6"/><circle cx="46" cy="19" r="2.6"/><circle cx="11" cy="38" r="2.2"/><circle cx="52" cy="46" r="2.2"/><circle cx="26" cy="53" r="3.2"/></g></svg><span>astra</span></div><div class="path">{escape(str(target))}</div></header>
<nav><button class="tab active" data-panel="structure">Structural graph</button><button class="tab" data-panel="vectors">Vector chunks</button></nav>
<main>
<section id="structure" class="panel active"><div class="graph-toolbar"><input id="node-filter" type="search" placeholder="Search nodes by name or path..."><div id="legend" class="legend"></div></div><div id="graph"></div><div id="edge-info" class="edge-info">Select an edge to inspect its relationship.</div></section>
<section id="vectors" class="panel"><div class="toolbar"><input id="filter" type="search" placeholder="Filter files, symbols, or source..."><span id="count"></span></div><div id="chunks"></div></section>
</main>
<script>
const graphData = {graph_json};
const chunks = {chunks_json};
const palette = {{ module:'#9698ab', class:'#b5abfc', function:'#9184d9', method:'#d2cefd', file:'#75798c' }};
const graphEl = document.getElementById('graph');
const nodeFilterEl = document.getElementById('node-filter');
const legendEl = document.getElementById('legend');
const edgeInfoEl = document.getElementById('edge-info');
const activeGroups = new Set(Object.keys(palette));
const allNodes = graphData.nodes.map(n => ({{...n, color:palette[n.group] || palette.file, font:{{color:'#e9e9ed'}}, shape:'dot' }}));
const allEdges = graphData.edges.map(e => ({{...e, arrows:'to', width:2, color:{{color:'#9184d9', opacity:.72, highlight:'#d2cefd'}}, font:{{color:'#cfd3e5', size:10, align:'middle'}}, smooth:{{type:'dynamic'}} }}));
let network;
function renderGraph() {{
    const query = nodeFilterEl.value.toLowerCase();
    const visibleNodes = allNodes.filter(n => activeGroups.has(n.group) && `${{n.label}} ${{n.title}}`.toLowerCase().includes(query));
    const visibleIds = new Set(visibleNodes.map(n => n.id));
    const visibleEdges = allEdges.filter(e => visibleIds.has(e.from) && visibleIds.has(e.to));
    if (network) network.setData({{ nodes:new vis.DataSet(visibleNodes), edges:new vis.DataSet(visibleEdges) }});
    else if (window.vis && graphData.nodes.length) network = new vis.Network(graphEl, {{ nodes:new vis.DataSet(visibleNodes), edges:new vis.DataSet(visibleEdges) }}, {{ physics:{{ stabilization:{{ iterations:180 }} }}, interaction:{{ hover:true, navigationButtons:true, keyboard:true }}, nodes:{{ size:15, borderWidth:1.5 }}, edges:{{ selectionWidth:3 }} }});
}}
if (window.vis && graphData.nodes.length) {{
    renderGraph();
}} else {{ graphEl.innerHTML = '<div class="empty">No structural graph nodes found, or the visualization library could not load.</div>'; }}
Object.keys(palette).forEach(group => {{ const button = document.createElement('button'); button.innerHTML = '<span class="swatch" style="background:' + palette[group] + '"></span>' + group; button.style.borderColor = palette[group]; button.addEventListener('click', () => {{ if (activeGroups.has(group)) {{ activeGroups.delete(group); button.classList.add('off'); }} else {{ activeGroups.add(group); button.classList.remove('off'); }} renderGraph(); }}); legendEl.appendChild(button); }});
nodeFilterEl.addEventListener('input', renderGraph);
if (network) network.on('selectEdge', params => {{ const edge = params.edges.length ? network.body.data.edges.get(params.edges[0]) : null; if (!edge) {{ edgeInfoEl.textContent = 'Select an edge to inspect its relationship.'; return; }} const source = network.body.data.nodes.get(edge.from); const target = network.body.data.nodes.get(edge.to); edgeInfoEl.innerHTML = `<strong>${{escapeHtml(edge.label || 'relationship')}}</strong> · ${{escapeHtml(source?.label || edge.from)}} → ${{escapeHtml(target?.label || edge.to)}}`; }});
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
