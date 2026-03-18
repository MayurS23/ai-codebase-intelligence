"""
embedding_pipeline.py — Batch-process CodeUnits through the embedding model.
"""
from __future__ import annotations
from tqdm import tqdm

from backend.config import get_settings
from backend.parsing.code_unit import CodeUnit
from backend.embeddings.embedding_model import get_embedding_model

settings = get_settings()


def embed_units(units: list[CodeUnit], show_progress: bool = True) -> list[CodeUnit]:
    """
    Embed all *units* in batches. Mutates unit.embedding in-place.
    Returns the same list (convenient for chaining).
    """
    model = get_embedding_model()
    batch_size = settings.embedding_batch_size

    batches = [units[i:i + batch_size] for i in range(0, len(units), batch_size)]
    iterator = tqdm(batches, desc="Embedding", unit="batch") if show_progress else batches

    for batch in iterator:
        texts = [u.to_embed_text() for u in batch]
        embeddings = model.embed(texts)
        for unit, emb in zip(batch, embeddings):
            unit.embedding = emb

    return units
