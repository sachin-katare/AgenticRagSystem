import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from app.services.document_catalogue import DocumentCatalogue, document_catalogue
from app.services.query_classifier import QueryClassifier


@dataclass(frozen=True)
class TabularQuestionResult:
    question: str
    route: str
    result: Any
    answer: str
    explanation: str


@dataclass(frozen=True)
class TableSource:
    path: Path
    filename: str
    sheet_name: str | None = None


@dataclass(frozen=True)
class LoadedTable:
    source: TableSource
    dataframe: pd.DataFrame


@dataclass(frozen=True)
class HybridCandidate:
    table: LoadedTable
    filters: dict[str, Any]
    count: int


@dataclass(frozen=True)
class MetricDefinition:
    name: str
    label: str
    aliases: tuple[str, ...]
    numerator_column: str
    denominator_column: str


class TabularQuestionService:
    """Routes supported natural-language table questions to uploaded table data."""

    def __init__(
        self,
        classifier: QueryClassifier | None = None,
        catalogue: DocumentCatalogue | None = None,
        table_sources: list[TableSource] | None = None,
    ) -> None:
        self._classifier = classifier or QueryClassifier()
        self._catalogue = catalogue or document_catalogue
        self._table_sources = table_sources

    def answer(self, question: str) -> TabularQuestionResult:
        clean_question = question.strip()
        classification = self._classifier.classify(clean_question)

        if classification.route == "clarification":
            return _result(
                question=clean_question,
                route="clarification",
                result="Please ask a more specific table question.",
                answer="Please ask a more specific table question.",
                explanation=classification.reason,
            )

        if classification.route == "semantic":
            return _result(
                question=clean_question,
                route="semantic",
                result="Use semantic retrieval for this question.",
                answer="Use semantic retrieval for this question.",
                explanation=classification.reason,
            )

        tables = self._load_tables()
        if not tables:
            return _result(
                question=clean_question,
                route="clarification",
                result="No uploaded CSV or Excel table is available for deterministic analysis.",
                answer="No uploaded CSV or Excel table is available for deterministic analysis.",
                explanation="Upload a CSV or XLSX file before asking a table calculation question.",
            )

        normalized_question = _normalize_text(clean_question)
        if classification.route == "structured":
            return self._answer_structured_question(clean_question, normalized_question, tables)

        if classification.route == "hybrid":
            return self._answer_hybrid_question(clean_question, normalized_question, tables)

        return _result(
            question=clean_question,
            route="clarification",
            result="The table question could not be routed.",
            answer="The table question could not be routed.",
            explanation=classification.reason,
        )

    def _answer_structured_question(
        self,
        question: str,
        normalized_question: str,
        tables: list[LoadedTable],
    ) -> TabularQuestionResult:
        if any(term in normalized_question for term in {"highest", "maximum", "lowest", "minimum"}):
            for table in tables:
                metric = _find_mentioned_metric(table.dataframe, normalized_question)
                value_column = _find_mentioned_numeric_column(table.dataframe, normalized_question)
                metric_series = _metric_series(table.dataframe, metric or value_column)
                if metric_series is None:
                    continue
                group_column = _find_result_dimension_column(table.dataframe, normalized_question)
                if group_column:
                    aggregate_operation = _aggregate_operation_for_metric(metric)
                    grouped = metric_series.groupby(table.dataframe[group_column]).agg(aggregate_operation)
                    if grouped.empty:
                        continue
                    is_lowest = any(term in normalized_question for term in {"lowest", "minimum"})
                    winning_group = grouped.idxmin() if is_lowest else grouped.idxmax()
                    winning_value = float(grouped.min() if is_lowest else grouped.max())
                    result_key = metric.label if metric else str(value_column)
                    result = {group_column: _plain_value(winning_group), result_key: winning_value}
                    direction = "lowest" if is_lowest else "highest"
                    metric_verb = _metric_description(metric, value_column)
                    aggregate_description = _aggregate_description(metric)
                    return _result(
                        question=question,
                        route="structured",
                        result=result,
                        answer=f"The structured table result is {_format_mapping(result)}.",
                        explanation=(
                            f"Used {table.source.filename}{_sheet_suffix(table.source.sheet_name)}. "
                            f"Grouped by {group_column}, {aggregate_description} {metric_verb}, and selected the {direction} group."
                        ),
                    )

        filters = _find_exact_value_filters(tables, normalized_question)
        if any(term in normalized_question for term in {"how many", "count"}):
            table, table_filters = _first_filter_match(tables, filters)
            if table:
                filtered = _apply_exact_filters(table.dataframe, table_filters)
                count = int(len(filtered))
                return _result(
                    question=question,
                    route="structured",
                    result=count,
                    answer=f"The structured table result is {count}.",
                    explanation=(
                        f"Used {table.source.filename}{_sheet_suffix(table.source.sheet_name)}. "
                        f"Counted rows after applying filters: {_format_filters(table_filters)}."
                    ),
                )

        if any(term in normalized_question for term in {"total", "sum", "average"}):
            for table in tables:
                metric = _find_mentioned_metric(table.dataframe, normalized_question)
                value_column = _find_mentioned_numeric_column(table.dataframe, normalized_question)
                metric_series = _metric_series(table.dataframe, metric or value_column)
                if metric_series is None:
                    continue
                table_filters = filters.get(id(table), {})
                filtered = _apply_exact_filters(table.dataframe.assign(__metric__=metric_series), table_filters)
                if "average" in normalized_question:
                    value = float(filtered["__metric__"].mean())
                    operation = "Averaged"
                else:
                    value = float(filtered["__metric__"].sum())
                    operation = "Summed"
                metric_verb = _metric_description(metric, value_column)
                return _result(
                    question=question,
                    route="structured",
                    result=value,
                    answer=f"The structured table result is {value}.",
                    explanation=(
                        f"Used {table.source.filename}{_sheet_suffix(table.source.sheet_name)}. "
                        f"{operation} {metric_verb} after applying filters: {_format_filters(table_filters)}."
                    ),
                )

        return _result(
            question=question,
            route="clarification",
            result="This structured table question is not supported yet.",
            answer="This structured table question is not supported yet.",
            explanation=(
                "The router detected a calculation, but no uploaded table had enough matching "
                "columns and values for a bounded deterministic operation."
            ),
        )

    def _answer_hybrid_question(
        self,
        question: str,
        normalized_question: str,
        tables: list[LoadedTable],
    ) -> TabularQuestionResult:
        filters = _find_exact_value_filters(tables, normalized_question)
        search_terms = _extract_search_terms(normalized_question, filters)
        if not search_terms:
            return _result(
                question=question,
                route="clarification",
                result="This hybrid table question needs a clearer text condition.",
                answer="This hybrid table question needs a clearer text condition.",
                explanation="The router detected meaning plus calculation, but no searchable term was found.",
            )

        candidates: list[HybridCandidate] = []
        for table in tables:
            table_filters = filters.get(id(table), {})
            filtered = _apply_exact_filters(table.dataframe, table_filters)
            if filtered.empty:
                continue
            text_mask = _text_contains_any(filtered, search_terms)
            count = int(text_mask.sum())
            if count > 0:
                candidates.append(HybridCandidate(table=table, filters=table_filters, count=count))

        if candidates:
            candidate = max(candidates, key=lambda item: (len(item.filters), item.count))
            return _result(
                question=question,
                route="hybrid",
                result=candidate.count,
                answer=f"The hybrid table result is {candidate.count}.",
                explanation=(
                    f"Used {candidate.table.source.filename}{_sheet_suffix(candidate.table.source.sheet_name)}. "
                    f"Applied exact filters {_format_filters(candidate.filters)}, then counted rows containing "
                    f"semantic term(s): {', '.join(search_terms)}."
                ),
            )

        return _result(
            question=question,
            route="clarification",
            result="This hybrid table question did not match uploaded table rows.",
            answer="This hybrid table question did not match uploaded table rows.",
            explanation="No uploaded table matched both the exact filters and semantic text terms.",
        )

    def _load_tables(self) -> list[LoadedTable]:
        sources = self._table_sources if self._table_sources is not None else self._catalogue_table_sources()
        tables: list[LoadedTable] = []
        for source in sources:
            if not source.path.exists():
                continue
            if source.path.suffix.lower() == ".csv":
                tables.append(LoadedTable(source=source, dataframe=pd.read_csv(source.path)))
            elif source.path.suffix.lower() == ".xlsx":
                sheets = pd.read_excel(source.path, sheet_name=None)
                for sheet_name, dataframe in sheets.items():
                    tables.append(
                        LoadedTable(
                            source=TableSource(
                                path=source.path,
                                filename=source.filename,
                                sheet_name=sheet_name,
                            ),
                            dataframe=dataframe,
                        )
                    )
        return tables

    def _catalogue_table_sources(self) -> list[TableSource]:
        sources: list[TableSource] = []
        for record in self._catalogue.list():
            if record.source_type in {"csv", "xlsx"}:
                sources.append(
                    TableSource(
                        path=Path(record.stored_path),
                        filename=record.filename,
                    )
                )
        return sources


