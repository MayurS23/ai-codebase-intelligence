"""
generic_parser.py — Regex-based parser for JS/TS/Java/Go/Rust/Ruby/PHP/C#.
FIX: safety limit on _extract_block to prevent runaway on mismatched braces
"""
from __future__ import annotations
import re
from pathlib import Path

from backend.parsing.code_unit import CodeUnit, CodeUnitType

PATTERNS: dict[str, dict] = {
    "javascript": {
        "function": re.compile(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\([^)]*\)\s*\{"),
        "class":    re.compile(r"class\s+(\w+)(?:\s+extends\s+\w+)?\s*\{"),
        "arrow":    re.compile(r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>"),
    },
    "typescript": {
        "function": re.compile(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*[<(]"),
        "class":    re.compile(r"class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{"),
        "arrow":    re.compile(r"(?:export\s+)?(?:const|let|var)\s+(\w+)\s*(?::\s*[\w<>]+\s*)?=\s*(?:async\s*)?\([^)]*\)\s*(?::\s*[\w<>]+\s*)?=>"),
    },
    "java": {
        "function": re.compile(r"(?:public|private|protected|static|final|\s)+[\w<>\[\]]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+\w+\s*)?\{"),
        "class":    re.compile(r"(?:public|private|protected|abstract|final|\s)*class\s+(\w+)"),
    },
    "go": {
        "function": re.compile(r"func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\("),
    },
    "rust": {
        "function": re.compile(r"(?:pub\s+)?fn\s+(\w+)\s*[<(]"),
        "class":    re.compile(r"(?:pub\s+)?(?:struct|impl|trait|enum)\s+(\w+)"),
    },
    "ruby": {
        "function": re.compile(r"def\s+(\w+)"),
        "class":    re.compile(r"class\s+(\w+)"),
    },
    "php": {
        "function": re.compile(r"function\s+(\w+)\s*\("),
        "class":    re.compile(r"class\s+(\w+)"),
    },
    "csharp": {
        "function": re.compile(r"(?:public|private|protected|internal|static|virtual|override|\s)+\w+\s+(\w+)\s*\([^)]*\)\s*\{"),
        "class":    re.compile(r"(?:public|internal|abstract|sealed|\s)*class\s+(\w+)"),
    },
}

MAX_BLOCK_LINES = 150   # FIX: safety cap — never consume more than this


def _extract_block(lines: list[str], start_idx: int) -> tuple[str, int]:
    """Extract brace-delimited block. Returns (code, end_line_idx)."""
    depth  = 0
    result = []
    limit  = min(start_idx + MAX_BLOCK_LINES, len(lines))
    for i in range(start_idx, limit):
        line = lines[i]
        result.append(line)
        depth += line.count("{") - line.count("}")
        if depth <= 0 and i > start_idx:
            return "\n".join(result), i
    return "\n".join(result), limit - 1


TYPE_MAP = {
    "function": CodeUnitType.FUNCTION,
    "arrow":    CodeUnitType.FUNCTION,
    "class":    CodeUnitType.CLASS,
}


def parse_generic_file(
    repo_id: str,
    rel_path: str,
    language: str,
    source_code: str,
) -> list[CodeUnit]:
    lines    = source_code.splitlines()
    patterns = PATTERNS.get(language, {})
    units: list[CodeUnit] = []

    # Module unit (whole file overview)
    units.append(CodeUnit(
        repo_id=repo_id, file_path=rel_path, language=language,
        unit_type=CodeUnitType.MODULE,
        name=Path(rel_path).stem,
        code=source_code[:3000],
        start_line=1, end_line=len(lines),
    ))

    seen_spans: set[tuple[int, int]] = set()   # FIX: avoid duplicate overlapping blocks

    for pattern_name, pattern in patterns.items():
        for line_idx, line in enumerate(lines):
            m = pattern.search(line)
            if not m:
                continue
            name = m.group(1)
            code_block, end_idx = _extract_block(lines, line_idx)
            span = (line_idx, end_idx)
            if span in seen_spans:
                continue
            seen_spans.add(span)
            units.append(CodeUnit(
                repo_id=repo_id, file_path=rel_path, language=language,
                unit_type=TYPE_MAP.get(pattern_name, CodeUnitType.FUNCTION),
                name=name,
                code=code_block[:4000],
                start_line=line_idx + 1,
                end_line=end_idx + 1,
            ))

    return units
