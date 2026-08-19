from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import pandas as pd


Operation = Literal["count", "sum", "average", "max_group", "count_text_contains"]


@dataclass(frozen=True)
class StructuredAnalysisResult:
    operation: str
    file: str
    sheet: str | None
    result: Any
    row_count: int
    explanation: str


class StructuredAnalysisService:
    """Deterministic analysis for CSV/XLSX files using pandas."""

    def analyze(
        self,
        path: Path,
        operation: Operation,
        value_column: str | None = None,
        group_by_column: str | None = None,
        filters: dict[str, Any] | None = None,
        sheet_name: str | None = None,
    ) -> StructuredAnalysisResult:
        dataframe = self._load_dataframe(path, sheet_name)
        filters = filters or {}
        search_text = _extract_search_text(filters)
        filtered_dataframe = self._apply_filters(dataframe, filters)

        if operation == "count":
            result = int(len(filtered_dataframe))
            explanation = f"Counted {result} matching rows."
        elif operation == "sum":
            column = _require_column(value_column, "sum")
            result = float(filtered_dataframe[column].sum())
            explanation = f"Summed {column} across {len(filtered_dataframe)} matching rows."
        elif operation == "average":
            column = _require_column(value_column, "average")
            result = float(filtered_dataframe[column].mean())
            explanation = f"Averaged {column} across {len(filtered_dataframe)} matching rows."
        elif operation == "max_group":
            column = _require_column(value_column, "max_group")
            group_column = _require_group_column(group_by_column)
            grouped = filtered_dataframe.groupby(group_column)[column].sum()
            winning_group = grouped.idxmax()
            winning_value = float(grouped.max())
            result = {
                group_column: winning_group,
                column: winning_value,
            }
            explanation = (
                f"Grouped by {group_column}, summed {column}, and selected the highest group."
            )
        elif operation == "count_text_contains":
            column = _require_column(value_column, "count_text_contains")
            search_text = _require_search_text(search_text)
            result = int(
                filtered_dataframe[column]
                .fillna("")
                .astype(str)
                .str.contains(search_text, case=False, regex=False)
                .sum()
            )
            explanation = (
                f"Counted rows where {column} contains '{search_text}' after applying filters."
            )
        else:
            raise ValueError(f"Unsupported operation: {operation}")

        return StructuredAnalysisResult(
            operation=operation,
            file=path.name,
            sheet=sheet_name,
            result=result,
            row_count=int(len(filtered_dataframe)),
            explanation=explanation,
        )

    def _load_dataframe(self, path: Path, sheet_name: str | None) -> pd.DataFrame:
        extension = path.suffix.lower()
        if extension == ".csv":
            return pd.read_csv(path)
        if extension == ".xlsx":
            selected_sheet = sheet_name or 0
            return pd.read_excel(path, sheet_name=selected_sheet)
        raise ValueError(f"Structured analysis supports CSV and XLSX only: {extension}")

    def _apply_filters(
        self,
        dataframe: pd.DataFrame,
        filters: dict[str, Any],
    ) -> pd.DataFrame:
        filtered_dataframe = dataframe
        for column, expected_value in filters.items():
            if column not in filtered_dataframe.columns:
                raise ValueError(f"Unknown filter column: {column}")
            filtered_dataframe = filtered_dataframe[
                filtered_dataframe[column].astype(str).str.lower()
                == str(expected_value).lower()
            ]
        return filtered_dataframe


def _require_column(column: str | None, operation: str) -> str:
    if not column:
        raise ValueError(f"{operation} requires a value column.")
    return column


def _require_group_column(column: str | None) -> str:
    if not column:
        raise ValueError("max_group requires a group-by column.")
    return column


def _extract_search_text(filters: dict[str, Any]) -> str | None:
    return filters.pop("__contains__", None)


def _require_search_text(search_text: str | None) -> str:
    if not search_text:
        raise ValueError("count_text_contains requires a __contains__ filter value.")
    return str(search_text)
