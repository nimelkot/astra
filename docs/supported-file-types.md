# Supported File Types

Astra indexes project files by reading local file contents. It does not execute imported code or run scripts.

## How file support works

1. Astra discovers files recursively under the target path.
2. It skips hidden, generated, and dependency directories.
3. It attempts to read each file as UTF-8 text.
4. It applies Python AST analysis for valid `.py` files.
5. It indexes other readable files as file-level chunks.

## Fully structured support

- `.py`

Valid Python files get AST-level extraction for:

- modules
- classes
- functions
- methods
- call references
- docstrings and symbol tokens

## General text-file support

Astra also indexes other readable UTF-8 files as searchable file-level chunks, including common:

- source files (for example: `.ts`, `.tsx`, `.js`, `.jsx`, `.java`, `.go`, `.rs`, `.c`, `.cpp`, `.cs`)
- config files (for example: `.json`, `.yaml`, `.yml`, `.toml`, `.ini`)
- markup and docs (for example: `.md`, `.html`, `.xml`, `.css`)
- plain text files (`.txt` and similar)

For these files, Astra stores content for search but does not build language-specific AST call graphs.

## Skipped files and folders

Astra skips files that cannot be safely indexed, including:

- binary files
- files that are not valid UTF-8 text
- files larger than 2 MB
- hidden paths (any path segment starting with `.`)
- dependency or generated directories such as:
  - `.git`
  - `.astra_vectors`
  - `__pycache__`
  - `.venv`
  - `venv`
  - `node_modules`

## Notes

- If the target path is a single file, Astra will attempt to index that file directly.
- Re-running `astra index` on the same path replaces prior index artifacts for that target.
