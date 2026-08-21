from app.services.document_catalogue import DocumentCatalogue


def test_document_catalogue_stores_and_returns_record() -> None:
    catalogue = DocumentCatalogue()

    record = catalogue.add(
        document_id="doc-1",
        filename="notes.txt",
        source_type="txt",
        stored_path="data/uploads/doc-1.txt",
        extracted_unit_count=1,
        tabular_schema_count=0,
        content_hash="hash-1",
    )

    assert catalogue.get("doc-1") == record
    assert catalogue.list() == [record]
    assert record.uploaded_at
    assert record.content_hash == "hash-1"
    assert catalogue.find_by_content_hash("hash-1") == record

    removed_record = catalogue.remove("doc-1")

    assert removed_record == record
    assert catalogue.get("doc-1") is None


def test_document_catalogue_persists_records(tmp_path) -> None:
    storage_path = tmp_path / "document_catalogue.json"
    catalogue = DocumentCatalogue(storage_path)

    catalogue.add(
        document_id="doc-1",
        filename="notes.txt",
        source_type="txt",
        stored_path="data/uploads/doc-1.txt",
        extracted_unit_count=1,
        tabular_schema_count=0,
        content_hash="hash-1",
    )

    reloaded_catalogue = DocumentCatalogue(storage_path)

    assert reloaded_catalogue.get("doc-1") is not None
    assert reloaded_catalogue.get("doc-1").filename == "notes.txt"
    assert reloaded_catalogue.find_by_content_hash("hash-1").document_id == "doc-1"
