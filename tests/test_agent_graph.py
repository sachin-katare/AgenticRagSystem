from app.agents.graph import build_agent_graph
from app.core.config import get_settings
from app.services.replier_service import ReplierResult
from app.services.tabular_question_service import TabularQuestionResult
from app.services.vector_store import SearchResult


class FakeReplier:
    def answer(self, question: str) -> ReplierResult:
        return self.answer_from_matches(question, [])

    def answer_from_matches(self, question: str, matches: list[SearchResult]) -> ReplierResult:
        return ReplierResult(
            question=question,
            answer="Audio ads must follow campaign approval rules. [1]",
            citations=matches,
            status="answered",
        )


class FakeSearcher:
    def search(self, question: str, limit: int = 4):
        from app.services.search_service import SearcherResult

        return SearcherResult(
            question=question,
            matches=[
                SearchResult(
                    chunk_id="chunk-1",
                    text="Streaming audio placements follow campaign approval rules.",
                    metadata={"file": "policy.pdf", "page": 1},
                    distance=0.12,
                )
            ],
        )


class FakeTabularQuestionService:
    def answer(self, question: str) -> TabularQuestionResult:
        if "highest revenue" in question.lower():
            return TabularQuestionResult(
                question=question,
                route="structured",
                result={"Region": "South", "Revenue_USD": 337500.0},
                explanation="Structured calculation.",
            )
        if "tell me about sales" in question.lower():
            return TabularQuestionResult(
                question=question,
                route="clarification",
                result="Please ask a more specific table question.",
                explanation="Too broad.",
            )
        return TabularQuestionResult(
            question=question,
            route="hybrid",
            result=3,
            explanation="Hybrid calculation.",
        )


def test_agent_graph_routes_structured_questions_to_table_tool() -> None:
    from app.agents.nodes import AgentNodes

    nodes = AgentNodes(
        settings=get_settings(),
        searcher=FakeSearcher(),
        replier=FakeReplier(),
        tabular_question_service=FakeTabularQuestionService(),
    )
    graph = build_agent_graph(
        get_settings(),
        nodes=nodes,
    )
    # This verifies the graph compiles without calling real Ollama or Chroma services.
    assert graph is not None


def test_agent_graph_answers_structured_question_with_trace() -> None:
    from app.agents.nodes import AgentNodes

    nodes = AgentNodes(
        settings=get_settings(),
        searcher=FakeSearcher(),
        replier=FakeReplier(),
        tabular_question_service=FakeTabularQuestionService(),
    )
    graph = build_agent_graph(get_settings(), nodes=nodes)

    result = graph.invoke({"question": "Which region has the highest revenue?"})

    assert result["route"] == "structured"
    assert result["result"] == {"Region": "South", "Revenue_USD": 337500.0}
    assert result["trace"] == [
        "Validator(input)",
        "Planner",
        "Retriever",
        "Reasoner",
        "Responder",
        "Validator(output)",
    ]


def test_agent_graph_answers_hybrid_question_with_trace() -> None:
    from app.agents.nodes import AgentNodes

    nodes = AgentNodes(
        settings=get_settings(),
        searcher=FakeSearcher(),
        replier=FakeReplier(),
        tabular_question_service=FakeTabularQuestionService(),
    )
    graph = build_agent_graph(get_settings(), nodes=nodes)

    result = graph.invoke({"question": "How many high-risk renewals mention attribution issues?"})

    assert result["route"] == "hybrid"
    assert result["result"] == 3
    assert result["trace"] == [
        "Validator(input)",
        "Planner",
        "Retriever",
        "Reasoner",
        "Responder",
        "Validator(output)",
    ]


def test_agent_graph_routes_broad_question_to_clarification() -> None:
    from app.agents.nodes import AgentNodes

    nodes = AgentNodes(
        settings=get_settings(),
        searcher=FakeSearcher(),
        replier=FakeReplier(),
        tabular_question_service=FakeTabularQuestionService(),
    )
    graph = build_agent_graph(get_settings(), nodes=nodes)

    result = graph.invoke({"question": "Tell me about sales"})

    assert result["route"] == "clarification"
    assert result["status"] == "clarification"
    assert result["trace"] == [
        "Validator(input)",
        "Planner",
        "Reasoner",
        "Responder",
        "Validator(output)",
    ]


def test_agent_graph_answers_rag_question_with_six_agent_trace() -> None:
    from app.agents.nodes import AgentNodes

    nodes = AgentNodes(
        settings=get_settings(),
        searcher=FakeSearcher(),
        replier=FakeReplier(),
        tabular_question_service=FakeTabularQuestionService(),
    )
    graph = build_agent_graph(get_settings(), nodes=nodes)

    result = graph.invoke({"question": "What rules apply to audio ads?"})

    assert result["route"] == "rag"
    assert result["answer"] == "Audio ads must follow campaign approval rules. [1]"
    assert result["citations"][0]["metadata"]["file"] == "policy.pdf"
    assert result["trace"] == [
        "Validator(input)",
        "Planner",
        "Retriever",
        "Reasoner",
        "Responder",
        "Validator(output)",
    ]
