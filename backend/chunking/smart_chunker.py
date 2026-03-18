"""
smart_chunker.py — Assign chunk IDs and optionally split oversized units.

Design principle: chunk at function/class boundaries, NOT arbitrary token
windows. This preserves semantic coherence — the LLM always sees complete
logical units, never half a function.

For units that are still too large (> MAX_TOKENS), we split by lines while
trying to keep logical sub-blocks together.
"""
from __future__ import annotations
import hashlib
from backend.parsing.code_unit import CodeUnit

MAX_CHARS = 6000    # ~1500 tokens — safe for all embedding models


def _make_chunk_id(repo_id: str, file_path: str, name: str, start: int) -> str:
    raw = f"{repo_id}::{file_path}::{name}::{start}"
    return hashlib.md5(raw.encode()).hexdigest()


def _split_large_unit(unit: CodeUnit) -> list[CodeUnit]:
    """Split a CodeUnit whose code exceeds MAX_CHARS into overlapping windows."""
    lines = unit.code.splitlines()
    chunks: list[CodeUnit] = []
    window_lines = 80
    overlap_lines = 10
    start = 0

    while start < len(lines):
        end = min(start + window_lines, len(lines))
        chunk_code = "\n".join(lines[start:end])
        chunk_start_line = unit.start_line + start
        chunk_end_line = unit.start_line + end - 1

        new_unit = CodeUnit(
            repo_id=unit.repo_id,
            file_path=unit.file_path,
            language=unit.language,
            unit_type=unit.unit_type,
            name=f"{unit.name}[part{len(chunks)+1}]",
            code=chunk_code,
            start_line=chunk_start_line,
            end_line=chunk_end_line,
            parent_class=unit.parent_class,
            docstring=unit.docstring,
            decorators=unit.decorators,
            imports=unit.imports,
            calls=unit.calls,
        )
        new_unit.chunk_id = _make_chunk_id(
            unit.repo_id, unit.file_path, new_unit.name, chunk_start_line
        )
        chunks.append(new_unit)

        if end == len(lines):
            break
        start += window_lines - overlap_lines

    return chunks


def chunk_units(units: list[CodeUnit]) -> list[CodeUnit]:
    """
    Process a list of CodeUnits:
    1. Assign chunk IDs
    2. Split oversized units
    Returns the final list ready for embedding.
    """
    result: list[CodeUnit] = []

    for unit in units:
        if len(unit.code) > MAX_CHARS:
            result.extend(_split_large_unit(unit))
        else:
            unit.chunk_id = _make_chunk_id(
                unit.repo_id, unit.file_path, unit.name, unit.start_line
            )
            result.append(unit)

    return result
