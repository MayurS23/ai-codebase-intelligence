"""test_vectordb.py — ChromaDB store: store, search, clear."""


def test_store_count(chroma_store, embedded_units):
    assert chroma_store.count() == len(embedded_units)


def test_search_returns_results(chroma_store):
    from backend.embeddings.embedding_model import LocalEmbeddingModel
    q_vec = LocalEmbeddingModel().embed_one("login authentication function")
    results = chroma_store.search(q_vec, top_k=5)
    assert len(results) > 0


def test_search_scores_in_range(chroma_store):
    from backend.embeddings.embedding_model import LocalEmbeddingModel
    q_vec = LocalEmbeddingModel().embed_one("token generation")
    results = chroma_store.search(q_vec, top_k=5)
    for r in results:
        assert 0.0 <= r.score <= 1.0


def test_search_results_have_metadata(chroma_store):
    from backend.embeddings.embedding_model import LocalEmbeddingModel
    q_vec = LocalEmbeddingModel().embed_one("class method")
    results = chroma_store.search(q_vec, top_k=3)
    for r in results:
        assert "file_path" in r.metadata
        assert "name" in r.metadata


def test_empty_collection_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "empty_db"))
    from backend.config import get_settings
    get_settings.cache_clear()
    from backend.vectordb.chroma_store import ChromaCodeStore
    store = ChromaCodeStore("empty_repo_xyz")
    from backend.embeddings.embedding_model import LocalEmbeddingModel
    q_vec = LocalEmbeddingModel().embed_one("anything")
    results = store.search(q_vec, top_k=5)
    assert results == []
    get_settings.cache_clear()


def test_collection_exists(chroma_store):
    assert chroma_store.collection_exists() is True
