from app.services.tabular_question_service import TabularQuestionService


def test_tabular_question_service_answers_highest_revenue_region() -> None:
    service = TabularQuestionService()

    result = service.answer("Which region has the highest revenue?")

    assert result.route == "structured"
    assert result.result == {"Region": "South", "Revenue_USD": 337500.0}


def test_tabular_question_service_answers_streaming_audio_count() -> None:
    service = TabularQuestionService()

    result = service.answer("How many streaming audio campaigns are there?")

    assert result.route == "structured"
    assert result.result == 3


def test_tabular_question_service_answers_hybrid_attribution_question() -> None:
    service = TabularQuestionService()

    result = service.answer("How many high-risk renewals mention attribution issues?")

    assert result.route == "hybrid"
    assert result.result == 3


def test_tabular_question_service_routes_semantic_questions_without_calculating() -> None:
    service = TabularQuestionService()

    result = service.answer("What issue did the advertiser report?")

    assert result.route == "semantic"
    assert result.result == "Use semantic retrieval for this question."


def test_tabular_question_service_asks_for_clarification_on_broad_questions() -> None:
    service = TabularQuestionService()

    result = service.answer("Tell me about sales")

    assert result.route == "clarification"
    assert "more specific" in result.result
