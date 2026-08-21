import logging
from pathlib import Path

from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routers.ask import set_agent_graph_override
from app.core.config import Settings
from app.core.logging_config import LOGGER_NAME, configure_logging
from app.utils.safe_logging import safe_log_fields


class FakeAgentGraph:
    def invoke(self, state: dict) -> dict:
        return {
            "question": state["question"].strip(),
            "answer": "Audio ads require approval. [1]",
            "citations": [
                {
                    "chunk_id": "chunk-1",
                    "text": "Audio campaigns require approval.",
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


def test_configure_logging_creates_log_file(tmp_path: Path) -> None:
    settings = Settings(log_directory=str(tmp_path), log_file="test.log", error_log_file="error.log")

    logger = configure_logging(settings)
    logger.info("logging_smoke_test")
    _flush_logger(logger)

    log_file = tmp_path / "test.log"
    assert log_file.exists(), f"Expected test log file at {log_file}"
    assert "logging_smoke_test" in log_file.read_text(
        encoding="utf-8"
    ), f"Expected log event in test log file at {log_file}"


def test_configure_logging_writes_warnings_to_error_log(tmp_path: Path) -> None:
    settings = Settings(log_directory=str(tmp_path), log_file="app.log", error_log_file="error.log")

    logger = configure_logging(settings)
    logger.info("normal_workflow_event")
    logger.warning("validation_warning_event")
    _flush_logger(logger)

    app_log_text = (tmp_path / "app.log").read_text(encoding="utf-8")
    error_log_text = (tmp_path / "error.log").read_text(encoding="utf-8")
    app_log_path = tmp_path / "app.log"
    error_log_path = tmp_path / "error.log"
    assert "normal_workflow_event" in app_log_text, f"Expected INFO event in {app_log_path}"
    assert "validation_warning_event" in app_log_text, f"Expected WARNING event in {app_log_path}"
    assert "normal_workflow_event" not in error_log_text, f"Unexpected INFO event in {error_log_path}"
    assert "validation_warning_event" in error_log_text, f"Expected WARNING event in {error_log_path}"


def test_configure_logging_uses_size_based_rotation(tmp_path: Path) -> None:
    settings = Settings(
        log_directory=str(tmp_path),
        log_file="rotating.log",
        error_log_file="rotating-error.log",
        log_max_bytes=120,
        log_backup_count=2,
    )

    logger = configure_logging(settings)
    for index in range(20):
        logger.info("rotation_test_event number=%s payload=abcdefghijklmnopqrstuvwxyz", index)
    _flush_logger(logger)

    assert (tmp_path / "rotating.log").exists(), f"Expected active rotating log at {tmp_path / 'rotating.log'}"
    assert (tmp_path / "rotating.log.1").exists(), (
        f"Expected rotated backup log at {tmp_path / 'rotating.log.1'}"
    )


def test_safe_log_fields_redacts_document_body_fields() -> None:
    fields = safe_log_fields(
        {
            "filename": "policy.pdf",
            "text": "full document body",
            "answer": "generated answer",
            "token": "secret token",
        }
    )

    assert fields["filename"] == "policy.pdf"
    assert fields["text"] == "[redacted]"
    assert fields["answer"] == "[redacted]"
    assert fields["token"] == "[redacted]"


def test_ask_endpoint_writes_safe_route_log(tmp_path: Path) -> None:
    settings = Settings(log_directory=str(tmp_path), log_file="api.log")
    configure_logging(settings)
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
    _flush_logger(logging.getLogger(LOGGER_NAME))
    log_text = (tmp_path / "api.log").read_text(encoding="utf-8")
    log_path = tmp_path / "api.log"
    assert "ask_questions_completed" in log_text, f"Expected ask route event in {log_path}"
    assert "/ask-questions" in log_text, f"Expected route name in {log_path}"
    assert "Validator(input)" in log_text, f"Expected agent trace in {log_path}"
    assert "Audio ads require approval" not in log_text, f"Answer body leaked into {log_path}"


def _flush_logger(logger: logging.Logger) -> None:
    for handler in logger.handlers:
        handler.flush()
