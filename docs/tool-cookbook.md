# Astra Tool Cookbook

This guide shows how to use every Astra tool from the CLI and MCP. Outputs are representative examples; paths, scores, line numbers, and counts depend on the indexed workspace.

## Index First

Astra keeps graph and vector artifacts in the target repository. The CLI analysis commands and MCP analysis tools automatically refresh the incremental index before they run. An explicit index call is still useful in CI or at the start of an agent workflow.

### CLI

```powershell
astra index C:\path\to\project
```

Example output:

```json
{
  "root": "C:\\path\\to\\project",
  "files": 42,
  "chunks": 318,
  "graph": "C:\\path\\to\\project\\.astra_graph.json",
  "vectors": "C:\\path\\to\\project\\.astra_vectors"
}
```

### MCP

```text
astra_index_repo({"path": "C:\\path\\to\\project"})
```

Use this when an agent begins work on a repository, after a large checkout change, or before handing the workspace to another tool.

**Interpretation:** `files` counts indexed files and `chunks` counts searchable graph/vector records. The graph and vectors paths confirm which local artifacts later tools will consume. A successful response does not mean every file parsed successfully; compare counts between runs and inspect parser warnings or missing expected symbols.

## Search and Context

### 1. `astra_semantic_search`

**Use case:** Find code by behavior or concept when the exact symbol or filename is unknown.

CLI:

```powershell
astra search "authentication token validation" --path C:\path\to\project --limit 3
```

Example output:

```text
 Score  Kind      Path                    Symbol              Lines
 0.912  function  src/auth/service.py    validate_token      18-42
 0.774  method    src/api/middleware.py  authenticate        31-57
```

MCP:

```text
astra_semantic_search({
  "path": "C:\\path\\to\\project",
  "query": "authentication token validation",
  "limit": 3
})
```

Returns a list of scored chunks with paths, symbols, line ranges, and source text.

**Interpretation:** Higher `score` means a stronger lexical or semantic match, not proof that the chunk is the answer. Use `path`, line ranges, and `source` to inspect the best few results, then use graph tools to verify relationships.

### 2. `astra_get_callers`

**Use case:** Identify direct callers before changing a function or method.

CLI:

```powershell
astra query callers validate_token --path C:\path\to\project
```

MCP:

```text
astra_get_callers({
  "path": "C:\\path\\to\\project",
  "target": "validate_token",
  "limit": 20
})
```

Example output:

```json
[
  {
    "id": "src/api/middleware.py:31:authenticate",
    "name": "authenticate",
    "kind": "method",
    "path": "src/api/middleware.py",
    "start_line": 31,
    "relationship": "calls"
  }
]
```

**Interpretation:** Each returned item is a direct incoming relationship. `calls` indicates a call edge and `depends_on` indicates a structural dependency. An empty list means no matching incoming edges were found, not necessarily that the symbol is unused in runtime behavior.

### 3. `astra_hybrid_context`

**Use case:** Give an agent semantic matches plus structural callers for a dependency-aware answer.

CLI:

```powershell
astra dipper "payment retry flow" --path C:\path\to\project --limit 5
```

For the direct hybrid API, use MCP:

```text
astra_hybrid_context({
  "path": "C:\\path\\to\\project",
  "query": "payment retry flow",
  "limit": 5,
  "expansion": 5
})
```

Example output shape:

```json
{
  "matches": [{"name": "retry_payment", "path": "src/payments.py", "score": 0.84}],
  "related": [{"name": "checkout", "path": "src/checkout.py", "relationship": "calls"}]
}
```

**Interpretation:** `matches` are semantic candidates and `related` are graph-expanded callers. Prefer results that appear in both lists when building context for an edit; a result in only one list needs normal source inspection.

### 4. `astra_dipper`

**Use case:** Scoop a compact dependency-complete context window before asking an LLM to explain or edit code.

CLI:

```powershell
astra dipper retry_payment --path C:\path\to\project --limit 4 --parent-depth 2 --child-depth 1
```

MCP:

```text
astra_dipper({
  "path": "C:\\path\\to\\project",
  "query": "retry_payment",
  "limit": 4,
  "parent_depth": 2,
  "child_depth": 1,
  "max_nodes": 80,
  "max_source_chars": 280
})
```

Example output shape:

```json
{
  "summary": {"nodes": 7, "edges": 8, "snippets": 6},
  "seeds": ["src/payments.py:18:retry_payment"],
  "snippets": [{"path": "src/payments.py", "name": "retry_payment", "source": "..."}]
}
```

**Interpretation:** `seeds` are the initial symbol or search matches. `nodes` and `edges` define the selected subgraph, while `snippets` are the source excerpts safe to place in an LLM prompt. Increase depth or limits only when the current context is missing a dependency.

## Graph Analysis

### 5. `astra_path`

**Use case:** Explain how two declarations are structurally connected.

CLI:

```powershell
astra path checkout charge_card --path C:\path\to\project --max-hops 8
```

MCP:

```text
astra_path({
  "path": "C:\\path\\to\\project",
  "source": "checkout",
  "target": "charge_card",
  "max_hops": 8
})
```

Example CLI output:

