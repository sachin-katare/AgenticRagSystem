from typing import Any, TypedDict

from app.models.schemas import SearchMatch


class AgentState(TypedDict, total=False):
    question: str
    route: str
    answer: str
    result: Any
    evidence: list[Any]
    reasoning_result: Any
    citations: list[SearchMatch]
    status: str
    trace: list[str]
    error: str
