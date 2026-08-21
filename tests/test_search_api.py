from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routers.search import set_searcher_service_override
from app.services.exceptions import ExternalServiceError
from app.services.search_service import SearcherResult
from app.services.vector_store import SearchResult


class FakeSearcherService:
    def search(self, question: str, limit: int = 4) -> SearcherResult:
        return SearcherResult(
            question=question.strip(),
            matches=[
                SearchResult(
                    chunk_id="chunk-1",
                    text="Audio campaigns require frequency caps.",
                    metadata={"file": "policy.pdf", "page": 1},
                    distance=0.12,
                )
            ],
        )


class FailingSearcherService:
    def search(self, question: str, limit: int = 4) -> SearcherResult:
        raise ValueError("Question cannot be empty.")


class UnavailableSearcherService:
    def search(self, question: str, limit: int = 4) -> SearcherResult:
        raise ExternalServiceError("Ollama embedding service is unavailable.")


def test_search_endpoint_returns_matching_chunks() -> None:
    client = TestClient(app)
    set_searcher_service_override(FakeSearcherService())

    try:
        response = client.post(
            "/search",
            json={"question": "What rules apply to audio ads?", "limit": 2},
        )
    finally:
        set_searcher_service_override(None)

    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "What rules apply to audio ads?"
    assert body["match_count"] == 1
    assert body["matches"][0]["text"] == "Audio campaigns require frequency caps."
    assert body["matches"][0]["metadata"]["file"] == "policy.pdf"


def test_search_endpoint_returns_validation_errors() -> None:
    client = TestClient(app)
    set_searcher_service_override(FailingSearcherService())

    try:
        response = client.post("/search", json={"question": "   "})
    finally:
        set_searcher_service_override(None)

    assert response.status_code == 400
    assert "Question cannot be empty" in response.json()["detail"]


def test_search_endpoint_returns_friendly_service_unavailable_error() -> None:
    client = TestClient(app)
    set_searcher_service_override(UnavailableSearcherService())

    try:
        response = client.post("/search", json={"question": "What rules apply to audio ads?"})
    finally:
        set_searcher_service_override(None)

    assert response.status_code == 503
    assert "Ollama embedding service is unavailable" in response.json()["detail"]
