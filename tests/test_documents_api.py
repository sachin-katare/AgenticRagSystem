from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routers.documents import set_indexing_service_override
from app.core.config import get_settings
from app.services.document_catalogue import document_catalogue
from app.services.exceptions import ExternalServiceError


SAMPLE_DATA = Path("sample_data")


class FakeIndexingService:
    def index_document(self, document):
        class Result:
            chunk_count = len(document.units)

        return Result()


class UnavailableIndexingService:
    def index_document(self, document):
        raise ExternalServiceError("Ollama embedding service is unavailable.")


def test_upload_document_accepts_txt_file() -> None:
    client = TestClient(app)
    set_indexing_service_override(FakeIndexingService())
    unique_content = f"unique happy path upload test content {uuid4()}".encode()

    try:
        response = client.post(
            "/upload-document",
            files={"file": ("happy-path-upload.txt", unique_content, "text/plain")},
        )
    finally:
        set_indexing_service_override(None)

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "happy-path-upload.txt"
    assert body["source_type"] == "txt"
    assert body["extracted_unit_count"] == 1
    assert body["indexed_chunk_count"] == 1
    assert body["status"] == "uploaded"

    upload_directory = Path(get_settings().upload_directory)
    stored_files = list(upload_directory.glob(f"{body['document_id']}.*"))
    for stored_file in stored_files:
        stored_file.unlink()
    document_catalogue.remove(body["document_id"])


def test_upload_document_rejects_unsupported_file_type() -> None:
    client = TestClient(app)

    response = client.post(
        "/upload-document",
        files={"file": ("notes.exe", b"not allowed", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


def test_upload_document_returns_friendly_service_unavailable_error() -> None:
    client = TestClient(app)
    set_indexing_service_override(UnavailableIndexingService())
    unique_content = f"unique unavailable service test content {uuid4()}".encode()

    try:
        response = client.post(
            "/upload-document",
            files={"file": ("unavailable-service.txt", unique_content, "text/plain")},
        )
    finally:
        set_indexing_service_override(None)

    assert response.status_code == 503
    assert "Ollama embedding service is unavailable" in response.json()["detail"]


def test_upload_document_rejects_duplicate_content() -> None:
    client = TestClient(app)
    set_indexing_service_override(FakeIndexingService())
    unique_content = f"unique duplicate detection test content {uuid4()}".encode()
    created_document_id = ""

    try:
        first_response = client.post(
            "/upload-document",
            files={"file": ("duplicate-source.txt", unique_content, "text/plain")},
        )
        if first_response.status_code == 200:
            created_document_id = first_response.json()["document_id"]
        duplicate_response = client.post(
            "/upload-document",
            files={"file": ("renamed-duplicate-source.txt", unique_content, "text/plain")},
        )
    finally:
        set_indexing_service_override(None)
        if created_document_id:
            record = document_catalogue.remove(created_document_id)
            if record is not None:
                stored_path = Path(record.stored_path)
                if stored_path.exists():
                    stored_path.unlink()

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 409
    assert "already uploaded as duplicate-source.txt" in duplicate_response.json()["detail"]
