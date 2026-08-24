# astra_affected_tests

## Purpose
Select the smallest indexed test-file set affected by changed paths.

## CLI
```powershell
astra affected-tests src/payments.py src/checkout.py --path C:\path\to\project
```

## MCP
```text
astra_affected_tests({"path":"C:\\path\\to\\project","changed_paths":["src/payments.py"],"limit":100})
```

## Output
Returns changed nodes, `test_files`, test node IDs, and `uncovered_changed_nodes`.

## Interpretation
An empty test list means no structural test path was found. Uncovered nodes need manual or new-test work.

## Agent guidance
Use before `astra_run_impacted` or `astra_validate_change`.
