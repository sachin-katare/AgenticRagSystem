import requests
import pytest

from app.services.chat_service import OllamaChatService
from app.services.exceptions import ExternalServiceError


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


def test_ollama_chat_service_calls_generate_endpoint(monkeypatch) -> None:
    calls = []

    def fake_post(url, json, timeout):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse({"response": "Use frequency caps for audio ads. [1]"})

    monkeypatch.setattr(requests, "post", fake_post)
    service = OllamaChatService(
        base_url="http://localhost:11434",
        model="llama3.2:3b",
    )

    answer = service.generate("Question and evidence")

    assert answer == "Use frequency caps for audio ads. [1]"
    assert calls[0]["url"] == "http://localhost:11434/api/generate"
    assert calls[0]["json"]["model"] == "llama3.2:3b"
    assert calls[0]["json"]["stream"] is False


def test_ollama_chat_service_rejects_empty_prompt() -> None:
    service = OllamaChatService(
        base_url="http://localhost:11434",
        model="llama3.2:3b",
    )

    try:
        service.generate("   ")
    except ValueError as exc:
        assert "Prompt cannot be empty" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty prompt.")


def test_ollama_chat_service_wraps_request_failures(monkeypatch) -> None:
    def fake_post(url, json, timeout):
        raise requests.ConnectionError("connection refused")

    monkeypatch.setattr(requests, "post", fake_post)
    service = OllamaChatService(
        base_url="http://localhost:11434",
        model="llama3.2:3b",
    )

    with pytest.raises(ExternalServiceError, match="Ollama chat service is unavailable"):
        service.generate("Question and evidence")
