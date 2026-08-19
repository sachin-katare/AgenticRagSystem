from pathlib import Path

from app.services.structured_analysis import StructuredAnalysisService


SAMPLE_DATA = Path("sample_data")


def test_structured_analysis_counts_filtered_csv_rows() -> None:
    service = StructuredAnalysisService()

    result = service.analyze(
        SAMPLE_DATA / "sales.csv",
        operation="count",
        filters={"Channel": "Streaming Audio"},
    )

    assert result.result == 3
    assert result.row_count == 3
    assert result.file == "sales.csv"


def test_structured_analysis_finds_highest_revenue_region_from_csv() -> None:
    service = StructuredAnalysisService()

    result = service.analyze(
        SAMPLE_DATA / "sales.csv",
        operation="max_group",
        value_column="Revenue_USD",
        group_by_column="Region",
    )

    assert result.result == {"Region": "South", "Revenue_USD": 337500.0}
    assert "Grouped by Region" in result.explanation


def test_structured_analysis_sums_filtered_csv_values() -> None:
    service = StructuredAnalysisService()

    result = service.analyze(
        SAMPLE_DATA / "sales.csv",
        operation="sum",
        value_column="Spend_USD",
        filters={"Channel": "Streaming Audio"},
    )

    assert result.result == 160000.0


def test_structured_analysis_counts_text_contains_after_filters_in_xlsx() -> None:
    service = StructuredAnalysisService()

    result = service.analyze(
        SAMPLE_DATA / "renewals.xlsx",
        operation="count_text_contains",
        value_column="Concern",
        filters={
            "Risk_Level": "High",
            "__contains__": "attribution",
        },
        sheet_name="Renewals",
    )

    assert result.result == 3
    assert result.row_count == 4


def test_structured_analysis_rejects_unknown_filter_column() -> None:
    service = StructuredAnalysisService()

    try:
        service.analyze(
            SAMPLE_DATA / "sales.csv",
            operation="count",
            filters={"Missing": "value"},
        )
    except ValueError as exc:
        assert "Unknown filter column" in str(exc)
    else:
        raise AssertionError("Expected ValueError for unknown filter column.")
