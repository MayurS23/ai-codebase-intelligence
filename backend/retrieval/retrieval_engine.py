"""
retrieval_engine.py — Semantic retrieval over the vector store.

Responsibilities:
  1. Embed the user query.
  2. Search ChromaDB for top-K relevant chunks.
  3. Optionally re-rank by keyword overlap (cheap but effective).
  4. Return enriched context ready for the LLM prompt.
"""
from __future__ import annotations
from dataclasses import dataclass

from backend.embeddings.embedding_model import get_embedding_model
from backend.vectordb.chroma_store import ChromaCodeStore, SearchResult


@dataclass
class RetrievedContext:
    results: list[SearchResult]

    def to_prompt_context(self, max_chars: int = 12000) -> str:
        """Format retrieved chunks into a context block for the LLM."""
        parts: list[str] = []
        total = 0
        for r in self.results:
            block = (
                f"--- File: {r.metadata.get('file_path', '?')} | "
                f"{r.metadata.get('unit_type', '')} `{r.metadata.get('name', '')}` "
                f"(lines {r.metadata.get('start_line', '?')}–{r.metadata.get('end_line', '?')}, "
                f"score={r.score:.2f}) ---\n{r.code}"
            )
            if total + len(block) > max_chars:
                break
            parts.append(block)
            total += len(block)
        return "\n\n".join(parts)

    def source_files(self) -> list[str]:
        seen: list[str] = []
        for r in self.results:
            fp = r.metadata.get("file_path", "")
            if fp and fp not in seen:
                seen.append(fp)
        return seen


class RetrievalEngine:
    def __init__(self, repo_id: str, top_k: int = 10):
        self.store = ChromaCodeStore(repo_id)
        self.model = get_embedding_model()
        self.top_k = top_k

    def retrieve(self, query: str, top_k: int | None = None) -> RetrievedContext:
        k = top_k or self.top_k
        query_vec = self.model.embed_one(query)
        results = self.store.search(query_vec, top_k=k)
        results = self._rerank(query, results)
        return RetrievedContext(results=results)

    def _rerank(self, query: str, results: list[SearchResult]) -> list[SearchResult]:
        """
        Boost score for chunks whose code/metadata contains query keywords.
        Simple lexical bonus on top of semantic similarity.
        """
        keywords = set(query.lower().split())
        stop = {"the", "a", "an", "is", "how", "does", "what", "where", "in", "of", "to"}
        keywords -= stop

        for r in results:
            text = (r.code + " " + r.metadata.get("name", "")).lower()
            bonus = sum(0.05 for kw in keywords if kw in text)
            r.score = min(r.score + bonus, 1.0)

        return sorted(results, key=lambda x: x.score, reverse=True)
