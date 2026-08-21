from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class ApiResult:
    ok: bool
    status_code: int
    data: dict[str, Any]


class FastApiClient:
    """Small HTTP client used by the Streamlit UI."""

    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout_seconds: int = 120) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    def health_check(self) -> ApiResult:
        return self._get("/health-check")

    def upload_document(self, filename: str, content: bytes, content_type: str) -> ApiResult:
        try:
            response = requests.post(
                f"{self._base_url}/upload-document",
                files={"file": (filename, content, content_type)},
                timeout=self._timeout_seconds,
            )
        except requests.RequestException as exc:
            return _connection_error(exc)
        return _to_result(response)

    def ask_question(self, question: str, limit: int = 4) -> ApiResult:
        return self._post_json("/ask-questions", {"question": question, "limit": limit})

    def _get(self, path: str) -> ApiResult:
        try:
            response = requests.get(f"{self._base_url}{path}", timeout=self._timeout_seconds)
        except requests.RequestException as exc:
            return _connection_error(exc)
        return _to_result(response)

    def _post_json(self, path: str, payload: dict[str, Any]) -> ApiResult:
        try:
            response = requests.post(
                f"{self._base_url}{path}",
                json=payload,
                timeout=self._timeout_seconds,
            )
        except requests.RequestException as exc:
            return _connection_error(exc)
        return _to_result(response)


def _to_result(response: requests.Response) -> ApiResult:
    try:
        data = response.json()
    except ValueError:
        data = {"detail": response.text or "API returned a non-JSON response."}
    return ApiResult(ok=response.ok, status_code=response.status_code, data=data)


def _connection_error(exc: requests.RequestException) -> ApiResult:
    return ApiResult(
        ok=False,
        status_code=0,
        data={"detail": f"Could not connect to the FastAPI service: {exc}"},
    )
