from typing import Any

import requests


class OllamaEmbeddingService:
    """Client for Ollama's local embedding API."""

    def __init__(self, base_url: str, model: str, timeout_seconds: int = 60) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds

    def embed_text(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Cannot embed empty text.")

        response = requests.post(
            f"{self._base_url}/api/embeddings",
            json={"model": self._model, "prompt": text},
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()

        payload: dict[str, Any] = response.json()
        embedding = payload.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            raise ValueError("Ollama embedding response did not include an embedding.")

        return [float(value) for value in embedding]

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]
