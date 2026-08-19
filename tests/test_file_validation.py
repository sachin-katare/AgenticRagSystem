import pytest

from app.services.file_validation import validate_upload_file


def test_validate_upload_file_accepts_supported_extension() -> None:
    validation = validate_upload_file("campaign_notes.txt", 100, max_upload_mb=10)

    assert validation.safe_filename == "campaign_notes.txt"
    assert validation.extension == ".txt"


def test_validate_upload_file_rejects_unsupported_extension() -> None:
    with pytest.raises(ValueError, match="Unsupported file type"):
        validate_upload_file("campaign_notes.exe", 100, max_upload_mb=10)


def test_validate_upload_file_rejects_empty_file() -> None:
    with pytest.raises(ValueError, match="empty"):
        validate_upload_file("campaign_notes.txt", 0, max_upload_mb=10)
