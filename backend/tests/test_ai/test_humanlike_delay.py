import pytest

from app.ai.humanlike.delay import HumanLikeDelay


class TestCalculateDelay:
    def test_short_text_minimum_delay(self):
        """Short text should have at least 1 second delay."""
        delay = HumanLikeDelay.calculate_delay("네")
        assert delay >= 1.0

    def test_short_text_reasonable_upper_bound(self):
        """Short text should not exceed 4 seconds."""
        delays = [HumanLikeDelay.calculate_delay("네") for _ in range(20)]
        assert all(d <= 4.0 for d in delays)

    def test_long_text_more_delay(self):
        """Longer text should produce longer average delay than short text."""
        short_delays = [HumanLikeDelay.calculate_delay("네") for _ in range(50)]
        long_text = "안녕하세요! 보톡스에 대해 자세히 안내드리겠습니다. 보톡스는 근육 이완을 통해 주름을 개선하는 시술입니다."
        long_delays = [HumanLikeDelay.calculate_delay(long_text) for _ in range(50)]
        assert sum(long_delays) / len(long_delays) > sum(short_delays) / len(short_delays)

    def test_maximum_delay_cap(self):
        """Delay should never exceed 8 seconds even for very long text."""
        very_long = "보톡스 " * 500
        delays = [HumanLikeDelay.calculate_delay(very_long) for _ in range(20)]
        assert all(d <= 8.0 for d in delays)

    def test_minimum_delay_floor(self):
        """Delay should never be less than 1 second."""
        delays = [HumanLikeDelay.calculate_delay("") for _ in range(20)]
        assert all(d >= 1.0 for d in delays)

    def test_returns_float(self):
        delay = HumanLikeDelay.calculate_delay("테스트 메시지")
        assert isinstance(delay, float)

    def test_different_calls_produce_variation(self):
        """Delays should have some randomness (jitter)."""
        text = "보톡스 가격이 얼마인가요?"
        delays = [HumanLikeDelay.calculate_delay(text) for _ in range(30)]
        unique_delays = set(round(d, 4) for d in delays)
        # Should have at least some variation
        assert len(unique_delays) > 1
