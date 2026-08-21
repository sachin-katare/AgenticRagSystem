from unittest.mock import Mock

import requests

from app.ui.api_client import FastApiClient


def test_api_client_calls_health_check(monkeypatch) -> None:
    response = Mock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {"status": "ok"}
    monkeypatch.setattr("app.ui.api_client.requests.get", Mock(return_value=response))

    result = FastApiClient().health_check()

    assert result.ok is True
    assert result.status_code == 200
    assert result.data == {"status": "ok"}


def test_api_client_uploads_document(monkeypatch) -> None:
    post = Mock()
    response = Mock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {"filename": "notes.txt", "status": "uploaded"}
    post.return_value = response
    monkeypatch.setattr("app.ui.api_client.requests.post", post)

    result = FastApiClient().upload_document("notes.txt", b"hello", "text/plain")

    assert result.ok is True
    assert result.data["status"] == "uploaded"
    assert post.call_args.kwargs["files"]["file"] == ("notes.txt", b"hello", "text/plain")


def test_api_client_asks_question(monkeypatch) -> None:
    post = Mock()
    response = Mock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {"answer": "Use citations. [1]", "status": "answered"}
    post.return_value = response
    monkeypatch.setattr("app.ui.api_client.requests.post", post)

    result = FastApiClient().ask_question("What rules apply?", limit=3)

    assert result.ok is True
    assert result.data["status"] == "answered"
    assert post.call_args.args[0] == "http://127.0.0.1:8000/ask-questions"
    assert post.call_args.kwargs["json"] == {"question": "What rules apply?", "limit": 3}


def test_api_client_returns_connection_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.ui.api_client.requests.get",
        Mock(side_effect=requests.ConnectionError("connection refused")),
    )

    result = FastApiClient().health_check()

    assert result.ok is False
    assert result.status_code == 0
    assert "Could not connect" in result.data["detail"]