def _result(
    question: str,
    route: str,
    result: Any,
    answer: str,
    explanation: str,
) -> TabularQuestionResult:
    return TabularQuestionResult(
        question=question,
        route=route,
        result=result,
        answer=answer,
        explanation=explanation,
    )


def _normalize_text(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())


DERIVED_METRICS = (
    MetricDefinition(
        name="click_through_rate",
        label="Click_Through_Rate",
        aliases=("click through rate", "ctr"),
        numerator_column="Clicks",
        denominator_column="Impressions",
    ),
    MetricDefinition(
        name="return_on_ad_spend",
        label="Return_On_Ad_Spend",
        aliases=("return on ad spend", "roas"),
        numerator_column="Revenue_USD",
        denominator_column="Spend_USD",
    ),
    MetricDefinition(
        name="conversion_rate",
        label="Conversion_Rate",
        aliases=("conversion rate",),
        numerator_column="Conversions",
        denominator_column="Clicks",
    ),
)


def _column_tokens(column: str) -> set[str]:
    return set(_normalize_text(column).split())


def _find_mentioned_metric(dataframe: pd.DataFrame, normalized_question: str) -> MetricDefinition | None:
    for metric in DERIVED_METRICS:
        if any(alias in normalized_question for alias in metric.aliases):
            if metric.numerator_column in dataframe.columns and metric.denominator_column in dataframe.columns:
                return metric
    return None


