"""test_ingestion.py — File scanner and ingestion orchestrator tests."""
import pytest
from pathlib import Path


def test_scan_finds_python_files(temp_repo_dir):
    from backend.ingestion.file_scanner import scan_repo
    files = scan_repo(temp_repo_dir)
    langs = {f.language for f in files}
    assert "python" in langs


def test_scan_ignores_pycache(tmp_path):
    from backend.ingestion.file_scanner import scan_repo
    pycache = tmp_path / "__pycache__"
    pycache.mkdir()
    (pycache / "module.pyc").write_bytes(b"PK")
    (tmp_path / "real.py").write_text("x = 1")
    files = scan_repo(tmp_path)
    paths = [f.rel_path for f in files]
    assert not any("__pycache__" in p for p in paths)


def test_scan_relative_paths(temp_repo_dir):
    from backend.ingestion.file_scanner import scan_repo
    files = scan_repo(temp_repo_dir)
    for f in files:
        assert not f.rel_path.startswith("/")


def test_parse_all_files_in_repo(temp_repo_dir):
    from backend.ingestion.file_scanner import scan_repo
    from backend.parsing.parser_dispatcher import parse_file
    files = scan_repo(temp_repo_dir)
    units = []
    for sf in files:
        units.extend(parse_file("repo", sf))
    assert len(units) > 0


def test_full_pipeline_no_clone(temp_repo_dir, tmp_path, monkeypatch):
    """
    Integration test: run the full pipeline (parse→chunk→embed→store)
    using a local dir instead of cloning from GitHub.
    """
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "pipeline_db"))
    monkeypatch.setenv("REPOS_DIR", str(tmp_path / "repos"))
    from backend.config import get_settings
    get_settings.cache_clear()

    from backend.ingestion.file_scanner import scan_repo
    from backend.parsing.parser_dispatcher import parse_file
    from backend.chunking.smart_chunker import chunk_units
    from backend.embeddings.embedding_pipeline import embed_units
    from backend.vectordb.chroma_store import ChromaCodeStore
    from backend.graphs.call_graph import CallGraph
    from backend.graphs.dependency_graph import DependencyGraph

    files     = scan_repo(temp_repo_dir)
    all_units = []
    for sf in files:
        all_units.extend(parse_file("pipeline_repo", sf))

    assert len(all_units) > 0, "Should parse at least some units"

    chunked  = chunk_units(all_units)
    embedded = embed_units(chunked, show_progress=False)

    store = ChromaCodeStore("pipeline_repo")
    store.upsert_units(embedded)
    assert store.count() > 0, "ChromaDB should have stored chunks"

    cg = CallGraph("pipeline_repo").build(all_units)
    dg = DependencyGraph("pipeline_repo").build(all_units)
    assert cg.graph.number_of_nodes() > 0
    assert dg.graph.number_of_nodes() > 0

    get_settings.cache_clear()
