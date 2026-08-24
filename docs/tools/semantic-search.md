# astra_semantic_search

## Purpose
Find code by concept, identifier, docstring, or source meaning when the exact symbol is unknown.

## CLI
```powershell
astra search "authentication token validation" --path C:\path\to\project --limit 5
```

## MCP
```text
astra_semantic_search({"path":"C:\\path\\to\\project","query":"authentication token validation","limit":5})
```

## Output
Returns scored chunks with `path`, `name`, `kind`, line range, score, and source.

## Interpretation
Higher scores are ranked matches, not proof. Inspect top results and confirm relationships with graph tools.

## Agent guidance
Use for discovery, then pass strong candidates to `astra_dipper`, `astra_get_callers`, or `astra_path`.
