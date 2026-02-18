"""ResponseChain — 3-layer pipeline orchestrator.

Executes: KnowledgeChain → StyleChain → SalesSkillChain
"""

from app.ai.chains.knowledge_chain import KnowledgeChain
from app.ai.chains.sales_skill_chain import SalesSkillChain
from app.ai.chains.style_chain import StyleChain


class ResponseChain:
    """Orchestrates the 3-layer AI response pipeline."""

    def __init__(
        self,
        knowledge_chain: KnowledgeChain,
        style_chain: StyleChain,
        sales_chain: SalesSkillChain,
    ):
        self.knowledge_chain = knowledge_chain
        self.style_chain = style_chain
        self.sales_chain = sales_chain

    async def ainvoke(
        self,
        query: str,
        rag_results: str,
        clinic_manual: str,
        country_code: str,
        language_code: str,
        cultural_profile: dict,
        persona: dict,
        conversation_history: str,
        sales_context: dict,
    ) -> str:
        # Layer 1: Knowledge extraction
        knowledge_output = await self.knowledge_chain.ainvoke(
            query=query,
            rag_results=rag_results,
            clinic_manual=clinic_manual,
        )

        # Layer 2: Cultural styling + translation
        styled_output = await self.style_chain.ainvoke(
            knowledge_output=knowledge_output,
            country_code=country_code,
            language_code=language_code,
            cultural_profile=cultural_profile,
            persona=persona,
        )

        # Layer 3: Sales strategy
        final_output = await self.sales_chain.ainvoke(
            styled_output=styled_output,
            conversation_history=conversation_history,
            sales_context=sales_context,
        )

        return final_output
