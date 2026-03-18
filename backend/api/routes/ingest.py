"""
ingest.py — POST /ingest-repo
FIX: guard against None call_graph/dep_graph before registering session
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException

from backend.api.models.schemas import IngestRequest, IngestResponse
from backend.api.session_cache import register_session
from backend.ingestion.ingestion_orchestrator import ingest_repository
from backend.graphs.call_graph import CallGraph
from backend.graphs.dependency_graph import DependencyGraph

router = APIRouter(prefix="/api", tags=["ingestion"])


@router.post("/ingest-repo", response_model=IngestResponse)
async def ingest_repo(request: IngestRequest):
    """Clone a GitHub repo and run the full ingestion pipeline."""
    try:
        result = ingest_repository(request.repo_url, force=request.force)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)

    # FIX: provide empty graphs if somehow missing (shouldn't happen on success)
    cg = result.call_graph or CallGraph(repo_id=result.repo_id)
    dg = result.dep_graph  or DependencyGraph(repo_id=result.repo_id)

    register_session(
        repo_id=result.repo_id,
        units=result.units,
        call_graph=cg,
        dep_graph=dg,
    )

    return IngestResponse(
        repo_id=result.repo_id,
        files_scanned=result.files_scanned,
        units_parsed=result.units_parsed,
        units_embedded=result.units_embedded,
        duration_seconds=round(result.duration_seconds, 2),
        message=f"Repository '{result.repo_id}' indexed successfully.",
    )
