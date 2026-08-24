# astra_visualize

## Purpose
Render the current Astra knowledge graph, vector chunks, Dipper scoop, Tether health, communities, hotspots, and star nodes.

## CLI
```powershell
astra visualize C:\path\to\project
```

## MCP
```text
astra_visualize({"path":"C:\\path\\to\\project","output":"C:\\path\\to\\project\\report.html"})
```

## Output
Returns a local report path and browser URL.

## Interpretation
The report renders Astra artifacts; missing nodes indicate an indexing or discovery issue, not an HTML-generation task.

## Agent guidance
Use after indexing or analysis when visual inspection is useful. Do not generate a competing HTML graph manually.
