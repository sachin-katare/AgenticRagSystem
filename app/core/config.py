from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env."""

    app_name: str = "Agentic RAG System"
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = Field(
        default="llama3.2:3b",
        validation_alias=AliasChoices("OLLAMA_CHAT_MODEL", "CHAT_MODEL"),
    )
    ollama_embedding_model: str = Field(
        default="nomic-embed-text",
        validation_alias=AliasChoices("OLLAMA_EMBEDDING_MODEL", "EMBEDDING_MODEL"),
    )
    chroma_persist_directory: str = "data/chroma"
    upload_directory: str = "data/uploads"
    log_directory: str = "logs"
    log_file: str = "app.log"
    error_log_file: str = "error.log"
    log_max_bytes: int = 10 * 1024 * 1024
    log_backup_count: int = 5
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
