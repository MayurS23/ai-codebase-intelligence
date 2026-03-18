"""test_embeddings.py — Embedding model and pipeline tests (no API key needed)."""
from backend.embeddings.embedding_model import LocalEmbeddingModel


def test_local_model_returns_list():
    m = LocalEmbeddingModel()
    result = m.embed(["hello world"])
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], list)


def test_local_model_dimension():
    m = LocalEmbeddingModel()
    vec = m.embed_one("some code here")
    assert len(vec) == LocalEmbeddingModel.DIM


def test_local_model_normalised():
    import math
    m = LocalEmbeddingModel()
    vec = m.embed_one("normalise this vector")
    norm = math.sqrt(sum(x * x for x in vec))
    assert abs(norm - 1.0) < 1e-6


def test_batch_embed(chunked_units):
    from backend.embeddings.embedding_pipeline import embed_units
    result = embed_units(chunked_units, show_progress=False)
    assert all(u.embedding is not None for u in result)
    assert all(len(u.embedding) == LocalEmbeddingModel.DIM for u in result)


def test_different_texts_different_vectors():
    m = LocalEmbeddingModel()
    v1 = m.embed_one("authentication login function")
    v2 = m.embed_one("database connection pool")
    # They should NOT be identical
    assert v1 != v2
