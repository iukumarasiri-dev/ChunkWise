"""Application configuration, loaded from environment / .env.

See .env.example for the overridable settings.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    storage_dir: Path = Path("storage")

    # Origin the frontend is served from, for CORS. The dev Vite server by
    # default; override in production with the deployed frontend's URL.
    frontend_origin: str = "http://localhost:5173"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    chunk_size: int = 800
    chunk_overlap: int = 150

    top_k: int = 5

    # Reranking: hybrid search casts this wide a net before the cross-encoder
    # picks the final top_k. Larger = better recall for the reranker to work
    # with, at the cost of more cross-encoder inference per query.
    rerank_pool_size: int = 20
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Answer generation: stub | ollama
    llm_provider: str = "stub"
    # Model tag for the chosen provider (e.g. an Ollama tag like "llama3.1:8b").
    # Empty -> the provider falls back to its own default.
    llm_model: str = ""
    # Ollama server base URL. Local: http://localhost:11434
    # Ollama Cloud (hosted, no install): https://ollama.com
    ollama_host: str = "http://localhost:11434"
    # Required for Ollama Cloud, unused for a local server.
    ollama_api_key: str = ""

    # Shared secret required in the X-API-Key header on every request except
    # /health. Blank disables auth (fine for pure localhost use). Required
    # before exposing the app beyond localhost - e.g. via a tunnel.
    api_key: str = ""

    @property
    def uploads_dir(self) -> Path:
        return self.storage_dir / "uploads"

    @property
    def chroma_dir(self) -> Path:
        return self.storage_dir / "chroma"

    @property
    def db_path(self) -> Path:
        return self.storage_dir / "chunkwise.sqlite3"

    def ensure_dirs(self) -> None:
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()