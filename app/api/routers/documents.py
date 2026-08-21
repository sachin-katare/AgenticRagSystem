from pathlib import Path
from hashlib import sha256
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.models.schemas import DocumentUploadResponse
from app.services.document_catalogue import document_catalogue
from app.services.exceptions import ExternalServiceError
from app.services.file_validation import validate_upload_file
from app.services.indexing_service import DocumentIndexingService
from app.services.loaders import load_document
from app.utils.safe_logging import safe_log_fields


router = APIRouter()
logger = get_logger()

indexing_service_override: DocumentIndexingService | None = None


def set_indexing_service_override(indexing_service: DocumentIndexingService | None) -> None:
    global indexing_service_override
    indexing_service_override = indexing_service


def get_indexing_service(settings) -> DocumentIndexingService:
    return indexing_service_override or DocumentIndexingService(settings)


@router.post("/upload-document", response_model=DocumentUploadResponse)
def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    settings = get_settings()
    upload_path: Path | None = None
    try:
        validation = validate_upload_file(file.filename, file.size, settings.max_upload_mb)
        file_bytes = file.file.read()
        content_hash = sha256(file_bytes).hexdigest()
        existing_record = document_catalogue.find_by_content_hash(content_hash)
        if existing_record is not None:
            logger.warning(
                "upload_document_duplicate_rejected %s",
                safe_log_fields(
                    {
                        "route": "/upload-document",
                        "filename": validation.safe_filename,
                        "existing_document_id": existing_record.document_id,
                        "existing_filename": existing_record.filename,
                    }
                ),
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"This document was already uploaded as {existing_record.filename}.",
            )

        document_id = str(uuid4())
        upload_path = Path(settings.upload_directory) / f"{document_id}{validation.extension}"

        upload_path.parent.mkdir(parents=True, exist_ok=True)
        with upload_path.open("wb") as output_file:
            output_file.write(file_bytes)

        loaded_document = load_document(upload_path, original_filename=validation.safe_filename)
        indexing_result = get_indexing_service(settings).index_document(loaded_document)
        record = document_catalogue.add(
            document_id=document_id,
            filename=validation.safe_filename,
            source_type=loaded_document.source_type,
            stored_path=str(upload_path),
            extracted_unit_count=len(loaded_document.units),
            tabular_schema_count=len(loaded_document.tabular_schemas),
            content_hash=content_hash,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        _remove_saved_upload(upload_path)
        logger.warning(
            "upload_document_rejected %s",
            safe_log_fields(
                {
                    "route": "/upload-document",
                    "filename": file.filename,
                    "reason": str(exc),
                }
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ExternalServiceError as exc:
        _remove_saved_upload(upload_path)
        logger.error(
            "upload_document_service_unavailable %s",
            safe_log_fields(
                {
                    "route": "/upload-document",
                    "filename": file.filename,
                    "reason": str(exc),
                }
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    logger.info(
        "upload_document_completed %s",
        safe_log_fields(
            {
                "route": "/upload-document",
                "document_id": record.document_id,
                "filename": record.filename,
                "source_type": record.source_type,
                "extracted_unit_count": record.extracted_unit_count,
                "tabular_schema_count": record.tabular_schema_count,
                "indexed_chunk_count": indexing_result.chunk_count,
            }
        ),
    )

    return DocumentUploadResponse(
        document_id=record.document_id,
        filename=record.filename,
        source_type=record.source_type,
        extracted_unit_count=record.extracted_unit_count,
        tabular_schema_count=record.tabular_schema_count,
        indexed_chunk_count=indexing_result.chunk_count,
        status="uploaded",
    )


def _remove_saved_upload(upload_path: Path | None) -> None:
    if upload_path is not None and upload_path.exists():
        upload_path.unlink()
