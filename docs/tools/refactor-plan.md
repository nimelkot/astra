# astra_refactor_plan

## Purpose
Preview a graph-ordered identifier rename without editing files.

## CLI
```powershell
astra refactor-plan charge_card process_card --path C:\path\to\project
```

## MCP
```text
astra_refactor_plan({"path":"C:\\path\\to\\project","target":"charge_card","replacement":"process_card"})
```

## Output
Returns dependency order, cycles flag, affected chunks, occurrence counts, and before/after previews.

## Interpretation
`apply: false` means no edit occurred. `cycles: true` requires human review because no perfect topological order exists.

## Agent guidance
Review before applying a host-side edit, then re-index and run affected tests.
