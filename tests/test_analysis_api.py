from pathlib import Path

from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routers.analysis import set_tabular_question_service_override
from app.services.tabular_question_service import TableSource, TabularQuestionService


def _tabular_service() -> TabularQuestionService:
    return TabularQuestionService(
        table_sources=[
            TableSource(path=Path("sample_data") / "sales.csv", filename="sales.csv"),
            TableSource(path=Path("sample_data") / "renewals.xlsx", filename="renewals.xlsx"),
        ]
    )


def test_analyze_table_endpoint_counts_filtered_rows() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze_table",
        json={
            "path": "sample_data/sales.csv",
            "operation": "count",
            "filters": {"Channel": "Streaming Audio"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "structured"
    assert body["result"] == 3
    assert body["row_count"] == 3


def test_analyze_table_endpoint_finds_highest_revenue_region() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze_table",
        json={
            "path": "sample_data/sales.csv",
            "operation": "max_group",
            "value_column": "Revenue_USD",
            "group_by_column": "Region",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "structured"
    assert body["result"] == {"Region": "South", "Revenue_USD": 337500.0}


def test_analyze_table_endpoint_returns_validation_error() -> None:
    client = TestClient(app)

    response = client.post(
        "/analyze_table",
        json={
            "path": "sample_data/sales.csv",
            "operation": "count",
            "filters": {"Missing": "value"},
        },
    )

    assert response.status_code == 400
    assert "Unknown filter column" in response.json()["detail"]


def test_ask_table_endpoint_answers_natural_language_structured_question() -> None:
    client = TestClient(app)
    set_tabular_question_service_override(_tabular_service())

    try:
        response = client.post(
            "/ask_table",
            json={"question": "Which region has the highest revenue?"},
        )
    finally:
        set_tabular_question_service_override(None)

    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "structured"
    assert body["result"] == {"Region": "South", "Revenue_USD": 337500.0}
    assert body["answer"] == "The structured table result is Region: South, Revenue_USD: 337500.0."


def test_ask_table_endpoint_answers_natural_language_hybrid_question() -> None:
    client = TestClient(app)
    set_tabular_question_service_override(_tabular_service())

    try:
        response = client.post(
            "/ask_table",
            json={"question": "How many high-risk renewals mention attribution issues?"},
        )
    finally:
        set_tabular_question_service_override(None)

    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "hybrid"
    assert body["result"] == 3
    assert body["answer"] == "The hybrid table result is 3."


def test_ask_table_endpoint_returns_clarification_for_broad_question() -> None:
    client = TestClient(app)
    set_tabular_question_service_override(_tabular_service())

    try:
        response = client.post(
            "/ask_table",
            json={"question": "Tell me about data"},
        )
    finally:
        set_tabular_question_service_override(None)

    assert response.status_code == 200
    body = response.json()
    assert body["route"] == "clarification"
    assert "more specific" in body["result"]
