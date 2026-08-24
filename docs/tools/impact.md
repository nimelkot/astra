# astra_impact

## Purpose
Calculate a declaration's recursive upstream blast radius.

## CLI
```powershell
astra impact charge_card --path C:\path\to\project --max-nodes 200
```

## MCP
```text
astra_impact({"path":"C:\\path\\to\\project","target":"charge_card","max_nodes":200})
```

## Output
Returns resolved seeds, impacted nodes, graph distances, affected files, and a truncation flag.

## Interpretation
`distance` is incoming graph depth. `truncated: true` means increase `max_nodes` before relying on completeness.

## Agent guidance
Run before edits and feed affected source paths to `astra_affected_tests`.
