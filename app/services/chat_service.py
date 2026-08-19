from typing import Any

import requests


class OllamaChatService:
    """Client for Ollama's local chat-generation API."""

    def __init__(self, base_url: str, model: str, timeout_seconds: int = 120) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty.")

        response = requests.post(
            f"{self._base_url}/api/generate",
            json={
                "model": self._model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()

        payload: dict[str, Any] = response.json()
        generated_text = payload.get("response")
        if not isinstance(generated_text, str) or not generated_text.strip():
            raise ValueError("Ollama chat response did not include generated text.")

        return generated_text.strip()