```text
checkout()
src/checkout.py:44
↳ charge_card()
src/payments.py:18

Shortest path (1 hops):
  checkout() --calls--> charge_card()
```

**Interpretation:** The arrows show relationship direction. The hop count measures graph edges, not source distance or runtime latency. `No structural path found` means the symbols could not be resolved or are disconnected in the indexed graph.

### 6. `astra_tether`

**Use case:** Run an architecture health gate for circular dependencies, orphan declarations, and high fan-out nodes.

CLI:

```powershell
astra tether --path C:\path\to\project --cycle-limit 20 --fanout-threshold 12
```

MCP:

```text
astra_tether({
  "path": "C:\\path\\to\\project",
  "cycle_limit": 20,
  "fanout_threshold": 12
})
```

Example output shape:

```json
{
  "status": "warn",
  "summary": {"cycles": 2, "orphans": 14, "high_fanout": 1},
  "details": {"cycles": [{"length": 2, "nodes": ["a", "b"]}]}
}
```

**Interpretation:** `pass` means no cycles were detected; `warn` means at least one cycle exists. Treat `orphans` as a review queue rather than automatic dead-code proof, and inspect the node lists before removing declarations. High fan-out indicates coupling that may deserve a refactor.

### 7. `astra_get_fragility_hotspots`

**Use case:** Find declarations where dependency centrality, AST complexity, and coupling combine into elevated change risk.

CLI:

```powershell
astra fragility --path C:\path\to\project --limit 10 --threshold 75
```

MCP:

```text
astra_get_fragility_hotspots({
  "path": "C:\\path\\to\\project",
  "limit": 10,
  "threshold": 75
})
```

Example output shape:

```json
{
  "hotspots": [{
    "name": "parse_request",
    "path": "src/parser.py",
    "score": 81.4,
    "classification": "critical",
    "centrality": 78.2,
    "complexity": 86.0,
    "instability": 79.9
  }],
  "critical": 1
}
```

**Interpretation:** Scores range from 0 to 100 relative to the indexed workspace. `critical` means the score meets the supplied threshold; `watch` means it is below it. Compare the component values to decide whether risk comes from callers, logic complexity, or coupling rather than acting on the composite score alone.

### 8. `astra_impact`

**Use case:** Calculate the upstream blast radius before editing a function or class, including affected files.

CLI:

```powershell
astra impact charge_card --path C:\path\to\project --max-nodes 200
```

MCP:

```text
astra_impact({
  "path": "C:\\path\\to\\project",
  "target": "charge_card",
  "max_nodes": 200
})
```

Example output shape:

```json
{
  "target": "charge_card",
  "found": true,
  "files": ["src/checkout.py", "src/payments.py", "tests/test_payments.py"],
  "nodes": [{"name": "checkout", "distance": 1, "path": "src/checkout.py"}],
  "truncated": false
}
```

**Interpretation:** `found` confirms the target resolved. `distance` is the number of incoming graph steps from the target, `files` is the review scope, and `truncated` warns that `max_nodes` limited the result. A missing target should be resolved before editing.

### 9. `astra_refactor_plan`

**Use case:** Preview a graph-ordered identifier rename before an agent applies an edit.

CLI:

```powershell
astra refactor-plan charge_card process_card --path C:\path\to\project
```

MCP:

```text
astra_refactor_plan({
  "path": "C:\\path\\to\\project",
  "target": "charge_card",
  "replacement": "process_card"
})
```

Example output shape:

```json
{
  "target": "charge_card",
  "replacement": "process_card",
  "apply": false,
  "cycles": false,
  "order": ["src/payments.py:18:charge_card", "src/checkout.py:44:checkout"],
  "changes": [{
    "path": "src/payments.py",
    "occurrences": 2,
    "before": "def charge_card(...): ...",
    "after": "def process_card(...): ..."
  }]
}
```

The plan is intentionally read-only. Review it, apply an approved syntax-aware edit, and re-index.

**Interpretation:** `order` is the recommended dependency order, `changes` contains source previews, and `occurrences` counts identifier-boundary matches in each chunk. `cycles: true` means no perfect topological order exists and the returned order requires human review. Never treat `apply: false` as an applied rename.

### 10. `astra_visualize`

**Use case:** Inspect the indexed graph, vector chunks, Dipper context, and Tether anomalies in a local HTML report.

CLI:

```powershell
astra visualize C:\path\to\project --output C:\path\to\project\astra-report.html
```

MCP:

```text
astra_visualize({
  "path": "C:\\path\\to\\project",
  "output": "C:\\path\\to\\project\\astra-report.html"
})
```

Example output:

```json
{
  "path": "C:\\path\\to\\project\\astra-report.html",
  "url": "file:///C:/path/to/project/astra-report.html"
}
```

The tool refreshes the incremental index and renders Astra's artifacts. Agents should use this tool instead of generating an HTML graph manually.

**Interpretation:** The returned `path` is the generated report and `url` is the local browser URL. The report is a view of the current Astra artifacts; if nodes are missing, re-check the index counts and source discovery rather than editing the HTML.

## Targeted Testing

### 11. `astra_test_map`

