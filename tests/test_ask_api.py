from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routers.ask import set_agent_graph_override
from app.services.exceptions import ExternalServiceError


class FakeAgentGraph:
    def invoke(self, state: dict) -> dict:
        return {
            "question": state["question"].strip(),
            "answer": "Audio ads require frequency caps. [1]",
            "citations": [
                {
                    "chunk_id": "chunk-1",
                    "text": "Audio campaigns require frequency caps.",
                    "metadata": {"file": "policy.pdf", "page": 1},
                    "distance": 0.12,
                }
            ],
            "status": "answered",
            "trace": [
                "Validator(input)",
                "Planner(route=rag)",
                "Retriever",
                "Reasoner",
                "Responder",
                "Validator(output)",
            ],
        }


class FailingAgentGraph:
    def invoke(self, state: dict) -> dict:
        raise ValueError("Question cannot be empty.")


class UnavailableAgentGraph:
    def invoke(self, state: dict) -> dict:
        raise ExternalServiceError("Ollama chat service is unavailable.")


def test_ask_endpoint_returns_grounded_answer_and_citations() -> None:
    client = TestClient(app)
    set_agent_graph_override(FakeAgentGraph())

    try:
        response = client.post(
            "/ask-questions",
            json={"question": "What rules apply to audio ads?", "limit": 2},
        )
    finally:
        set_agent_graph_override(None)

    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "What rules apply to audio ads?"
    assert body["answer"] == "Audio ads require frequency caps. [1]"
    assert body["citation_count"] == 1
    assert body["citations"][0]["metadata"]["file"] == "policy.pdf"
    assert body["status"] == "answered"
    assert body["trace"] == [
        "Validator(input)",
        "Planner(route=rag)",
        "Retriever",
        "Reasoner",
        "Responder",
        "Validator(output)",
    ]


def test_ask_endpoint_returns_validation_errors() -> None:
    client = TestClient(app)
    set_agent_graph_override(FailingAgentGraph())

    try:
        response = client.post("/ask-questions", json={"question": "   "})
    finally:
        set_agent_graph_override(None)

    assert response.status_code == 400
    assert "Question cannot be empty" in response.json()["detail"]


def test_ask_endpoint_returns_friendly_service_unavailable_error() -> None:
    client = TestClient(app)
    set_agent_graph_override(UnavailableAgentGraph())

    try:
        response = client.post(
            "/ask-questions",
            json={"question": "What rules apply to audio ads?", "limit": 2},
        )
    finally:
        set_agent_graph_override(None)

    assert response.status_code == 503
    assert "Ollama chat service is unavailable" in response.json()["detail"]
