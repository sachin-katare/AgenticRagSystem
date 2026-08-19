from pathlib import Path

from app.services.loaders import load_document


SAMPLE_DATA = Path("sample_data")


def test_load_txt_extracts_one_text_unit() -> None:
    document = load_document(SAMPLE_DATA / "notes.txt")

    assert document.source_type == "txt"
    assert len(document.units) == 1
    assert "LumaWave" in document.units[0].text
    assert document.units[0].metadata["file"] == "notes.txt"


def test_load_pdf_extracts_page_units() -> None:
    document = load_document(SAMPLE_DATA / "policy.pdf")

    assert document.source_type == "pdf"
    assert len(document.units) >= 1
    assert all("page" in unit.metadata for unit in document.units)


def test_load_csv_extracts_row_units_and_schema() -> None:
    document = load_document(SAMPLE_DATA / "sales.csv")

    assert document.source_type == "csv"
    assert len(document.units) > 1
    assert document.tabular_schemas[0]["row_count"] == len(document.units)
    assert "Campaign_ID" in document.tabular_schemas[0]["columns"]


def test_load_xlsx_extracts_sheet_units_and_schemas() -> None:
    document = load_document(SAMPLE_DATA / "renewals.xlsx")

    assert document.source_type == "xlsx"
    assert len(document.units) > 1
    assert len(document.tabular_schemas) >= 1
    assert any("sheet" in unit.metadata for unit in document.units)
