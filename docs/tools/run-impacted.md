# astra_run_impacted

## Purpose
Execute only graph-selected tests for changed paths.

## CLI
```powershell
astra run-impacted src/payments.py --path C:\path\to\project --timeout 120
```

## MCP
```text
astra_run_impacted({"path":"C:\\path\\to\\project","changed_paths":["src/payments.py"],"timeout":120})
```

## Output
Returns selected files, command, status, return code, and bounded output.

## Interpretation
Statuses are `passed`, `failed`, `timeout`, or `no_tests`. Always inspect `returncode` and `output`.

## Agent guidance
Use after an approved edit or through `astra_validate_change`.
