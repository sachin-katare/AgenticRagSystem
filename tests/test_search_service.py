from app.core.config import get_settings
from app.services.search_service import SearcherService
from app.services.vector_store import SearchResult


class FakeEmbeddingClient:
    def __init__(self) -> None:
        self.last_text = ""

    def embed_text(self, text: str) -> list[float]:
        self.last_text = text
        return [1.0, 0.0, 0.0]


class FakeVectorStore:
    def __init__(self) -> None:
        self.last_embedding = []
        self.last_limit = 0

    def search(self, query_embedding: list[float], limit: int = 4) -> list[SearchResult]:
        self.last_embedding = query_embedding
        self.last_limit = limit
        return [
            SearchResult(
                chunk_id="chunk-1",
                text="Audio campaigns require frequency caps.",
                metadata={"file": "policy.pdf", "page": 1},
                distance=0.12,
            )
        ]


def test_searcher_embeds_question_and_searches_vector_store() -> None:
    embedding_client = FakeEmbeddingClient()
    vector_store = FakeVectorStore()
    searcher = SearcherService(
        settings=get_settings(),
        embedding_client=embedding_client,
        vector_store=vector_store,
    )

    result = searcher.search("  What rules apply to audio ads?  ", limit=2)

    assert result.question == "What rules apply to audio ads?"
    assert embedding_client.last_text == "What rules apply to audio ads?"
    assert vector_store.last_embedding == [1.0, 0.0, 0.0]
    assert vector_store.last_limit == 2
    assert result.matches[0].metadata["file"] == "policy.pdf"


def test_searcher_rejects_empty_question() -> None:
    searcher = SearcherService(
        settings=get_settings(),
        embedding_client=FakeEmbeddingClient(),
        vector_store=FakeVectorStore(),
    )

    try:
        searcher.search("   ")
    except ValueError as exc:
        assert "Question cannot be empty" in str(exc)
    else:
        raise AssertionError("Expected ValueError for empty question.")
