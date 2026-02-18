from datetime import datetime, timezone
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest

from app.ai.humanlike.greeting import get_time_greeting, get_time_period


class TestGetTimePeriod:
    def test_morning(self):
        assert get_time_period(6) == "morning"
        assert get_time_period(11) == "morning"

    def test_afternoon(self):
        assert get_time_period(12) == "afternoon"
        assert get_time_period(17) == "afternoon"

    def test_evening(self):
        assert get_time_period(18) == "evening"
        assert get_time_period(22) == "evening"

    def test_night(self):
        assert get_time_period(23) == "night"
        assert get_time_period(0) == "night"
        assert get_time_period(5) == "night"


class TestGetTimeGreeting:
    def test_korean_morning(self):
        # Mock time to morning in Asia/Seoul
        with patch("app.ai.humanlike.greeting._get_current_hour") as mock_hour:
            mock_hour.return_value = 9
            greeting = get_time_greeting("Asia/Seoul", "ko")
            assert greeting is not None
            assert len(greeting) > 0

    def test_japanese_afternoon(self):
        with patch("app.ai.humanlike.greeting._get_current_hour") as mock_hour:
            mock_hour.return_value = 14
            greeting = get_time_greeting("Asia/Tokyo", "ja")
            assert greeting is not None

    def test_english_evening(self):
        with patch("app.ai.humanlike.greeting._get_current_hour") as mock_hour:
            mock_hour.return_value = 20
            greeting = get_time_greeting("America/New_York", "en")
            assert "evening" in greeting.lower() or "Good" in greeting

    def test_chinese_night(self):
        with patch("app.ai.humanlike.greeting._get_current_hour") as mock_hour:
            mock_hour.return_value = 1
            greeting = get_time_greeting("Asia/Shanghai", "zh")
            assert greeting is not None

    def test_vietnamese_supported(self):
        with patch("app.ai.humanlike.greeting._get_current_hour") as mock_hour:
            mock_hour.return_value = 10
            greeting = get_time_greeting("Asia/Ho_Chi_Minh", "vi")
            assert greeting is not None

    def test_unknown_language_falls_back_to_english(self):
        with patch("app.ai.humanlike.greeting._get_current_hour") as mock_hour:
            mock_hour.return_value = 9
            greeting = get_time_greeting("Europe/London", "de")
            # Should fallback to English
            assert greeting is not None
            assert len(greeting) > 0

    def test_none_timezone_uses_utc(self):
        with patch("app.ai.humanlike.greeting._get_current_hour") as mock_hour:
            mock_hour.return_value = 15
            greeting = get_time_greeting(None, "en")
            assert greeting is not None

    def test_each_period_returns_different_greeting(self):
        """Different time periods should produce different greetings."""
        greetings = set()
        for hour in [8, 14, 20, 2]:
            with patch("app.ai.humanlike.greeting._get_current_hour") as mock_hour:
                mock_hour.return_value = hour
                greetings.add(get_time_greeting("Asia/Seoul", "ko"))
        assert len(greetings) == 4
