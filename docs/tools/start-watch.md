# astra_start_watch

## Purpose
Start one non-blocking background index watcher for a long-lived MCP session.

## MCP
```text
astra_start_watch({"path":"C:\\path\\to\\project","interval":1})
```

## Output
Returns root, running state, interval, index count, and last error.

## Interpretation
The initial index completes before return. Repeated calls for the same root reuse the watcher.

## Agent guidance
Start once for a long editing session; use status to observe it and stop-watch at session end.
