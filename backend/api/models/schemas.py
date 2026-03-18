"""
schemas.py — Pydantic request/response models for the FastAPI layer.
"""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, HttpUrl, Field


# ── Request models ─────────────────────────────────────────────────────────── #
class IngestRequest(BaseModel):
    repo_url: str = Field(..., description="Full GitHub repository URL")
    force: bool = Field(False, description="Force re-clone and re-index")


class QuestionRequest(BaseModel):
    repo_id: str
    question: str = Field(..., min_length=3)


class TraceRequest(BaseModel):
    repo_id: str
    entry_function: str
    max_depth: int = Field(6, ge=1, le=10)


# ── Response models ────────────────────────────────────────────────────────── #
class GraphNode(BaseModel):
    id: str
    name: Optional[str] = None
    file_path: Optional[str] = None
    unit_type: Optional[str] = None


class GraphEdge(BaseModel):
    source: str
    target: str


class GraphData(BaseModel):
    nodes: list[dict]
    edges: list[dict]


class IngestResponse(BaseModel):
    repo_id: str
    files_scanned: int
    units_parsed: int
    units_embedded: int
    duration_seconds: float
    message: str


class AnswerResponse(BaseModel):
    repo_id: str
    question: str
    answer: str
    source_files: list[str] = []
    call_graph: Optional[GraphData] = None
    dependency_graph: Optional[GraphData] = None
    trace_text: Optional[str] = None


class ArchitectureResponse(BaseModel):
    repo_id: str
    answer: str
    dependency_graph: Optional[GraphData] = None
    source_files: list[str] = []


class RepoStatusResponse(BaseModel):
    repo_id: str
    indexed: bool
    chunk_count: int
