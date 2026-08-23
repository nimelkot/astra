# Fragility Hotspots

Astra exposes the `fragility` CLI command and the `astra_get_fragility_hotspots` MCP tool. Both rank functions and classes that combine high dependency impact with high intrinsic complexity.

## Metrics

The analyzer uses the indexed structural graph and parser metadata. It does not use Git history, so results are deterministic and work in local or CI environments without repository history.

- **Graph centrality** combines normalized incoming relationship count (callers and dependencies) with normalized PageRank.
- **AST complexity** combines branch count, control-flow nesting depth, and parameter count. Python files provide these metrics from the Python AST; other supported formats remain available with zero-valued AST metrics until a format-specific parser supplies them.
- **Instability** is calculated as `Ce / (Ca + Ce)`, where `Ce` is outgoing coupling and `Ca` is incoming coupling.

The composite score is normalized to 0-100:

```text
Fragility Score = (Centrality * 0.4) + (Complexity * 0.4) + (Instability * 0.2)
```

Nodes at or above the default threshold of `75` are classified as `critical`; lower-scoring nodes are classified as `watch`. Every result includes the component scores and raw counts so an agent can explain why a node was ranked.

## CLI

Index the workspace first, then request the top hotspots:

```powershell
astra index C:\path\to\project
astra fragility --path C:\path\to\project --limit 10 --threshold 75
```

The command returns JSON containing `hotspots`, `critical`, `analyzed`, the threshold, and the scoring formula.

## MCP

Register `astra-mcp` with an MCP client, then call:

```text
astra_get_fragility_hotspots(
  path="C:\\path\\to\\project",
  limit=10,
  threshold=75
)
```

The tool returns the same report as the CLI. This gives an LLM structured evidence before it edits a highly connected function or class.

## Agent Workflows

## Impact and Refactoring Tools

### Blast radius

Use the impact tool before changing a function or class. It follows incoming `calls` and `depends_on` edges recursively, returning the affected declarations, distance from the target, and unique files:

```powershell
astra impact calculate_total --path C:\path\to\project --max-nodes 200
```

The MCP equivalent is `astra_impact(path, target, max_nodes)`. A missing target returns `found: false`; a large result can be bounded with `max_nodes`.

### Dead code and circular dependencies

`astra tether` reports orphan declarations, circular call/dependency chains, and high fan-out nodes. Its `cycles` and `orphans` details are available through both the CLI JSON output and `astra_tether`. Use `astra visualize` to inspect the corresponding structural graph and Tether panels.

### Graph-aware refactor planning

Generate a preview for a structural identifier rename:

```powershell
astra refactor-plan calculate_total sum_total --path C:\path\to\project
```

The MCP equivalent is `astra_refactor_plan(path, target, replacement)`. The plan uses indexed declarations and graph relationships to order impacted dependencies, reports each affected source chunk and occurrence count, and includes `before`/`after` previews. It is deliberately read-only (`apply: false`); the agent reviews the plan, applies an appropriate syntax-aware edit, and re-indexes afterward. Cyclic dependency groups are reported with `cycles: true` and a deterministic fallback order for review.

### Proactive test generation

1. Call `astra_get_fragility_hotspots`.
2. Select the highest-scoring critical nodes with weak or missing test coverage.
3. Inspect each node's `path`, `start_line`, `branches`, `nesting`, and `parameters`.
4. Generate focused unit or property-based tests, then run the project test suite.

### Pre-refactor sanity check

Run `astra fragility` before changing a target. A high score indicates that the agent should first consider smaller helpers, narrower interfaces, and additional regression tests. Use `astra_dipper` or `astra_path` to gather the dependency context around the target.

### Architecture review in CI

Run the command against the pull request checkout and compare critical counts or scores with the base branch. Tether remains the broader graph-health gate for cycles, orphans, and high fan-out; fragility adds a risk ranking for complex, highly connected declarations. Teams can fail CI when a protected module gains a new critical hotspot or exceeds an agreed score threshold.

## Visualization

Use `astra visualize` to inspect the structural graph and existing Tether anomaly panels. The hotspot report is JSON-first so it can be consumed by CI and MCP orchestration; visualization can be extended with the same report data without changing the scoring logic.

## Git history metrics

Git churn is intentionally not part of the initial score. Commit frequency, author count, and recent ownership can be useful risk signals, but they require policy decisions about history depth, renames, generated files, and shallow CI checkouts. They can be added later as a separate optional signal rather than changing the deterministic AST-and-graph baseline.

## Targeted Test Tools

The test tools close the loop between graph analysis and validation:

```powershell
astra test-map --path C:\path\to\project
astra affected-tests astra/core/engine.py --path C:\path\to\project
astra test-scaffold AstraEngine --path C:\path\to\project
astra run-impacted astra/core/engine.py --path C:\path\to\project
```

The MCP equivalents are `astra_test_map`, `astra_affected_tests`, `astra_gen_test_scaffold`, and `astra_run_impacted`.

- `test-map` maps each indexed source declaration to test declarations that reach it and reports untested nodes.
- `affected-tests` accepts changed repository-relative paths and returns the minimal test files reachable from those changes.
- `test-scaffold` emits a read-only pytest stub with the target location and graph caller hints.
- `run-impacted` executes only the selected test files using the active Python interpreter and a timeout. It returns `passed`, `failed`, `timeout`, or `no_tests`.

All CLI and MCP analysis tools refresh the incremental index first. A practical agent loop is: refresh, map or select tests, inspect impact and fragility, generate a scaffold when needed, apply an approved edit, then run the affected tests.
