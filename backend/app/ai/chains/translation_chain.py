"""Translation pipeline — language detection, medical term matching, AI translation."""

import re
from dataclasses import dataclass, field

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

# --- Language Detection ---

SUPPORTED_LANGUAGES = ("ko", "ja", "en", "zh-CN", "zh-TW", "vi", "th", "id")
_LANG_LOOKUP = {code.lower(): code for code in SUPPORTED_LANGUAGES}

DETECT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "당신은 언어 감지 전문가입니다. 주어진 텍스트의 언어 코드만 답하세요.\n"
               "가능한 코드: ko, ja, en, zh-CN, zh-TW, vi, th, id\n"
               "코드만 답하세요."),
    ("human", "{text}"),
])


class LanguageDetector:
    """Detects the language of input text using LLM."""

    def __init__(self, llm: BaseChatModel):
        self._chain = DETECT_PROMPT | llm | StrOutputParser()

    async def detect(self, text: str, known_language: str | None = None) -> str:
        if known_language:
            return known_language
        result = await self._chain.ainvoke({"text": text})
        raw = result.strip()
        return _LANG_LOOKUP.get(raw.lower(), raw)


# --- Medical Term Matcher ---

TERM_PATTERN = re.compile(r"\[TERM:(.+?)\]")


class MedicalTermMatcher:
    """Replaces medical terms with markup for accurate translation."""

    def __init__(self, term_dict: dict[str, dict[str, str]]):
        """term_dict: {language_code: {foreign_term: korean_term}}"""
        self._term_dict = term_dict

    def replace_terms(self, text: str, language: str) -> str:
        """Replace foreign medical terms with [TERM:korean] markup."""
        terms = self._term_dict.get(language, {})
        if not terms:
            return text

        result = text
        for foreign_term, korean_term in sorted(terms.items(), key=lambda x: -len(x[0])):
            pattern = re.compile(re.escape(foreign_term), re.IGNORECASE)
            result = pattern.sub(f"[TERM:{korean_term}]", result)
        return result

    def restore_terms(self, text: str) -> str:
        """Remove [TERM:...] markup, keeping the Korean term."""
        return TERM_PATTERN.sub(r"\1", text)


# --- Translation Result ---

@dataclass
class TranslationResult:
    translated_text: str
    source_language: str
    target_language: str
    skipped: bool = False


# --- Translation Chain ---

TRANSLATE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "당신은 미용의료 전문 번역가입니다.\n"
               "[TERM:xxx]로 표시된 부분은 이미 번역된 전문 용어입니다. 그대로 사용하세요.\n"
               "나머지를 {target_language_name}으로 자연스럽게 번역하세요.\n"
               "번역 결과만 출력하세요."),
    ("human", "{text}"),
])

LANGUAGE_NAMES = {
    "ko": "한국어",
    "ja": "일본어",
    "en": "영어",
    "zh-CN": "중국어(간체)",
    "zh-TW": "중국어(번체)",
    "vi": "베트남어",
    "th": "태국어",
    "id": "인도네시아어",
}


class TranslationChain:
    """Full translation pipeline: detect → term match → translate."""

    def __init__(
        self,
        translation_llm: BaseChatModel,
        detection_llm: BaseChatModel,
        term_dict: dict[str, dict[str, str]],
    ):
        self._detector = LanguageDetector(detection_llm)
        self._matcher = MedicalTermMatcher(term_dict)
        self._translate_chain = TRANSLATE_PROMPT | translation_llm | StrOutputParser()

    async def translate_incoming(
        self,
        text: str,
        known_language: str | None = None,
    ) -> TranslationResult:
        """Translate incoming message (foreign → Korean)."""
        source_lang = await self._detector.detect(text, known_language)

        if source_lang == "ko":
            return TranslationResult(
                translated_text=text,
                source_language="ko",
                target_language="ko",
                skipped=True,
            )

        marked = self._matcher.replace_terms(text, source_lang)
        translated = await self._translate_chain.ainvoke({
            "text": marked,
            "target_language_name": "한국어",
        })
        restored = self._matcher.restore_terms(translated)

        return TranslationResult(
            translated_text=restored,
            source_language=source_lang,
            target_language="ko",
        )

    async def translate_outgoing(
        self,
        text: str,
        target_language: str,
    ) -> TranslationResult:
        """Translate outgoing message (Korean → foreign)."""
        if target_language == "ko":
            return TranslationResult(
                translated_text=text,
                source_language="ko",
                target_language="ko",
                skipped=True,
            )

        lang_name = LANGUAGE_NAMES.get(target_language, target_language)
        translated = await self._translate_chain.ainvoke({
            "text": text,
            "target_language_name": lang_name,
        })

        return TranslationResult(
            translated_text=translated,
            source_language="ko",
            target_language=target_language,
        )
