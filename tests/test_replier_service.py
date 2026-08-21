from app.core.config import get_settings
from app.services.replier_service import ReplierService
from app.services.search_service import SearcherResult
from app.services.vector_store import SearchResult


class FakeSearcher:
    def __init__(self, matches: list[SearchResult]) -> None:
        self.matches = matches
        self.last_question = ""
        self.last_limit = 0

    def search(self, question: str, limit: int = 4) -> SearcherResult:
        self.last_question = question
        self.last_limit = limit
        return SearcherResult(question=question, matches=self.matches)


class FakeChatClient:
    def __init__(
        self,
        answer: str = "Audio ads require frequency caps. [1]",
        follow_up_answer: str | None = None,
    ) -> None:
        self.answers = [answer]
        if follow_up_answer is not None:
            self.answers.append(follow_up_answer)
        self.last_prompt = ""
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        self.prompts.append(prompt)
        return self.answers.pop(0)


def test_replier_generates_grounded_answer_from_search_results() -> None:
    matches = [
        SearchResult(
            chunk_id="chunk-1",
            text="Audio campaigns require frequency caps.",
            metadata={"file": "policy.pdf", "page": 1},
            distance=0.12,
        )
    ]
    searcher = FakeSearcher(matches)
    chat_client = FakeChatClient()
    replier = ReplierService(
        settings=get_settings(),
        searcher=searcher,
        chat_client=chat_client,
    )

    result = replier.answer(" What rules apply to audio ads? ", limit=2)

    assert result.status == "answered"
    assert result.answer == "Audio ads require frequency caps. [1]"
    assert result.citations == matches
    assert searcher.last_question == "What rules apply to audio ads?"
    assert searcher.last_limit == 2
    assert "Audio campaigns require frequency caps." in chat_client.last_prompt
    assert "policy.pdf, page 1" in chat_client.last_prompt
    assert "close synonyms, abbreviations, and domain" in chat_client.last_prompt


def test_replier_returns_insufficient_evidence_without_calling_chat_model() -> None:
    searcher = FakeSearcher([])
    chat_client = FakeChatClient()
    replier = ReplierService(
        settings=get_settings(),
        searcher=searcher,
        chat_client=chat_client,
    )

    result = replier.answer("What is the renewal risk?")

    assert result.status == "insufficient_evidence"
    assert "not have enough information" in result.answer
    assert result.citations == []
    assert chat_client.last_prompt == ""


def test_replier_repairs_uncited_answers_once() -> None:
    matches = [
        SearchResult(
            chunk_id="chunk-1",
            text="Streaming audio placements must follow campaign approval rules.",
            metadata={"file": "policy.pdf", "page": 1},
            distance=0.12,
        )
    ]
    replier = ReplierService(
        settings=get_settings(),
        searcher=FakeSearcher(matches),
        chat_client=FakeChatClient(
            answer="Audio ads must follow approval rules.",
            follow_up_answer="Audio ads must follow approval rules. [1]",
        ),
    )

    result = replier.answer("What rules apply to audio ads?")

    assert result.status == "answered"
    assert result.answer == "Audio ads must follow approval rules. [1]"
    assert result.citations == matches
    assert len(replier._chat_client.prompts) == 2
    assert "Rewrite the draft answer" in replier._chat_client.prompts[1]


def test_replier_repairs_out_of_range_citation_markers() -> None:
    matches = [
        SearchResult(
            chunk_id="chunk-1",
            text="Streaming audio placements must follow campaign approval rules.",
            metadata={"file": "policy.pdf", "page": 1},
            distance=0.12,
        ),
        SearchResult(
            chunk_id="chunk-2",
            text="Streaming audio placements must follow frequency caps.",
            metadata={"file": "policy.pdf", "page": 1},
            distance=0.14,
        ),
    ]
    replier = ReplierService(
        settings=get_settings(),
        searcher=FakeSearcher(matches),
        chat_client=FakeChatClient(
            answer="Audio ads must follow approval rules. [6]",
            follow_up_answer="Audio ads must follow approval rules. [1]",
        ),
    )

    result = replier.answer("What rules apply to audio ads?")

    assert result.status == "answered"
    assert result.answer == "Audio ads must follow approval rules. [1]"
    assert len(replier._chat_client.prompts) == 2


