from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

KNOWLEDGE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 {clinic_name}의 의료 지식 전문가입니다.

[지식 우선순위]
1순위: 클리닉 자체 매뉴얼 (아래 제공)
2순위: 검색된 의학 정보 (아래 제공)

[클리닉 매뉴얼]
{clinic_manual}

[검색된 의학 정보]
{rag_results}

[규칙]
- 클리닉 매뉴얼에 있는 정보가 교과서와 다르면 클리닉 매뉴얼을 따른다
- 내부 전용 정보(재료비, 마진, 난이도 등)는 절대 포함하지 않는다
- 확실하지 않은 의료 정보는 "담당 의료진에게 확인해 드리겠습니다"로 안내
- 위험한 부작용 정보는 반드시 포함한다"""),
    ("human", "고객 질문: {query}\n\n정확한 의학 정보만 추출하세요 (표현이나 세일즈 전략은 포함하지 마세요):"),
])


class KnowledgeChain:
    """Layer 1: Extracts medical facts from RAG results and clinic manual."""

    def __init__(self, llm: BaseChatModel, clinic_name: str = "클리닉"):
        self.llm = llm
        self.clinic_name = clinic_name
        self.prompt = KNOWLEDGE_PROMPT
        self._chain = self.prompt | self.llm | StrOutputParser()

    async def ainvoke(
        self,
        query: str,
        rag_results: str,
        clinic_manual: str,
    ) -> str:
        return await self._chain.ainvoke({
            "clinic_name": self.clinic_name,
            "query": query,
            "rag_results": rag_results or "(검색 결과 없음)",
            "clinic_manual": clinic_manual or "(매뉴얼 없음)",
        })
