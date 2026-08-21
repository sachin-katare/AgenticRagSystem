from dataclasses import dataclass
import re
from typing import Protocol

from app.core.config import Settings
from app.core.logging_config import get_logger
from app.services.chat_service import OllamaChatService
from app.services.search_service import SearcherResult, SearcherService
from app.services.vector_store import SearchResult
from app.utils.safe_logging import safe_log_fields


logger = get_logger()


class SearcherClient(Protocol):
    def search(self, question: str, limit: int = 4) -> SearcherResult:
        """Retrieve evidence chunks for a user question."""


class ChatClient(Protocol):
    def generate(self, prompt: str) -> str:
        """Generate an answer from a grounded prompt."""


@dataclass(frozen=True)
class ReplierResult:
    question: str
    answer: str
    citations: list[SearchResult]
    status: str


class ReplierService:
    """Answer-writing service that responds using retrieved evidence."""

    def __init__(
        self,
        settings: Settings,
        searcher: SearcherClient | None = None,
        chat_client: ChatClient | None = None,
    ) -> None:
        self._searcher = searcher or SearcherService(settings)
        self._chat_client = chat_client or OllamaChatService(
            base_url=settings.ollama_base_url,
            model=settings.ollama_chat_model,
        )

    def answer(self, question: str, limit: int = 4) -> ReplierResult:
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("Question cannot be empty.")

        search_result = self._searcher.search(clean_question, limit=limit)
        return self.answer_from_matches(clean_question, search_result.matches)

    def answer_from_matches(self, question: str, matches: list[SearchResult]) -> ReplierResult:
        clean_question = question.strip()
        if not clean_question:
            raise ValueError("Question cannot be empty.")

        if not matches:
            logger.warning(
                "replier_insufficient_evidence %s",
                safe_log_fields({"match_count": 0}),
            )
            return ReplierResult(
                question=clean_question,
                answer="I do not have enough information in the uploaded documents to answer that question.",
                citations=[],
                status="insufficient_evidence",
            )

        prompt = self._build_grounded_prompt(
            question=clean_question,
            matches=matches,
        )
        answer = self._chat_client.generate(prompt)
        citation_repair_attempted = False
        if not _answer_uses_only_supplied_citations(answer, len(matches)):
            citation_repair_attempted = True
            logger.warning(
                "replier_citation_repair_started %s",
                safe_log_fields({"available_citation_count": len(matches)}),
            )
            repair_prompt = self._build_citation_repair_prompt(
                question=clean_question,
                matches=matches,
                draft_answer=answer,
            )
            answer = self._chat_client.generate(repair_prompt)

        if not _answer_uses_only_supplied_citations(answer, len(matches)):
            logger.error(
                "replier_citation_validation_failed %s",
                safe_log_fields(
                    {
                        "available_citation_count": len(matches),
                        "citation_repair_attempted": citation_repair_attempted,
                    }
                ),
            )
            return ReplierResult(
                question=clean_question,
                answer=(
                    "I found potentially relevant evidence, but I could not produce a "
                    "properly cited answer from it."
                ),
                citations=matches,
                status="citation_validation_failed",
            )

        if _claims_insufficient_evidence(answer):
            logger.warning(
                "replier_model_claimed_insufficient_evidence %s",
                safe_log_fields({"citation_count": len(matches)}),
            )
            return ReplierResult(
                question=clean_question,
                answer=answer,
                citations=matches,
                status="insufficient_evidence",
            )

        logger.info(
            "replier_answer_completed %s",
            safe_log_fields(
                {
                    "citation_count": len(matches),
                    "citation_repair_attempted": citation_repair_attempted,
                }
            ),
        )
        return ReplierResult(
            question=clean_question,
            answer=answer,
            citations=matches,
            status="answered",
        )

    def _build_grounded_prompt(self, question: str, matches: list[SearchResult]) -> str:
        evidence_blocks = []
        for index, match in enumerate(matches, start=1):
            source = match.metadata.get("file", "unknown source")
            page = match.metadata.get("page")
            source_label = f"{source}, page {page}" if page else source
            evidence_blocks.append(
                f"[{index}] Source: {source_label}\n{match.text}"
            )

        evidence = "\n\n".join(evidence_blocks)
        return (
            "You are answering questions using only the provided evidence.\n"
            "If the evidence is insufficient, say you do not have enough information.\n"
            "Cite evidence using bracket numbers like [1] or [2].\n\n"
            "Important relevance rule: treat close synonyms, abbreviations, and domain "
            "terms as relevant when the supplied evidence clearly supports that mapping. "
            "Do not invent a synonym relationship when the evidence does not support it.\n\n"
            "Answer requirements:\n"
            "- Start with the direct answer.\n"
            "- If the evidence directly states an exact fact such as a duration, count, threshold, owner, or approval window, answer with that fact plainly.\n"
            "- Do not call the evidence insufficient when a cited evidence block already states the answer directly.\n"
            "- Include at least one citation marker from the supplied evidence.\n"
            "- Every citation marker must map to a supplied evidence number.\n"
            "- Do not use outside knowledge.\n"
            "- Do not cite sources that are not listed below.\n\n"
            f"Question:\n{question}\n\n"
            f"Evidence:\n{evidence}\n\n"
            "Answer:"
        )

    def _build_citation_repair_prompt(
        self,
        question: str,
        matches: list[SearchResult],
        draft_answer: str,
    ) -> str:
        evidence_blocks = []
        for index, match in enumerate(matches, start=1):
            source = match.metadata.get("file", "unknown source")
            page = match.metadata.get("page")
            source_label = f"{source}, page {page}" if page else source
            evidence_blocks.append(
                f"[{index}] Source: {source_label}\n{match.text}"
            )

        evidence = "\n\n".join(evidence_blocks)
        return (
            "Rewrite the draft answer so every factual claim is supported by the "
            "provided evidence and at least one valid bracket citation such as [1].\n"
            "Use only citation numbers that appear in the evidence below.\n"
            "If the draft cannot be supported, say the evidence is insufficient and cite "
            "the closest evidence.\n\n"
            f"Question:\n{question}\n\n"
            f"Draft answer:\n{draft_answer}\n\n"
            f"Evidence:\n{evidence}\n\n"
            "Rewritten cited answer:"
        )


def _answer_uses_only_supplied_citations(answer: str, citation_count: int) -> bool:
    citation_numbers = [int(number) for number in re.findall(r"\[(\d+)]", answer)]
    return bool(citation_numbers) and all(
        1 <= citation_number <= citation_count for citation_number in citation_numbers
    )


def _claims_insufficient_evidence(answer: str) -> bool:
    lowered_answer = answer.lower()
    insufficient_phrases = [
        "do not have enough information",
        "do not have sufficient information",
        "does not provide sufficient information",
        "doesn't provide sufficient information",
        "don't have enough information",
        "don't have sufficient information",
        "insufficient evidence",
        "evidence is insufficient",
        "insufficient to support",
        "unable to find a clear",
        "cannot answer",
        "can't answer",
    ]
    return any(phrase in lowered_answer for phrase in insufficient_phrases)
