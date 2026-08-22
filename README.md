<p align="center">
	<img src="assets/astra-logo-dark.png" alt="astra logo" width="325">
</p>

<p align="center">Local code intelligence for AI agents.</p>

# Astra

Astra is a local code intelligence service for AI agents. It parses Python code into a structural NetworkX graph and a searchable local code-chunk index. The same engine is available through the `astra` CLI and the official MCP Python SDK.

## Components

The repository uses a constellation mark to represent the relationships Astra discovers across a codebase. The canonical brand assets are available as [the light icon](assets/astra-icon-light.png), [the dark icon](assets/astra-icon-dark.png), [the light logo](assets/astra-logo-light.png), and [the dark logo](assets/astra-logo-dark.png). The [social preview](assets/astra-social-preview.png) is the 2:1 repository cover, and the [wide social banner](assets/astra-social-banner.png) is available for other sharing contexts.

| Component | Role | Output |
| --- | --- | --- |
| AST parser | Reads Python declarations, docstrings, symbols, and calls without executing project code. | Code chunks and references |
| Structural graph | Builds directed NetworkX relationships between modules, declarations, and callers. | `.astra_graph.json` |
| Vector index | Stores searchable chunks locally, with optional Sentence Transformers and Chroma acceleration. | `.astra_vectors/` |
| Dual interfaces | Makes the same engine available to terminal users and MCP hosts. | `astra` and `astra-mcp` |

The MCP surface exposes four tools: `astra_index_repo`, `astra_semantic_search`, `astra_get_callers`, and `astra_hybrid_context`.

![Astra indexing pipeline](assets/astra-pipeline.png)

The system moves through four stages: parse Python files without executing them, build the structural graph, index code chunks, and retrieve semantic matches with graph expansion. The [component map](assets/astra-components.png) shows how the CLI and MCP host connect to the shared engine and its on-disk artifacts.

## Install

Python 3.10+ is required.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

The first indexing run may download the Sentence Transformers model when the optional Chroma path is available. Astra still works without model access using its deterministic local lexical fallback.

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
