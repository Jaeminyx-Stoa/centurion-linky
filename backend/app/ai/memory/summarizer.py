"""Conversation summarizer — generates concise summaries of long conversations."""

import logging

logger = logging.getLogger(__name__)

SUMMARY_PROMPT = """Summarize this medical consultation conversation in 3-5 sentences (Korean).
Include: what the customer asked about, procedures discussed, decisions made, customer sentiment.
---
{messages}"""


class ConversationSummarizer:
    """Generates conversation summaries using LLM."""

    def __init__(self, llm=None):
        if llm is None:
            from app.ai.llm_router import get_light_llm

            self._llm = get_light_llm()
        else:
            self._llm = llm

    async def summarize(self, messages: list[dict], *, tracker=None) -> str:
        """Summarize a list of message dicts into a concise Korean summary.

        Each message dict should have: sender_type, content.
        """
        if not messages:
            return ""

        text = "\n".join(
            f"{m.get('sender_type', 'unknown')}: {m.get('content', '')}"
            for m in messages
        )
        prompt = SUMMARY_PROMPT.format(messages=text)

        try:
            if tracker:
                from app.ai.tracked_llm import tracked_ainvoke

                result = await tracked_ainvoke(
                    self._llm, prompt, tracker=tracker, operation="summarization"
                )
            else:
                result = await self._llm.ainvoke(prompt)
            content = result.content if hasattr(result, "content") else str(result)
            return content.strip()
        except Exception:
            logger.exception("Conversation summarization failed")
            return ""
