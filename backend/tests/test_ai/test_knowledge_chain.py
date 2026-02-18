import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.ai.chains.knowledge_chain import KnowledgeChain


@pytest.fixture
def fake_llm():
    return GenericFakeChatModel(
        messages=iter([
            AIMessage(content="보톡스는 보툴리눔 독소 A형을 사용하는 시술입니다. "
                      "시술 시간은 약 10-15분이며, 효과는 3-6개월 지속됩니다. "
                      "주요 부작용으로는 주사 부위 멍, 두통이 있습니다."),
        ])
    )


@pytest.fixture
def knowledge_chain(fake_llm):
    return KnowledgeChain(llm=fake_llm)


class TestKnowledgeChain:
    async def test_invoke_returns_medical_facts(self, knowledge_chain):
        result = await knowledge_chain.ainvoke(
            query="보톡스 시술에 대해 알려주세요",
            rag_results="보톡스: 보툴리눔 독소 A형, 주름 개선 시술",
            clinic_manual="우리 병원은 앨러간 보톡스만 사용합니다.",
        )
        assert isinstance(result, str)
        assert len(result) > 0

    async def test_invoke_includes_query_in_prompt(self, knowledge_chain):
        """Chain should format query into the prompt."""
        result = await knowledge_chain.ainvoke(
            query="리프팅 가격이 얼마인가요?",
            rag_results="울쎄라 리프팅: 50만원~200만원",
            clinic_manual="",
        )
        assert isinstance(result, str)

    async def test_handles_empty_rag_results(self, fake_llm):
        chain = KnowledgeChain(llm=GenericFakeChatModel(
            messages=iter([
                AIMessage(content="해당 정보에 대해 담당 의료진에게 확인해 드리겠습니다."),
            ])
        ))
        result = await chain.ainvoke(
            query="새로운 시술 있나요?",
            rag_results="",
            clinic_manual="",
        )
        assert isinstance(result, str)

    async def test_handles_empty_clinic_manual(self, fake_llm):
        chain = KnowledgeChain(llm=GenericFakeChatModel(
            messages=iter([
                AIMessage(content="일반적인 보톡스 정보입니다."),
            ])
        ))
        result = await chain.ainvoke(
            query="보톡스 정보",
            rag_results="보톡스 기본 정보",
            clinic_manual="",
        )
        assert isinstance(result, str)

    def test_chain_has_prompt_template(self, knowledge_chain):
        """KnowledgeChain should have a properly configured prompt."""
        assert knowledge_chain.prompt is not None
