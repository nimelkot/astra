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
#dipper-graph {{ height:420px; border:1px solid var(--line); border-radius:8px; background:#1b1d2c; margin-top:10px; }}
.graph-toolbar {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:12px; }}
.graph-toolbar input {{ flex:1 1 280px; }}
.graph-toolbar label {{ color:var(--muted); font-size:12px; display:flex; align-items:center; gap:6px; }}
.legend {{ display:flex; flex-wrap:wrap; gap:6px; }}
.legend button {{ display:inline-flex; align-items:center; gap:6px; padding:6px 9px; font-size:12px; }}
.legend .swatch {{ width:9px; height:9px; border-radius:50%; flex:none; }}
.legend button.off {{ opacity:.4; }}
.edge-info {{ min-height:42px; margin-top:10px; padding:10px 12px; border:1px solid var(--line); border-radius:6px; color:var(--muted); background:var(--surface); overflow-wrap:anywhere; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:8px; margin:10px 0; }}
.card {{ border:1px solid var(--line); border-radius:8px; background:var(--surface); padding:10px 12px; }}
.card strong {{ display:block; color:var(--accent); font-size:15px; }}
.card span {{ color:var(--muted); font-size:12px; }}
.list {{ border:1px solid var(--line); border-radius:8px; background:var(--surface); padding:10px 12px; max-height:260px; overflow:auto; }}
.list ul {{ margin:0; padding-left:18px; }}
.list li {{ margin:6px 0; color:#cfd3e5; }}
.anomaly-warn {{ color:#f7d481; }}
.anomaly-info {{ color:#9db7ff; }}
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
<nav><button class="tab active" data-panel="structure">Structural graph</button><button class="tab" data-panel="vectors">Vector chunks</button><button class="tab" data-panel="dipper">Dipper scoop</button><button class="tab" data-panel="tether">Tether health</button></nav>
<main>
<section id="structure" class="panel active"><div class="graph-toolbar"><input id="node-filter" type="search" placeholder="Search nodes by name or path..."><div id="legend" class="legend"></div></div><div id="graph"></div><div id="edge-info" class="edge-info">Select an edge to inspect its relationship.</div></section>
<section id="vectors" class="panel"><div class="toolbar"><input id="filter" type="search" placeholder="Filter files, symbols, or source..."><span id="count"></span></div><div id="chunks"></div></section>
<section id="dipper" class="panel"><div class="graph-toolbar"><input id="dipper-query" type="search" placeholder="Query symbol or concept (for example: checkout, parser, sql)"><label>Seeds <input id="dipper-limit" type="number" value="5" min="1" max="25" style="width:72px"></label><label>Parent depth <input id="dipper-parent" type="number" value="1" min="0" max="6" style="width:72px"></label><label>Child depth <input id="dipper-child" type="number" value="1" min="0" max="6" style="width:72px"></label><label>Max nodes <input id="dipper-max" type="number" value="80" min="5" max="300" style="width:72px"></label><button id="dipper-run">Scoop context</button></div><div id="dipper-summary" class="cards"></div><div id="dipper-graph"></div><div id="dipper-snippets" class="list" style="margin-top:10px;"></div></section>
<section id="tether" class="panel"><div class="graph-toolbar"><label>Fanout threshold <input id="tether-fanout" type="number" value="12" min="1" max="200" style="width:80px"></label><label>Cycle limit <input id="tether-cycles" type="number" value="20" min="1" max="200" style="width:80px"></label><button id="tether-run">Run health checks</button></div><div id="tether-summary" class="cards"></div><div id="tether-anomalies" class="list"></div></section>
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
const nodeById = new Map(allNodes.map(node => [node.id, node]));
const chunkById = new Map(chunks.map(chunk => [chunk.id, chunk]));
let network;
let dipperNetwork;
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

function relationshipEdge(edge) {{ return edge.label === 'calls' || edge.label === 'depends_on'; }}
function symbolForNode(node) {{ return node && (node.group === 'function' || node.group === 'method') ? node.label + '()' : (node?.label || 'unknown'); }}

function walkNeighborhood(seeds, parentDepth, childDepth, maxNodes) {{
    const collected = new Set(seeds);
    function walk(direction, depth) {{
        let frontier = new Set(seeds);
        for (let step = 0; step < depth; step++) {{
            const next = new Set();
            frontier.forEach(nodeId => {{
                allEdges.forEach(edge => {{
                    const neighbor = direction === 'up'
                        ? (edge.to === nodeId ? edge.from : null)
                        : (edge.from === nodeId ? edge.to : null);
                    if (!neighbor || collected.has(neighbor) || collected.size >= maxNodes) return;
                    collected.add(neighbor);
                    next.add(neighbor);
                }});
            }});
            frontier = next;
            if (!frontier.size || collected.size >= maxNodes) break;
        }}
    }}
    walk('up', parentDepth);
    walk('down', childDepth);
    return collected;
}}

function runDipper() {{
    const query = document.getElementById('dipper-query').value.trim().toLowerCase();
    const limit = Number(document.getElementById('dipper-limit').value || 5);
    const parentDepth = Number(document.getElementById('dipper-parent').value || 1);
    const childDepth = Number(document.getElementById('dipper-child').value || 1);
    const maxNodes = Number(document.getElementById('dipper-max').value || 80);
    const summaryEl = document.getElementById('dipper-summary');
    const snippetsEl = document.getElementById('dipper-snippets');
    const dipperGraphEl = document.getElementById('dipper-graph');

    const matched = allNodes.filter(node => `${{node.label}} ${{node.title}}`.toLowerCase().includes(query));
    const seeds = matched.slice(0, Math.max(1, limit)).map(node => node.id);
    if (!seeds.length) {{
        summaryEl.innerHTML = '<div class="card"><strong>0</strong><span>No seeds found for query</span></div>';
        snippetsEl.innerHTML = '<div class="empty">Try a broader query (for example: parser, search, engine).</div>';
        dipperGraphEl.innerHTML = '<div class="empty" style="padding:16px;">No subgraph to render.</div>';
        if (dipperNetwork) {{ dipperNetwork.destroy(); dipperNetwork = null; }}
        return;
    }}

    const nodeIds = walkNeighborhood(seeds, parentDepth, childDepth, maxNodes);
    const visibleNodes = allNodes.filter(node => nodeIds.has(node.id));
    const visibleEdges = allEdges.filter(edge => nodeIds.has(edge.from) && nodeIds.has(edge.to));

    summaryEl.innerHTML = `
        <div class="card"><strong>${{seeds.length}}</strong><span>seed nodes</span></div>
        <div class="card"><strong>${{visibleNodes.length}}</strong><span>scooped nodes</span></div>
        <div class="card"><strong>${{visibleEdges.length}}</strong><span>structural edges</span></div>
        <div class="card"><strong>${{parentDepth}}/${{childDepth}}</strong><span>parent/child depth</span></div>
    `;

    const snippets = visibleNodes
        .map(node => chunkById.get(node.id))
        .filter(Boolean)
        .slice(0, 24)
        .map(chunk => `<li><strong>${{escapeHtml(symbolForNode(nodeById.get(chunk.id)))}}</strong> · ${{escapeHtml(chunk.path)}}:${{chunk.start_line}}<br><span style="color:#9aa0b5;">${{escapeHtml(String(chunk.source).replace(/\\s+/g, ' ').slice(0, 220))}}</span></li>`)
        .join('');
    snippetsEl.innerHTML = snippets ? `<ul>${{snippets}}</ul>` : '<div class="empty">No chunk snippets available for this scoop.</div>';

    if (dipperNetwork) dipperNetwork.destroy();
    if (!window.vis || !visibleNodes.length) {{
        dipperGraphEl.innerHTML = '<div class="empty" style="padding:16px;">No subgraph to render.</div>';
        return;
    }}
    dipperNetwork = new vis.Network(
        dipperGraphEl,
        {{ nodes:new vis.DataSet(visibleNodes), edges:new vis.DataSet(visibleEdges) }},
        {{
            physics:{{ stabilization:{{ iterations:120 }} }},
            interaction:{{ hover:true, navigationButtons:true }},
            nodes:{{ size:14, borderWidth:1.4 }},
            edges:{{ selectionWidth:3 }}
        }}
    );
}}

function detectCycles(limit) {{
    const adjacency = new Map();
    allEdges.filter(relationshipEdge).forEach(edge => {{
        if (!adjacency.has(edge.from)) adjacency.set(edge.from, []);
        adjacency.get(edge.from).push(edge.to);
    }});
    const cycles = [];
    const seen = new Set();
    function dfs(start, node, stack, visited, depth) {{
        if (cycles.length >= limit || depth > 12) return;
        const neighbors = adjacency.get(node) || [];
        neighbors.forEach(next => {{
            if (cycles.length >= limit) return;
            if (next === start && stack.length > 1) {{
                const cycle = [...stack, start];
                const key = cycle.slice().sort().join('|');
                if (!seen.has(key)) {{ seen.add(key); cycles.push(cycle); }}
                return;
            }}
            if (visited.has(next)) return;
            visited.add(next);
            stack.push(next);
            dfs(start, next, stack, visited, depth + 1);
            stack.pop();
            visited.delete(next);
        }});
    }}
    allNodes.forEach(node => {{
        if (cycles.length >= limit) return;
        const visited = new Set([node.id]);
        dfs(node.id, node.id, [node.id], visited, 0);
    }});
    return cycles;
}}

function runTether() {{
    const fanoutThreshold = Number(document.getElementById('tether-fanout').value || 12);
    const cycleLimit = Number(document.getElementById('tether-cycles').value || 20);
    const summaryEl = document.getElementById('tether-summary');
    const anomaliesEl = document.getElementById('tether-anomalies');

    const relationshipEdges = allEdges.filter(relationshipEdge);
    const cycles = detectCycles(cycleLimit);
    const outgoing = new Map();
    const incoming = new Map();
    relationshipEdges.forEach(edge => {{
        outgoing.set(edge.from, (outgoing.get(edge.from) || 0) + 1);
        incoming.set(edge.to, (incoming.get(edge.to) || 0) + 1);
    }});
    const nonModuleNodes = allNodes.filter(node => node.group !== 'module');
    const orphans = nonModuleNodes.filter(node => !incoming.get(node.id) && !outgoing.get(node.id));
    const highFanout = nonModuleNodes.filter(node => (outgoing.get(node.id) || 0) >= fanoutThreshold);
    const status = cycles.length ? 'warn' : 'pass';

    summaryEl.innerHTML = `
        <div class="card"><strong>${{status.toUpperCase()}}</strong><span>graph health status</span></div>
        <div class="card"><strong>${{allNodes.length}}</strong><span>total nodes</span></div>
        <div class="card"><strong>${{relationshipEdges.length}}</strong><span>relationship edges</span></div>
        <div class="card"><strong>${{cycles.length}}</strong><span>cycles</span></div>
        <div class="card"><strong>${{orphans.length}}</strong><span>orphans</span></div>
        <div class="card"><strong>${{highFanout.length}}</strong><span>high fan-out</span></div>
    `;

    const items = [];
    if (cycles.length) {{
        items.push(`<li class="anomaly-warn"><strong>cycle_detected</strong>: Circular call/dependency chains detected (${{cycles.length}}).</li>`);
        cycles.slice(0, 8).forEach(cycle => {{
            const labels = cycle.map(id => escapeHtml(symbolForNode(nodeById.get(id) || {{label:id}}))).join(' -> ');
            items.push(`<li class="anomaly-warn">Cycle: ${{labels}}</li>`);
        }});
    }} else {{
        items.push('<li class="anomaly-info"><strong>cycle_detected</strong>: none detected.</li>');
    }}
    if (orphans.length) items.push(`<li class="anomaly-info"><strong>orphan_nodes</strong>: ${{orphans.length}} declarations without relationship edges.</li>`);
    if (highFanout.length) items.push(`<li class="anomaly-info"><strong>high_fanout</strong>: ${{highFanout.length}} declarations exceed threshold ${{fanoutThreshold}}.</li>`);

    anomaliesEl.innerHTML = `<ul>${{items.join('')}}</ul>`;
}}

document.getElementById('dipper-run').addEventListener('click', runDipper);
document.getElementById('tether-run').addEventListener('click', runTether);
runDipper();
runTether();
renderChunks();
</script>
</body>
</html>'''


def write_visualization(root: str | Path, output: str | Path | None = None) -> Path:
    target = Path(root).resolve()
    destination = Path(output).resolve() if output else target / ".astra_visualization.html"
    destination.write_text(build_visualization(target), encoding="utf-8")
    return destination
