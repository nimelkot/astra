# astra_tether

## Purpose
Check architecture health for cycles, orphan declarations, and high fan-out.

## CLI
```powershell
astra tether --path C:\path\to\project --cycle-limit 20 --fanout-threshold 12
```

## MCP
```text
astra_tether({"path":"C:\\path\\to\\project","cycle_limit":20,"fanout_threshold":12})
```

## Output
Returns `status`, summary counts, anomalies, cycles, orphans, and high-fanout details.

## Interpretation
`pass` means no cycles; `warn` means cycles exist. Orphans are review candidates, not proof of dead code.

## Agent guidance
Use for architecture gates and investigate reported nodes before removal or refactoring.
