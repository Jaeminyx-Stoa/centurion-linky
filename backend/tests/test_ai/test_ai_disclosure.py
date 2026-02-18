import pytest

from app.ai.humanlike.disclosure import AI_DISCLOSURE, get_ai_disclosure


class TestAIDisclosure:
    def test_korean(self):
        msg = get_ai_disclosure("ko")
        assert "AI" in msg
        assert len(msg) > 10

    def test_japanese(self):
        msg = get_ai_disclosure("ja")
        assert "AI" in msg

    def test_english(self):
        msg = get_ai_disclosure("en")
        assert "AI" in msg.upper()

    def test_chinese(self):
        msg = get_ai_disclosure("zh")
        assert "AI" in msg

    def test_vietnamese(self):
        msg = get_ai_disclosure("vi")
        assert "AI" in msg

    def test_unknown_language_falls_back_to_english(self):
        msg = get_ai_disclosure("de")
        assert msg == AI_DISCLOSURE["en"]

    def test_all_supported_languages(self):
        for lang in ("ko", "ja", "en", "zh", "vi"):
            msg = get_ai_disclosure(lang)
            assert isinstance(msg, str)
            assert len(msg) > 0
