# astra_test_map

## Purpose
Map source declarations to indexed tests that reach them and identify untested nodes.

## CLI
```powershell
astra test-map --path C:\path\to\project
```

## MCP
```text
astra_test_map({"path":"C:\\path\\to\\project","limit":1000})
```

## Output
Returns source records with `tests` and `tested`, plus an `untested` count.

## Interpretation
This is graph reachability, not a coverage percentage. Dynamic test behavior may not be represented.

## Agent guidance
Use to prioritize test additions and feed changed paths to `astra_affected_tests`.
