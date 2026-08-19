from fastapi.testclient import TestClient

from app.api.main import app


def test_health_check_returns_configured_app_details() -> None:
    client = TestClient(app)

    response = client.get("/health-check")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app_name": "Agentic RAG System",
        "llm_provider": "ollama",
        "chat_model": "llama3.2:3b",
        "embedding_model": "nomic-embed-text",
    }
