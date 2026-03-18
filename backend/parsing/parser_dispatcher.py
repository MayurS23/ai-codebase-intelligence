"""
parser_dispatcher.py — Route each file to the correct parser.
"""
from __future__ import annotations
from backend.parsing.code_unit import CodeUnit
from backend.parsing.python_parser import parse_python_file
from backend.parsing.generic_parser import parse_generic_file
from backend.ingestion.file_scanner import ScannedFile


def parse_file(repo_id: str, scanned: ScannedFile) -> list[CodeUnit]:
    """
    Parse a single ScannedFile and return its CodeUnits.
    Falls back to generic parser for any unsupported language.
    """
    try:
        source = scanned.path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    if scanned.language == "python":
        return parse_python_file(repo_id, scanned.rel_path, source)
    else:
        return parse_generic_file(repo_id, scanned.rel_path, scanned.language, source)
