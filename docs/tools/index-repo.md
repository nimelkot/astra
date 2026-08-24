# astra_index_repo

## Purpose
Create or refresh the local structural graph, vector chunks, and hash cache.

## CLI
```powershell
astra index C:\path\to\project
```

## MCP
```text
astra_index_repo({"path": "C:\\path\\to\\project"})
```

## Output
Returns `root`, indexed `files`, `chunks`, graph path, and vector path.

## Interpretation
Use this at the start of a task or after a large checkout change. Stable counts indicate the index completed; they do not guarantee every file parsed successfully. Subsequent tools refresh incrementally.

## Agent guidance
Call once before independent analysis calls. Do not rebuild the graph or vector index yourself.
