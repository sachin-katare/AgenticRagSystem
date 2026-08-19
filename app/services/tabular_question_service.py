from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.services.hybrid_analysis import HybridAnalysisService
from app.services.query_classifier import QueryClassifier
from app.services.structured_analysis import StructuredAnalysisService


@dataclass(frozen=True)
class TabularQuestionResult:
    question: str
    route: str
    result: Any
    explanation: str


class TabularQuestionService:
    """Routes supported natural-language table questions to deterministic tools."""

    def __init__(
        self,
        classifier: QueryClassifier | None = None,
        structured_analysis: StructuredAnalysisService | None = None,
        hybrid_analysis: HybridAnalysisService | None = None,
    ) -> None:
        self._classifier = classifier or QueryClassifier()
        self._structured_analysis = structured_analysis or StructuredAnalysisService()
        self._hybrid_analysis = hybrid_analysis or HybridAnalysisService(
            structured_analysis=self._structured_analysis,
        )

    def answer(self, question: str, data_directory: Path = Path("sample_data")) -> TabularQuestionResult:
        clean_question = question.strip()
        classification = self._classifier.classify(clean_question)

        if classification.route == "clarification":
            return TabularQuestionResult(
                question=clean_question,
                route="clarification",
                result="Please ask a more specific table question.",
                explanation=classification.reason,
            )

        normalized_question = clean_question.lower()
        if classification.route == "structured":
            return self._answer_structured_question(clean_question, normalized_question, data_directory)

        if classification.route == "hybrid":
            return self._answer_hybrid_question(clean_question, normalized_question, data_directory)

        return TabularQuestionResult(
            question=clean_question,
            route="semantic",
            result="Use semantic retrieval for this question.",
            explanation=classification.reason,
        )

    def _answer_structured_question(
        self,
        question: str,
        normalized_question: str,
        data_directory: Path,
    ) -> TabularQuestionResult:
        if "highest revenue" in normalized_question and "region" in normalized_question:
            analysis = self._structured_analysis.analyze(
                path=data_directory / "sales.csv",
                operation="max_group",
                value_column="Revenue_USD",
                group_by_column="Region",
            )
            return _from_structured(question, "structured", analysis.result, analysis.explanation)

        if "streaming audio" in normalized_question and (
            "how many" in normalized_question or "count" in normalized_question
        ):
            analysis = self._structured_analysis.analyze(
                path=data_directory / "sales.csv",
                operation="count",
                filters={"Channel": "Streaming Audio"},
            )
            return _from_structured(question, "structured", analysis.result, analysis.explanation)

        if "streaming audio" in normalized_question and (
            "spend" in normalized_question or "total" in normalized_question
        ):
            analysis = self._structured_analysis.analyze(
                path=data_directory / "sales.csv",
                operation="sum",
                value_column="Spend_USD",
                filters={"Channel": "Streaming Audio"},
            )
            return _from_structured(question, "structured", analysis.result, analysis.explanation)

        return TabularQuestionResult(
            question=question,
            route="clarification",
            result="This structured table question is not supported yet.",
            explanation="The router detected a calculation, but no bounded operation matched it.",
        )

    def _answer_hybrid_question(
        self,
        question: str,
        normalized_question: str,
        data_directory: Path,
    ) -> TabularQuestionResult:
        if "high-risk" in normalized_question and "attribution" in normalized_question:
            analysis = self._hybrid_analysis.count_high_risk_attribution_renewals(
                path=data_directory / "renewals.xlsx",
                question=question,
            )
            return TabularQuestionResult(
                question=question,
                route=analysis.route,
                result=analysis.result,
                explanation=analysis.explanation,
            )

        return TabularQuestionResult(
            question=question,
            route="clarification",
            result="This hybrid table question is not supported yet.",
            explanation="The router detected meaning plus calculation, but no bounded hybrid operation matched it.",
        )


def _from_structured(
    question: str,
    route: str,
    result: Any,
    explanation: str,
) -> TabularQuestionResult:
    return TabularQuestionResult(
        question=question,
        route=route,
        result=result,
        explanation=explanation,
    )
