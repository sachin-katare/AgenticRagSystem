from app.core.config import Settings
from app.services.indexing_service import DocumentIndexingService
from app.services.loaders import ExtractedUnit, LoadedDocument


class FakeEmbeddingService:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0] for _ in texts]


class FakeVectorStore:
    def __init__(self) -> None:
        self.added_chunk_count = 0

    def add_chunks(self, chunks, embeddings) -> int:
        self.added_chunk_count = len(chunks)
        assert len(chunks) == len(embeddings)
        return len(chunks)


def test_index_document_chunks_embeds_and_stores_document() -> None:
    settings = Settings(chunk_size=10, chunk_overlap=2)
    vector_store = FakeVectorStore()
    service = DocumentIndexingService(
        settings=settings,
        embedding_service=FakeEmbeddingService(),
        vector_store=vector_store,
    )
    document = LoadedDocument(
        filename="notes.txt",
        source_type="txt",
        units=[ExtractedUnit(text="This is a longer policy note.", metadata={"file": "notes.txt"})],
    )

    result = service.index_document(document)

    assert result.chunk_count == vector_store.added_chunk_count
    assert result.chunk_count > 1
