from __future__ import annotations

import ast
from pathlib import Path

from .models import CodeChunk

MAX_TEXT_FILE_SIZE = 2 * 1024 * 1024
EXCLUDED_DIRS = {".git", ".astra_vectors", "__pycache__", ".venv", "venv", "node_modules"}


class CodeParser:
    """Extract Python declarations and references without executing project code."""

    def parse_file(self, path: Path, root: Path) -> tuple[list[CodeChunk], list[dict[str, str]]]:
        try:
            if path.stat().st_size > MAX_TEXT_FILE_SIZE:
                return [], []
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return [], []

        relative = path.relative_to(root).as_posix()
        chunks: list[CodeChunk] = []
        references: list[dict[str, str]] = []
        tree = None
        if path.suffix.lower() == ".py":
            try:
                tree = ast.parse(source, filename=str(path))
            except SyntaxError:
                return [], []
        module_id = f"{relative}:module"
        chunks.append(
            CodeChunk(module_id, relative, path.stem, "module", 1, len(source.splitlines()), source)
        )

        if tree is None:
            return chunks, references

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "class" if isinstance(node, ast.ClassDef) else "function"
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                    isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    for p in ast.walk(tree)
                    if p is not node
                    and isinstance(getattr(p, "body", None), list)
                    and node in p.body
                ):
                    kind = "method"
                start = getattr(node, "lineno", 1)
                end = getattr(node, "end_lineno", start)
                lines = source.splitlines()
                body = "\n".join(lines[start - 1 : end])
                name = node.name
                chunk_id = f"{relative}:{start}:{name}"
                symbols = sorted({n.id for n in ast.walk(node) if isinstance(n, ast.Name)})
                chunks.append(
                    CodeChunk(
                        chunk_id,
                        relative,
                        name,
                        kind,
                        start,
                        end,
                        body,
                        ast.get_docstring(node) or "",
                        symbols,
                    )
                )
                for call in ast.walk(node):
                    if isinstance(call, ast.Call):
                        target = (
                            call.func.id
                            if isinstance(call.func, ast.Name)
                            else call.func.attr
                            if isinstance(call.func, ast.Attribute)
                            else None
                        )
                        if target:
                            references.append(
                                {"source": chunk_id, "target": target, "kind": "calls"}
                            )

        return chunks, references

    def discover(self, target: str | Path) -> list[Path]:
        root = Path(target).resolve()
        if root.is_file():
            return [root]
        return sorted(
            p
            for p in root.rglob("*")
            if p.is_file()
            and not any(
                part.startswith(".") or part in EXCLUDED_DIRS
                for part in p.relative_to(root).parts
            )
        )
