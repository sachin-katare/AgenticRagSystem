from dataclasses import dataclass
from pathlib import Path
from re import sub


SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".csv", ".xlsx"}


@dataclass(frozen=True)
class UploadValidation:
    safe_filename: str
    extension: str


def validate_upload_file(
    filename: str | None,
    size_bytes: int | None,
    max_upload_mb: int,
) -> UploadValidation:
    if not filename:
        raise ValueError("A filename is required.")

    original_name = Path(filename).name
    safe_filename = sub(r"[^A-Za-z0-9._-]", "_", original_name)
    extension = Path(safe_filename).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported file type. Allowed extensions: {allowed}.")

    if size_bytes is not None:
        max_bytes = max_upload_mb * 1024 * 1024
        if size_bytes <= 0:
            raise ValueError("Uploaded file is empty.")
        if size_bytes > max_bytes:
            raise ValueError(f"Uploaded file exceeds the {max_upload_mb} MB limit.")

    return UploadValidation(safe_filename=safe_filename, extension=extension)
