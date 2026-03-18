"""
chroma_store.py — ChromaDB integration for storing and querying code embeddings.
FIX: handle empty-collection crash + batch upserts
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.config import get_settings
from backend.parsing.code_unit import CodeUnit

settings = get_settings()


@dataclass
class SearchResult:
    chunk_id: str
    code: str
    metadata: dict
    score: float


class ChromaCodeStore:
    def __init__(self, repo_id: str):
        self.repo_id = repo_id
        persist_dir = Path(settings.chroma_persist_dir)
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        collection_name = f"{settings.chroma_collection_name}_{repo_id}"[:63]
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_units(self, units: list[CodeUnit]) -> None:
        ready = [u for u in units if u.embedding and u.chunk_id]
        if not ready:
            return
        for i in range(0, len(ready), 500):
            batch = ready[i:i + 500]
            self._collection.upsert(
                ids=[u.chunk_id for u in batch],
                embeddings=[u.embedding for u in batch],
                documents=[u.code for u in batch],
                metadatas=[u.metadata_dict() for u in batch],
            )

    def clear(self) -> None:
        self._client.delete_collection(self._collection.name)
        self._collection = self._client.get_or_create_collection(
            name=self._collection.name,
            metadata={"hnsw:space": "cosine"},
        )

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        where: Optional[dict] = None,
    ) -> list[SearchResult]:
        total = self._collection.count()
        if total == 0:          # FIX: was crashing when empty
            return []
        n_results = min(top_k, total)
        kwargs: dict = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where
        result = self._collection.query(**kwargs)
        output: list[SearchResult] = []
        for chunk_id, doc, meta, dist in zip(
            result["ids"][0],
            result["documents"][0],
            result["metadatas"][0],
            result["distances"][0],
        ):
            output.append(SearchResult(
                chunk_id=chunk_id,
                code=doc,
                metadata=meta,
                score=max(0.0, 1 - dist),
            ))
        return output

    def count(self) -> int:
        return self._collection.count()

    def collection_exists(self) -> bool:
        return self._collection.count() > 0
