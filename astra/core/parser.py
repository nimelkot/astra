from __future__ import annotations

import ast
import json
import re
from pathlib import Path

from .models import CodeChunk

MAX_TEXT_FILE_SIZE = 2 * 1024 * 1024
EXCLUDED_DIRS = {".git", ".astra_vectors", "__pycache__", ".venv", "venv", "node_modules"}
STRUCTURED_SUFFIXES = {
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".java",
    ".cs",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".rs",
    ".php",
    ".swift",
    ".kt",
    ".kts",
    ".rb",
    ".dart",
    ".scala",
    ".pl",
    ".r",
    ".m",
    ".lua",
    ".vb",
    ".vbs",
    ".bas",
    ".ps1",
    ".sh",
    ".bash",
    ".zsh",
    ".bat",
    ".cmd",
    ".proto",
    ".graphql",
    ".gql",
}
SQL_SUFFIXES = {".sql"}
MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdx"}
MARKUP_SUFFIXES = {".html", ".htm", ".xml"}
JSON_SUFFIXES = {".json", ".jsonc"}
KEY_VALUE_SUFFIXES = {".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env"}
BSON_SUFFIXES = {".bson"}

IDENTIFIER_RE = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")
CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
MARKDOWN_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
TAG_RE = re.compile(r"<([A-Za-z][A-Za-z0-9:_-]*)([^>]*)>")
ATTR_RE = re.compile(r"\b(id|name)\s*=\s*['\"]([^'\"]+)['\"]")
KEY_VALUE_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_.-]*)\s*[:=]")
SQL_DECL_RE = re.compile(
    r"^\s*CREATE\s+(?:OR\s+REPLACE\s+)?(?:TEMP\s+|TEMPORARY\s+)?"
    r"(TABLE|VIEW|FUNCTION|PROCEDURE|TRIGGER)\s+(?:IF\s+NOT\s+EXISTS\s+)?"
    r"([A-Za-z_][A-Za-z0-9_$.]*)",
    flags=re.IGNORECASE,
)
SQL_REF_RE = re.compile(
    r"\b(?:FROM|JOIN|UPDATE|INTO|CALL|EXEC(?:UTE)?)\s+([A-Za-z_][A-Za-z0-9_$.]*)",
    flags=re.IGNORECASE,
)

CLASS_PATTERNS = [
    re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)\b"),
    re.compile(r"^\s*(?:export\s+)?interface\s+([A-Za-z_][A-Za-z0-9_]*)\b"),
    re.compile(r"^\s*type\s+([A-Za-z_][A-Za-z0-9_]*)\s+struct\b"),
    re.compile(r"^\s*struct\s+([A-Za-z_][A-Za-z0-9_]*)\b"),
]

FUNCTION_PATTERNS = [
    re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("),
    re.compile(
        r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"
    ),
    re.compile(
        r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*function\b"
    ),
    re.compile(r"^\s*func\s+(?:\([^)]+\)\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*\("),
    re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_!?=]*)\b"),
    re.compile(r"^\s*sub\s+([A-Za-z_][A-Za-z0-9_]*)\b"),
    re.compile(
        r"^\s*(?:public|private|protected|friend)?\s*(?:sub|function)\s+([A-Za-z_][A-Za-z0-9_]*)\b",
        flags=re.IGNORECASE,
    ),
    re.compile(
        r"^\s*function\s+(?:\[[^\]]+\]\s*=\s*|[A-Za-z_][A-Za-z0-9_]*\s*=\s*)?([A-Za-z_][A-Za-z0-9_]*)\s*\("
    ),
    re.compile(r"^\s*function\s+([A-Za-z_][A-Za-z0-9_-]*)\b"),
    re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_-]*)\s*\(\s*\)\s*\{"),
    re.compile(
        r"^\s*(?:public|private|protected|internal|static|final|virtual|override|abstract|sealed|async|inline|constexpr|friend|extern|unsafe|\s)+[A-Za-z_][A-Za-z0-9_:<>,\[\]\*&\s]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;{}]*\)\s*\{"
    ),
]

