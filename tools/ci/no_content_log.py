#!/usr/bin/env python3
"""No-content-log check (hard rule 3: never log screenshot content).

Fails when a logging/printing call references a content-bearing name such as
OCR text, image bytes, extracted fields, model output or a request body, and
when `print(` appears anywhere in server/app.

Python files are checked with `ast` (exact call boundaries, docstrings ignored).
TS/JS/Kotlin/Java files are checked with a call-start regex plus parenthesis
balancing, so multi-line calls are covered.

Usage:
    python tools/ci/no_content_log.py            # scan the default roots
    python tools/ci/no_content_log.py PATH ...   # scan given files/dirs
Exit 0 = clean, 1 = findings (printed as path:line: message). Stdlib only.
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_ROOTS = (
    "server/app",
    "apps/mobile/src",
    "apps/mobile/app",
    "apps/mobile/modules",
)
# Any print() in these roots fails, whatever it prints.
PRINT_FORBIDDEN_ROOTS = ("server/app",)

SKIP_DIRS = {
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "build",
    "dist",
    ".expo",
    ".gradle",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
}
# This checker's own deliberately-bad fixtures. Skipped in directory walks unless
# the fixtures directory itself (or a path inside it) is the explicit target.
FIXTURES_DIR = REPO_ROOT / "tools" / "ci" / "tests" / "fixtures"
PY_EXT = {".py"}
CLIKE_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".kt", ".kts", ".java"}

# Content-bearing names. Matched case-insensitively at an identifier start, so
# `ocrText`, `ocr_text`, `OCR_TEXT`, `extractedFields` and `rawTextLines` all hit.
CONTENT_PATTERNS: tuple[tuple[str, str], ...] = (
    ("ocr_text", r"ocr_?text"),
    ("image_bytes", r"image_?bytes"),
    ("image_base64", r"image_?b(ase)?64"),
    ("raw_text", r"raw_?text"),
    ("model_output", r"model_?output"),
    ("extracted", r"extracted"),
    ("fields", r"fields\b"),
    ("request.body", r"(request|req)\s*\.\s*(body|json|form|stream)\b"),
)
_CONTENT_RE = [
    (label, re.compile(r"(?<![A-Za-z0-9])" + pat, re.IGNORECASE)) for label, pat in CONTENT_PATTERNS
]

PY_LOG_METHODS = {
    "debug",
    "info",
    "warning",
    "warn",
    "error",
    "exception",
    "critical",
    "fatal",
    "log",
}

# Start of a logging call in TS/JS/Kotlin/Java. The match ends at the opening paren.
CLIKE_CALL_RE = re.compile(
    r"""(?x)
    (?<![A-Za-z0-9_.])
    (?:
        console\s*\.\s*(?:log|info|warn|error|debug|trace|dir|table)
      | [A-Za-z_]*[Ll]og(?:ger)?\s*\.\s*
        (?:v|d|i|w|e|wtf|log|info|warn|warning|error|debug|trace|fatal)
      | Timber\s*\.\s*(?:v|d|i|w|e|wtf|tag\s*\([^)]*\)\s*\.\s*[a-z]+)
      | (?:Sentry\s*\.\s*)?(?:addBreadcrumb|captureMessage|captureException|setContext|setExtra)
      | System\s*\.\s*(?:out|err)\s*\.\s*print(?:ln|f)?
      | println | print
    )
    \s*\(
    """
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def content_names(text: str) -> list[str]:
    return [label for label, rx in _CONTENT_RE if rx.search(text)]


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _print_forbidden(path: Path) -> bool:
    rel = _rel(path)
    return any(rel == r or rel.startswith(r + "/") for r in PRINT_FORBIDDEN_ROOTS)


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return _dotted(node.value) + "." + node.attr
    if isinstance(node, ast.Call):
        return _dotted(node.func) + "()"
    return ""


def scan_python(path: Path, source: str, forbid_print: bool) -> list[Finding]:
    rel = _rel(path)
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [Finding(rel, exc.lineno or 0, "could not parse file")]
    out: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        kind = ""
        if isinstance(func, ast.Name) and func.id == "print":
            kind = "print()"
            if forbid_print:
                out.append(Finding(rel, node.lineno, "print() is not allowed in server/app"))
                continue
        elif isinstance(func, ast.Attribute) and func.attr in PY_LOG_METHODS:
            base = _dotted(func.value).lower()
            if "log" in base:
                kind = f"{_dotted(func)}()"
        if not kind:
            continue
        segment = ast.get_source_segment(source, node) or ""
        for name in content_names(segment):
            msg = f"{kind} references content-bearing name '{name}'"
            out.append(Finding(rel, node.lineno, msg))
    return out


def _call_extent(text: str, open_idx: int) -> int:
    """Index just past the paren matching text[open_idx] == '(' (naive string skipping)."""
    depth = 0
    i = open_idx
    quote = ""
    while i < len(text):
        ch = text[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = ""
        elif ch in "\"'`":
            quote = ch
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return len(text)


def scan_clike(path: Path, source: str) -> list[Finding]:
    rel = _rel(path)
    out: list[Finding] = []
    for m in CLIKE_CALL_RE.finditer(source):
        start = m.start()
        end = _call_extent(source, m.end() - 1)
        call = source[start:end]
        line = source.count("\n", 0, start) + 1
        head = re.sub(r"\s+", "", m.group(0))[:-1]
        for name in content_names(call[len(m.group(0)) :]):
            out.append(Finding(rel, line, f"{head}() references content-bearing name '{name}'"))
    return out


def scan_file(path: Path) -> list[Finding]:
    ext = path.suffix.lower()
    if ext not in PY_EXT and ext not in CLIKE_EXT:
        return []
    source = path.read_text(encoding="utf-8", errors="replace")
    if ext in PY_EXT:
        return scan_python(path, source, _print_forbidden(path))
    return scan_clike(path, source)


def _under(path: Path, parent: Path) -> bool:
    return path.resolve().is_relative_to(parent.resolve())


def iter_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    skip_fixtures = not _under(target, FIXTURES_DIR)
    files: list[Path] = []
    for p in sorted(target.rglob("*")):
        if not p.is_file() or any(part in SKIP_DIRS for part in p.relative_to(target).parts):
            continue
        if skip_fixtures and _under(p, FIXTURES_DIR):
            continue
        files.append(p)
    return files


def scan(targets: list[Path]) -> list[Finding]:
    findings: list[Finding] = []
    for t in targets:
        if not t.exists():
            continue
        for f in iter_files(t):
            findings.extend(scan_file(f))
    return findings


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    targets = [Path(a) for a in args] if args else [REPO_ROOT / r for r in DEFAULT_ROOTS]
    findings = scan(targets)
    for f in findings:
        print(f)
    if findings:
        print(f"no-content-log: {len(findings)} finding(s). Log enums/counts only (hard rule 3).")
        return 1
    scanned = ", ".join(_rel(t) for t in targets if t.exists()) or "(no roots present)"
    print(f"no-content-log: clean ({scanned})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
