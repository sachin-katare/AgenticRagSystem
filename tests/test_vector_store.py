from app.services.chunking import TextChunk
from app.services.vector_store import VectorStore


def test_vector_store_adds_and_searches_chunks(tmp_path) -> None:
    vector_store = VectorStore(tmp_path / "chroma")
    chunks = [
        TextChunk(
            chunk_id="chunk-1",
            text="audio ads need frequency caps",
            metadata={"file": "policy.pdf", "page": 1},
        ),
        TextChunk(
            chunk_id="chunk-2",
            text="display ads need landing page checks",
            metadata={"file": "notes.txt"},
        ),
    ]
    embeddings = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
    ]

    inserted_count = vector_store.add_chunks(chunks, embeddings)
    results = vector_store.search([1.0, 0.0, 0.0], limit=1)

    assert inserted_count == 2
    assert len(results) == 1
    assert results[0].chunk_id == "chunk-1"
    assert results[0].metadata["file"] == "policy.pdf"


def test_vector_store_rejects_mismatched_chunk_and_embedding_counts(tmp_path) -> None:
    vector_store = VectorStore(tmp_path / "chroma")

    try:
        vector_store.add_chunks(
            [TextChunk(chunk_id="chunk-1", text="text", metadata={})],
            [],
        )
    except ValueError as exc:
        assert "counts must match" in str(exc)
    else:
        raise AssertionError("Expected ValueError for mismatched counts.")
