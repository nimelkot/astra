# astra_gen_test_scaffold

## Purpose
Generate a read-only pytest stub with target location and dependency hints.

## CLI
```powershell
astra test-scaffold charge_card --path C:\path\to\project
```

## MCP
```text
astra_gen_test_scaffold({"path":"C:\\path\\to\\project","target":"charge_card"})
```

## Output
Returns `found`, target node, and scaffold text.

## Interpretation
The scaffold intentionally contains `pytest.fail`; it is not passing coverage. Add real fixtures, mocks, and assertions.

## Agent guidance
Use after test-map or health-gate reports uncovered nodes.
