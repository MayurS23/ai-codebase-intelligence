"""
file_scanner.py — Walk a cloned repo and collect all analysable source files.
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass

from backend.config import get_settings

settings = get_settings()

# ── Language detection ────────────────────────────────────────────────────── #
EXTENSION_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".cs": "csharp",
    ".rb": "ruby",
    ".php": "php",
    ".kt": "kotlin",
    ".swift": "swift",
}

# Directories that are never useful to analyse
IGNORE_DIRS: set[str] = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "coverage", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "vendor", "third_party",
}


@dataclass
class ScannedFile:
    path: Path          # absolute path
    rel_path: str       # relative to repo root
    language: str
    size_bytes: int


def scan_repo(repo_root: Path) -> list[ScannedFile]:
    """
    Recursively walk *repo_root*, returning a list of ScannedFile objects
    for every source file that passes the size filter.
    """
    max_bytes = settings.max_file_size_kb * 1024
    results: list[ScannedFile] = []

    for path in repo_root.rglob("*"):
        # Skip directories and ignored paths
        if path.is_dir():
            continue
        if any(part in IGNORE_DIRS for part in path.parts):
            continue

        lang = EXTENSION_MAP.get(path.suffix.lower())
        if lang is None:
            continue

        size = path.stat().st_size
        if size > max_bytes:
            continue
        if size == 0:
            continue

        results.append(ScannedFile(
            path=path,
            rel_path=str(path.relative_to(repo_root)),
            language=lang,
            size_bytes=size,
        ))

    return results
