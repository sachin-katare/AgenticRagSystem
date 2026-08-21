from fastapi import APIRouter, HTTPException, status

from app.agents.graph import build_agent_graph
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.models.schemas import AskRequest, AskResponse, SearchMatch
from app.services.exceptions import ExternalServiceError
from app.utils.safe_logging import safe_log_fields


router = APIRouter()
logger = get_logger()

agent_graph_override = None


def set_agent_graph_override(agent_graph) -> None:
    global agent_graph_override
    agent_graph_override = agent_graph


def get_agent_graph(settings):
    return agent_graph_override or build_agent_graph(settings)


@router.post("/ask-questions", response_model=AskResponse)
def ask_question(request: AskRequest) -> AskResponse:
    settings = get_settings()
    try:
        result = get_agent_graph(settings).invoke({"question": request.question, "limit": request.limit})
    except ValueError as exc:
        logger.warning(
            "ask_questions_rejected %s",
            safe_log_fields({"route": "/ask-questions", "reason": str(exc)}),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ExternalServiceError as exc:
        logger.error(
            "ask_questions_service_unavailable %s",
            safe_log_fields({"route": "/ask-questions", "reason": str(exc)}),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    citations = [
        SearchMatch(
            chunk_id=citation["chunk_id"],
            text=citation["text"],
            metadata=citation["metadata"],
            distance=citation["distance"],
        )
        for citation in result.get("citations", [])
    ]

    response = AskResponse(
        question=result["question"],
        answer=result["answer"],
        citation_count=len(citations),
        citations=citations,
        status=result["status"],
        trace=result.get("trace", []),
    )
    logger.info(
        "ask_questions_completed %s",
        safe_log_fields(
            {
                "route": "/ask-questions",
                "status": response.status,
                "citation_count": response.citation_count,
                "trace": response.trace,
            }
        ),
    )
    return response
