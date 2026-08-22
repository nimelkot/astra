<p align="center">
	<img src="assets/astra-social-banner.png" alt="Astra: local code intelligence for AI agents" width="100%">
</p>

Astra is a local code intelligence service for AI agents. It parses Python code into a structural NetworkX graph and a searchable local code-chunk index. The same engine is available through the `astra` CLI and the official MCP Python SDK.

## Architecture

The constellation mark represents the relationships Astra discovers across a codebase. Its pipeline has four stages: parse Python files without executing them, build the structural graph, index code chunks, and retrieve semantic matches with graph expansion.

| Component | Role | Output |
| --- | --- | --- |
| AST and text parser | Reads Python declarations, docstrings, symbols, and calls; indexes other UTF-8 text files as file-level chunks. | Code chunks and references |
| Structural graph | Builds directed NetworkX relationships between modules, declarations, and callers. | `.astra_graph.json` |
| Vector index | Stores searchable chunks locally, with optional Sentence Transformers and Chroma acceleration. | `.astra_vectors/` |
| Dual interfaces | Makes the same engine available to terminal users and MCP hosts. | `astra` and `astra-mcp` |

The MCP surface exposes four tools: `astra_index_repo`, `astra_semantic_search`, `astra_get_callers`, and `astra_hybrid_context`.

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

If `Get-ChildItem pyproject.toml` cannot find the file, you are not in the Astra repository root yet. The folder you want to analyze can be anywhere; it does not need to be inside the Astra checkout.

## Quick start

Index a project first. Replace the example path with the folder you want Astra to analyze:

```powershell
astra index C:\Users\YourName\Downloads\my-project
```

The command recursively scans nested folders for UTF-8 text files without importing or executing them. Valid Python files receive AST-level declarations and call relationships; other text-based source, configuration, markup, and documentation files receive searchable file-level chunks. Binary files, files larger than 2 MB, and generated or dependency directories such as `.git`, `.venv`, `node_modules`, and `.astra_vectors` are skipped.
| AST and text parser | Reads Python declarations, docstrings, symbols, and calls; indexes other UTF-8 text files as file-level chunks. | Code chunks and references |

```text
my-project/
├── .astra_graph.json   # structural modules, declarations, and call relationships
└── .astra_vectors/     # local searchable code chunks
```

Run `astra index` again after the source code changes. Indexing replaces the previous graph and chunk index for that target directory.

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

## MCP

Astra also exposes its engine as an official MCP server over stdio. Configure your MCP host to run `astra-mcp`; the server must be installed in the environment used by that host.

The four native tools are:

| Tool | Purpose |
| --- | --- |
| `astra_index_repo(path)` | Index a local Python repository. |
| `astra_semantic_search(path, query, limit)` | Search indexed code chunks. |
| `astra_get_callers(path, target, limit)` | Find callers through the structural graph. |
| `astra_hybrid_context(path, query, limit, expansion)` | Combine semantic matches with graph expansion. |

The repository includes [.vscode/mcp.json](.vscode/mcp.json) for VS Code MCP clients. For other hosts, register the server in the host's configuration:

```toml
[mcp_servers.astra]
command = "astra-mcp"
args = []
```

If the host cannot find commands from your shell, use the absolute executable path: `.venv\Scripts\astra-mcp.exe` on Windows or `.venv/bin/astra-mcp` on macOS/Linux. The server communicates over stdio, so do not redirect its stdout.

## Development

```bash
pytest
ruff check .
```

Astra never imports or executes files it indexes. Parsing failures are skipped and reported only through the resulting counts, which keeps indexing useful for partially broken working trees.

<p align="center">
	<img src="assets/astra-social-preview.png" alt="Astra social preview" width="100%">
</p>
