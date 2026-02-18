"""LLM Router — provides configured LLM instances with fallback chains.

Usage:
    from app.ai.llm_router import get_consultation_llm, get_light_llm, get_embeddings

    consultation_llm = get_consultation_llm()   # Claude → GPT-4o → Gemini
    light_llm = get_light_llm()                 # GPT-4o-mini → Gemini Flash
    embeddings = get_embeddings()               # Azure text-embedding-3-small
"""

from functools import lru_cache

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

from app.config import settings


def _build_claude() -> ChatAnthropic:
    return ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        api_key=settings.anthropic_api_key,
        temperature=settings.ai_temperature,
        max_tokens=settings.ai_max_tokens,
    )


def _build_gpt4o() -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_deployment=settings.azure_openai_deployment_name,
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        temperature=settings.ai_temperature,
        max_tokens=settings.ai_max_tokens,
    )


def _build_gpt4o_mini() -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_deployment=settings.azure_openai_mini_deployment_name,
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
        temperature=settings.ai_temperature,
        max_tokens=settings.ai_max_tokens,
    )


def _build_gemini() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=settings.google_api_key,
        temperature=settings.ai_temperature,
        max_output_tokens=settings.ai_max_tokens,
    )


@lru_cache
def get_consultation_llm() -> BaseChatModel:
    """Main consultation LLM: Claude → GPT-4o → Gemini fallback chain."""
    claude = _build_claude()
    gpt4o = _build_gpt4o()
    gemini = _build_gemini()
    return claude.with_fallbacks([gpt4o, gemini])


@lru_cache
def get_light_llm() -> BaseChatModel:
    """Light LLM for classification, keyword extraction, language detection.
    GPT-4o-mini → Gemini Flash fallback chain.
    """
    gpt4o_mini = _build_gpt4o_mini()
    gemini = _build_gemini()
    return gpt4o_mini.with_fallbacks([gemini])


@lru_cache
def get_embeddings() -> AzureOpenAIEmbeddings:
    """Embedding model for RAG vector store."""
    return AzureOpenAIEmbeddings(
        azure_deployment=settings.azure_openai_embedding_deployment,
        api_key=settings.azure_openai_api_key,
        azure_endpoint=settings.azure_openai_endpoint,
        api_version=settings.azure_openai_api_version,
    )
