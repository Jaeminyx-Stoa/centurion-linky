"""ConsultationAgent — LangChain tool-calling agent for medical consultations.

Uses an LLM with bound tools to handle bookings, payments, and escalation
while answering general Q&A directly.
"""

import logging

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = """You are {persona_name}, a medical consultation AI assistant \
for a cosmetic clinic.

Your personality: {persona_personality}

## Knowledge Context
{rag_results}

## Clinic Manual
{clinic_manual}

## Cultural Style
Respond in {language_code}. Cultural context: {cultural_context}

## Rules
- Use tools when the customer wants to: book a procedure, pay, check availability, \
or needs human help.
- For general Q&A about procedures, pricing, aftercare, respond directly without tools.
- Always be professional, warm, and helpful.
- If you don't know the answer, suggest escalating to a human.
- Never make up medical information not in the knowledge context.
- Respond naturally in the customer's language."""


class ConsultationAgent:
    """Tool-calling agent for medical consultation with booking/payment capabilities."""

    def __init__(self, llm, tools: list):
        prompt = ChatPromptTemplate.from_messages([
            ("system", AGENT_SYSTEM_PROMPT),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ])
        agent = create_tool_calling_agent(llm, tools, prompt)
        self.executor = AgentExecutor(
            agent=agent,
            tools=tools,
            max_iterations=5,
            return_intermediate_steps=True,
            verbose=False,
        )

    async def ainvoke(
        self,
        input: str,
        chat_history: list,
        **context,
    ) -> str:
        """Run the agent with input and context.

        Args:
            input: Customer message text
            chat_history: List of LangChain message objects
            **context: Additional context (persona_name, rag_results, etc.)

        Returns:
            Agent response text.
        """
        result = await self.executor.ainvoke({
            "input": input,
            "chat_history": chat_history,
            **context,
        })
        return result["output"]
