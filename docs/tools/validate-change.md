# astra_validate_change

## Purpose
Orchestrate impact analysis, risk signals, test selection, scaffolds, and test execution.

## CLI
```powershell
astra validate-change --path C:\path\to\project --changed src\payments.py --mode targeted
astra validate-change --path C:\path\to\project --target charge_card --mode plan
```

## MCP
```text
astra_validate_change({"path":"C:\\path\\to\\project","changed_paths":["src/payments.py"],"mode":"targeted","timeout":120})
```

## Modes
`plan` analyzes only, `targeted` runs selected tests, `scaffold` returns stubs, and `full` explicitly runs the complete pytest suite.

## Interpretation
Read `test_selection`, `risk`, `execution`, and `recommendations` together. `plan` must return `execution.status: not_run`.

## Agent guidance
Use as the testing quality gate; use `astra_health_gate` for architecture readiness.
