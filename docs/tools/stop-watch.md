# astra_stop_watch

## Purpose
Stop a background index watcher for a workspace.

## MCP
```text
astra_stop_watch({"path":"C:\\path\\to\\project"})
```

## Output
Returns stopped state, index count, and last error.

## Interpretation
`running: false` confirms shutdown. Existing graph, vector, and cache artifacts remain available.

## Agent guidance
Call when a long-lived MCP editing session ends.
