<p align="center">
	<img src="assets/astra-social-banner.png" alt="Astra: local code intelligence for AI agents" width="100%">
</p>

Astra is dual-licensed under the [MIT License](LICENSE) or [Apache License 2.0](LICENSE-APACHE), at your option.

Astra is a local code intelligence service for AI agents. It parses repository files into a structural NetworkX graph and a searchable local code-chunk index, with full Python AST analysis and AST-compatible structural extraction across common source, markup, and configuration formats. The same engine is available through the `astra` CLI and the official MCP Python SDK.

## Architecture

Astra is designed as a local **code intelligence fabric**: a deterministic structural layer explains how a codebase is assembled, while a semantic retrieval layer explains what the code means. Both layers feed the same knowledge graph and are exposed through the CLI and MCP so engineers, CI systems, and AI agents operate on one shared model of the repository.

| Intelligence layer | What it does | Business value | Primary artifact or interface |
| --- | --- | --- | --- |
| **Discovery and change sensing** | Recursively inventories supported files, ignores generated/dependency directories, and uses SHA-256 fingerprints to detect additions, edits, and removals. | Keeps repository intelligence current while minimizing repeat processing and update time. | `.astra_index_cache.json` and `astra watch` |
| **AST structural intelligence** | Parses Python with the native AST and extracts declarations, methods, calls, branches, nesting, parameters, and source locations. Other supported formats receive language-aware structural extraction. | Turns source code into inspectable business entities and measurable logic risk without importing or executing the project. | Code chunks and structural references |
| **Knowledge graph** | Builds directed relationships between modules, declarations, callers, dependencies, and definitions using NetworkX. | Makes blast radius, dependency paths, circularity, orphan code, refactor order, and architecture health queryable. | `.astra_graph.json` |
| **Semantic retrieval** | Searches indexed code by concepts, identifiers, docstrings, and source content; hybrid workflows combine semantic matches with graph expansion. | Lets teams find capabilities by intent instead of memorizing filenames or symbol names. | `.astra_vectors/` and `astra_semantic_search` |
| **Optional neural retrieval** | Can use Sentence Transformers and Chroma for embedding-based similarity; the default local lexical path requires no model download. | Adds meaning-based recall when terminology differs between a request and the implementation, while preserving a lightweight offline baseline. | Optional embedding backend |
| **Risk and impact intelligence** | Scores fragility through graph centrality, AST complexity, and coupling; traces upstream blast radius and maps source nodes to tests. | Helps prioritize review, testing, and refactoring effort where change risk is highest. | `fragility`, `impact`, and test workflow tools |
| **Agent orchestration** | Provides Dipper context scoops, Tether architecture checks, refactor plans, targeted test execution, and the `astra_codebase_workflow` MCP prompt. | Gives AI agents a disciplined operating model with evidence before edits and validation after edits. | CLI commands and MCP tools/prompts |
| **Live delivery surfaces** | Serves the same engine through terminal commands, MCP, local HTML visualization, and a continuous filesystem watcher. | Fits developer workstations, CI pipelines, long-running agent sessions, and visual architecture reviews without duplicating logic. | `astra`, `astra-mcp`, and `astra visualize` |

The MCP surface exposes nineteen tools and one orchestration prompt: `astra_index_repo`, `astra_semantic_search`, `astra_get_callers`, `astra_path`, `astra_dipper`, `astra_tether`, `astra_get_fragility_hotspots`, `astra_star_nodes`, `astra_impact`, `astra_refactor_plan`, `astra_test_map`, `astra_affected_tests`, `astra_gen_test_scaffold`, `astra_run_impacted`, `astra_start_watch`, `astra_index_status`, `astra_stop_watch`, `astra_hybrid_context`, and `astra_visualize`.

<p align="center">
	<img src="assets/astra-pipeline.png" alt="Astra indexing pipeline: parse, graph, index, and retrieve" width="900">
</p>

<p align="center"><em>Indexing pipeline</em></p>

<p align="center">
	<img src="assets/astra-components.png" alt="Astra component map connecting the CLI and MCP host to the shared engine" width="900">
</p>

<p align="center"><em>Component map</em></p>

## Install

