from dataclasses import dataclass
from typing import Protocol

from app.core.config import Settings
from app.core.logging_config import get_logger
from app.services.embedding_service import OllamaEmbeddingService
from app.services.vector_store import SearchResult, VectorStore
from app.utils.safe_logging import safe_log_fields


logger = get_logger()


class EmbeddingClient(Protocol):
    def embed_text(self, text: str) -> list[float]:
        """Convert one text value into a vector embedding."""


class VectorSearchClient(Protocol):
    def search(self, query_embedding: list[float], limit: int = 4) -> list[SearchResult]:
        """Find semantically similar chunks for the query embedding."""


@dataclass(frozen=True)
class SearcherResult:
    question: str
    matches: list[SearchResult]


class SearcherService:
    """Retrieval service that searches indexed document chunks."""

    def __init__(
        self,
        settings: Settings,
        embedding_client: EmbeddingClient | None = None,
        vector_store: VectorSearchClient | None = None,
    ) -> None:
        self._embedding_client = embedding_client or OllamaEmbeddingService(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
        )
        self._vector_store = vector_store or VectorStore(
            persist_directory=settings.chroma_persist_directory,
        )

    def search(self, question: str, limit: int = 4) -> SearcherResult:
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("Question cannot be empty.")
        if limit <= 0:
            raise ValueError("Search limit must be greater than zero.")

        query_embedding = self._embedding_client.embed_text(clean_question)
        matches = self._vector_store.search(query_embedding, limit=limit)
        source_files = sorted(
            {
                str(match.metadata.get("file"))
                for match in matches
                if match.metadata.get("file")
            }
        )
        logger.info(
            "search_completed %s",
            safe_log_fields(
                {
                    "route": "rag",
                    "limit": limit,
                    "match_count": len(matches),
                    "source_files": source_files,
                }
            ),
        )

        return SearcherResult(question=clean_question, matches=matches)
