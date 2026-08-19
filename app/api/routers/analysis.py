from pathlib import Path

from fastapi import APIRouter, HTTPException, status

from app.models.schemas import (
    AskTableRequest,
    AskTableResponse,
    StructuredAnalysisRequest,
    StructuredAnalysisResponse,
)
from app.services.structured_analysis import StructuredAnalysisService
from app.services.tabular_question_service import TabularQuestionService


router = APIRouter()

structured_analysis_service_override: StructuredAnalysisService | None = None
tabular_question_service_override: TabularQuestionService | None = None


def set_structured_analysis_service_override(
    structured_analysis_service: StructuredAnalysisService | None,
) -> None:
    global structured_analysis_service_override
    structured_analysis_service_override = structured_analysis_service


def get_structured_analysis_service() -> StructuredAnalysisService:
    return structured_analysis_service_override or StructuredAnalysisService()


def set_tabular_question_service_override(
    tabular_question_service: TabularQuestionService | None,
) -> None:
    global tabular_question_service_override
    tabular_question_service_override = tabular_question_service


def get_tabular_question_service() -> TabularQuestionService:
    return tabular_question_service_override or TabularQuestionService()


@router.post("/analyze_table", response_model=StructuredAnalysisResponse)
def analyze_table(request: StructuredAnalysisRequest) -> StructuredAnalysisResponse:
    try:
        result = get_structured_analysis_service().analyze(
            path=Path(request.path),
            operation=request.operation,
            value_column=request.value_column,
            group_by_column=request.group_by_column,
            filters=request.filters,
            sheet_name=request.sheet_name,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return StructuredAnalysisResponse(
        operation=result.operation,
        file=result.file,
        sheet=result.sheet,
        result=result.result,
        row_count=result.row_count,
        explanation=result.explanation,
    )


@router.post("/ask_table", response_model=AskTableResponse)
def ask_table(request: AskTableRequest) -> AskTableResponse:
    result = get_tabular_question_service().answer(request.question)
    return AskTableResponse(
        question=result.question,
        route=result.route,
        result=result.result,
        explanation=result.explanation,
    )
