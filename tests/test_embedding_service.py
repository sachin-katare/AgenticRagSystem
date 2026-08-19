from unittest.mock import Mock

import pytest

from app.services.embedding_service import OllamaEmbeddingService


def test_embed_text_calls_ollama_embedding_endpoint(monkeypatch) -> None:
    response = Mock()
    response.json.return_value = {"embedding": [0.1, 0.2, 0.3]}
    response.raise_for_status.return_value = None
    post = Mock(return_value=response)
    monkeypatch.setattr("app.services.embedding_service.requests.post", post)
    service = OllamaEmbeddingService(
        base_url="http://localhost:11434",
        model="nomic-embed-text",
    )

    embedding = service.embed_text("campaign policy")

    assert embedding == [0.1, 0.2, 0.3]
    post.assert_called_once_with(
        "http://localhost:11434/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": "campaign policy"},
        timeout=60,
    )


def test_embed_text_rejects_empty_text() -> None:
    service = OllamaEmbeddingService(
        base_url="http://localhost:11434",
        model="nomic-embed-text",
    )

    with pytest.raises(ValueError, match="empty text"):
        service.embed_text("   ")


def test_embed_text_rejects_missing_embedding(monkeypatch) -> None:
    response = Mock()
    response.json.return_value = {}
    response.raise_for_status.return_value = None
    monkeypatch.setattr("app.services.embedding_service.requests.post", Mock(return_value=response))
    service = OllamaEmbeddingService(
        base_url="http://localhost:11434",
        model="nomic-embed-text",
    )

    with pytest.raises(ValueError, match="did not include an embedding"):
        service.embed_text("campaign policy")


def test_embed_texts_embeds_each_text(monkeypatch) -> None:
    responses = []
    for embedding in ([1.0, 0.0], [0.0, 1.0]):
        response = Mock()
        response.json.return_value = {"embedding": embedding}
        response.raise_for_status.return_value = None
        responses.append(response)
    monkeypatch.setattr("app.services.embedding_service.requests.post", Mock(side_effect=responses))
    service = OllamaEmbeddingService(
        base_url="http://localhost:11434",
        model="nomic-embed-text",
    )

    embeddings = service.embed_texts(["first text", "second text"])

    assert embeddings == [[1.0, 0.0], [0.0, 1.0]]
