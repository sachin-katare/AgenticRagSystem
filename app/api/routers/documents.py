from pathlib import Path
from shutil import copyfileobj
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.models.schemas import DocumentUploadResponse
from app.services.document_catalogue import document_catalogue
from app.services.file_validation import validate_upload_file
from app.services.indexing_service import DocumentIndexingService
from app.services.loaders import load_document


router = APIRouter()

indexing_service_override: DocumentIndexingService | None = None


def set_indexing_service_override(indexing_service: DocumentIndexingService | None) -> None:
    global indexing_service_override
    indexing_service_override = indexing_service


def get_indexing_service(settings) -> DocumentIndexingService:
    return indexing_service_override or DocumentIndexingService(settings)


@router.post("/upload-document", response_model=DocumentUploadResponse)
def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    settings = get_settings()
    try:
        validation = validate_upload_file(file.filename, file.size, settings.max_upload_mb)
        document_id = str(uuid4())
        upload_path = Path(settings.upload_directory) / f"{document_id}{validation.extension}"

        upload_path.parent.mkdir(parents=True, exist_ok=True)
        with upload_path.open("wb") as output_file:
            copyfileobj(file.file, output_file)

        loaded_document = load_document(upload_path, original_filename=validation.safe_filename)
        indexing_result = get_indexing_service(settings).index_document(loaded_document)
        record = document_catalogue.add(
            document_id=document_id,
            filename=validation.safe_filename,
            source_type=loaded_document.source_type,
            stored_path=str(upload_path),
            extracted_unit_count=len(loaded_document.units),
            tabular_schema_count=len(loaded_document.tabular_schemas),
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return DocumentUploadResponse(
        document_id=record.document_id,
        filename=record.filename,
        source_type=record.source_type,
        extracted_unit_count=record.extracted_unit_count,
        tabular_schema_count=record.tabular_schema_count,
        indexed_chunk_count=indexing_result.chunk_count,
        status="uploaded",
    )
