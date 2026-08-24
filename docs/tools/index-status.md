# astra_index_status

## Purpose
Check continuous background indexing state.

## MCP
```text
astra_index_status({"path":"C:\\path\\to\\project"})
```

## Output
Returns running state, index count, and last error.

## Interpretation
A rising index count confirms detected changes were processed. A non-null error needs inspection and possibly an explicit re-index.

## Agent guidance
Use sparingly for long sessions, not before every read-only tool call.
