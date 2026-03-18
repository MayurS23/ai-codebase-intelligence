"""
query.py — /ask-question and /trace-flow
FIX: graceful GraphData construction + proper error messages
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException

from backend.api.models.schemas import QuestionRequest, TraceRequest, AnswerResponse, GraphData
from backend.api.session_cache import get_session
from backend.flow_tracer.execution_tracer import ExecutionTracer

router = APIRouter(prefix="/api", tags=["query"])


def _require_session(repo_id: str):
    session = get_session(repo_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Repo '{repo_id}' is not loaded in memory. "
                "Call POST /api/ingest-repo first (or again if the server restarted)."
            ),
        )
    return session


def _safe_graph(data: dict | None) -> GraphData | None:
    """Convert raw dict to GraphData, capping nodes for API response size."""
    if not data:
        return None
    nodes = data.get("nodes", [])[:300]   # cap at 300 to keep response fast
    edges = data.get("edges", [])[:500]
    return GraphData(nodes=nodes, edges=edges)


@router.post("/ask-question", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest):
    """Ask any natural-language question about the indexed codebase."""
    session = _require_session(request.repo_id)
    resp = session.engine.answer(request.question)

    return AnswerResponse(
        repo_id=request.repo_id,
        question=request.question,
        answer=resp.answer,
        source_files=resp.source_files,
        call_graph=_safe_graph(resp.call_graph_data),
        dependency_graph=_safe_graph(resp.dependency_graph_data),
        trace_text=resp.trace_text,
    )


@router.post("/trace-flow", response_model=AnswerResponse)
async def trace_flow(request: TraceRequest):
    """Trace execution flow starting from a given entry function."""
    session = _require_session(request.repo_id)

    tracer    = ExecutionTracer(session.call_graph, session.units)
    trace     = tracer.trace(request.entry_function, max_depth=request.max_depth)
    trace_txt = trace.to_text()

    question = f"Trace the execution flow starting from `{request.entry_function}`"
    resp     = session.engine.answer(question)

    return AnswerResponse(
        repo_id=request.repo_id,
        question=question,
        answer=resp.answer,
        source_files=resp.source_files,
        trace_text=trace_txt,
        call_graph=_safe_graph(session.call_graph.to_dict()),
    )
