"""
test_api.py — FastAPI endpoint integration tests.
The LLM is mocked so no API key is needed. Embeddings use the local model.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from pathlib import Path


# ── Fixture: fully loaded app with a pre-ingested session ──────────────── #
@pytest.fixture(scope="module")
def client(tmp_path_factory, temp_repo_dir):
    """
    Build a TestClient with:
      - a real local embedding model
      - a temp ChromaDB
      - a real parsed + embedded session
      - LLM mocked to return a canned answer
    """
    tmp = tmp_path_factory.mktemp("api_db")

    import os
    os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chromadb")
    os.environ["REPOS_DIR"]          = str(tmp / "repos")

    from backend.config import get_settings
    get_settings.cache_clear()

    # Run the pipeline directly (no GitHub clone)
    from backend.ingestion.file_scanner import scan_repo
    from backend.parsing.parser_dispatcher import parse_file
    from backend.chunking.smart_chunker import chunk_units
    from backend.embeddings.embedding_pipeline import embed_units
    from backend.vectordb.chroma_store import ChromaCodeStore
    from backend.graphs.call_graph import CallGraph
    from backend.graphs.dependency_graph import DependencyGraph
    from backend.api.session_cache import register_session

    REPO_ID = "api_test_repo"
    files   = scan_repo(temp_repo_dir)
    units   = []
    for sf in files:
        units.extend(parse_file(REPO_ID, sf))
    chunked  = chunk_units(units)
    embedded = embed_units(chunked, show_progress=False)

    store = ChromaCodeStore(REPO_ID)
    store.upsert_units(embedded)

    cg = CallGraph(REPO_ID).build(units)
    dg = DependencyGraph(REPO_ID).build(units)
    register_session(REPO_ID, embedded, cg, dg)

    # Patch LLM so tests never call Anthropic
    with patch("backend.llm.llm_client.LLMClient.complete",
               return_value="**Mocked LLM answer.** The login function authenticates users."):
        from backend.main import app
        with TestClient(app) as c:
            c.repo_id = REPO_ID
            yield c

    get_settings.cache_clear()


# ── Health checks ─────────────────────────────────────────────────────── #
def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "running"


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── /repo-status ──────────────────────────────────────────────────────── #
def test_repo_status_indexed(client):
    r = client.get(f"/api/repo-status/{client.repo_id}")
    assert r.status_code == 200
    d = r.json()
    assert d["indexed"] is True
    assert d["chunk_count"] > 0
    assert d["session_loaded"] is True


def test_repo_status_unknown(client):
    r = client.get("/api/repo-status/totally_unknown_xyz")
    assert r.status_code == 200
    assert r.json()["indexed"] is False


# ── /ask-question ─────────────────────────────────────────────────────── #
def test_ask_question_success(client):
    with patch("backend.llm.llm_client.LLMClient.complete",
               return_value="The login function authenticates users."):
        r = client.post("/api/ask-question", json={
            "repo_id": client.repo_id,
            "question": "How does the login function work?",
        })
    assert r.status_code == 200
    d = r.json()
    assert d["answer"]
    assert d["repo_id"] == client.repo_id
    assert isinstance(d["source_files"], list)


def test_ask_question_unknown_repo(client):
    r = client.post("/api/ask-question", json={
        "repo_id": "no_such_repo_xyz",
        "question": "How does login work?",
    })
    assert r.status_code == 404


def test_ask_question_returns_source_files(client):
    with patch("backend.llm.llm_client.LLMClient.complete",
               return_value="Auth is in auth.py"):
        r = client.post("/api/ask-question", json={
            "repo_id": client.repo_id,
            "question": "Where is authentication implemented?",
        })
    assert r.status_code == 200
    assert len(r.json()["source_files"]) > 0


# ── /trace-flow ───────────────────────────────────────────────────────── #
def test_trace_flow_success(client):
    with patch("backend.llm.llm_client.LLMClient.complete",
               return_value="Login calls authenticate_user which calls generate_token."):
        r = client.post("/api/trace-flow", json={
            "repo_id": client.repo_id,
            "entry_function": "login",
            "max_depth": 4,
        })
    assert r.status_code == 200
    d = r.json()
    assert d["answer"]
    assert d["trace_text"] is not None


def test_trace_flow_unknown_function(client):
    """Unknown function should still return 200 with graceful empty trace."""
    with patch("backend.llm.llm_client.LLMClient.complete",
               return_value="No trace found for this function."):
        r = client.post("/api/trace-flow", json={
            "repo_id": client.repo_id,
            "entry_function": "totally_nonexistent_xyz",
            "max_depth": 3,
        })
    assert r.status_code == 200


# ── /get-architecture ─────────────────────────────────────────────────── #
def test_get_architecture(client):
    with patch("backend.llm.llm_client.LLMClient.complete",
               return_value="This is a simple Python application with auth and utils modules."):
        r = client.get(f"/api/get-architecture/{client.repo_id}")
    assert r.status_code == 200
    d = r.json()
    assert d["answer"]
    assert d["repo_id"] == client.repo_id


# ── /list-functions ───────────────────────────────────────────────────── #
def test_list_functions(client):
    r = client.get(f"/api/list-functions/{client.repo_id}?limit=20")
    assert r.status_code == 200
    d = r.json()
    assert "functions" in d
    assert "total" in d
    assert d["total"] > 0


# ── /ingest-repo (with mocked clone) ─────────────────────────────────── #
def test_ingest_repo_mocked(client, temp_repo_dir, tmp_path_factory):
    """Test the ingest endpoint by mocking clone_repo to return our temp dir."""
    tmp = tmp_path_factory.mktemp("ingest_test")

    import os
    os.environ["CHROMA_PERSIST_DIR"] = str(tmp / "chromadb")

    from backend.config import get_settings
    get_settings.cache_clear()

    with patch("backend.ingestion.ingestion_orchestrator.clone_repo",
               return_value=temp_repo_dir), \
         patch("backend.llm.llm_client.LLMClient.complete",
               return_value="Done."):
        r = client.post("/api/ingest-repo", json={
            "repo_url": "https://github.com/fake/repo",
            "force": False,
        })

    assert r.status_code == 200
    d = r.json()
    assert d["files_scanned"] > 0
    assert d["units_parsed"] > 0
    assert "repo_id" in d

    get_settings.cache_clear()
