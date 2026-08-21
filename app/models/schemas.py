from pydantic import BaseModel


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    source_type: str
    extracted_unit_count: int
    tabular_schema_count: int
    indexed_chunk_count: int
    status: str


class SearchRequest(BaseModel):
    question: str
    limit: int = 4


class SearchMatch(BaseModel):
    chunk_id: str
    text: str
    metadata: dict
    distance: float


class SearchResponse(BaseModel):
    question: str
    match_count: int
    matches: list[SearchMatch]


class AskRequest(BaseModel):
    question: str
    limit: int = 4


class AskResponse(BaseModel):
    question: str
    answer: str
    citation_count: int
    citations: list[SearchMatch]
    status: str
    trace: list[str] = []


class StructuredAnalysisRequest(BaseModel):
    path: str
    operation: str
    value_column: str | None = None
    group_by_column: str | None = None
    filters: dict[str, str] = {}
    sheet_name: str | None = None


class StructuredAnalysisResponse(BaseModel):
    operation: str
    file: str
    sheet: str | None
    result: dict | float | int | str
    row_count: int
    explanation: str
    route: str = "structured"


class AskTableRequest(BaseModel):
    question: str


class AskTableResponse(BaseModel):
    question: str
    route: str
    result: dict | float | int | str
    answer: str
    explanation: str
