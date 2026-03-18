"""
session_cache.py — In-memory session registry.
FIX: add reload_session() to recover after server restart without re-embedding.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from backend.graphs.call_graph import CallGraph
from backend.graphs.dependency_graph import DependencyGraph
from backend.llm.reasoning_engine import ReasoningEngine
from backend.parsing.code_unit import CodeUnit


@dataclass
class RepoSession:
    repo_id: str
    units: list[CodeUnit]
    call_graph: CallGraph
    dep_graph: DependencyGraph
    engine: ReasoningEngine


_SESSIONS: dict[str, RepoSession] = {}


def register_session(
    repo_id: str,
    units: list[CodeUnit],
    call_graph: CallGraph,
    dep_graph: DependencyGraph,
) -> RepoSession:
    engine  = ReasoningEngine(repo_id, units, call_graph, dep_graph)
    session = RepoSession(
        repo_id=repo_id, units=units,
        call_graph=call_graph, dep_graph=dep_graph,
        engine=engine,
    )
    _SESSIONS[repo_id] = session
    return session


def get_session(repo_id: str) -> RepoSession | None:
    return _SESSIONS.get(repo_id)


def session_exists(repo_id: str) -> bool:
    return repo_id in _SESSIONS


def reload_session_from_disk(repo_id: str) -> RepoSession | None:
    """
    If the server restarted and the repo clone still exists on disk,
    re-parse and rebuild graphs (no re-embedding — ChromaDB data is kept).
    Returns the new session or None if the clone is missing.
    """
    from backend.config import get_settings
    from backend.ingestion.file_scanner import scan_repo
    from backend.parsing.parser_dispatcher import parse_file
    from backend.chunking.smart_chunker import chunk_units

    settings  = get_settings()
    repo_root = Path(settings.repos_dir) / repo_id.replace("__", "/")

    # Try common slug patterns
    candidates = [
        Path(settings.repos_dir) / repo_id,
        Path(settings.repos_dir) / repo_id.replace("__", "/"),
    ]
    found: Path | None = None
    for c in candidates:
        if c.exists():
            found = c
            break

    if not found:
        return None

    scanned  = scan_repo(found)
    all_units: list[CodeUnit] = []
    for sf in scanned:
        all_units.extend(parse_file(repo_id, sf))

    chunked  = chunk_units(all_units)
    cg = CallGraph(repo_id=repo_id).build(all_units)
    dg = DependencyGraph(repo_id=repo_id).build(all_units)

    return register_session(repo_id, chunked, cg, dg)
