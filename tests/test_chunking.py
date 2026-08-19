from app.services.chunking import chunk_document
from app.services.loaders import ExtractedUnit, LoadedDocument


def test_chunk_document_keeps_very_small_text_as_one_chunk() -> None:
    document = LoadedDocument(
        filename="notes.txt",
        source_type="txt",
        units=[ExtractedUnit(text="short policy note", metadata={"file": "notes.txt"})],
    )

    chunks = chunk_document(document, chunk_size=1000, chunk_overlap=150)

    assert len(chunks) == 1
    assert chunks[0].text == "short policy note"
    assert chunks[0].metadata["chunking_policy"] == "very_small_single_unit"
    assert chunks[0].metadata["chunk_overlap"] == 0


def test_chunk_document_uses_overlap_for_small_medium_documents() -> None:
    document = LoadedDocument(
        filename="notes.txt",
        source_type="txt",
        units=[ExtractedUnit(text="abcdefghij" * 30, metadata={"file": "notes.txt"})],
    )

    chunks = chunk_document(
        document,
        chunk_size=100,
        chunk_overlap=20,
        very_small_document_threshold=100,
    )

    assert len(chunks) > 1
    assert chunks[0].text[-20:] == chunks[1].text[:20]
    assert chunks[0].metadata["chunking_policy"] == "small_medium_fixed_size_with_overlap"
    assert chunks[0].metadata["chunk_overlap"] == 20


def test_chunk_document_removes_overlap_for_large_documents() -> None:
    large_text = "".join(chr(65 + (index % 26)) for index in range(300))
    document = LoadedDocument(
        filename="large.txt",
        source_type="txt",
        units=[ExtractedUnit(text=large_text, metadata={"file": "large.txt"})],
    )

    chunks = chunk_document(
        document,
        chunk_size=100,
        chunk_overlap=20,
        very_small_document_threshold=100,
        large_document_threshold=200,
    )

    assert len(chunks) == 3
    assert chunks[0].text[-20:] != chunks[1].text[:20]
    assert chunks[0].metadata["chunking_policy"] == "large_fixed_size_no_overlap"
    assert chunks[0].metadata["chunk_overlap"] == 0


def test_chunk_document_prefers_sentence_boundaries_for_normal_text() -> None:
    document = LoadedDocument(
        filename="policy.pdf",
        source_type="pdf",
        units=[
            ExtractedUnit(
                text=(
                    "Campaign event data is retained for ninety days. "
                    "Aggregated non identifying campaign reports support renewal planning. "
                    "Uploaded files must exclude passwords authentication tokens and payment data."
                ),
                metadata={"file": "policy.pdf", "page": 2},
            )
        ],
    )

    chunks = chunk_document(
        document,
        chunk_size=80,
        chunk_overlap=20,
        very_small_document_threshold=80,
    )

    assert len(chunks) > 1
    assert chunks[1].text.startswith("Aggregated")
    assert not chunks[1].text.startswith("mpaign")


def test_chunk_document_preserves_source_metadata() -> None:
    document = LoadedDocument(
        filename="policy.pdf",
        source_type="pdf",
        units=[ExtractedUnit(text="a" * 120, metadata={"file": "policy.pdf", "page": 2})],
    )

    chunks = chunk_document(document, chunk_size=100, chunk_overlap=10)

    assert chunks[0].metadata["file"] == "policy.pdf"
    assert chunks[0].metadata["page"] == 2
    assert chunks[0].metadata["source_type"] == "pdf"
