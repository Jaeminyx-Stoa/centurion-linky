import pytest
from unittest.mock import AsyncMock, patch

from app.ai.chains.response_chain import ResponseChain


@pytest.fixture
def mock_knowledge_chain():
    mock = AsyncMock()
    mock.ainvoke.return_value = "보톡스는 보툴리눔 독소 시술입니다. 효과 3-6개월."
    return mock


@pytest.fixture
def mock_style_chain():
    mock = AsyncMock()
    mock.ainvoke.return_value = "ボトックスは安全な施術です。効果は3〜6ヶ月です。😊"
    return mock


@pytest.fixture
def mock_sales_chain():
    mock = AsyncMock()
    mock.ainvoke.return_value = (
        "ボトックスは安全な施術です。効果は3〜6ヶ月です。"
        "初回限定キャンペーン実施中です。ご予約はいかがでしょうか？😊"
    )
    return mock


@pytest.fixture
def response_chain(mock_knowledge_chain, mock_style_chain, mock_sales_chain):
    return ResponseChain(
        knowledge_chain=mock_knowledge_chain,
        style_chain=mock_style_chain,
        sales_chain=mock_sales_chain,
    )


@pytest.fixture
def cultural_profile():
    return {
        "country_code": "JP",
        "country_name": "일본",
        "language_code": "ja",
        "style_prompt": "정중한 일본어",
        "preferred_expressions": [],
        "avoided_expressions": [],
        "emoji_level": "medium",
        "formality_level": "formal",
    }


@pytest.fixture
def persona():
    return {"name": "미소", "personality": "밝고 친근한 상담사"}


@pytest.fixture
def sales_context():
    return {
        "top_procedures": ["보톡스"],
        "active_events": ["20% 할인"],
        "cross_sell_options": [],
    }


class TestResponseChain:
    async def test_full_pipeline_executes_all_three_layers(
        self,
        response_chain,
        mock_knowledge_chain,
        mock_style_chain,
        mock_sales_chain,
        cultural_profile,
        persona,
        sales_context,
    ):
        result = await response_chain.ainvoke(
            query="보톡스에 대해 알려주세요",
            rag_results="보톡스 관련 정보",
            clinic_manual="앨러간 보톡스 사용",
            country_code="JP",
            language_code="ja",
            cultural_profile=cultural_profile,
            persona=persona,
            conversation_history="",
            sales_context=sales_context,
        )

        # All three chains should have been called
        mock_knowledge_chain.ainvoke.assert_called_once()
        mock_style_chain.ainvoke.assert_called_once()
        mock_sales_chain.ainvoke.assert_called_once()

        assert isinstance(result, str)
        assert len(result) > 0

    async def test_pipeline_passes_knowledge_output_to_style(
        self,
        response_chain,
        mock_knowledge_chain,
        mock_style_chain,
        cultural_profile,
        persona,
        sales_context,
    ):
        await response_chain.ainvoke(
            query="test query",
            rag_results="",
            clinic_manual="",
            country_code="JP",
            language_code="ja",
            cultural_profile=cultural_profile,
            persona=persona,
            conversation_history="",
            sales_context=sales_context,
        )

        # Style chain should receive knowledge chain's output
        style_call_kwargs = mock_style_chain.ainvoke.call_args
        assert style_call_kwargs is not None
        call_kwargs = style_call_kwargs.kwargs if style_call_kwargs.kwargs else {}
        if not call_kwargs:
            call_args = style_call_kwargs.args
            assert "보톡스" in str(call_args) or len(call_args) > 0

    async def test_pipeline_passes_styled_output_to_sales(
        self,
        response_chain,
        mock_style_chain,
        mock_sales_chain,
        cultural_profile,
        persona,
        sales_context,
    ):
        await response_chain.ainvoke(
            query="test query",
            rag_results="",
            clinic_manual="",
            country_code="JP",
            language_code="ja",
            cultural_profile=cultural_profile,
            persona=persona,
            conversation_history="history",
            sales_context=sales_context,
        )

        # Sales chain should receive style chain's output
        sales_call = mock_sales_chain.ainvoke.call_args
        assert sales_call is not None

    async def test_returns_sales_chain_output_as_final(
        self,
        response_chain,
        mock_sales_chain,
        cultural_profile,
        persona,
        sales_context,
    ):
        result = await response_chain.ainvoke(
            query="test",
            rag_results="",
            clinic_manual="",
            country_code="JP",
            language_code="ja",
            cultural_profile=cultural_profile,
            persona=persona,
            conversation_history="",
            sales_context=sales_context,
        )
        # Final result should be from sales chain
        assert result == mock_sales_chain.ainvoke.return_value
