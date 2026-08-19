from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    app_name: str = "Agentic RAG System"
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.2:3b"
    ollama_embedding_model: str = "nomic-embed-text"
    chroma_persist_directory: str = "data/chroma"
    upload_directory: str = "data/uploads"
    max_upload_mb: int = 10
    chunk_size: int = 1000
    chunk_overlap: int = 150
    very_small_document_threshold: int = 1000
    large_document_threshold: int = 20000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached app settings so every module uses the same config."""
    return Settings()
