"""
architecture.py — /get-architecture, /repo-status, /reload-session, /list-functions
FIX: add /reload-session so users can recover after server restart
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.api.models.schemas import ArchitectureResponse, GraphData
from backend.api.session_cache import get_session, reload_session_from_disk
from backend.vectordb.chroma_store import ChromaCodeStore

router = APIRouter(prefix="/api", tags=["architecture"])


class StatusResponse(BaseModel):
    repo_id: str
    indexed: bool
    chunk_count: int
    node_count: int
    edge_count: int
    session_loaded: bool


@router.get("/get-architecture/{repo_id}", response_model=ArchitectureResponse)
async def get_architecture(repo_id: str):
    session = get_session(repo_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Repo '{repo_id}' not loaded. Call /ingest-repo first.")

    resp = session.engine.answer("Describe the overall architecture of this codebase.")
    dep_data = resp.dependency_graph_data
    return ArchitectureResponse(
        repo_id=repo_id,
        answer=resp.answer,
        source_files=resp.source_files,
        dependency_graph=GraphData(
            nodes=dep_data.get("nodes", [])[:300],
            edges=dep_data.get("edges", [])[:500],
        ) if dep_data else None,
    )


@router.get("/repo-status/{repo_id}", response_model=StatusResponse)
async def repo_status(repo_id: str):
    store   = ChromaCodeStore(repo_id)
    session = get_session(repo_id)
    return StatusResponse(
        repo_id=repo_id,
        indexed=store.collection_exists(),
        chunk_count=store.count(),
        node_count=session.call_graph.graph.number_of_nodes() if session else 0,
        edge_count=session.call_graph.graph.number_of_edges() if session else 0,
        session_loaded=session is not None,
    )


@router.post("/reload-session/{repo_id}")
async def reload_session(repo_id: str):
    """Restore in-memory graphs after a server restart (no re-embedding)."""
    session = reload_session_from_disk(repo_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find cloned repo for '{repo_id}'. Run /ingest-repo again."
        )
    return {
        "repo_id": repo_id,
        "message": "Session restored from disk.",
        "units": len(session.units),
        "nodes": session.call_graph.graph.number_of_nodes(),
    }


@router.get("/list-functions/{repo_id}")
async def list_functions(repo_id: str, limit: int = 50):
    session = get_session(repo_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Repo '{repo_id}' not loaded.")
    nodes = [
        {
            "id":   n,
            "name": session.call_graph.graph.nodes[n].get("name"),
            "file": session.call_graph.graph.nodes[n].get("file_path"),
            "type": session.call_graph.graph.nodes[n].get("unit_type"),
        }
        for n in list(session.call_graph.graph.nodes)[:limit]
    ]
    return {
        "repo_id": repo_id,
        "functions": nodes,
        "total": session.call_graph.graph.number_of_nodes(),
    }
