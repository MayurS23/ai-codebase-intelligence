"""
ingestion_orchestrator.py — Full pipeline: clone → scan → parse → chunk → embed → store.

This is the single entry point for ingesting a GitHub repository.
It is designed to be called from the FastAPI endpoint and returns
a rich status object.
"""
from __future__ import annotations
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

from rich.console import Console

from backend.ingestion.repo_cloner import clone_repo
from backend.ingestion.file_scanner import scan_repo
from backend.parsing.parser_dispatcher import parse_file
from backend.chunking.smart_chunker import chunk_units
from backend.embeddings.embedding_pipeline import embed_units
from backend.vectordb.chroma_store import ChromaCodeStore
from backend.graphs.call_graph import CallGraph
from backend.graphs.dependency_graph import DependencyGraph
from backend.parsing.code_unit import CodeUnit

console = Console()


@dataclass
class IngestionResult:
    repo_id: str
    repo_url: str
    files_scanned: int = 0
    units_parsed: int = 0
    units_embedded: int = 0
    duration_seconds: float = 0.0
    call_graph: CallGraph | None = None
    dep_graph: DependencyGraph | None = None
    units: list[CodeUnit] = field(default_factory=list)
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None


def _repo_id(url: str) -> str:
    url = url.rstrip("/").removesuffix(".git")
    match = re.search(r"github\.com[:/](.+)", url)
    if match:
        return match.group(1).replace("/", "__")[:40]
    return re.sub(r"[^\w\-]", "_", url)[-40:]


def ingest_repository(url: str, force: bool = False) -> IngestionResult:
    """
    Full ingestion pipeline for a GitHub repository URL.
    """
    start = time.time()
    repo_id = _repo_id(url)
    result = IngestionResult(repo_id=repo_id, repo_url=url)

    try:
        # ── 1. Clone ──────────────────────────────────────────────────── #
        console.rule(f"[bold cyan]Ingesting: {url}[/bold cyan]")
        repo_path: Path = clone_repo(url, force=force)

        # ── 2. Scan ───────────────────────────────────────────────────── #
        console.print("[cyan]Scanning files...[/cyan]")
        scanned_files = scan_repo(repo_path)
        result.files_scanned = len(scanned_files)
        console.print(f"  Found {len(scanned_files)} code files")

        # ── 3. Parse ──────────────────────────────────────────────────── #
        console.print("[cyan]Parsing code...[/cyan]")
        all_units: list[CodeUnit] = []
        for sf in scanned_files:
            units = parse_file(repo_id, sf)
            all_units.extend(units)
        result.units_parsed = len(all_units)
        console.print(f"  Parsed {len(all_units)} code units")

        # ── 4. Build Graphs ───────────────────────────────────────────── #
        console.print("[cyan]Building call graph & dependency graph...[/cyan]")
        cg = CallGraph(repo_id=repo_id).build(all_units)
        dg = DependencyGraph(repo_id=repo_id).build(all_units)
        result.call_graph = cg
        result.dep_graph = dg
        console.print(
            f"  Call graph: {cg.graph.number_of_nodes()} nodes, {cg.graph.number_of_edges()} edges"
        )
        console.print(
            f"  Dep graph:  {dg.graph.number_of_nodes()} nodes, {dg.graph.number_of_edges()} edges"
        )

        # ── 5. Chunk ──────────────────────────────────────────────────── #
        console.print("[cyan]Chunking...[/cyan]")
        chunked = chunk_units(all_units)

        # ── 6. Embed ──────────────────────────────────────────────────── #
        console.print("[cyan]Embedding...[/cyan]")
        embedded = embed_units(chunked)
        result.units_embedded = len(embedded)

        # ── 7. Store ──────────────────────────────────────────────────── #
        console.print("[cyan]Storing in ChromaDB...[/cyan]")
        store = ChromaCodeStore(repo_id)
        if force:
            store.clear()
        store.upsert_units(embedded)
        console.print(f"  Stored {store.count()} chunks in vector DB")

        result.units = all_units
        result.duration_seconds = time.time() - start
        console.print(f"[bold green]✓ Ingestion complete in {result.duration_seconds:.1f}s[/bold green]")

    except Exception as exc:
        result.error = str(exc)
        console.print(f"[bold red]✗ Ingestion failed: {exc}[/bold red]")
        raise

    return result
