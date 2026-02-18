import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.ai.chains.sales_skill_chain import SalesSkillChain


@pytest.fixture
def fake_llm():
    return GenericFakeChatModel(
        messages=iter([
            AIMessage(
                content="ボトックスの施術についてご案内いたします。"
                "当院では現在、初回限定20%OFFキャンペーンを実施しております。"
                "まずは無料カウンセリングのご予約はいかがでしょうか？😊"
            ),
        ])
    )


@pytest.fixture
def sales_chain(fake_llm):
    return SalesSkillChain(llm=fake_llm)


@pytest.fixture
def sales_context():
    return {
        "top_procedures": ["보톡스", "필러", "울쎄라"],
        "active_events": ["초회 한정 20% 할인"],
        "cross_sell_options": ["보톡스 + 필러 세트 10% 추가 할인"],
    }


class TestSalesSkillChain:
    async def test_invoke_returns_final_response(
        self, sales_chain, sales_context
    ):
        result = await sales_chain.ainvoke(
            styled_output="ボトックスは安全な施術です。",
            conversation_history="顧客: ボトックスについて知りたいです\nAI: はい、ご案内いたします。",
            sales_context=sales_context,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_invoke_with_empty_sales_context(self, fake_llm):
        chain = SalesSkillChain(llm=GenericFakeChatModel(
            messages=iter([
                AIMessage(content="ボトックスの施術は安全です。ご質問があればお気軽にどうぞ。"),
            ])
        ))
        result = await chain.ainvoke(
            styled_output="기본 답변",
            conversation_history="",
            sales_context={
                "top_procedures": [],
                "active_events": [],
                "cross_sell_options": [],
            },
        )
        assert isinstance(result, str)

    async def test_invoke_with_conversation_history(self, fake_llm):
        chain = SalesSkillChain(llm=GenericFakeChatModel(
            messages=iter([
                AIMessage(content="お待たせいたしました。それでは予約のご案内をさせていただきます。"),
            ])
        ))
        result = await chain.ainvoke(
            styled_output="예약 안내 답변",
            conversation_history="顧客: 予約したいです\nAI: はい\n顧客: いつがいいですか？",
            sales_context={
                "top_procedures": [],
                "active_events": [],
                "cross_sell_options": [],
            },
        )
        assert isinstance(result, str)

    def test_chain_has_prompt_template(self, sales_chain):
        assert sales_chain.prompt is not None
