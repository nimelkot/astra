# astra_dipper

## Purpose
Scoop a compact, dependency-aware context package for an LLM.

## CLI
```powershell
astra dipper retry_payment --path C:\path\to\project --limit 4 --parent-depth 2 --child-depth 1
```

## MCP
```text
astra_dipper({"path":"C:\\path\\to\\project","query":"retry_payment","limit":4,"parent_depth":2,"child_depth":1,"max_nodes":80,"max_source_chars":280})
```

## Output
Returns seeds, graph nodes, edges, summary counts, and trimmed source snippets.

## Interpretation
Increase depth or limits only when a required dependency is absent. Snippets are bounded prompt material, not complete files.

## Agent guidance
Prefer before editing to reduce token usage and preserve local dependency context.
