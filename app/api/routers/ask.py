from fastapi import APIRouter, HTTPException, status

from app.agents.graph import build_agent_graph
from app.core.config import get_settings
from app.models.schemas import AskRequest, AskResponse, SearchMatch


router = APIRouter()

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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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

    return AskResponse(
        question=result["question"],
        answer=result["answer"],
        citation_count=len(citations),
        citations=citations,
        status=result["status"],
        trace=result.get("trace", []),
    )
