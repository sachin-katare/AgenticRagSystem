from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.models.schemas import SearchMatch, SearchRequest, SearchResponse
from app.services.exceptions import ExternalServiceError
from app.services.search_service import SearcherService
from app.utils.safe_logging import safe_log_fields


router = APIRouter()
logger = get_logger()

searcher_service_override: SearcherService | None = None


def set_searcher_service_override(searcher_service: SearcherService | None) -> None:
    global searcher_service_override
    searcher_service_override = searcher_service


def get_searcher_service(settings) -> SearcherService:
    return searcher_service_override or SearcherService(settings)


@router.post("/search", response_model=SearchResponse)
def search_documents(request: SearchRequest) -> SearchResponse:
    settings = get_settings()
    try:
        result = get_searcher_service(settings).search(
            question=request.question,
            limit=request.limit,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ExternalServiceError as exc:
        logger.error(
            "search_service_unavailable %s",
            safe_log_fields({"route": "/search", "reason": str(exc)}),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    matches = [
        SearchMatch(
            chunk_id=match.chunk_id,
            text=match.text,
            metadata=match.metadata,
            distance=match.distance,
        )
        for match in result.matches
    ]

    return SearchResponse(
        question=result.question,
        match_count=len(matches),
        matches=matches,
    )
