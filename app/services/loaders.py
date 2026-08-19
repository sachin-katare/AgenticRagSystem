from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
from pypdf import PdfReader


@dataclass(frozen=True)
class ExtractedUnit:
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class LoadedDocument:
    filename: str
    source_type: str
    units: list[ExtractedUnit]
    tabular_schemas: list[dict[str, Any]] = field(default_factory=list)


def load_document(path: Path, original_filename: str | None = None) -> LoadedDocument:
    extension = path.suffix.lower()
    filename = original_filename or path.name

    if extension == ".txt":
        return _load_txt(path, filename)
    if extension == ".pdf":
        return _load_pdf(path, filename)
    if extension == ".csv":
        return _load_csv(path, filename)
    if extension == ".xlsx":
        return _load_xlsx(path, filename)

    raise ValueError(f"Unsupported file type: {extension}")


def _load_txt(path: Path, filename: str) -> LoadedDocument:
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise ValueError("No readable text was extracted from the TXT file.")

    return LoadedDocument(
        filename=filename,
        source_type="txt",
        units=[ExtractedUnit(text=text, metadata={"file": filename, "type": "txt"})],
    )


def _load_pdf(path: Path, filename: str) -> LoadedDocument:
    reader = PdfReader(str(path))
    units: list[ExtractedUnit] = []

    for page_index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            units.append(
                ExtractedUnit(
                    text=text,
                    metadata={"file": filename, "type": "pdf", "page": page_index},
                )
            )

    if not units:
        raise ValueError("No readable text was extracted from the PDF file.")

    return LoadedDocument(filename=filename, source_type="pdf", units=units)


def _load_csv(path: Path, filename: str) -> LoadedDocument:
    dataframe = pd.read_csv(path)
    return _load_dataframe(filename, "csv", dataframe, sheet_name=None)


def _load_xlsx(path: Path, filename: str) -> LoadedDocument:
    sheets = pd.read_excel(path, sheet_name=None)
    units: list[ExtractedUnit] = []
    schemas: list[dict[str, Any]] = []

    for sheet_name, dataframe in sheets.items():
        loaded_sheet = _load_dataframe(filename, "xlsx", dataframe, sheet_name=sheet_name)
        units.extend(loaded_sheet.units)
        schemas.extend(loaded_sheet.tabular_schemas)

    if not units:
        raise ValueError("No readable text was extracted from the XLSX file.")

    return LoadedDocument(filename=filename, source_type="xlsx", units=units, tabular_schemas=schemas)


def _load_dataframe(
    filename: str,
    source_type: str,
    dataframe: pd.DataFrame,
    sheet_name: str | None,
) -> LoadedDocument:
    if dataframe.empty:
        raise ValueError(f"No rows were found in the {source_type.upper()} file.")

    units: list[ExtractedUnit] = []
    for row_index, row in dataframe.fillna("").iterrows():
        values = [f"{column}: {row[column]}" for column in dataframe.columns if str(row[column]).strip()]
        if not values:
            continue

        metadata: dict[str, Any] = {
            "file": filename,
            "type": source_type,
            "row": int(row_index) + 2,
        }
        if sheet_name is not None:
            metadata["sheet"] = sheet_name

        units.append(ExtractedUnit(text="; ".join(values), metadata=metadata))

    if not units:
        raise ValueError(f"No readable row text was extracted from the {source_type.upper()} file.")

    schema: dict[str, Any] = {
        "file": filename,
        "type": source_type,
        "columns": list(dataframe.columns),
        "row_count": int(len(dataframe)),
    }
    if sheet_name is not None:
        schema["sheet"] = sheet_name

    return LoadedDocument(filename=filename, source_type=source_type, units=units, tabular_schemas=[schema])
