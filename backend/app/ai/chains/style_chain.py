import json

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

STYLE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 {persona_name}입니다. ({persona_personality})

[문화 스타일 가이드 - {country_name}]
{style_prompt}

[선호 표현]
{preferred_expressions}

[피해야 할 표현]
{avoided_expressions}

[이모지 사용 수준: {emoji_level}]

[격식 수준: {formality_level}]"""),
    ("human", "아래 정보를 {language_code} 언어로, 위 문화 스타일에 맞게 자연스럽게 표현하세요:\n{knowledge_output}"),
])


class StyleChain:
    """Layer 2: Applies cultural styling and language translation."""

    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        self.prompt = STYLE_PROMPT
        self._chain = self.prompt | self.llm | StrOutputParser()

    async def ainvoke(
        self,
        knowledge_output: str,
        country_code: str,
        language_code: str,
        cultural_profile: dict,
        persona: dict,
    ) -> str:
        preferred = cultural_profile.get("preferred_expressions", [])
        avoided = cultural_profile.get("avoided_expressions", [])

        return await self._chain.ainvoke({
            "persona_name": persona.get("name", "상담사"),
            "persona_personality": persona.get("personality", ""),
            "country_name": cultural_profile.get("country_name", country_code),
            "style_prompt": cultural_profile.get("style_prompt", ""),
            "preferred_expressions": json.dumps(preferred, ensure_ascii=False) if preferred else "(없음)",
            "avoided_expressions": json.dumps(avoided, ensure_ascii=False) if avoided else "(없음)",
            "emoji_level": cultural_profile.get("emoji_level", "medium"),
            "formality_level": cultural_profile.get("formality_level", "polite"),
            "language_code": language_code,
            "knowledge_output": knowledge_output,
        })
