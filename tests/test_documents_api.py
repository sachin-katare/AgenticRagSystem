from pathlib import Path

from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routers.documents import set_indexing_service_override
from app.core.config import get_settings


SAMPLE_DATA = Path("sample_data")


class FakeIndexingService:
    def index_document(self, document):
        class Result:
            chunk_count = len(document.units)

        return Result()


def test_upload_document_accepts_txt_file() -> None:
    client = TestClient(app)
    set_indexing_service_override(FakeIndexingService())

    try:
        with (SAMPLE_DATA / "notes.txt").open("rb") as file:
            response = client.post(
                "/upload-document",
                files={"file": ("notes.txt", file, "text/plain")},
            )
    finally:
        set_indexing_service_override(None)

    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "notes.txt"
    assert body["source_type"] == "txt"
    assert body["extracted_unit_count"] == 1
    assert body["indexed_chunk_count"] == 1
    assert body["status"] == "uploaded"

    upload_directory = Path(get_settings().upload_directory)
    stored_files = list(upload_directory.glob(f"{body['document_id']}.*"))
    for stored_file in stored_files:
        stored_file.unlink()


def test_upload_document_rejects_unsupported_file_type() -> None:
    client = TestClient(app)

    response = client.post(
        "/upload-document",
        files={"file": ("notes.exe", b"not allowed", "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
