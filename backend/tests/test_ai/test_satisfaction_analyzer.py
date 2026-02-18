from datetime import datetime, timedelta, timezone

import pytest

from app.ai.satisfaction.analyzer import (
    AnalysisResult,
    SatisfactionAnalyzer,
    score_to_level,
)


# --- score_to_level tests ---
class TestScoreToLevel:
    def test_green(self):
        assert score_to_level(95) == "green"
        assert score_to_level(90) == "green"

    def test_yellow(self):
        assert score_to_level(85) == "yellow"
        assert score_to_level(70) == "yellow"

    def test_orange(self):
        assert score_to_level(65) == "orange"
        assert score_to_level(50) == "orange"

    def test_red(self):
        assert score_to_level(49) == "red"
        assert score_to_level(0) == "red"


# --- Helper ---
def _msg(sender_type: str, content: str, minutes_ago: int = 0) -> dict:
    return {
        "sender_type": sender_type,
        "content": content,
        "created_at": datetime.now(timezone.utc) - timedelta(minutes=minutes_ago),
    }


# --- SatisfactionAnalyzer tests ---
class TestAnalyzerBasic:
    def test_returns_analysis_result(self):
        analyzer = SatisfactionAnalyzer()
        msgs = [_msg("customer", "안녕하세요")]
        result = analyzer.analyze(msgs)
        assert isinstance(result, AnalysisResult)
        assert 0 <= result.score <= 100
        assert result.level in ("green", "yellow", "orange", "red")

    def test_empty_messages(self):
        analyzer = SatisfactionAnalyzer()
        result = analyzer.analyze([])
        assert result.score == 70  # neutral baseline
        assert result.level == "yellow"


class TestLanguageSignals:
    def test_positive_keywords_boost_score(self):
        analyzer = SatisfactionAnalyzer()
        msgs = [_msg("customer", "감사합니다 예약하고 싶어요")]
        result = analyzer.analyze(msgs)
        assert result.score > 70
        assert result.language_signals["positive_hits"]

    def test_negative_keywords_reduce_score(self):
        analyzer = SatisfactionAnalyzer()
        msgs = [_msg("customer", "됐어요 비싸요 다른 병원 갈게요")]
        result = analyzer.analyze(msgs)
        assert result.score < 70
        assert result.language_signals["negative_hits"]

    def test_japanese_positive(self):
        analyzer = SatisfactionAnalyzer()
        msgs = [_msg("customer", "ありがとうございます 予約お願いします")]
        result = analyzer.analyze(msgs)
        assert result.score > 70

    def test_english_negative(self):
        analyzer = SatisfactionAnalyzer()
        msgs = [_msg("customer", "no thanks, not interested, too expensive")]
        result = analyzer.analyze(msgs)
        assert result.score < 70

    def test_neutral_message(self):
        analyzer = SatisfactionAnalyzer()
        msgs = [_msg("customer", "이 시술 시간이 어떻게 되나요?")]
        result = analyzer.analyze(msgs)
        # Should be around baseline
        assert 60 <= result.score <= 80


class TestBehaviorSignals:
    def test_message_length_drop(self):
        analyzer = SatisfactionAnalyzer()
        msgs = [
            _msg("customer", "안녕하세요 보톡스에 대해 자세히 알고 싶습니다 가격이랑 시간이랑 효과도 궁금합니다", 5),
            _msg("customer", "네", 1),
        ]
        result = analyzer.analyze(msgs)
        assert result.behavior_signals.get("length_drop") is True

    def test_long_response_gap(self):
        analyzer = SatisfactionAnalyzer()
        msgs = [
            _msg("customer", "안녕하세요", 20),
            _msg("customer", "네 알겠습니다", 0),
        ]
        result = analyzer.analyze(msgs)
        assert result.behavior_signals.get("gap_seconds", 0) > 600

    def test_quick_response(self):
        analyzer = SatisfactionAnalyzer()
        now = datetime.now(timezone.utc)
        msgs = [
            {"sender_type": "customer", "content": "안녕하세요", "created_at": now - timedelta(seconds=20)},
            {"sender_type": "customer", "content": "예약할게요!", "created_at": now},
        ]
        result = analyzer.analyze(msgs)
        assert result.behavior_signals.get("quick_response") is True


class TestFlowSignals:
    def test_booking_intent_positive(self):
        analyzer = SatisfactionAnalyzer()
        msgs = [_msg("customer", "예약하고 싶어요 언제 가능하나요?")]
        result = analyzer.analyze(msgs)
        assert result.flow_signals.get("booking_intent")
        assert result.score > 70

    def test_exit_signals_negative(self):
        analyzer = SatisfactionAnalyzer()
        msgs = [_msg("customer", "생각해볼게요 다른 병원도 알아볼게요")]
        result = analyzer.analyze(msgs)
        assert result.flow_signals.get("exit_signals")
        assert result.score < 70

    def test_repeated_messages(self):
        analyzer = SatisfactionAnalyzer()
        msgs = [
            _msg("customer", "가격이 얼마인가요?", 5),
            _msg("customer", "가격이 얼마인가요?", 3),
            _msg("customer", "가격이 얼마인가요?", 1),
        ]
        result = analyzer.analyze(msgs)
        assert result.flow_signals.get("repeated_messages", 0) >= 1
        assert result.score < 70


class TestCombinedAnalysis:
    def test_highly_satisfied_customer(self):
        analyzer = SatisfactionAnalyzer()
        now = datetime.now(timezone.utc)
        msgs = [
            {"sender_type": "customer", "content": "좋아요 감사합니다", "created_at": now - timedelta(seconds=20)},
            {"sender_type": "ai", "content": "예약 도와드릴게요", "created_at": now - timedelta(seconds=15)},
            {"sender_type": "customer", "content": "네 예약하고 싶어요! 감사합니다", "created_at": now},
        ]
        result = analyzer.analyze(msgs)
        assert result.level in ("green", "yellow")
        assert result.score >= 70

    def test_dissatisfied_customer(self):
        analyzer = SatisfactionAnalyzer()
        now = datetime.now(timezone.utc)
        msgs = [
            {"sender_type": "customer", "content": "보톡스 가격이 얼마인가요? 효과는 어떤가요?", "created_at": now - timedelta(minutes=15)},
            {"sender_type": "ai", "content": "보톡스는 10만원입니다", "created_at": now - timedelta(minutes=14)},
            {"sender_type": "customer", "content": "비싸요 됐어요", "created_at": now},
        ]
        result = analyzer.analyze(msgs)
        assert result.level in ("orange", "red")
        assert result.score < 70
