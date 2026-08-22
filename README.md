<p align="center">
	<img src="assets/astra-social-banner.png" alt="Astra: local code intelligence for AI agents" width="100%">
</p>

Astra is a local code intelligence service for AI agents. It parses Python code into a structural NetworkX graph and a searchable local code-chunk index. The same engine is available through the `astra` CLI and the official MCP Python SDK.

## Architecture

The constellation mark represents the relationships Astra discovers across a codebase. Its pipeline has four stages: parse Python files without executing them, build the structural graph, index code chunks, and retrieve semantic matches with graph expansion.

| Component | Role | Output |
| --- | --- | --- |
| AST parser | Reads Python declarations, docstrings, symbols, and calls without executing project code. | Code chunks and references |
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

## Brand Assets

The canonical brand kit is included for repository pages, documentation, and integrations:

The canonical brand assets are available as the [light icon](assets/astra-icon-light.png), [dark icon](assets/astra-icon-dark.png), [light logo](assets/astra-logo-light.png), [dark logo](assets/astra-logo-dark.png), [compact lockup](assets/astra-logo-compact.png), and [tagline lockup](assets/astra-wordmark-tagline.png). The [wide social banner](assets/astra-social-banner.png) is used at the top of this README.

## Install

Python 3.10+ is required.

Clone the repository and change into its root directory. The install command must be run from the directory that contains `pyproject.toml`:

```bash
git clone https://github.com/nimelkot/astra.git
cd astra
```

On Windows PowerShell, verify that you are in the correct directory before installing:

```powershell
Get-ChildItem pyproject.toml
```

If that command reports that the file is missing, use `cd` to enter the cloned `astra` directory first. Do not run `pip install -e ".[dev]"` from `Downloads`, a parent folder, or a separate test folder.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

The first indexing run may download the Sentence Transformers model when the optional Chroma path is available. Astra still works without model access using its deterministic local lexical fallback.

### Install directly from GitHub

Users who only need the `astra` and `astra-mcp` commands can install the latest committed version directly from GitHub without cloning the repository:

```powershell
python -m pip install "git+https://github.com/nimelkot/astra.git"
```

For an isolated command-line installation, use `pipx`:

```powershell
pipx install "git+https://github.com/nimelkot/astra.git"
```

Use the clone-and-editable setup above when developing Astra or running its tests locally.

## CLI

```bash
astra index .
astra search "authentication token validation" --path . --limit 8
astra query callers calculate_total --path .
```

Index artifacts are written inside the target directory: `.astra_graph.json` and `.astra_vectors/`. They are ignored by Git by default.

## MCP

The package exposes an stdio MCP server with four native tools:

- `astra_index_repo(path)` indexes a repository.
- `astra_semantic_search(path, query, limit)` searches code chunks.
- `astra_get_callers(path, target, limit)` resolves graph callers.
- `astra_hybrid_context(path, query, limit, expansion)` combines semantic matches and structural expansion.

The repository includes [.vscode/mcp.json](.vscode/mcp.json) for VS Code MCP clients. For other hosts, register the installed command in the host's server configuration:

```toml
# Example shape for hosts using TOML server configuration
[mcp_servers.astra]
command = "astra-mcp"
args = []
```

For a host that requires an explicit Python interpreter, use the absolute path to `.venv/Scripts/astra-mcp.exe` on Windows or `.venv/bin/astra-mcp` on macOS/Linux. The server communicates over stdio, so do not redirect its stdout.

## Development

```bash
pytest
ruff check .
```

Astra never imports or executes files it indexes. Parsing failures are skipped and reported only through the resulting counts, which keeps indexing useful for partially broken working trees.

<p align="center">
	<img src="assets/astra-social-preview.png" alt="Astra social preview" width="100%">
</p>
