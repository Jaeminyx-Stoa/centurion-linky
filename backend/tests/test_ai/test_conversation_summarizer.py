"""Tests for ConversationSummarizer — LLM-based conversation summarization."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.ai.memory.summarizer import ConversationSummarizer


@pytest.mark.asyncio
async def test_summarize_basic():
    """Should generate a summary from message dicts."""
    mock_llm = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = "고객이 보톡스 시술에 대해 문의했으며, 가격과 시술 시간을 확인했습니다."
    mock_llm.ainvoke.return_value = mock_response

    summarizer = ConversationSummarizer(llm=mock_llm)
    messages = [
        {"sender_type": "customer", "content": "보톡스 가격이 얼마인가요?"},
        {"sender_type": "ai", "content": "보톡스는 5만원~15만원입니다."},
        {"sender_type": "customer", "content": "시술 시간은요?"},
        {"sender_type": "ai", "content": "약 20분 소요됩니다."},
    ]

    result = await summarizer.summarize(messages)
    assert "보톡스" in result
    mock_llm.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_summarize_empty_messages():
    """Should return empty string for empty messages."""
    mock_llm = AsyncMock()
    summarizer = ConversationSummarizer(llm=mock_llm)

    result = await summarizer.summarize([])
    assert result == ""
    mock_llm.ainvoke.assert_not_called()


@pytest.mark.asyncio
async def test_summarize_llm_failure():
    """Should return empty string on LLM failure."""
    mock_llm = AsyncMock()
    mock_llm.ainvoke.side_effect = Exception("API error")

    summarizer = ConversationSummarizer(llm=mock_llm)
    messages = [
        {"sender_type": "customer", "content": "안녕하세요"},
    ]

    result = await summarizer.summarize(messages)
    assert result == ""


@pytest.mark.asyncio
async def test_summarize_prompt_contains_messages():
    """The prompt sent to LLM should contain the message content."""
    mock_llm = AsyncMock()
    mock_response = MagicMock()
    mock_response.content = "요약입니다."
    mock_llm.ainvoke.return_value = mock_response

    summarizer = ConversationSummarizer(llm=mock_llm)
    messages = [
        {"sender_type": "customer", "content": "필러에 대해 알고 싶습니다"},
    ]

    await summarizer.summarize(messages)

    # Verify the prompt contains the message text
    call_args = mock_llm.ainvoke.call_args[0][0]
    assert "필러에 대해 알고 싶습니다" in call_args
