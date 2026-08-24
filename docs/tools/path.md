# astra_path

## Purpose
Find the shortest structural relationship between two symbols.

## CLI
```powershell
astra path checkout charge_card --path C:\path\to\project --max-hops 8
```

## MCP
```text
astra_path({"path":"C:\\path\\to\\project","source":"checkout","target":"charge_card","max_hops":8})
```

## Output
Returns hop count, ordered nodes, locations, and relationship edges, or `null` when unresolved/disconnected.

## Interpretation
Hops are graph edges, not source distance or runtime latency. Arrow direction describes stored relationship direction.

## Agent guidance
Use to explain one dependency chain; use `astra_impact` for all upstream dependents.