def test_replier_marks_uncited_retry_as_validation_failure() -> None:
    matches = [
        SearchResult(
            chunk_id="chunk-1",
            text="Streaming audio placements must follow campaign approval rules.",
            metadata={"file": "policy.pdf", "page": 1},
            distance=0.12,
        )
    ]
    replier = ReplierService(
        settings=get_settings(),
        searcher=FakeSearcher(matches),
        chat_client=FakeChatClient(
            answer="Audio ads must follow approval rules.",
            follow_up_answer="Audio ads must follow approval rules.",
        ),
    )

    result = replier.answer("What rules apply to audio ads?")

    assert result.status == "citation_validation_failed"
    assert "properly cited answer" in result.answer
    assert result.citations == matches


def test_replier_marks_out_of_range_retry_as_validation_failure() -> None:
    matches = [
        SearchResult(
            chunk_id="chunk-1",
            text="Streaming audio placements must follow campaign approval rules.",
            metadata={"file": "policy.pdf", "page": 1},
            distance=0.12,
        )
    ]
    replier = ReplierService(
        settings=get_settings(),
        searcher=FakeSearcher(matches),
        chat_client=FakeChatClient(
            answer="Audio ads must follow approval rules. [2]",
            follow_up_answer="Audio ads must follow approval rules. [6]",
        ),
    )

    result = replier.answer("What rules apply to audio ads?")

    assert result.status == "citation_validation_failed"
    assert "properly cited answer" in result.answer


def test_replier_marks_insufficient_evidence_answer_status() -> None:
    matches = [
        SearchResult(
            chunk_id="chunk-1",
            text="Streaming audio placements must follow campaign approval rules.",
            metadata={"file": "policy.pdf", "page": 1},
            distance=0.12,
        )
    ]
    replier = ReplierService(
        settings=get_settings(),
        searcher=FakeSearcher(matches),
        chat_client=FakeChatClient("I do not have enough information. [1]"),
    )

    result = replier.answer("What rules apply to audio ads?")

    assert result.status == "insufficient_evidence"
    assert result.citations == matches


def test_replier_marks_sufficient_information_wording_as_insufficient_evidence() -> None:
    matches = [
        SearchResult(
            chunk_id="chunk-1",
            text="Campaign approval rules are documented, but refund policy is not mentioned.",
            metadata={"file": "policy.pdf", "page": 1},
            distance=0.12,
        )
    ]
    replier = ReplierService(
        settings=get_settings(),
        searcher=FakeSearcher(matches),
        chat_client=FakeChatClient(
            "I do not have sufficient information to provide a refund policy. [1]"
        ),
    )

    result = replier.answer("What is the refund policy for advertisers?")

    assert result.status == "insufficient_evidence"
    assert result.citations == matches


def test_replier_marks_does_not_provide_sufficient_information_as_insufficient() -> None:
    matches = [
        SearchResult(
            chunk_id="chunk-1",
            text="Campaign approval rules are documented, but refund policy is not mentioned.",
            metadata={"file": "policy.pdf", "page": 1},
            distance=0.12,
        )
    ]
    replier = ReplierService(
        settings=get_settings(),
        searcher=FakeSearcher(matches),
        chat_client=FakeChatClient(
            "Unfortunately, the provided evidence does not provide sufficient information to establish a refund policy for advertisers. [1]"
        ),
    )

    result = replier.answer("What is the refund policy for advertisers?")

    assert result.status == "insufficient_evidence"
    assert result.citations == matches
