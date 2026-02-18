import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.ai.chains.style_chain import StyleChain


@pytest.fixture
def fake_llm():
    return GenericFakeChatModel(
        messages=iter([
            AIMessage(content="ボトックスは、ボツリヌス毒素A型を使用する施術です。"
                      "施術時間は約10〜15分で、効果は3〜6ヶ月持続します。😊"),
        ])
    )


@pytest.fixture
def style_chain(fake_llm):
    return StyleChain(llm=fake_llm)


@pytest.fixture
def japanese_profile():
    return {
        "country_code": "JP",
        "country_name": "일본",
        "language_code": "ja",
        "style_prompt": "일본 고객에게는 존경어(敬語)를 사용하고, "
                        "부드럽고 정중한 표현을 선호합니다.",
        "preferred_expressions": ["ございます", "いただけます", "ご案内"],
        "avoided_expressions": ["やばい", "マジ"],
        "emoji_level": "medium",
        "formality_level": "formal",
    }


@pytest.fixture
def persona():
    return {
        "name": "미소",
        "personality": "밝고 친근한 상담사",
    }


class TestStyleChain:
    async def test_invoke_returns_styled_response(
        self, style_chain, japanese_profile, persona
    ):
        result = await style_chain.ainvoke(
            knowledge_output="보톡스는 보툴리눔 독소 A형을 사용하는 시술입니다.",
            country_code="JP",
            language_code="ja",
            cultural_profile=japanese_profile,
            persona=persona,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_invoke_with_different_country(self, fake_llm):
        chain = StyleChain(llm=GenericFakeChatModel(
            messages=iter([
                AIMessage(content="肉毒素是使用A型肉毒杆菌毒素的治疗方法。"),
            ])
        ))
        chinese_profile = {
            "country_code": "CN",
            "country_name": "중국",
            "language_code": "zh-CN",
            "style_prompt": "중국 고객에게는 직접적이고 실용적인 표현을 사용합니다.",
            "preferred_expressions": ["您好", "欢迎"],
            "avoided_expressions": [],
            "emoji_level": "high",
            "formality_level": "polite",
        }
        result = await chain.ainvoke(
            knowledge_output="보톡스 기본 정보",
            country_code="CN",
            language_code="zh-CN",
            cultural_profile=chinese_profile,
            persona={"name": "유나", "personality": "전문적"},
        )
        assert isinstance(result, str)

    def test_chain_has_prompt_template(self, style_chain):
        assert style_chain.prompt is not None