**Use case:** Discover which tests reach each source declaration and identify untested reachable code.

CLI:

```powershell
astra test-map --path C:\path\to\project
```

MCP:

```text
astra_test_map({"path": "C:\\path\\to\\project", "limit": 1000})
```

Example output shape:

```json
{
  "untested": 12,
  "sources": [{
    "name": "charge_card",
    "path": "src/payments.py",
    "tested": true,
    "tests": ["tests/test_payments.py:8:test_charge_card"]
  }]
}
```

**Interpretation:** `tested: true` means at least one indexed test declaration reaches the source node through graph edges. `untested` is a prioritization signal, not a code-coverage percentage. Review the `tests` IDs and remember dynamically discovered tests may not appear in the structural graph.

### 12. `astra_affected_tests`

**Use case:** Convert changed files from a pull request into the smallest graph-selected test file set.

CLI:

```powershell
astra affected-tests src/payments.py src/checkout.py --path C:\path\to\project
```

MCP:

```text
astra_affected_tests({
  "path": "C:\\path\\to\\project",
  "changed_paths": ["src/payments.py", "src/checkout.py"],
  "limit": 100
})
```

Example output shape:

```json
{
  "changed_paths": ["src/payments.py", "src/checkout.py"],
  "test_files": ["tests/test_payments.py", "tests/test_checkout.py"],
  "uncovered_changed_nodes": []
}
```

**Interpretation:** `test_files` is the minimal graph-selected file list to pass to pytest. `uncovered_changed_nodes` identifies changed declarations with no discovered test path, which should trigger focused manual or new-test work. An empty test list means no structural test dependency was found.

### 13. `astra_gen_test_scaffold`

**Use case:** Start a focused pytest test for a target with its real indexed location and dependency hints, without pretending to generate complete assertions.

CLI:

```powershell
astra test-scaffold charge_card --path C:\path\to\project
```

MCP:

```text
astra_gen_test_scaffold({
  "path": "C:\\path\\to\\project",
  "target": "charge_card"
})
```

Example output shape:

```json
{
  "found": true,
  "target_node": "src/payments.py:18:charge_card",
  "scaffold": "import pytest\\n\\ndef test_charge_card_behavior():\\n    ..."
}
```

The scaffold is text output only. The agent should add project-specific fixtures, mocks, and assertions before writing it to a test file.

**Interpretation:** `found` and `target_node` confirm which declaration was selected. The scaffold's dependency comment is a review hint, not a complete fixture plan. The intentional `pytest.fail` keeps an incomplete scaffold from being mistaken for passing coverage.

### 14. `astra_run_impacted`

**Use case:** Close the pre-commit or CI loop by selecting and executing only tests affected by changed files.

CLI:

```powershell
astra run-impacted src/payments.py --path C:\path\to\project --timeout 120
```

MCP:

```text
astra_run_impacted({
  "path": "C:\\path\\to\\project",
  "changed_paths": ["src/payments.py"],
  "timeout": 120
})
```

Example output shape:

```json
{
  "status": "passed",
  "returncode": 0,
  "test_files": ["tests/test_payments.py"],
  "command": ["python", "-m", "pytest", "tests/test_payments.py"]
}
```

Possible statuses are `passed`, `failed`, `timeout`, and `no_tests`. The runner uses the active Python interpreter, does not invoke a shell, and truncates captured output to keep MCP responses manageable.

**Interpretation:** `passed` means pytest returned exit code 0 for the selected files; `failed` exposes a nonzero test result in `output`; `timeout` requires a narrower test set or longer timeout; and `no_tests` means the graph found no test files. Always inspect `returncode` and `output` before reporting success.

## Recommended Agent Sequences

### Understand before editing

```text
astra_index_repo -> astra_hybrid_context or astra_dipper -> astra_impact -> astra_get_fragility_hotspots
```

### Refactor safely

```text
astra_refactor_plan -> review changes -> apply approved edit -> astra_index_repo -> astra_affected_tests -> astra_run_impacted
```

### Review a pull request

```text
astra_index_repo -> astra_affected_tests -> astra_run_impacted -> astra_tether -> astra_get_fragility_hotspots -> astra_visualize
```

All sequences use Astra's returned graph, source locations, test selections, and local report URLs. The agent should not recreate indexes, dependency graphs, or visualizations independently.

## MCP Orchestration Prompt

MCP clients that expose prompts can select `astra_codebase_workflow` with a local path and task:

```text
astra_codebase_workflow({
  "path": "C:\\path\\to\\project",
  "task": "Prepare a safe rename of charge_card and run the smallest relevant test set"
})
```

The prompt returns instructions to call `astra_index_repo` first, choose only the narrowest analysis tools, interpret uncertainty and warnings, review `astra_refactor_plan` before editing, and run `astra_affected_tests` plus `astra_run_impacted` afterward. For visualization requests it directs the agent to call `astra_visualize`, which renders Astra's existing artifacts rather than generating HTML independently.

Prompts are guidance templates, not executable workflows: the MCP client or LLM still decides whether and when to call each tool. The tools' automatic incremental index refresh remains the enforcement layer when a client skips the prompt.
