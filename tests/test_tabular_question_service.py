from pathlib import Path

from app.services.tabular_question_service import TableSource, TabularQuestionService


SAMPLE_DATA = Path("sample_data")


def _service() -> TabularQuestionService:
    return TabularQuestionService(
        table_sources=[
            TableSource(path=SAMPLE_DATA / "sales.csv", filename="sales.csv"),
            TableSource(path=SAMPLE_DATA / "renewals.xlsx", filename="renewals.xlsx"),
        ]
    )


def test_tabular_question_service_answers_highest_revenue_region() -> None:
    service = _service()

    result = service.answer("Which region has the highest revenue?")

    assert result.route == "structured"
    assert result.result == {"Region": "South", "Revenue_USD": 337500.0}
    assert result.answer == "The structured table result is Region: South, Revenue_USD: 337500.0."
    assert "sales.csv" in result.explanation


def test_tabular_question_service_answers_streaming_audio_count() -> None:
    service = _service()

    result = service.answer("How many streaming audio campaigns are there?")

    assert result.route == "structured"
    assert result.result == 3
    assert result.answer == "The structured table result is 3."


def test_tabular_question_service_answers_hybrid_attribution_question() -> None:
    service = _service()

    result = service.answer("How many high-risk renewals mention attribution issues?")

    assert result.route == "hybrid"
    assert result.result == 3
    assert result.answer == "The hybrid table result is 3."
    assert "renewals.xlsx" in result.explanation


def test_tabular_question_service_routes_semantic_questions_without_calculating() -> None:
    service = _service()

    result = service.answer("What issue did the advertiser report?")

    assert result.route == "semantic"
    assert result.result == "Use semantic retrieval for this question."


def test_tabular_question_service_asks_for_clarification_on_broad_questions() -> None:
    service = _service()

    result = service.answer("Tell me about data")

    assert result.route == "clarification"
    assert "more specific" in result.result


def test_tabular_question_service_uses_non_demo_table_columns(tmp_path) -> None:
    expense_file = tmp_path / "expenses.csv"
    expense_file.write_text(
        "Department,Amount\nEngineering,100\nMarketing,250\nEngineering,50\n",
        encoding="utf-8",
    )
    service = TabularQuestionService(
        table_sources=[TableSource(path=expense_file, filename="expenses.csv")]
    )

    result = service.answer("Which department has the highest amount?")

    assert result.route == "structured"
    assert result.result == {"Department": "Marketing", "Amount": 250.0}
    assert result.answer == "The structured table result is Department: Marketing, Amount: 250.0."