Python 3.10+ is required. Choose one of these installation paths.

### Install directly from GitHub

This is the simplest option for using Astra. It installs the `astra` and `astra-mcp` commands without placing a checkout in your current folder:

```powershell
python -m pip install "git+https://github.com/nimelkot/astra.git"
```

To upgrade only Astra without reinstalling its already-satisfied dependencies:

```powershell
python -m pip install --upgrade --no-deps "git+https://github.com/nimelkot/astra.git"
```

`--no-deps` is the targeted update option: it updates the Astra package and its `astra`/`astra-mcp` entry points while skipping dependency resolution and downloads. If the command completes but the installed Astra version or entry points do not update, force-reinstall only Astra while still skipping dependency downloads:

```powershell
python -m pip install --force-reinstall --no-deps "git+https://github.com/nimelkot/astra.git"
```

Use the regular upgrade command if Astra's dependency requirements have changed or this is a new environment:

```powershell
python -m pip install --upgrade "git+https://github.com/nimelkot/astra.git"
```

The force-reinstall fallback reinstalls Astra itself but does not reinstall its dependencies because `--no-deps` is still present. Use it only when the targeted upgrade does not replace the installed package correctly.

For an isolated command-line installation, use `pipx`:

```powershell
pipx install "git+https://github.com/nimelkot/astra.git"
```

### Clone for development

Use this option when you want to edit Astra or run its tests. Run the editable install from the cloned repository root, the directory containing `pyproject.toml`:

```powershell
git clone https://github.com/nimelkot/astra.git
cd astra
Get-ChildItem pyproject.toml
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

For a checkout that already has Astra installed in editable mode, the fastest update is to pull the latest source and refresh only when dependencies changed:

```powershell
git pull
python -m pip install -e . --no-deps
```

The editable package points directly at the checkout, so Python code changes are available immediately. Run the install command again only when `pyproject.toml` or dependency versions change.

If `Get-ChildItem pyproject.toml` cannot find the file, you are not in the Astra repository root yet. The folder you want to analyze can be anywhere; it does not need to be inside the Astra checkout.

## Quick start

Index a project first. Replace the example path with the folder you want Astra to analyze:

```powershell
astra index C:\Users\YourName\Downloads\my-project
```

The command recursively scans nested folders for files without importing or executing them. Valid Python files receive AST-level declarations and call relationships. Common source file types (`.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.java`, `.cs`, `.c`, `.cc`, `.cpp`, `.h`, `.hpp`, `.rs`, `.php`, `.swift`, `.kt`, `.kts`, `.rb`, `.dart`, `.scala`, `.pl`, `.r`, `.m`, `.lua`, `.vb`, `.vbs`, `.bas`, `.ps1`, `.sh`, `.bash`, `.zsh`, `.bat`, `.cmd`, `.proto`, `.graphql`, `.gql`) receive structural declaration and call extraction into the same graph format. SQL files (`.sql`) receive table/view/function/procedure/trigger extraction and dependency links from statements such as `FROM` and `JOIN`. Markdown (`.md`, `.markdown`, `.mdx`) gets section-level extraction, HTML/XML gets element-level extraction, JSON/JSONC and YAML/TOML/INI-style configs get key-level extraction, and BSON files are handled safely with optional key extraction when a BSON decoder is available. Other readable files remain searchable as file-level chunks. Binary files, unsupported encodings, files larger than 2 MB, and generated or dependency directories such as `.git`, `.venv`, `node_modules`, and `.astra_vectors` are skipped.

For a complete support matrix, see [docs/supported-file-types.md](docs/supported-file-types.md).

```text
my-project/
├── .astra_graph.json   # structural modules, declarations, and call relationships
└── .astra_vectors/     # local searchable code chunks
```

Run `astra index` again after the source code changes. Indexing replaces the previous graph and chunk index for that target directory.

Astra uses a lightweight hash cache (`.astra_index_cache.json`) so repeated indexing only reparses files whose contents changed. Unchanged files reuse cached structural chunks and references.

## CLI

### Semantic search

Search by a concept, behavior, symbol name, or docstring text:

```powershell
astra search "authentication token validation" --path C:\Users\YourName\Downloads\my-project --limit 8
```

The result table shows the match score, declaration kind, file path, symbol, and source lines. Search results are empty when no indexed chunk shares terms with the query.

### Structural callers

Find functions that call a target function:

```powershell
astra query callers calculate_total --path C:\Users\YourName\Downloads\my-project
```

The `callers` query uses the saved AST graph and reports matching caller nodes as JSON. The current CLI structural query type is `callers`.

### Structural shortest path

Find the shortest relationship path between two symbols:

```powershell
astra path "FastAPI" "ModelField" --path C:\Users\YourName\Downloads\my-project
```

Example output:

```text
FastAPI
fastapi/applications.py:65
↳ DefaultPlaceholder
fastapi/dependencies/models.py:21
↳ get_request_handler()
fastapi/routing.py:310
↳ ModelField
pydantic/fields.py:740

