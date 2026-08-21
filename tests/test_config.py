from app.core.config import get_settings
from app.core.config import Settings


def test_get_settings_loads_default_ollama_values() -> None:
    settings = get_settings()

    assert settings.llm_provider == "ollama"
    assert settings.ollama_base_url == "http://localhost:11434"
    assert settings.ollama_chat_model == "llama3.2:3b"
    assert settings.ollama_embedding_model == "nomic-embed-text"


def test_get_settings_returns_cached_instance() -> None:
    first_settings = get_settings()
    second_settings = get_settings()

    assert first_settings is second_settings


def test_settings_accepts_legacy_course_model_env_names(monkeypatch) -> None:
    monkeypatch.setenv("CHAT_MODEL", "legacy-chat")
    monkeypatch.setenv("EMBEDDING_MODEL", "legacy-embedding")

    settings = Settings()

    assert settings.ollama_chat_model == "legacy-chat"
    assert settings.ollama_embedding_model == "legacy-embedding"
