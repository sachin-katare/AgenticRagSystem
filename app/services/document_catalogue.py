import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class DocumentRecord:
    document_id: str
    filename: str
    source_type: str
    stored_path: str
    extracted_unit_count: int
    tabular_schema_count: int
    uploaded_at: str
    content_hash: str = ""


class DocumentCatalogue:
    """Catalogue of uploaded documents, optionally persisted to local JSON."""

    def __init__(self, storage_path: Path | None = None) -> None:
        self._storage_path = storage_path
        self._records: dict[str, DocumentRecord] = {}
        self._load()

    def add(
        self,
        document_id: str,
        filename: str,
        source_type: str,
        stored_path: str,
        extracted_unit_count: int,
        tabular_schema_count: int,
        content_hash: str = "",
    ) -> DocumentRecord:
        record = DocumentRecord(
            document_id=document_id,
            filename=filename,
            source_type=source_type,
            stored_path=stored_path,
            extracted_unit_count=extracted_unit_count,
            tabular_schema_count=tabular_schema_count,
            content_hash=content_hash,
            uploaded_at=datetime.now(UTC).isoformat(),
        )
        self._records[document_id] = record
        self._save()
        return record

    def get(self, document_id: str) -> DocumentRecord | None:
        return self._records.get(document_id)

    def remove(self, document_id: str) -> DocumentRecord | None:
        record = self._records.pop(document_id, None)
        if record is not None:
            self._save()
        return record

    def list(self) -> list[DocumentRecord]:
        return list(self._records.values())

    def find_by_content_hash(self, content_hash: str) -> DocumentRecord | None:
        if not content_hash:
            return None
        for record in self._records.values():
            if record.content_hash == content_hash:
                return record
        return None

    def _load(self) -> None:
        if self._storage_path is None or not self._storage_path.exists():
            return

        raw_records = json.loads(self._storage_path.read_text(encoding="utf-8"))
        self._records = {
            record["document_id"]: DocumentRecord(**record)
            for record in raw_records
        }

    def _save(self) -> None:
        if self._storage_path is None:
            return

        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        raw_records = [asdict(record) for record in self.list()]
        self._storage_path.write_text(
            json.dumps(raw_records, indent=2),
            encoding="utf-8",
        )


document_catalogue = DocumentCatalogue(Path("data/document_catalogue.json"))