def _find_mentioned_numeric_column(dataframe: pd.DataFrame, normalized_question: str) -> str | None:
    numeric_columns = list(dataframe.select_dtypes(include="number").columns)
    return _find_mentioned_column(numeric_columns, normalized_question)


def _find_mentioned_non_numeric_column(dataframe: pd.DataFrame, normalized_question: str) -> str | None:
    non_numeric_columns = [column for column in dataframe.columns if column not in dataframe.select_dtypes(include="number").columns]
    return _find_mentioned_column(non_numeric_columns, normalized_question)


def _find_result_dimension_column(dataframe: pd.DataFrame, normalized_question: str) -> str | None:
    non_numeric_columns = [
        str(column)
        for column in dataframe.columns
        if column not in dataframe.select_dtypes(include="number").columns
    ]
    question_tokens = set(normalized_question.split())
    best_column: str | None = None
    best_score: tuple[float, float] | None = None
    for column in non_numeric_columns:
        score = _score_dimension_column(column, question_tokens)
        if score[0] <= 0:
            continue
        if best_score is None or score > best_score:
            best_column = column
            best_score = score
    return best_column or _find_mentioned_non_numeric_column(dataframe, normalized_question)


def _find_mentioned_column(columns: list[str], normalized_question: str) -> str | None:
    question_tokens = set(normalized_question.split())
    best_column: str | None = None
    best_score = 0
    for column in columns:
        tokens = _column_tokens(str(column))
        score = len(tokens & question_tokens)
        if score > best_score:
            best_column = str(column)
            best_score = score
    return best_column