CALL_EXCLUDE = {
    "if",
    "for",
    "while",
    "switch",
    "catch",
    "return",
    "new",
    "sizeof",
    "typeof",
    "function",
    "class",
}


class CodeParser:
    """Extract structural declarations and references without executing project code."""

    def parse_file(self, path: Path, root: Path) -> tuple[list[CodeChunk], list[dict[str, str]]]:
        try:
            if path.stat().st_size > MAX_TEXT_FILE_SIZE:
                return [], []
        except OSError:
            return [], []

        relative = path.relative_to(root).as_posix()
        suffix = path.suffix.lower()

        if suffix in BSON_SUFFIXES:
            return self._parse_bson_file(path, relative)

        try:
            source = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return [], []

        lines = source.splitlines()

        if suffix == ".py":
            return self._parse_python(path, relative, source, lines)

        chunks = [self._module_chunk(relative, path.stem, lines, source)]
        references: list[dict[str, str]] = []

        if suffix in STRUCTURED_SUFFIXES:
            extra_chunks, extra_refs = self._parse_structured_file(relative, lines)
            chunks.extend(extra_chunks)
            references.extend(extra_refs)
        elif suffix in MARKDOWN_SUFFIXES:
            extra_chunks, extra_refs = self._parse_markdown(relative, lines)
            chunks.extend(extra_chunks)
            references.extend(extra_refs)
        elif suffix in MARKUP_SUFFIXES:
            extra_chunks = self._parse_markup(relative, lines)
            chunks.extend(extra_chunks)
        elif suffix in JSON_SUFFIXES:
            extra_chunks = self._parse_json(relative, lines)
            chunks.extend(extra_chunks)
        elif suffix in KEY_VALUE_SUFFIXES:
            extra_chunks = self._parse_key_values(relative, lines)
            chunks.extend(extra_chunks)
        elif suffix in SQL_SUFFIXES:
            extra_chunks, extra_refs = self._parse_sql(relative, lines)
            chunks.extend(extra_chunks)
            references.extend(extra_refs)

        return chunks, references

    def _module_chunk(self, relative: str, stem: str, lines: list[str], source: str) -> CodeChunk:
        return CodeChunk(f"{relative}:module", relative, stem, "module", 1, len(lines), source)

    def _parse_python(
        self, path: Path, relative: str, source: str, lines: list[str]
    ) -> tuple[list[CodeChunk], list[dict[str, str]]]:
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            return [], []

        chunks = [self._module_chunk(relative, path.stem, lines, source)]
        references: list[dict[str, str]] = []

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

    def _parse_structured_file(
        self, relative: str, lines: list[str]
    ) -> tuple[list[CodeChunk], list[dict[str, str]]]:
        chunks: list[CodeChunk] = []
        references: list[dict[str, str]] = []

        for index, line in enumerate(lines):
            declaration = self._match_declaration(line)
            if declaration is None:
                continue
            kind, name = declaration
            start = index + 1
            end = self._estimate_block_end(lines, index)
            body = "\n".join(lines[start - 1 : end])
            chunk_id = f"{relative}:{start}:{name}"
            symbols = sorted(set(IDENTIFIER_RE.findall(body)))
            chunks.append(CodeChunk(chunk_id, relative, name, kind, start, end, body, "", symbols))
            for target in self._extract_calls(body):
                if target != name:
                    references.append({"source": chunk_id, "target": target, "kind": "calls"})

        return chunks, references

    def _match_declaration(self, line: str) -> tuple[str, str] | None:
        for pattern in CLASS_PATTERNS:
            match = pattern.match(line)
            if match:
                return "class", match.group(1)
        for pattern in FUNCTION_PATTERNS:
            match = pattern.match(line)
            if match:
                return "function", match.group(1)
        return None

    def _estimate_block_end(self, lines: list[str], start_index: int) -> int:
        brace_balance = 0
        saw_open_brace = False
        for index in range(start_index, len(lines)):
            line = lines[index]
            opens = line.count("{")
            closes = line.count("}")
            if opens:
                saw_open_brace = True
            brace_balance += opens - closes
            if saw_open_brace and brace_balance <= 0:
                return index + 1
            if not saw_open_brace and line.strip().endswith(";"):
                return index + 1
        return start_index + 1

    def _extract_calls(self, source: str) -> list[str]:
        names: list[str] = []
        for match in CALL_RE.finditer(source):
            target = match.group(1)
            if target not in CALL_EXCLUDE:
                names.append(target)
        return names

    def _parse_markdown(
        self, relative: str, lines: list[str]
    ) -> tuple[list[CodeChunk], list[dict[str, str]]]:
        chunks: list[CodeChunk] = []
        references: list[dict[str, str]] = []
        headings: list[tuple[int, int, str]] = []
        for index, line in enumerate(lines):
            match = MARKDOWN_HEADING_RE.match(line)
            if match:
                title = match.group(2).strip()
                level = len(match.group(1))
                headings.append((index + 1, level, title))

        if not headings:
            return chunks, references

        for i, (start_line, _level, title) in enumerate(headings):
            end_line = headings[i + 1][0] - 1 if i + 1 < len(headings) else len(lines)
            body = "\n".join(lines[start_line - 1 : end_line])
            chunk_id = f"{relative}:{start_line}:{title}"
            symbols = sorted(set(IDENTIFIER_RE.findall(body)))
            chunks.append(
                CodeChunk(
                    chunk_id,
                    relative,
                    title,
                    "section",
                    start_line,
                    end_line,
                    body,
                    "",
                    symbols,
                )
            )
            for link in MARKDOWN_LINK_RE.findall(body):
                target = link.lstrip("#").split("/")[-1].split(".")[0]
                if target:
                    references.append({"source": chunk_id, "target": target, "kind": "depends_on"})

        return chunks, references

    def _parse_markup(self, relative: str, lines: list[str]) -> list[CodeChunk]:
        chunks: list[CodeChunk] = []
        for index, line in enumerate(lines):
            for match in TAG_RE.finditer(line):
                tag = match.group(1).lower()
                if tag.startswith("/") or tag.startswith("!"):
                    continue
                attrs = match.group(2)
                attr_match = ATTR_RE.search(attrs)
                name = attr_match.group(2) if attr_match else tag
                start = index + 1
                body = line.strip()
                chunk_id = f"{relative}:{start}:{name}"
                symbols = sorted(set(IDENTIFIER_RE.findall(body)))
                chunks.append(
                    CodeChunk(chunk_id, relative, name, "element", start, start, body, "", symbols)
                )
        return chunks

    def _parse_json(self, relative: str, lines: list[str]) -> list[CodeChunk]:
        source = "\n".join(lines)
        try:
            payload = json.loads(self._strip_json_comments(source))
        except json.JSONDecodeError:
            return []

        chunks: list[CodeChunk] = []
        for key_path, value in self._flatten_json(payload):
            token = f'"{key_path.split(".")[-1]}"'
            line = self._find_line(lines, token)
            rendered = self._render_value(value)
            chunk_id = f"{relative}:{line}:{key_path}"
            symbols = sorted(set(IDENTIFIER_RE.findall(f"{key_path} {rendered}")))
            chunks.append(
                CodeChunk(chunk_id, relative, key_path, "key", line, line, rendered, "", symbols)
            )
        return chunks

    def _parse_key_values(self, relative: str, lines: list[str]) -> list[CodeChunk]:
        chunks: list[CodeChunk] = []
        for index, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or stripped.startswith(";"):
                continue
            match = KEY_VALUE_RE.match(line)
            if not match:
                continue
            key = match.group(1)
            chunk_id = f"{relative}:{index + 1}:{key}"
            symbols = sorted(set(IDENTIFIER_RE.findall(line)))
            chunks.append(
                CodeChunk(
                    chunk_id,
                    relative,
                    key,
                    "key",
                    index + 1,
                    index + 1,
                    line.strip(),
                    "",
                    symbols,
                )
            )
        return chunks

    def _parse_bson_file(
        self, path: Path, relative: str
    ) -> tuple[list[CodeChunk], list[dict[str, str]]]:
        try:
            raw = path.read_bytes()
        except OSError:
            return [], []

        fallback = "Binary BSON content (decoded when bson library is available)."
        chunks: list[CodeChunk] = [
            CodeChunk(f"{relative}:module", relative, path.stem, "module", 1, 1, fallback)
        ]

        try:
            from bson import BSON  # type: ignore
        except Exception:
            return chunks, []

        try:
            payload = BSON(raw).decode()
        except Exception:
            return chunks, []

        for key_path, value in self._flatten_json(payload):
            rendered = self._render_value(value)
            chunk_id = f"{relative}:1:{key_path}"
            symbols = sorted(set(IDENTIFIER_RE.findall(f"{key_path} {rendered}")))
            chunks.append(
                CodeChunk(chunk_id, relative, key_path, "key", 1, 1, rendered, "", symbols)
            )
        return chunks, []

    def _parse_sql(
        self, relative: str, lines: list[str]
    ) -> tuple[list[CodeChunk], list[dict[str, str]]]:
        chunks: list[CodeChunk] = []
        references: list[dict[str, str]] = []
        for index, line in enumerate(lines):
            decl = SQL_DECL_RE.match(line)
            if decl is None:
                continue
            kind_token, raw_name = decl.groups()
            kind = kind_token.lower()
            name = raw_name.split(".")[-1]
            start = index + 1
            end = self._estimate_sql_end(lines, index)
            body = "\n".join(lines[start - 1 : end])
            chunk_id = f"{relative}:{start}:{name}"
            symbols = sorted(set(IDENTIFIER_RE.findall(body)))
            chunks.append(CodeChunk(chunk_id, relative, name, kind, start, end, body, "", symbols))
            for target in SQL_REF_RE.findall(body):
                target_name = target.split(".")[-1]
                if target_name != name:
                    references.append(
                        {"source": chunk_id, "target": target_name, "kind": "depends_on"}
                    )
        return chunks, references

    def _estimate_sql_end(self, lines: list[str], start_index: int) -> int:
        for index in range(start_index, len(lines)):
            if ";" in lines[index]:
                return index + 1
        return len(lines)

    def _strip_json_comments(self, source: str) -> str:
        source = re.sub(r"//.*$", "", source, flags=re.MULTILINE)
        source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
        return source

    def _flatten_json(self, payload: object, prefix: str = "") -> list[tuple[str, object]]:
        items: list[tuple[str, object]] = []
        if isinstance(payload, dict):
            for key, value in payload.items():
                path = f"{prefix}.{key}" if prefix else str(key)
                items.append((path, value))
                items.extend(self._flatten_json(value, path))
        elif isinstance(payload, list):
            for index, value in enumerate(payload):
                path = f"{prefix}[{index}]"
                items.append((path, value))
                items.extend(self._flatten_json(value, path))
        return items

    def _render_value(self, value: object) -> str:
        if isinstance(value, (dict, list)):
            text = json.dumps(value, ensure_ascii=True)
        else:
            text = str(value)
        return text[:600]

    def _find_line(self, lines: list[str], token: str) -> int:
        for index, line in enumerate(lines):
            if token in line:
                return index + 1
        return 1

    def discover(self, target: str | Path) -> list[Path]:
        root = Path(target).resolve()
        if root.is_file():
            return [root]
        return sorted(
            p
            for p in root.rglob("*")
            if p.is_file()
            and not any(
                part.startswith(".") or part in EXCLUDED_DIRS for part in p.relative_to(root).parts
            )
        )
