# astra_health_gate

## Purpose
Return one architecture-readiness decision for CI, pull requests, or agent pre-edit review.

## CLI
```powershell
astra health-gate --path C:\path\to\project --changed src\payments.py --fail-on critical
```

## MCP
```text
astra_health_gate({"path":"C:\\path\\to\\project","changed_paths":["src/payments.py"],"fail_on":"critical"})
```

## Output
Combines Tether cycles/orphans, fragility hotspots, star nodes, blast radius, affected tests, findings, and a `pass`/`warn`/`fail` status. Each cycle finding includes `cycle_number` and source-located `nodes`.

## Interpretation
`fail_on: critical` fails only for critical findings, `warn` also fails for warnings, and `never` reports without failing. Read each cycle's node list as one circular chain rather than treating the total cycle count as one problem. Findings are evidence for review, not automatic proof of a defect.

## Agent guidance
Prefer this one call for merge readiness. Investigate individual findings with detailed tools only when needed.
