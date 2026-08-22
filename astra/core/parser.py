from __future__ import annotations

import ast
from pathlib import Path

from .models import CodeChunk

SUPPORTED_SUFFIXES = {".py"}


class CodeParser:
    """Extract Python declarations and references without executing project code."""

    def parse_file(self, path: Path, root: Path) -> tuple[list[CodeChunk], list[dict[str, str]]]:
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError, UnicodeDecodeError):
            return [], []

        relative = path.relative_to(root).as_posix()
        chunks: list[CodeChunk] = []
        references: list[dict[str, str]] = []
        module_id = f"{relative}:module"
        chunks.append(
            CodeChunk(module_id, relative, path.stem, "module", 1, len(source.splitlines()), source)
        )

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "class" if isinstance(node, ast.ClassDef) else "function"
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(
                    isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                    for p in ast.walk(tree)
                    if p is not node and hasattr(p, "body") and node in getattr(p, "body", [])
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
            return [root] if root.suffix in SUPPORTED_SUFFIXES else []
        return sorted(
            p
            for p in root.rglob("*.py")
            if not any(
                part.startswith(".") or part in {"__pycache__", ".venv", "venv"} for part in p.parts
            )
        )
