# Supported File Types

Astra indexes project files by reading local file contents. It does not execute imported code or run scripts.

## Support Matrix

| Supported | Category | Extensions | Extraction style | Notes |
| --- | --- | --- | --- | --- |
| ✅ | Full Python AST | `.py` | Module, class, function, method, calls, docstrings, symbols | Native Python AST parsing |
| ✅ | Structured source parsing | `.js`, `.jsx`, `.ts`, `.tsx`, `.go`, `.java`, `.cs`, `.c`, `.cc`, `.cpp`, `.h`, `.hpp`, `.rs`, `.php`, `.swift`, `.kt`, `.kts`, `.rb`, `.dart`, `.scala`, `.pl`, `.r`, `.m`, `.lua`, `.vb`, `.vbs`, `.bas`, `.ps1`, `.sh`, `.bash`, `.zsh`, `.bat`, `.cmd`, `.proto`, `.graphql`, `.gql` | Module/function/class chunks and call references | Language-aware pattern extraction |
| ✅ | Structured SQL parsing | `.sql` | Table/view/function/procedure/trigger chunks and dependency links | Captures `FROM`, `JOIN`, `UPDATE`, `INTO`, `CALL`, `EXEC`/`EXECUTE` references |
| ✅ | Structured docs and markup | `.md`, `.markdown`, `.mdx`, `.html`, `.htm`, `.xml` | Markdown section chunks and links; HTML/XML element chunks | Uses heading, link, tag, `id`, and `name` signals |
| ✅ | Structured data/config parsing | `.json`, `.jsonc`, `.yaml`, `.yml`, `.toml`, `.ini`, `.cfg`, `.conf`, `.env` | Key-path/key chunks | Nested JSON keys are flattened into searchable paths |
| ✅ | BSON handling | `.bson` | Safe file-level chunk; optional key extraction | Key extraction is enabled when a compatible BSON decoder is installed |
| ✅ | General file-level indexing | Other readable UTF-8 files | File-level searchable chunk | No language-specific declaration/call graph |

## How file support works

1. Astra discovers files recursively under the target path.
2. It skips hidden, generated, and dependency directories.
3. It attempts to read each file as UTF-8 text (or BSON binary when applicable).
4. It applies language-specific structural parsing when available.
5. It indexes remaining readable files as file-level chunks.

## Skipped files and folders

- Binary files (except `.bson` handled by the BSON flow)
- Files that are not valid UTF-8 text
- Files larger than 2 MB
- Hidden paths (any path segment starting with `.`)
- Dependency or generated directories such as `.git`, `.astra_vectors`, `__pycache__`, `.venv`, `venv`, and `node_modules`

## Notes

- If the target path is a single file, Astra attempts to index that file directly.
- Re-running `astra index` on the same path replaces prior index artifacts for that target.
