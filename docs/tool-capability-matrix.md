# Astra Tool Capability Matrix

This matrix ranks tools by breadth of responsibility. Higher-level orchestrators appear first because they combine more Astra capabilities and are usually the best starting point for an agent trying to save calls and tokens. A check mark means the tool directly specializes in that capability; it does not mean every result includes every signal.

| Rank | Tool | Discovery | Context | Graph | Risk | Refactor | Testing | Live sync | Visualization | Orchestration |
| ---: | --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `astra_health_gate` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 2 | `astra_validate_change` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |  | ✓ |
| 3 | `astra_visualize` |  | ✓ | ✓ | ✓ |  |  | ✓ | ✓ | ✓ |
| 4 | `astra_codebase_workflow` | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| 5 | `astra_dipper` | ✓ | ✓ | ✓ |  |  |  | ✓ | ✓ | ✓ |
| 6 | `astra_hybrid_context` | ✓ | ✓ | ✓ |  |  |  | ✓ |  | ✓ |
| 7 | `astra_impact` |  |  | ✓ | ✓ | ✓ | ✓ | ✓ |  | ✓ |
| 8 | `astra_tether` |  |  | ✓ | ✓ |  |  | ✓ | ✓ | ✓ |
| 9 | `astra_get_fragility_hotspots` |  |  | ✓ | ✓ |  |  | ✓ |  | ✓ |
| 10 | `astra_star_nodes` |  |  | ✓ | ✓ |  |  | ✓ | ✓ | ✓ |
| 11 | `astra_refactor_plan` |  |  | ✓ | ✓ | ✓ |  | ✓ |  | ✓ |
| 12 | `astra_run_impacted` |  |  | ✓ |  |  | ✓ | ✓ |  | ✓ |
| 13 | `astra_affected_tests` |  |  | ✓ |  |  | ✓ | ✓ |  | ✓ |
| 14 | `astra_test_map` |  |  | ✓ |  |  | ✓ | ✓ |  | ✓ |
| 15 | `astra_gen_test_scaffold` |  | ✓ | ✓ |  | ✓ | ✓ | ✓ |  | ✓ |
| 16 | `astra_semantic_search` | ✓ | ✓ |  |  |  |  | ✓ |  |  |
| 17 | `astra_get_callers` |  |  | ✓ |  |  |  | ✓ |  |  |
| 18 | `astra_path` |  |  | ✓ |  |  |  | ✓ |  |  |
| 19 | `astra_start_watch` |  |  |  |  |  |  | ✓ |  | ✓ |
| 20 | `astra_index_repo` |  |  | ✓ |  |  |  | ✓ |  | ✓ |
| 21 | `astra_index_status` / `astra_stop_watch` |  |  |  |  |  |  | ✓ |  | ✓ |

## How to Use the Ranking

- Start with `astra_health_gate` for one architecture-readiness decision.
- Start with `astra_validate_change` when the main question is test scope and execution.
- Use `astra_dipper` or `astra_hybrid_context` when an agent needs compact code context.
- Use `astra_impact`, `astra_tether`, `astra_get_fragility_hotspots`, or `astra_star_nodes` to investigate a reported risk.
- Use `astra_refactor_plan` before applying a structural rename.
- Use `astra_affected_tests` and `astra_run_impacted` after an edit.
- Use `astra_visualize` to inspect the current knowledge graph and the Command Center tab, which summarizes health-gate and validation-plan results.
- Use `astra_start_watch` for long-lived sessions; otherwise rely on automatic incremental refresh.

For exact parameters, example output, interpretation guidance, and CLI equivalents, see [tool-cookbook.md](tool-cookbook.md) and the individual pages in [tools/](tools/).
