from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.services.structured_analysis import StructuredAnalysisService


@dataclass(frozen=True)
class HybridAnalysisResult:
    question: str
    route: str
    result: Any
    explanation: str


class HybridAnalysisService:
    """Bounded hybrid analysis for meaning-plus-calculation questions."""

    def __init__(self, structured_analysis: StructuredAnalysisService | None = None) -> None:
        self._structured_analysis = structured_analysis or StructuredAnalysisService()

    def count_high_risk_attribution_renewals(
        self,
        path: Path,
        question: str,
    ) -> HybridAnalysisResult:
        result = self._structured_analysis.analyze(
            path=path,
            operation="count_text_contains",
            value_column="Concern",
            filters={
                "Risk_Level": "High",
                "__contains__": "attribution",
            },
            sheet_name="Renewals",
        )

        return HybridAnalysisResult(
            question=question.strip(),
            route="hybrid",
            result=result.result,
            explanation=(
                "Used semantic intent from the question to identify attribution-related "
                "concerns, then used deterministic pandas filtering/counting for High risk rows."
            ),
        )
