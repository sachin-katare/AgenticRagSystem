from dataclasses import dataclass

from app.core.config import Settings
from app.services.chunking import chunk_document
from app.services.embedding_service import OllamaEmbeddingService
from app.services.loaders import LoadedDocument
from app.services.vector_store import VectorStore


@dataclass(frozen=True)
class IndexingResult:
    chunk_count: int


class DocumentIndexingService:
    """Indexes loaded documents by chunking, embedding, and storing them in ChromaDB."""

    def __init__(
        self,
        settings: Settings,
        embedding_service: OllamaEmbeddingService | None = None,
        vector_store: VectorStore | None = None,
    ) -> None:
        self._settings = settings
        self._embedding_service = embedding_service or OllamaEmbeddingService(
            base_url=settings.ollama_base_url,
            model=settings.ollama_embedding_model,
        )
        self._vector_store = vector_store or VectorStore(settings.chroma_persist_directory)

    def index_document(self, document: LoadedDocument) -> IndexingResult:
        chunks = chunk_document(
            document,
            chunk_size=self._settings.chunk_size,
            chunk_overlap=self._settings.chunk_overlap,
            very_small_document_threshold=self._settings.very_small_document_threshold,
            large_document_threshold=self._settings.large_document_threshold,
        )
        embeddings = self._embedding_service.embed_texts([chunk.text for chunk in chunks])
        chunk_count = self._vector_store.add_chunks(chunks, embeddings)

        return IndexingResult(chunk_count=chunk_count)
