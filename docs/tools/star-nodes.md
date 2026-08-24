# astra_star_nodes

## Purpose
Identify high-importance declarations with concentrated dependency pressure.

## CLI
```powershell
astra star-nodes --path C:\path\to\project --limit 20 --threshold 60
```

## MCP
```text
astra_star_nodes({"path":"C:\\path\\to\\project","limit":20,"threshold":60})
```

## Output
Returns incoming/outgoing counts, PageRank, normalized score, and `is_star` status.

## Interpretation
A star node is important, not necessarily defective. Review it carefully before API changes, deletion, or broad refactoring.

## Agent guidance
Pair with `astra_impact` and `astra_get_fragility_hotspots` for change-risk analysis.
