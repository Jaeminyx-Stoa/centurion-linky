import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from app.ai.chains.translation_chain import (
    LanguageDetector,
    MedicalTermMatcher,
    TranslationChain,
)


# --- LanguageDetector ---

class TestLanguageDetector:
    async def test_detect_japanese(self):
        fake_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="ja")])
        )
        detector = LanguageDetector(llm=fake_llm)
        result = await detector.detect("ボトックスはいくらですか？")
        assert result == "ja"

    async def test_detect_chinese(self):
        fake_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="zh-CN")])
        )
        detector = LanguageDetector(llm=fake_llm)
        result = await detector.detect("肉毒素多少钱？")
        assert result == "zh-CN"

    async def test_detect_english(self):
        fake_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="en")])
        )
        detector = LanguageDetector(llm=fake_llm)
        result = await detector.detect("How much is Botox?")
        assert result == "en"

    async def test_detect_korean(self):
        fake_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="ko")])
        )
        detector = LanguageDetector(llm=fake_llm)
        result = await detector.detect("보톡스 얼마예요?")
        assert result == "ko"

    async def test_uses_known_language_if_provided(self):
        fake_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="en")])  # won't be called
        )
        detector = LanguageDetector(llm=fake_llm)
        result = await detector.detect(
            "some text",
            known_language="ja",
        )
        assert result == "ja"


# --- MedicalTermMatcher ---

class TestMedicalTermMatcher:
    @pytest.fixture
    def term_dict(self):
        """Simulated term lookup: language -> {foreign_term: korean_term}"""
        return {
            "ja": {"ボトックス": "보톡스", "ヒアルロン酸": "히알루론산"},
            "en": {"botox": "보톡스", "filler": "필러"},
            "zh-CN": {"肉毒素": "보톡스", "玻尿酸": "히알루론산"},
        }

    @pytest.fixture
    def matcher(self, term_dict):
        return MedicalTermMatcher(term_dict)

    def test_match_japanese_terms(self, matcher):
        text = "ボトックスの値段を教えてください"
        result = matcher.replace_terms(text, "ja")
        assert "[TERM:보톡스]" in result
        assert "ボトックス" not in result

    def test_match_english_terms(self, matcher):
        text = "How much does botox cost?"
        result = matcher.replace_terms(text, "en")
        assert "[TERM:보톡스]" in result

    def test_match_chinese_terms(self, matcher):
        text = "肉毒素和玻尿酸可以一起打吗？"
        result = matcher.replace_terms(text, "zh-CN")
        assert "[TERM:보톡스]" in result
        assert "[TERM:히알루론산]" in result

    def test_no_match_returns_original(self, matcher):
        text = "예약하고 싶어요"
        result = matcher.replace_terms(text, "ko")
        assert result == text

    def test_case_insensitive_english(self, matcher):
        text = "I want Botox please"
        result = matcher.replace_terms(text, "en")
        assert "[TERM:보톡스]" in result

    def test_restore_terms(self, matcher):
        text = "이 [TERM:보톡스] 시술은 [TERM:히알루론산]과 함께 가능합니다."
        result = matcher.restore_terms(text)
        assert "보톡스" in result
        assert "히알루론산" in result
        assert "[TERM:" not in result

    def test_unknown_language_returns_original(self, matcher):
        text = "some text"
        result = matcher.replace_terms(text, "xx")
        assert result == text


# --- TranslationChain ---

class TestTranslationChain:
    @pytest.fixture
    def fake_translation_llm(self):
        return GenericFakeChatModel(
            messages=iter([
                AIMessage(content="보톡스 가격을 알려주세요"),
            ])
        )

    @pytest.fixture
    def fake_detect_llm(self):
        return GenericFakeChatModel(
            messages=iter([AIMessage(content="ja")])
        )

    @pytest.fixture
    def term_dict(self):
        return {
            "ja": {"ボトックス": "보톡스"},
            "en": {"botox": "보톡스"},
        }

    @pytest.fixture
    def chain(self, fake_translation_llm, fake_detect_llm, term_dict):
        return TranslationChain(
            translation_llm=fake_translation_llm,
            detection_llm=fake_detect_llm,
            term_dict=term_dict,
        )

    async def test_translate_incoming_japanese_to_korean(self, chain):
        result = await chain.translate_incoming(
            text="ボトックスはいくらですか？",
            known_language="ja",
        )
        assert result.translated_text is not None
        assert result.source_language == "ja"
        assert result.target_language == "ko"

    async def test_translate_incoming_detects_language(self, chain):
        result = await chain.translate_incoming(
            text="ボトックスはいくらですか？",
        )
        assert result.source_language == "ja"

    async def test_translate_incoming_korean_skips_translation(
        self, fake_translation_llm, term_dict
    ):
        detect_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="ko")])
        )
        chain = TranslationChain(
            translation_llm=fake_translation_llm,
            detection_llm=detect_llm,
            term_dict=term_dict,
        )
        result = await chain.translate_incoming(
            text="보톡스 얼마예요?",
            known_language="ko",
        )
        assert result.translated_text == "보톡스 얼마예요?"
        assert result.source_language == "ko"
        assert result.skipped is True

    async def test_translate_outgoing_korean_to_japanese(self):
        fake_llm = GenericFakeChatModel(
            messages=iter([AIMessage(content="ボトックスの料金をご案内いたします。")])
        )
        chain = TranslationChain(
            translation_llm=fake_llm,
            detection_llm=GenericFakeChatModel(messages=iter([AIMessage(content="ko")])),
            term_dict={"ja": {"ボトックス": "보톡스"}},
        )
        result = await chain.translate_outgoing(
            text="보톡스 가격을 안내드리겠습니다.",
            target_language="ja",
        )
        assert result.translated_text is not None
        assert result.target_language == "ja"