def _score_dimension_column(column: str, question_tokens: set[str]) -> tuple[float, float]:
    tokens = _column_tokens(str(column))
    overlap = len(tokens & question_tokens)
    readable_bonus = 1.0 if tokens & {"name", "title", "label"} else 0.0
    identifier_penalty = -1.0 if tokens & {"id", "code", "key", "number"} else 0.0
    return (float(overlap) + readable_bonus + identifier_penalty, float(overlap))


def _metric_series(dataframe: pd.DataFrame, metric: MetricDefinition | str | None) -> pd.Series | None:
    if metric is None:
        return None
    if isinstance(metric, MetricDefinition):
        denominator = dataframe[metric.denominator_column].replace(0, pd.NA)
        return dataframe[metric.numerator_column] / denominator
    return dataframe[str(metric)]


def _aggregate_operation_for_metric(metric: MetricDefinition | None) -> str:
    return "mean" if metric is not None else "sum"


def _aggregate_description(metric: MetricDefinition | None) -> str:
    return "averaged" if metric is not None else "summed"


def _metric_description(metric: MetricDefinition | None, value_column: str | None) -> str:
    if metric is not None:
        return metric.label
    return str(value_column)


def _find_exact_value_filters(
    tables: list[LoadedTable],
    normalized_question: str,
) -> dict[int, dict[str, Any]]:
    filters_by_table: dict[int, dict[str, Any]] = {}
    for table in tables:
        filters: dict[str, Any] = {}
        for column in table.dataframe.columns:
            if pd.api.types.is_numeric_dtype(table.dataframe[column]):
                continue
            unique_values = table.dataframe[column].dropna().astype(str).unique()
            for value in unique_values:
                normalized_value = _normalize_text(value)
                if normalized_value and _contains_phrase(normalized_question, normalized_value):
                    filters[str(column)] = value
                    break
        if filters:
            filters_by_table[id(table)] = filters
    return filters_by_table


def _contains_phrase(normalized_text: str, normalized_phrase: str) -> bool:
    return f" {normalized_phrase} " in f" {normalized_text} "


def _first_filter_match(
    tables: list[LoadedTable],
    filters: dict[int, dict[str, Any]],
) -> tuple[LoadedTable | None, dict[str, Any]]:
    for table in tables:
        table_filters = filters.get(id(table), {})
        if table_filters:
            return table, table_filters
    return (tables[0], {}) if tables else (None, {})


def _apply_exact_filters(dataframe: pd.DataFrame, filters: dict[str, Any]) -> pd.DataFrame:
    filtered = dataframe
    for column, value in filters.items():
        filtered = filtered[
            filtered[column].fillna("").astype(str).str.lower() == str(value).lower()
        ]
    return filtered


def _extract_search_terms(normalized_question: str, filters: dict[int, dict[str, Any]]) -> list[str]:
    filter_words = {
        token
        for table_filters in filters.values()
        for value in table_filters.values()
        for token in _normalize_text(str(value)).split()
    }
    stop_words = {
        "how",
        "many",
        "count",
        "counts",
        "row",
        "rows",
        "mention",
        "mentions",
        "mentioned",
        "issue",
        "issues",
        "concern",
        "concerns",
        "risk",
        "risks",
        "high",
        "medium",
        "low",
        "with",
        "the",
        "and",
        "or",
        "are",
        "is",
        "there",
    }
    terms = [
        token
        for token in normalized_question.split()
        if token not in stop_words and token not in filter_words and len(token) > 2
    ]
    return list(dict.fromkeys(terms))


def _text_contains_any(dataframe: pd.DataFrame, search_terms: list[str]) -> pd.Series:
    combined_text = dataframe.fillna("").astype(str).agg(" ".join, axis=1).str.lower()
    return combined_text.apply(
        lambda row_text: any(term in row_text for term in search_terms)
    )


def _plain_value(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    return value


def _format_mapping(result: dict[str, Any]) -> str:
    return ", ".join(f"{key}: {value}" for key, value in result.items())


def _format_filters(filters: dict[str, Any]) -> str:
    if not filters:
        return "none"
    return ", ".join(f"{key}={value}" for key, value in filters.items())


def _sheet_suffix(sheet_name: str | None) -> str:
    return f" sheet '{sheet_name}'" if sheet_name else ""
