# astra_get_callers

## Purpose
Find direct callers and dependency sources for a declaration.

## CLI
```powershell
astra query callers validate_token --path C:\path\to\project
```

## MCP
```text
astra_get_callers({"path":"C:\\path\\to\\project","target":"validate_token","limit":20})
```

## Output
Returns caller IDs, names, kinds, paths, lines, and `relationship` (`calls` or `depends_on`).

## Interpretation
An empty list means no indexed incoming relationship was found; dynamic or unresolved usage may be absent.

## Agent guidance
Use before a small change. Use `astra_impact` for recursive blast radius.
