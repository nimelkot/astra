<p align="center">
	<img src="assets/astra-logo.svg" alt="astra logo" width="246">
</p>

<p align="center">Local code intelligence for AI agents.</p>

# Astra

Astra is a local code intelligence service for AI agents. It parses Python code into a structural NetworkX graph and a searchable local code-chunk index. The same engine is available through the `astra` CLI and the official MCP Python SDK.

## Components

The repository uses a compact constellation mark to represent the relationships Astra discovers across a codebase. The supplied brand assets are available as [the icon](assets/astra-icon.svg) and [the lowercase logo lockup](assets/astra-logo.svg).

| Component | Role | Output |
| --- | --- | --- |
| AST parser | Reads Python declarations, docstrings, symbols, and calls without executing project code. | Code chunks and references |
| Structural graph | Builds directed NetworkX relationships between modules, declarations, and callers. | `.astra_graph.json` |
| Vector index | Stores searchable chunks locally, with optional Sentence Transformers and Chroma acceleration. | `.astra_vectors/` |
| Dual interfaces | Makes the same engine available to terminal users and MCP hosts. | `astra` and `astra-mcp` |

The MCP surface exposes four tools: `astra_index_repo`, `astra_semantic_search`, `astra_get_callers`, and `astra_hybrid_context`.

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
