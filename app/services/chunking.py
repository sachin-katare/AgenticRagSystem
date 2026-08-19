import re
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from app.services.loaders import ExtractedUnit, LoadedDocument


@dataclass(frozen=True)
class TextChunk:
    chunk_id: str
    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ChunkingPolicy:
    name: str
    chunk_size: int
    chunk_overlap: int


def chunk_document(
    document: LoadedDocument,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
    very_small_document_threshold: int = 1000,
    large_document_threshold: int = 20000,
) -> list[TextChunk]:
    total_characters = sum(len(unit.text) for unit in document.units)
    policy = choose_chunking_policy(
        total_characters=total_characters,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        very_small_document_threshold=very_small_document_threshold,
        large_document_threshold=large_document_threshold,
    )
    chunks: list[TextChunk] = []

    for unit_index, unit in enumerate(document.units):
        unit_chunks = _chunk_text(unit.text, policy.chunk_size, policy.chunk_overlap)
        for chunk_index, chunk_text in enumerate(unit_chunks):
            metadata = {
                **unit.metadata,
                "source_type": document.source_type,
                "unit_index": unit_index,
                "chunk_index": chunk_index,
                "chunking_policy": policy.name,
                "chunk_size": policy.chunk_size,
                "chunk_overlap": policy.chunk_overlap,
            }
            chunks.append(
                TextChunk(
                    chunk_id=str(uuid4()),
                    text=chunk_text,
                    metadata=metadata,
                )
            )

    return chunks


def choose_chunking_policy(
    total_characters: int,
    chunk_size: int = 1000,
    chunk_overlap: int = 150,
    very_small_document_threshold: int = 1000,
    large_document_threshold: int = 20000,
) -> ChunkingPolicy:
    if total_characters <= very_small_document_threshold:
        return ChunkingPolicy(
            name="very_small_single_unit",
            chunk_size=chunk_size,
            chunk_overlap=0,
        )

    if total_characters > large_document_threshold:
        return ChunkingPolicy(
            name="large_fixed_size_no_overlap",
            chunk_size=chunk_size,
            chunk_overlap=0,
        )

    return ChunkingPolicy(
        name="small_medium_fixed_size_with_overlap",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )


def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    clean_text = " ".join(text.split())
    if not clean_text:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")
    if len(clean_text) <= chunk_size:
        return [clean_text]
    if " " not in clean_text:
        return _chunk_text_by_character(clean_text, chunk_size, chunk_overlap)

    return _chunk_text_by_sentence_boundary(clean_text, chunk_size, chunk_overlap)


def _chunk_text_by_character(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - chunk_overlap

    return chunks


def _chunk_text_by_word_boundary(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    words = text.split(" ")
    chunks: list[str] = []
    current_words: list[str] = []

    for word in words:
        candidate_words = [*current_words, word]
        candidate_text = " ".join(candidate_words)
        if current_words and len(candidate_text) > chunk_size:
            chunks.append(" ".join(current_words))
            current_words = _overlap_words(current_words, chunk_overlap)

        current_words.append(word)

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def _chunk_text_by_sentence_boundary(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if len(sentences) == 1:
        return _chunk_text_by_word_boundary(text, chunk_size, chunk_overlap)

    chunks: list[str] = []
    current_sentences: list[str] = []

    for sentence in sentences:
        if len(sentence) > chunk_size:
            if current_sentences:
                chunks.append(" ".join(current_sentences))
                current_sentences = _overlap_sentences(current_sentences, chunk_overlap)
            chunks.extend(_chunk_text_by_word_boundary(sentence, chunk_size, chunk_overlap))
            current_sentences = []
            continue

        candidate_sentences = [*current_sentences, sentence]
        candidate_text = " ".join(candidate_sentences)
        if current_sentences and len(candidate_text) > chunk_size:
            chunks.append(" ".join(current_sentences))
            current_sentences = _overlap_sentences(current_sentences, chunk_overlap)

        current_sentences.append(sentence)

    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks


def _overlap_sentences(sentences: list[str], chunk_overlap: int) -> list[str]:
    if chunk_overlap == 0:
        return []

    overlap_sentences: list[str] = []
    overlap_length = 0
    for sentence in reversed(sentences):
        sentence_length = len(sentence) + (1 if overlap_sentences else 0)
        if overlap_length + sentence_length > chunk_overlap:
            break
        overlap_sentences.insert(0, sentence)
        overlap_length += sentence_length

    return overlap_sentences


def _overlap_words(words: list[str], chunk_overlap: int) -> list[str]:
    if chunk_overlap == 0:
        return []

    overlap_words: list[str] = []
    overlap_length = 0
    for word in reversed(words):
        word_length = len(word) + (1 if overlap_words else 0)
        if overlap_words and overlap_length + word_length > chunk_overlap:
            break
        overlap_words.insert(0, word)
        overlap_length += word_length

    return overlap_words
