# astra_hybrid_context

## Purpose
Combine semantic search matches with structural caller expansion.

## CLI
Use `astra dipper` for the CLI context scoop; the direct hybrid API is MCP-only.

## MCP
```text
astra_hybrid_context({"path":"C:\\path\\to\\project","query":"payment retry flow","limit":5,"expansion":5})
```

## Output
Returns `matches` and `related` records.

## Interpretation
Matches provide semantic evidence; related records provide graph evidence. Candidates present in both are especially useful for context.

## Agent guidance
Use as a compact first-pass investigation before deeper impact or refactor analysis.
