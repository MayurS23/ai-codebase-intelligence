"""test_retrieval.py — RetrievalEngine semantic search tests."""
import os
import pytest


@pytest.fixture
def retrieval_engine(embedded_units, tmp_path, monkeypatch):
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "ret_db"))
    from backend.config import get_settings
    get_settings.cache_clear()

    from backend.vectordb.chroma_store import ChromaCodeStore
    store = ChromaCodeStore("ret_repo")
    store.upsert_units(embedded_units)

    from backend.retrieval.retrieval_engine import RetrievalEngine
    engine = RetrievalEngine("ret_repo", top_k=5)
    yield engine
    get_settings.cache_clear()


def test_retrieve_returns_context(retrieval_engine):
    ctx = retrieval_engine.retrieve("how does login work?")
    assert len(ctx.results) > 0


def test_retrieve_source_files(retrieval_engine):
    ctx = retrieval_engine.retrieve("authenticate user")
    files = ctx.source_files()
    assert isinstance(files, list)
    assert len(files) > 0


def test_prompt_context_non_empty(retrieval_engine):
    ctx = retrieval_engine.retrieve("token generation")
    text = ctx.to_prompt_context()
    assert len(text) > 10
    assert "File:" in text


def test_reranking_boosts_keyword_match(retrieval_engine):
    ctx = retrieval_engine.retrieve("generate_token")
    # The top result should mention generate_token in some form
    names = [r.metadata.get("name", "") for r in ctx.results]
    assert any("generate" in n or "token" in n.lower() for n in names)
