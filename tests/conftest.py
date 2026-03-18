"""
conftest.py — Shared pytest fixtures for all test modules.
"""
import os
import tempfile
import pytest
from pathlib import Path

# ── Force local embedding (no API key needed in tests) ──────────────────── #
os.environ.setdefault("EMBEDDING_PROVIDER", "local")
os.environ.setdefault("ANTHROPIC_API_KEY",  "test-key")
os.environ.setdefault("OPENAI_API_KEY",     "test-key")


@pytest.fixture(scope="session")
def sample_python_code() -> str:
    return '''
"""Auth module."""
import os

def login(username: str, password: str) -> bool:
    """Authenticate a user."""
    user = authenticate_user(username, password)
    token = generate_token(user)
    return bool(token)

def authenticate_user(username: str, password: str) -> dict:
    """Check credentials."""
    return {"username": username, "valid": True}

def generate_token(user: dict) -> str:
    """Create a JWT-like token."""
    return user["username"] + "_token"

class AuthService:
    """Service class wrapping auth logic."""

    def __init__(self, db_url: str):
        self.db_url = db_url

    def verify(self, token: str) -> bool:
        """Verify a token is valid."""
        return token.endswith("_token")

    def revoke(self, token: str) -> None:
        """Invalidate a token."""
        pass
'''


@pytest.fixture(scope="session")
def temp_repo_dir(sample_python_code, tmp_path_factory) -> Path:
    """Create a minimal fake repo on disk."""
    root = tmp_path_factory.mktemp("fake_repo")
    (root / "auth.py").write_text(sample_python_code)
    (root / "main.py").write_text(
        'from auth import login\n\ndef main():\n    result = login("admin", "pass")\n    print(result)\n'
    )
    (root / "utils.py").write_text(
        'def helper():\n    return True\n\ndef another():\n    pass\n'
    )
    return root


@pytest.fixture(scope="session")
def parsed_units(sample_python_code):
    from backend.parsing.python_parser import parse_python_file
    return parse_python_file("test_repo", "auth.py", sample_python_code)


@pytest.fixture(scope="session")
def chunked_units(parsed_units):
    from backend.chunking.smart_chunker import chunk_units
    return chunk_units(parsed_units)


@pytest.fixture(scope="session")
def embedded_units(chunked_units):
    from backend.embeddings.embedding_pipeline import embed_units
    return embed_units(chunked_units, show_progress=False)


@pytest.fixture(scope="function")
def chroma_store(embedded_units, tmp_path, monkeypatch):
    """A fresh ChromaDB store for each test function, using a temp dir."""
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chromadb"))
    # Re-read settings after env change
    from backend.config import get_settings
    get_settings.cache_clear()

    from backend.vectordb.chroma_store import ChromaCodeStore
    store = ChromaCodeStore("test_repo")
    store.upsert_units(embedded_units)
    yield store
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def call_graph(parsed_units):
    from backend.graphs.call_graph import CallGraph
    return CallGraph(repo_id="test_repo").build(parsed_units)


@pytest.fixture(scope="session")
def dep_graph(parsed_units):
    from backend.graphs.dependency_graph import DependencyGraph
    return DependencyGraph(repo_id="test_repo").build(parsed_units)
