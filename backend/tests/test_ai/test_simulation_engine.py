import pytest

from app.ai.simulation_engine import (
    CUSTOMER_PERSONAS,
    analyze_simulation,
    is_conversation_ended,
)


class TestCustomerPersonas:
    def test_has_4_personas(self):
        assert len(CUSTOMER_PERSONAS) == 4

    def test_persona_structure(self):
        for p in CUSTOMER_PERSONAS:
            assert "name" in p
            assert "profile" in p
            assert "behavior" in p
            assert "language" in p
            assert "country" in p

    def test_unique_countries(self):
        countries = [p["country"] for p in CUSTOMER_PERSONAS]
        assert len(set(countries)) == 4


class TestIsConversationEnded:
    def test_booking_korean(self):
        ended, reason = is_conversation_ended("예약하고 싶어요")
        assert ended is True
        assert reason == "booked"

    def test_booking_english(self):
        ended, reason = is_conversation_ended("I'd like to book an appointment")
        assert ended is True
        assert reason == "booked"

    def test_booking_japanese(self):
        ended, reason = is_conversation_ended("予約お願いします")
        assert ended is True
        assert reason == "booked"

    def test_exit_korean(self):
        ended, reason = is_conversation_ended("됐어요 다음에 볼게요")
        assert ended is True
        assert reason == "abandoned"

    def test_exit_english(self):
        ended, reason = is_conversation_ended("no thanks, not interested")
        assert ended is True
        assert reason == "abandoned"

    def test_neutral_message(self):
        ended, reason = is_conversation_ended("가격이 얼마인가요?")
        assert ended is False
        assert reason is None


class TestAnalyzeSimulation:
    def test_empty_messages(self):
        result = analyze_simulation([])
        assert result["booked"] is False
        assert result["abandoned"] is True
        assert result["total_rounds"] == 0

    def test_booked_conversation(self):
        msgs = [
            {"role": "customer", "content": "보톡스 가격이 얼마인가요?", "round": 1},
            {"role": "ai", "content": "보톡스는 10만원입니다", "round": 1},
            {"role": "customer", "content": "좋아요 예약할게요", "round": 2},
        ]
        result = analyze_simulation(msgs)
        assert result["booked"] is True
        assert result["abandoned"] is False
        assert result["exit_reason"] == "booked"
        assert result["satisfaction_estimate"] >= 70

    def test_abandoned_conversation(self):
        msgs = [
            {"role": "customer", "content": "가격이 얼마인가요?", "round": 1},
            {"role": "ai", "content": "50만원입니다", "round": 1},
            {"role": "customer", "content": "됐어요 비싸요", "round": 2},
        ]
        result = analyze_simulation(msgs)
        assert result["booked"] is False
        assert result["abandoned"] is True
        assert result["exit_reason"] == "abandoned"

    def test_max_rounds_without_decision(self):
        msgs = [
            {"role": "customer", "content": f"질문 {i}", "round": i}
            for i in range(1, 11)
        ]
        result = analyze_simulation(msgs)
        assert result["booked"] is False
        assert result["exit_reason"] == "max_rounds"

    def test_customer_message_count(self):
        msgs = [
            {"role": "customer", "content": "안녕하세요", "round": 1},
            {"role": "ai", "content": "안녕하세요!", "round": 1},
            {"role": "customer", "content": "예약할게요", "round": 2},
        ]
        result = analyze_simulation(msgs)
        assert result["customer_message_count"] == 2
