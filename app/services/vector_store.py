from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb

from app.services.chunking import TextChunk


@dataclass(frozen=True)
class SearchResult:
    chunk_id: str
    text: str
    metadata: dict[str, Any]
    distance: float


class VectorStore:
    """Local ChromaDB-backed repository for text chunks and embeddings."""

    def __init__(
        self,
        persist_directory: str | Path,
        collection_name: str = "agentic_rag_chunks",
    ) -> None:
        self._client = chromadb.PersistentClient(path=str(persist_directory))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[TextChunk], embeddings: list[list[float]]) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunk and embedding counts must match.")
        if not chunks:
            return 0

        self._collection.add(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            metadatas=[chunk.metadata for chunk in chunks],
            embeddings=embeddings,
        )
        return len(chunks)

    def search(self, query_embedding: list[float], limit: int = 4) -> list[SearchResult]:
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            include=["documents", "metadatas", "distances"],
        )

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        return [
            SearchResult(
                chunk_id=chunk_id,
                text=document,
                metadata=metadata,
                distance=distance,
            )
            for chunk_id, document, metadata, distance in zip(
                ids,
                documents,
                metadatas,
                distances,
                strict=True,
            )
        ]
