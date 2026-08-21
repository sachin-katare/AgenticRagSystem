from dataclasses import dataclass
from typing import Literal


QueryRoute = Literal["semantic", "structured", "hybrid", "clarification"]


@dataclass(frozen=True)
class QueryClassification:
    route: QueryRoute
    reason: str


class QueryClassifier:
    """Deterministic route classifier for Phase 7 tabular questions."""

    def classify(self, question: str) -> QueryClassification:
        normalized_question = " ".join(question.lower().split())
        if not normalized_question:
            return QueryClassification(
                route="clarification",
                reason="The question is empty.",
            )

        if _is_ambiguous(normalized_question):
            return QueryClassification(
                route="clarification",
                reason="The question is too broad and needs a clearer intent.",
            )

        has_calculation_intent = _has_calculation_intent(normalized_question)
        has_meaning_intent = _has_meaning_intent(normalized_question)

        if has_calculation_intent and has_meaning_intent:
            return QueryClassification(
                route="hybrid",
                reason="The question combines semantic meaning with a deterministic calculation.",
            )

        if has_calculation_intent:
            return QueryClassification(
                route="structured",
                reason="The question asks for an exact table calculation.",
            )

        return QueryClassification(
            route="semantic",
            reason="The question asks for meaning or explanation from document text.",
        )


def _is_ambiguous(question: str) -> bool:
    ambiguous_questions = {
        "tell me about data",
        "show data",
        "summarize data",
        "analyze data",
    }
    return question in ambiguous_questions


def _has_calculation_intent(question: str) -> bool:
    calculation_phrases = [
        "how many",
        "count",
        "total",
        "sum",
        "average",
        "highest",
        "lowest",
        "maximum",
        "minimum",
    ]
    return any(phrase in question for phrase in calculation_phrases)


def _has_meaning_intent(question: str) -> bool:
    meaning_phrases = [
        "mention",
        "mentions",
        "issue",
        "issues",
        "concern",
        "concerns",
        "why",
        "explain",
        "describe",
        "reported",
        "risk",
    ]
    return any(phrase in question for phrase in meaning_phrases)
