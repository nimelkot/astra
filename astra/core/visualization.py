from __future__ import annotations

import base64
import json
from html import escape
from pathlib import Path

from .graph import StructuralGraph

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


def _logo_data_uri() -> str:
    candidates = (
        Path(__file__).resolve().parents[2] / "assets" / "astra-icon-light.png",
        Path(__file__).resolve().parents[1] / "assets" / "astra-icon-light.png",
    )
    for path in candidates:
        if path.exists():
            encoded = base64.b64encode(path.read_bytes()).decode("ascii")
            return f"data:image/png;base64,{encoded}"
    return ""


def build_visualization(root: str | Path) -> str:
    """Build an interactive HTML report from a target's generated Astra artifacts."""
    target = Path(root).resolve()
    graph = _load_json(target / ".astra_graph.json")
    chunks = _load_json(target / ".astra_vectors" / "chunks.json")
    structural_graph = StructuralGraph.load(target / ".astra_graph.json")
    star_report = structural_graph.star_nodes(
        limit=max(structural_graph.graph.number_of_nodes(), 1),
        threshold=60,
    )
    fragility_report = structural_graph.fragility_hotspots(
        limit=max(structural_graph.graph.number_of_nodes(), 1),
        threshold=50,
    )
    communities = structural_graph.communities()
    stars_by_id = {item["id"]: item for item in star_report["stars"]}
    hotspots_by_id = {item["id"]: item for item in fragility_report["hotspots"]}
    graph_data = {
        "nodes": [
            {
                "id": node.get("id"),
                "label": node.get("name", node.get("id", "")),
                "group": node.get("kind", "module"),
                "path": node.get("path", ""),
                "startLine": node.get("start_line"),
                "community": communities.get(node.get("id"), -1),
                "starScore": stars_by_id.get(node.get("id"), {}).get("score", 0),
                "isStar": stars_by_id.get(node.get("id"), {}).get("is_star", False),
                "hotspotScore": hotspots_by_id.get(node.get("id"), {}).get("score", 0),
                "isHotspot": hotspots_by_id.get(node.get("id"), {}).get(
                    "classification"
                )
                == "critical",
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
    logo_uri = _logo_data_uri()
    title = escape(f"Astra visualization - {target.name}")
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<script src="{VIS_NETWORK_URL}"></script>
<style>
:root {{ color-scheme:dark; --bg:#12141d; --surface:#1b1e29; --surface-2:#222633; --text:#f4f5f8; --muted:#9ba3b4; --accent:#7dd3fc; --violet:#a78bfa; --amber:#fbbf24; --rose:#fb7185; --line:#343a49; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; min-height:100vh; background:radial-gradient(circle at 12% 8%, #202536 0, var(--bg) 38%); color:var(--text); font:14px/1.5 "IBM Plex Sans", "Aptos", sans-serif; }}
header {{ display:flex; justify-content:space-between; gap:24px; align-items:flex-end; padding:24px 30px 18px; border-bottom:1px solid var(--line); background:rgba(18,20,29,.88); backdrop-filter:blur(18px); }}
.brand {{ display:flex; align-items:center; gap:12px; color:var(--text); font-size:27px; font-weight:650; }}
.brand img {{ width:42px; height:42px; object-fit:contain; flex:none; }}
.path {{ color:var(--muted); font:12px/1.4 ui-monospace, SFMono-Regular, Consolas, monospace; overflow-wrap:anywhere; text-align:right; max-width:52vw; }}
nav {{ display:flex; gap:4px; padding:12px 30px 0; border-bottom:1px solid var(--line); }}
button {{ border:1px solid var(--line); border-radius:6px; padding:8px 12px; color:var(--text); background:var(--surface); cursor:pointer; }}
button.active, button:hover {{ border-color:var(--accent); color:var(--accent); background:#202938; }}
nav button {{ border:0; border-bottom:2px solid transparent; border-radius:4px 4px 0 0; background:transparent; color:var(--muted); }}
nav button.active {{ border-bottom-color:var(--accent); color:var(--text); background:var(--surface); }}
main {{ padding:18px 30px 30px; }}
.panel {{ display:none; }}
.panel.active {{ display:block; }}
#graph {{ height:700px; min-width:0; background:#151822; }}
#dipper-graph {{ height:420px; border:1px solid var(--line); border-radius:8px; background:#1b1d2c; margin-top:10px; }}
.graph-heading {{ display:flex; justify-content:space-between; align-items:flex-end; gap:20px; margin-bottom:14px; }}
.graph-heading h2 {{ margin:0; font-size:20px; font-weight:650; }}
.graph-heading p {{ margin:3px 0 0; color:var(--muted); }}
.graph-shell {{ display:grid; grid-template-columns:minmax(0, 1fr) 290px; min-height:700px; overflow:hidden; border:1px solid var(--line); border-radius:8px; background:var(--surface); box-shadow:0 18px 50px rgba(0,0,0,.24); }}
.control-rail {{ height:700px; overflow:auto; padding:18px; border-left:1px solid var(--line); background:#191c26; }}
.rail-section {{ padding:0 0 16px; margin:0 0 16px; border-bottom:1px solid var(--line); }}
.rail-section:last-child {{ border:0; }}
.rail-title {{ margin:0 0 10px; color:var(--muted); font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.09em; }}
.rail-stat {{ display:flex; justify-content:space-between; margin:6px 0; color:var(--muted); font-size:12px; }}
.rail-stat strong {{ color:var(--text); }}
.switch-row {{ display:flex; justify-content:space-between; gap:12px; align-items:center; margin:9px 0; color:#d7dae2; font-size:12px; }}
.switch-row input {{ width:34px; height:18px; accent-color:var(--accent); }}
.graph-toolbar {{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; margin-bottom:12px; }}
.graph-toolbar input {{ flex:1 1 280px; }}
.graph-toolbar label {{ color:var(--muted); font-size:12px; display:flex; align-items:center; gap:6px; }}
.legend {{ display:grid; gap:6px; }}
.legend button {{ display:flex; width:100%; align-items:center; justify-content:flex-start; gap:8px; padding:7px 9px; font-size:12px; }}
.legend .swatch {{ width:9px; height:9px; border-radius:50%; flex:none; }}
.legend button.off {{ opacity:.4; }}
.community-list {{ display:grid; grid-template-columns:1fr 1fr; gap:6px; }}
.community-list button {{ padding:6px 8px; font-size:11px; }}
.community-list button.off {{ opacity:.35; }}
.edge-info {{ min-height:70px; padding:10px 12px; border:1px solid var(--line); border-radius:6px; color:var(--muted); background:var(--surface-2); overflow-wrap:anywhere; }}
.cards {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:8px; margin:10px 0; }}
.card {{ border:1px solid var(--line); border-radius:8px; background:var(--surface); padding:10px 12px; }}
.card strong {{ display:block; color:var(--accent); font-size:15px; }}
.card span {{ color:var(--muted); font-size:12px; }}
.list {{ border:1px solid var(--line); border-radius:8px; background:var(--surface); padding:10px 12px; max-height:260px; overflow:auto; }}
.list ul {{ margin:0; padding-left:18px; }}
.list li {{ margin:6px 0; color:#cfd3e5; }}
.anomaly-warn {{ color:#f7d481; }}
.anomaly-info {{ color:#9db7ff; }}
.vis-network .vis-button {{ position:relative; width:30px; height:30px; overflow:hidden; border:1px solid var(--line); border-radius:50% !important; background-color:var(--surface); background-image:none !important; box-shadow:none !important; filter:none !important; color:var(--accent); opacity:.92; }}
.vis-network .vis-button::after {{ content:''; position:absolute; inset:0; border-radius:inherit; background-position:center; background-repeat:no-repeat; background-size:15px 15px; pointer-events:none; }}
.vis-network .vis-button.vis-up::after {{ background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237dd3fc' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 15 6-6 6 6'/%3E%3C/svg%3E"); }}
.vis-network .vis-button.vis-down::after {{ background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237dd3fc' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E"); }}
.vis-network .vis-button.vis-left::after {{ background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237dd3fc' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m15 18-6-6 6-6'/%3E%3C/svg%3E"); }}
.vis-network .vis-button.vis-right::after {{ background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237dd3fc' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='m9 18 6-6-6-6'/%3E%3C/svg%3E"); }}
.vis-network .vis-button.vis-zoomIn::after {{ background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237dd3fc' stroke-width='2.2' stroke-linecap='round'%3E%3Cpath d='M12 5v14M5 12h14'/%3E%3C/svg%3E"); }}
.vis-network .vis-button.vis-zoomOut::after {{ background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237dd3fc' stroke-width='2.2' stroke-linecap='round'%3E%3Cpath d='M5 12h14'/%3E%3C/svg%3E"); }}
.vis-network .vis-button.vis-zoomExtends::after {{ background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%237dd3fc' stroke-width='2.1' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M9 4H4v5M15 4h5v5M20 15v5h-5M4 15v5h5'/%3E%3C/svg%3E"); }}
.vis-network .vis-button:hover {{ border-color:var(--accent); border-radius:50% !important; background-color:#243140; }}
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
@media (max-width:900px) {{ .graph-shell {{ grid-template-columns:1fr; }} .control-rail {{ height:auto; border-left:0; border-top:1px solid var(--line); }} #graph {{ height:560px; }} header {{ align-items:flex-start; flex-direction:column; }} .path {{ text-align:left; max-width:100%; }} }}
</style>
</head>
<body>
<header><div class="brand" aria-label="Astra"><img id="astra-mark" src="{logo_uri}" alt="Astra"><span>astra intelligence</span></div><div class="path">{escape(str(target))}</div></header>
<nav><button class="tab active" data-panel="structure">Structural graph</button><button class="tab" data-panel="vectors">Vector chunks</button><button class="tab" data-panel="dipper">Dipper scoop</button><button class="tab" data-panel="tether">Tether health</button></nav>
<main>
<section id="structure" class="panel active"><div class="graph-heading"><div><h2>Repository knowledge graph</h2><p>Explore dependencies, communities, hotspots, and high-importance star nodes.</p></div><input id="node-filter" type="search" placeholder="Search symbols or paths..."></div><div class="graph-shell"><div id="graph"></div><aside class="control-rail"><div class="rail-section"><div class="rail-title">Graph intelligence</div><label class="switch-row"><span>Hotspots only</span><input id="hotspot-only" type="checkbox"></label><label class="switch-row"><span>Community view</span><input id="community-mode" type="checkbox"></label><label class="switch-row"><span>Star nodes only</span><input id="star-only" type="checkbox"></label><label class="switch-row"><span>Edge labels</span><input id="edge-labels" type="checkbox" checked></label><div id="graph-stats"></div></div><div class="rail-section"><div class="rail-title">Node types</div><div id="legend" class="legend"></div></div><div class="rail-section"><div class="rail-title">Communities / subgraphs</div><div id="community-list" class="community-list"></div></div><div class="rail-section"><div class="rail-title">Relationships</div><div class="rail-stat"><span>defines</span><strong style="color:#94a3b8">solid</strong></div><div class="rail-stat"><span>calls</span><strong style="color:#7dd3fc">cyan</strong></div><div class="rail-stat"><span>depends_on</span><strong style="color:#fbbf24">amber</strong></div></div><div class="rail-section"><div class="rail-title">Selection</div><div id="edge-info" class="edge-info">Select a node or edge to inspect it.</div></div></aside></div></section>
<section id="vectors" class="panel"><div class="toolbar"><input id="filter" type="search" placeholder="Filter files, symbols, or source..."><span id="count"></span></div><div id="chunks"></div></section>
<section id="dipper" class="panel"><div class="graph-toolbar"><input id="dipper-query" type="search" placeholder="Query symbol or concept (for example: checkout, parser, sql)"><label>Seeds <input id="dipper-limit" type="number" value="5" min="1" max="25" style="width:72px"></label><label>Parent depth <input id="dipper-parent" type="number" value="1" min="0" max="6" style="width:72px"></label><label>Child depth <input id="dipper-child" type="number" value="1" min="0" max="6" style="width:72px"></label><label>Max nodes <input id="dipper-max" type="number" value="80" min="5" max="300" style="width:72px"></label><button id="dipper-run">Scoop context</button></div><div id="dipper-summary" class="cards"></div><div id="dipper-graph"></div><div id="dipper-snippets" class="list" style="margin-top:10px;"></div></section>
<section id="tether" class="panel"><div class="graph-toolbar"><label>Fanout threshold <input id="tether-fanout" type="number" value="12" min="1" max="200" style="width:80px"></label><label>Cycle limit <input id="tether-cycles" type="number" value="20" min="1" max="200" style="width:80px"></label><button id="tether-run">Run health checks</button></div><div id="tether-summary" class="cards"></div><div id="tether-anomalies" class="list"></div></section>
</main>
<script>
const graphData = {graph_json};
const chunks = {chunks_json};
const palette = {{ module:'#94a3b8', class:'#a78bfa', function:'#7dd3fc', method:'#34d399', file:'#64748b', section:'#fbbf24', key:'#fb7185', element:'#38bdf8' }};
const communityPalette = ['#7dd3fc','#a78bfa','#34d399','#fbbf24','#fb7185','#60a5fa','#f97316','#c084fc','#2dd4bf','#e879f9'];
const graphEl = document.getElementById('graph');
const nodeFilterEl = document.getElementById('node-filter');
const legendEl = document.getElementById('legend');
const communityListEl = document.getElementById('community-list');
const hotspotOnlyEl = document.getElementById('hotspot-only');
const communityModeEl = document.getElementById('community-mode');
const starOnlyEl = document.getElementById('star-only');
const edgeLabelsEl = document.getElementById('edge-labels');
const graphStatsEl = document.getElementById('graph-stats');
const edgeInfoEl = document.getElementById('edge-info');
const activeGroups = new Set(Object.keys(palette));
const allCommunities = [...new Set(graphData.nodes.map(n => n.community))].sort((a,b) => a-b);
const activeCommunities = new Set(allCommunities);
const edgePalette = {{ defines:'#64748b', calls:'#7dd3fc', depends_on:'#fbbf24' }};
const allNodes = graphData.nodes.map(n => ({{
    ...n,
    color:palette[n.group] || palette.file,
    font:{{color:'#f4f5f8', face:'IBM Plex Sans', size:13, strokeWidth:3, strokeColor:'#151822'}},
    shape:n.isStar ? 'star' : 'dot',
    size:n.isStar ? 25 : 14,
    borderWidth:n.isHotspot ? 4 : 1.5,
    borderWidthSelected:4,
    shadow:n.isStar ? {{enabled:true, color:'rgba(251,191,36,.45)', size:18}} : false
}}));
const allEdges = graphData.edges.map(e => ({{...e, arrows:'to', width:e.label === 'defines' ? 1 : 2, color:{{color:edgePalette[e.label] || '#64748b', opacity:.7, highlight:'#f4f5f8'}}, font:{{color:'#cbd5e1', face:'IBM Plex Sans', size:10, align:'middle', strokeWidth:4, strokeColor:'#151822'}}, smooth:{{type:'dynamic'}} }}));
const nodeById = new Map(allNodes.map(node => [node.id, node]));
const chunkById = new Map(chunks.map(chunk => [chunk.id, chunk]));
let network;
let dipperNetwork;
let physicsFreezeTimer;
function renderGraph() {{
    const query = nodeFilterEl.value.toLowerCase();
    const communityMode = communityModeEl.checked;
    const visibleNodes = allNodes.filter(n =>
        activeGroups.has(n.group)
        && activeCommunities.has(n.community)
        && (!hotspotOnlyEl.checked || n.isHotspot)
        && (!starOnlyEl.checked || n.isStar)
        && `${{n.label}} ${{n.title}}`.toLowerCase().includes(query)
    ).map(n => ({{
        ...n,
        color:communityMode ? communityPalette[Math.abs(n.community) % communityPalette.length] : (palette[n.group] || palette.file),
        level:communityMode ? n.community : undefined
    }}));
    const visibleIds = new Set(visibleNodes.map(n => n.id));
    const visibleEdges = allEdges.filter(e => visibleIds.has(e.from) && visibleIds.has(e.to)).map(e => {{
        const sourceCommunity = nodeById.get(e.from)?.community ?? -1;
        const targetCommunity = nodeById.get(e.to)?.community ?? -1;
        const sameCommunity = sourceCommunity === targetCommunity;
        const communityColor = communityPalette[Math.abs(sourceCommunity) % communityPalette.length];
        const edgeColor = communityMode
            ? (sameCommunity ? communityColor : '#475569')
            : (edgePalette[e.label] || '#64748b');
        return {{
            ...e,
            color:{{...e.color, color:edgeColor, highlight:sameCommunity && communityMode ? '#f4f5f8' : edgeColor}},
            dashes:communityMode && !sameCommunity,
            font:{{...e.font, size:edgeLabelsEl.checked ? 10 : 0}}
        }};
    }});
    const data = {{ nodes:new vis.DataSet(visibleNodes), edges:new vis.DataSet(visibleEdges) }};
    if (network) {{
        network.setOptions({{physics:{{enabled:true}}}});
        network.setData(data);
        network.stabilize(90);
        clearTimeout(physicsFreezeTimer);
        physicsFreezeTimer = setTimeout(() => network.setOptions({{physics:false}}), 1200);
    }}
    else if (window.vis && graphData.nodes.length) {{
        network = new vis.Network(graphEl, data, {{ layout:{{ improvedLayout:true }}, physics:{{ solver:'forceAtlas2Based', forceAtlas2Based:{{ gravitationalConstant:-55, centralGravity:.015, springLength:125, springConstant:.05, damping:.5 }}, stabilization:{{ iterations:110 }} }}, interaction:{{ hover:true, navigationButtons:true, keyboard:true, multiselect:true }}, nodes:{{ size:14, borderWidth:1.5 }}, edges:{{ selectionWidth:3 }} }});
        network.once('stabilizationIterationsDone', () => network.setOptions({{physics:false}}));
    }}
    graphStatsEl.innerHTML = `<div class="rail-stat"><span>Visible nodes</span><strong>${{visibleNodes.length}}</strong></div><div class="rail-stat"><span>Visible edges</span><strong>${{visibleEdges.length}}</strong></div><div class="rail-stat"><span>Star nodes</span><strong>${{visibleNodes.filter(n => n.isStar).length}}</strong></div><div class="rail-stat"><span>Hotspots</span><strong>${{visibleNodes.filter(n => n.isHotspot).length}}</strong></div>`;
}}
if (window.vis && graphData.nodes.length) {{
    renderGraph();
}} else {{ graphEl.innerHTML = '<div class="empty">No structural graph nodes found, or the visualization library could not load.</div>'; }}
Object.keys(palette).forEach(group => {{ const button = document.createElement('button'); button.innerHTML = '<span class="swatch" style="background:' + palette[group] + '"></span>' + group; button.style.borderColor = palette[group]; button.addEventListener('click', () => {{ if (activeGroups.has(group)) {{ activeGroups.delete(group); button.classList.add('off'); }} else {{ activeGroups.add(group); button.classList.remove('off'); }} renderGraph(); }}); legendEl.appendChild(button); }});
allCommunities.forEach(community => {{ const button = document.createElement('button'); const color = communityPalette[Math.abs(community) % communityPalette.length]; button.innerHTML = '<span class="swatch" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + color + '"></span> C' + (community + 1); button.style.borderColor = color; button.addEventListener('click', () => {{ if (activeCommunities.has(community)) {{ activeCommunities.delete(community); button.classList.add('off'); }} else {{ activeCommunities.add(community); button.classList.remove('off'); }} renderGraph(); }}); communityListEl.appendChild(button); }});
nodeFilterEl.addEventListener('input', renderGraph);
[hotspotOnlyEl, communityModeEl, starOnlyEl, edgeLabelsEl].forEach(control => control.addEventListener('change', renderGraph));
if (network) {{
    network.on('selectEdge', params => {{ const edge = params.edges.length ? network.body.data.edges.get(params.edges[0]) : null; if (!edge) return; const source = network.body.data.nodes.get(edge.from); const target = network.body.data.nodes.get(edge.to); edgeInfoEl.innerHTML = `<strong>${{escapeHtml(edge.label || 'relationship')}}</strong><br>${{escapeHtml(source?.label || edge.from)}} → ${{escapeHtml(target?.label || edge.to)}}`; }});
    network.on('selectNode', params => {{ const node = params.nodes.length ? network.body.data.nodes.get(params.nodes[0]) : null; if (!node) return; edgeInfoEl.innerHTML = `<strong>${{escapeHtml(node.label)}}</strong><br>${{escapeHtml(node.path || '')}}:${{node.startLine || ''}}<br>Star ${{Number(node.starScore || 0).toFixed(1)}} · Fragility ${{Number(node.hotspotScore || 0).toFixed(1)}} · Community C${{Number(node.community) + 1}}`; }});
}}
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
if (document.fonts) document.fonts.ready.then(renderGraph);
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