Shortest path (3 hops):
  FastAPI --uses--> DefaultPlaceholder <--references-- get_request_handler() --references--> ModelField
```

<p align="center">
	<img src="docs/astra-path.svg" alt="astra path resolving a call path across the code graph" width="900">
</p>

### Dipper sub-graph scoop

Extract a token-optimized, dependency-complete local sub-graph around a concept or symbol:

```powershell
astra dipper "checkout flow" --path C:\Users\YourName\Downloads\my-project --limit 6 --parent-depth 1 --child-depth 1
```

The command returns JSON with seeds, nodes, edges, and trimmed source snippets for direct LLM prompting.

### Tether structural health sentinel

Run graph-health checks to flag architectural drift risks:

```powershell
astra tether --path C:\Users\YourName\Downloads\my-project --cycle-limit 25 --fanout-threshold 12
```

The report includes cycles, orphan declarations, high fan-out symbols, anomaly summaries, and a pass/warn status.

### Fragility hotspots

Rank functions and classes by graph centrality, AST complexity, and architectural instability:

```powershell
astra fragility --path C:\Users\YourName\Downloads\my-project --limit 10 --threshold 75
```

The matching MCP tool is `astra_get_fragility_hotspots`. See [docs/fragility-hotspots.md](docs/fragility-hotspots.md) for the scoring formula and LLM/CI workflows.

### Star nodes

Rank declarations that act as high-dependency anchors in the knowledge graph:

```powershell
astra star-nodes --path C:\Users\YourName\Downloads\my-project --limit 20 --threshold 60
```

The matching MCP tool is `astra_star_nodes`. Star status combines normalized incoming dependencies and PageRank. In `astra visualize`, star nodes use a star shape and can be isolated with the **Star nodes only** filter.

### Impact and refactor planning

Inspect the upstream blast radius of a declaration:

```powershell
astra impact calculate_total --path C:\Users\YourName\Downloads\my-project
```

Preview a graph-ordered identifier rename without changing files:

```powershell
astra refactor-plan calculate_total sum_total --path C:\Users\YourName\Downloads\my-project
```

The MCP equivalents are `astra_impact` and `astra_refactor_plan`. `astra tether` continues to report orphan declarations and circular dependencies, while `astra visualize` provides the structural anomaly view. See [docs/fragility-hotspots.md](docs/fragility-hotspots.md) for the full CLI/MCP workflow.

### Targeted test workflows

Map declarations to tests, select tests for changed files, generate a scaffold, or run the selected tests:

```powershell
astra test-map --path C:\Users\YourName\Downloads\my-project
astra affected-tests app.py --path C:\Users\YourName\Downloads\my-project
astra test-scaffold calculate_total --path C:\Users\YourName\Downloads\my-project
astra run-impacted app.py --path C:\Users\YourName\Downloads\my-project
```

The MCP equivalents are `astra_test_map`, `astra_affected_tests`, `astra_gen_test_scaffold`, and `astra_run_impacted`. These tools automatically refresh the incremental index. The scaffold is read-only, and test execution is limited to graph-selected test files with a configurable timeout.

### Tether CI gate policy

Recommended policy for pull-request automation:

- **Fail** when new structural cycles are introduced.
- **Warn** when orphan-node count or high-fanout count increases beyond your baseline.
- **Pass** when cycles do not increase and coupling metrics stay within threshold.

A practical CI sequence:

1. Index the repository snapshot for the PR branch.
2. Run `astra tether` and store the JSON output.
3. Compare `summary.cycles`, `summary.orphans`, and `summary.high_fanout` against your `main` baseline.
4. Block merge only for hard-fail conditions (for example, cycle growth).
5. Post warn-level findings as automated PR comments.

Example command:

```powershell
astra index C:\Users\YourName\Downloads\my-project
astra tether --path C:\Users\YourName\Downloads\my-project --cycle-limit 25 --fanout-threshold 12
```

### Search behavior

The default index is deterministic and works offline using local lexical matching. To enable Sentence Transformers and Chroma vector retrieval, set this before indexing and searching:

```powershell
$env:ASTRA_ENABLE_EMBEDDINGS = "1"
astra index C:\Users\YourName\Downloads\my-project
astra search "rate limiting and retries" --path C:\Users\YourName\Downloads\my-project
```

The first embedding-enabled run may download the `all-MiniLM-L6-v2` model. If model access or the vector store is unavailable, Astra falls back to the local search implementation.

### Visualize an index

After indexing, generate a local HTML report for the target folder:

```powershell
astra visualize C:\Users\YourName\Downloads\my-project
```

This writes `.astra_visualization.html` into the target folder. Open that file in a browser to inspect two views:

- **Structural graph**: interactive modules, classes, functions, methods, and definition/call edges from `.astra_graph.json`.
- **Vector chunks**: searchable file and symbol cards from `.astra_vectors/chunks.json`, with expandable source previews.

You can choose a different output path:

```powershell
astra visualize C:\Users\YourName\Downloads\my-project --output C:\Users\YourName\Desktop\astra-report.html
```

The report uses the Vis Network browser library from its CDN for the structural canvas. The vector view and generated data remain local; an internet connection is only needed to load the interactive graph library when opening the report.

### Visualization examples

The structural graph view renders connected modules, declarations, and relationships across the indexed project:

<p align="center">
	<img src="assets/astra_viz_screenshot_2.png" alt="Astra structural graph visualization showing connected code nodes" width="100%">
</p>

The vector chunks view provides searchable cards with file paths, symbols, line ranges, and expandable source previews:

<p align="center">
	<img src="assets/astra_viz_screenshot_1.png" alt="Astra vector chunks visualization showing searchable source cards" width="100%">
</p>

## MCP

Astra also exposes its engine as an official MCP server over stdio. Configure your MCP host to run `astra-mcp`; the server must be installed in the environment used by that host.

The native tools are:

| Tool | Purpose |
| --- | --- |
| `astra_index_repo(path)` | Index a local repository. |
| `astra_semantic_search(path, query, limit)` | Search indexed code chunks. |
| `astra_get_callers(path, target, limit)` | Find callers through the structural graph. |
| `astra_path(path, source, target, max_hops)` | Find the shortest structural path between two symbols. |
| `astra_dipper(path, query, limit, parent_depth, child_depth, max_nodes, max_source_chars)` | Scoop a localized dependency-complete sub-graph for token-efficient LLM context. |
| `astra_tether(path, cycle_limit, fanout_threshold)` | Run structural health checks and return architecture anomaly findings. |
| `astra_get_fragility_hotspots(path, limit, threshold)` | Rank fragile declarations using graph centrality, AST complexity, and instability. |
| `astra_star_nodes(path, limit, threshold)` | Rank high-importance declarations using incoming dependencies and PageRank. |
| `astra_impact(path, target, max_nodes)` | Trace incoming calls and dependencies to report a declaration's blast radius. |
| `astra_refactor_plan(path, target, replacement)` | Preview a graph-ordered, read-only structural identifier rename. |
| `astra_test_map(path, limit)` | Map source declarations to tests that reach them and identify untested nodes. |
| `astra_affected_tests(path, changed_paths, limit)` | Select the minimal test files affected by changed paths. |
| `astra_gen_test_scaffold(path, target)` | Generate a read-only pytest scaffold with dependency hints. |
| `astra_run_impacted(path, changed_paths, timeout)` | Run graph-selected tests with a bounded local pytest process. |
| `astra_hybrid_context(path, query, limit, expansion)` | Combine semantic matches with graph expansion. |
| `astra_visualize(path, output)` | Generate a local HTML graph report and return its file path and URL. |

See [docs/tool-cookbook.md](docs/tool-cookbook.md) for example CLI and MCP calls, representative output, use cases, and recommended agent workflows for every tool.

The repository includes [.vscode/mcp.json](.vscode/mcp.json) for VS Code MCP clients. For other hosts, register the server in the host's configuration:

```toml
[mcp_servers.astra]
command = "astra-mcp"
args = []
```

If the host cannot find commands from your shell, use the absolute executable path: `.venv\Scripts\astra-mcp.exe` on Windows or `.venv/bin/astra-mcp` on macOS/Linux. The server communicates over stdio, so do not redirect its stdout.

The server also sends automatic MCP initialization instructions with the same baseline workflow, so compatible clients can receive Astra guidance without a slash command. MCP clients that expose prompts can additionally select `astra_codebase_workflow` with a local `path` and natural-language `task` for a task-specific sequence. Astra also publishes a companion `<tool>_prompt` for every MCP tool, so each tool has a discoverable slash-command workflow. Prompts guide the agent; they do not execute tools themselves.

### MCP tool orchestration

All analysis and report tools automatically run the incremental index preflight before reading graph or vector artifacts. The hash cache makes unchanged files inexpensive, so an agent can call tools directly after source changes without constructing its own HTML or search index.

For a codebase knowledge-graph visualization, use this sequence:

```text
1. astra_index_repo(path)
2. astra_visualize(path)
```

For investigation before an edit, use `astra_hybrid_context` or `astra_dipper`, then `astra_impact` and `astra_get_fragility_hotspots`. For a rename, call `astra_refactor_plan` first, review its read-only changes and order, apply the approved edit through the host's editing capability, then call `astra_index_repo` and `astra_visualize` again. Agents should use Astra's returned paths, URLs, nodes, snippets, and JSON reports rather than recreating equivalent artifacts.

For a continuously changing workspace, use `astra watch` or the MCP watcher lifecycle tools documented in [docs/tool-cookbook.md](docs/tool-cookbook.md). The watcher is optional; on-demand incremental indexing remains the fallback for short-lived commands and MCP sessions.

## Integrations

### Claude Desktop

Use the server over stdio (`astra-mcp`) and call tools like `astra_dipper` and `astra_tether` from Claude. A complete setup guide is available in [docs/claude-desktop.md](docs/claude-desktop.md).

### Claude CLI

Register Astra with Claude Code from your terminal:

```powershell
claude mcp add --transport stdio astra -- astra-mcp
```

Verify the server with `claude mcp list`, then start Claude Code and ask it to use Astra's MCP tools. If `astra-mcp` is not on your `PATH`, replace it with the absolute path to `.venv\Scripts\astra-mcp.exe` on Windows or `.venv/bin/astra-mcp` on macOS/Linux.

### Gemini CLI

Gemini can consume Astra through any MCP-compatible bridge or local tool host that supports stdio MCP servers. Register `astra-mcp`, then use `astra_dipper` to scoop focused context and `astra_tether` for PR health checks.

Register Astra with Gemini CLI:

```powershell
gemini mcp add astra astra-mcp
```

Verify the server with `gemini mcp list`, then start Gemini CLI and ask it to index or search your project with Astra. If `astra-mcp` is not on your `PATH`, use the absolute executable path as the command instead.

### Codex CLI

Codex CLI can run Astra directly from terminal commands:

```powershell
astra index C:\Users\YourName\Downloads\my-project
astra dipper "payment retry flow" --path C:\Users\YourName\Downloads\my-project
astra tether --path C:\Users\YourName\Downloads\my-project
```

For MCP-based Codex workflows, point your MCP client config to `astra-mcp` and invoke `astra_path`, `astra_dipper`, and `astra_tether` as needed.

## Development

```bash
pytest
ruff check .
```

Astra never imports or executes files it indexes. Parsing failures are skipped and reported only through the resulting counts, which keeps indexing useful for partially broken working trees.

<p align="center">
	<img src="assets/astra-social-preview.png" alt="Astra social preview" width="100%">
</p>
