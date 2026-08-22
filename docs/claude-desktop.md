# Use Astra with Claude Desktop

Astra can connect to Claude Desktop as a local Model Context Protocol (MCP) server. Claude can then use Astra to index and query Python code on the same computer.

## Requirements

- Claude Desktop with MCP server support
- Python 3.10 or newer
- Access to a local Python project you want to analyze

Astra communicates with Claude Desktop over stdio. The code being analyzed stays on the local computer; Astra does not upload it to a hosted service.

## Install Astra

Install the latest committed version directly from GitHub:

```powershell
python -m pip install "git+https://github.com/nimelkot/astra.git"
```

Confirm that the MCP command is available:

```powershell
Get-Command astra-mcp
```

The command should resolve to an executable installed in your Python environment.

### Virtual environment installation

If Astra is installed in a virtual environment, use the full executable path in Claude Desktop's configuration. For example:

```powershell
C:\Users\YourName\Downloads\astra\.venv\Scripts\astra-mcp.exe
```

Using an absolute path is often more reliable because Claude Desktop may not inherit the same `PATH` as PowerShell.

## Configure Claude Desktop

Open Claude Desktop's configuration file:

```text
%APPDATA%\Claude\claude_desktop_config.json
```

Add Astra under the `mcpServers` object:

```json
{
  "mcpServers": {
    "astra": {
      "command": "astra-mcp",
      "args": []
    }
  }
}
```

If you installed Astra inside a virtual environment, use the executable path instead:

```json
{
  "mcpServers": {
    "astra": {
      "command": "C:\\Users\\YourName\\Downloads\\astra\\.venv\\Scripts\\astra-mcp.exe",
      "args": []
    }
  }
}
```

If the configuration file already contains other MCP servers, add the `astra` entry inside the existing `mcpServers` object. Do not replace the other server entries.

Restart Claude Desktop after saving the configuration. MCP servers are normally discovered when Claude Desktop starts.

## Use Astra from Claude

The target project must be local to the computer running Claude Desktop. Ask Claude to index it first:

```text
Use Astra to index C:\Users\YourName\Downloads\my-project.
```

Claude can then call Astra's tools:

| Tool | Use |
| --- | --- |
| `astra_index_repo` | Index or re-index a local Python project. |
| `astra_semantic_search` | Find code related to a concept or behavior. |
| `astra_get_callers` | Find functions that call a target function. |
| `astra_hybrid_context` | Combine semantic matches with structural graph expansion. |

Example prompts:

```text
Use Astra to find where authentication tokens are validated.
```

```text
Use Astra to find every caller of calculate_total in C:\Users\YourName\Downloads\my-project.
```

```text
Use Astra's hybrid context to explain the retry flow in this project.
```

## Generated files

When indexing a project, Astra writes these files inside the target directory:

```text
my-project/
├── .astra_graph.json
└── .astra_vectors/
```

`.astra_graph.json` contains the structural graph. `.astra_vectors/` contains the local searchable code-chunk index. Both are generated artifacts and are ignored by Git when using Astra's repository configuration.

Run `astra_index_repo` again after source files change so Claude has current context.

## Embedding search

Astra works by default with a deterministic local lexical search that does not require model downloads. To enable Sentence Transformers and Chroma vector retrieval, set the environment variable before starting Claude Desktop:

```powershell
$env:ASTRA_ENABLE_EMBEDDINGS = "1"
```

Then start Claude Desktop from that same PowerShell session, or configure the environment variable using your operating system's environment settings. The first embedding-enabled index may download the `all-MiniLM-L6-v2` model.

If model access or the vector store is unavailable, Astra falls back to its local search implementation.

## Troubleshooting

### Astra does not appear in Claude Desktop

- Confirm that Claude Desktop was restarted after editing `claude_desktop_config.json`.
- Run `Get-Command astra-mcp` in PowerShell.
- Replace `"astra-mcp"` with the absolute path to `.venv\\Scripts\\astra-mcp.exe`.
- Check that the JSON is valid and that `mcpServers` contains no duplicate `astra` keys.

### Claude cannot index the project

- Use an absolute Windows path to the project directory.
- Confirm that the directory exists and contains Python files.
- Ask Claude to run `astra_index_repo` before asking for search results.
- Re-index after changing the project source.

### Search returns no results

- Confirm that indexing completed successfully.
- Use terms that occur in symbol names, docstrings, or source code.
- Try the local fallback first by leaving `ASTRA_ENABLE_EMBEDDINGS` unset.
- Check that the query's `path` is the same directory that was indexed.

## Security and privacy

Astra parses files without importing or executing the indexed project. The MCP server runs locally and receives filesystem paths from Claude Desktop, so only connect it to projects you trust Claude Desktop to access.
