"""
config.py — Centralised configuration via pydantic-settings.
All values are read from environment variables / .env file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-sonnet-4-20250514"
    llm_max_tokens: int = 4096

    # Embeddings
    embedding_provider: str = "openai"   # "openai" | "local"
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_batch_size: int = 100

    # Vector DB
    chroma_persist_dir: str = "./data/chromadb"
    chroma_collection_name: str = "codebase"

    # Ingestion
    repos_dir: str = "./data/repos"
    max_file_size_kb: int = 500

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
