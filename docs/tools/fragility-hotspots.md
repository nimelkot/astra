# astra_get_fragility_hotspots

## Purpose
Rank declarations by graph centrality, AST complexity, and architectural instability.

## CLI
```powershell
astra fragility --path C:\path\to\project --limit 10 --threshold 75
```

## MCP
```text
astra_get_fragility_hotspots({"path":"C:\\path\\to\\project","limit":10,"threshold":75})
```

## Output
Returns component scores, raw branch/nesting/parameter metrics, composite score, and `critical`/`watch` classification.

## Interpretation
Scores are normalized within the indexed workspace. Read the component scores before deciding whether risk comes from complexity, centrality, or coupling.

## Agent guidance
Run before changing highly connected or complex declarations.
