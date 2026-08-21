from app.core.config import Settings
from app.core.logging_config import get_logger
from app.services.query_classifier import QueryClassifier
from app.services.replier_service import ReplierResult, ReplierService
from app.services.search_service import SearcherService
from app.services.tabular_question_service import TabularQuestionResult, TabularQuestionService

from app.agents.state import AgentState
from app.utils.safe_logging import safe_log_fields


logger = get_logger()


class AgentNodes:
    """Thin LangGraph node implementations that orchestrate existing services."""

    def __init__(
        self,
        settings: Settings,
        classifier: QueryClassifier | None = None,
        searcher: SearcherService | None = None,
        replier: ReplierService | None = None,
        tabular_question_service: TabularQuestionService | None = None,
    ) -> None:
        self._classifier = classifier or QueryClassifier()
        self._searcher = searcher or SearcherService(settings)
        self._replier = replier or ReplierService(settings)
        self._tabular_question_service = tabular_question_service or TabularQuestionService()

    def validate_input(self, state: AgentState) -> AgentState:
        question = (state.get("question") or "").strip()
        trace = _append_trace(state, "Validator(input)")
        if not question:
            logger.warning(
                "agent_input_validation_failed %s",
                safe_log_fields({"agent": "Validator(input)", "reason": "Question is empty."}),
            )
            return {
                **state,
                "question": question,
                "route": "clarification",
                "answer": "Please ask a question.",
                "status": "clarification",
                "trace": trace,
                "error": "Question is empty.",
            }

        logger.info(
            "agent_input_validation_completed %s",
            safe_log_fields({"agent": "Validator(input)", "status": "accepted"}),
        )
        return {
            **state,
            "question": question,
            "trace": trace,
        }

    def plan(self, state: AgentState) -> AgentState:
        if state.get("status") == "clarification":
            return {**state, "trace": _append_trace(state, "Planner(skipped)")}

        classification = self._classifier.classify(state["question"])
        route = "rag" if classification.route == "semantic" else classification.route
        logger.info(
            "agent_planner_completed %s",
            safe_log_fields(
                {
                    "agent": "Planner",
                    "route": route,
                    "classification_reason": classification.reason,
                }
            ),
        )
        return {
            **state,
            "route": route,
            "trace": _append_trace(state, f"Planner(route={route})"),
        }

    def retrieve(self, state: AgentState) -> AgentState:
        route = state.get("route")
        if route == "rag":
            result = self._searcher.search(state["question"], limit=state.get("limit", 4))
            logger.info(
                "agent_retriever_completed %s",
                safe_log_fields({"agent": "Retriever", "route": "rag", "match_count": len(result.matches)}),
            )
            return {
                **state,
                "evidence": result.matches,
                "trace": _append_trace(state, "Retriever"),
            }

        if route in {"structured", "hybrid"}:
            result = self._tabular_question_service.answer(state["question"])
            if result.route == "clarification":
                search_result = self._searcher.search(state["question"], limit=state.get("limit", 4))
                logger.info(
                    "agent_retriever_fallback_completed %s",
                    safe_log_fields(
                        {
                            "agent": "Retriever",
                            "from_route": route,
                            "to_route": "rag",
                            "match_count": len(search_result.matches),
                        }
                    ),
                )
                return {
                    **state,
                    "route": "rag",
                    "evidence": search_result.matches,
                    "trace": _append_trace(state, "Retriever"),
                }
            logger.info(
                "agent_retriever_completed %s",
                safe_log_fields({"agent": "Retriever", "route": result.route}),
            )
            return {
                **state,
                "route": result.route,
                "result": result.result,
                "reasoning_result": result,
                "trace": _append_trace(state, "Retriever"),
            }

        return {**state, "trace": _append_trace(state, "Retriever(skipped)")}

    def reason(self, state: AgentState) -> AgentState:
        if state.get("route") == "rag":
            result: ReplierResult = self._replier.answer_from_matches(
                question=state["question"],
                matches=state.get("evidence", []),
            )
            logger.info(
                "agent_reasoner_completed %s",
                safe_log_fields({"agent": "Reasoner", "route": "rag", "status": result.status}),
            )
            return {
                **state,
                "reasoning_result": result,
                "trace": _append_trace(state, "Reasoner"),
            }

        if state.get("route") in {"structured", "hybrid"}:
            return {
                **state,
                "trace": _append_trace(state, "Reasoner"),
            }

        return {
            **state,
            "reasoning_result": TabularQuestionResult(
                question=state["question"],
                route="clarification",
                result="Please ask a more specific question.",
                answer="Please ask a more specific question.",
                explanation="The planner could not identify a supported route.",
            ),
            "trace": _append_trace(state, "Reasoner"),
        }

    def respond(self, state: AgentState) -> AgentState:
        result = state.get("reasoning_result")
        if isinstance(result, ReplierResult):
            citations = _serialize_citations(result.citations)
            logger.info(
                "agent_responder_completed %s",
                safe_log_fields(
                    {
                        "agent": "Responder",
                        "status": result.status,
                        "citation_count": len(citations),
                    }
                ),
            )
            return {
                **state,
                "answer": result.answer,
                "citations": citations,
                "status": result.status,
                "trace": _append_trace(state, "Responder"),
            }

        if isinstance(result, TabularQuestionResult):
            status = "clarification" if result.route == "clarification" else "answered"
            return {
                **state,
                "route": result.route,
                "answer": _append_explanation(result.answer, result.explanation),
                "result": result.result,
                "status": status,
                "trace": _append_trace(state, "Responder"),
            }

        return {
            **state,
            "answer": "I could not produce an answer from the current workflow state.",
            "status": "insufficient_evidence",
            "trace": _append_trace(state, "Responder"),
        }

    def validate_output(self, state: AgentState) -> AgentState:
        status = state.get("status") or "answered"
        if state.get("route") == "rag" and not state.get("citations"):
            status = "insufficient_evidence"

        logger.info(
            "agent_output_validation_completed %s",
            safe_log_fields({"agent": "Validator(output)", "status": status}),
        )
        return {
            **state,
            "status": status,
            "trace": _append_trace(state, "Validator(output)"),
        }


def choose_next_node(state: AgentState) -> str:
    route = state.get("route")
    if route == "clarification":
        return "reason"
    return "retrieve"


def _append_trace(state: AgentState, step: str) -> list[str]:
    return [*state.get("trace", []), step]


def _serialize_citations(citations) -> list[dict]:
    return [
        {
            "chunk_id": citation.chunk_id,
            "text": citation.text,
            "metadata": citation.metadata,
            "distance": citation.distance,
        }
        for citation in citations
    ]


def _append_explanation(answer: str, explanation: str) -> str:
    if not explanation:
        return answer
    return f"{answer} {explanation}"
