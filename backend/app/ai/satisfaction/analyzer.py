"""Real-time conversation satisfaction analyzer.

Analyzes customer messages using three signal types:
- Language signals (40%): keyword sentiment detection
- Behavior signals (35%): message length/gap patterns
- Flow signals (25%): conversation intent/direction
"""

from dataclasses import dataclass, field

_NEGATIVE_KEYWORDS: dict[str, list[str]] = {
    "ko": ["아니요", "됐어요", "그만", "싫어요", "답답", "왜 자꾸", "비싸", "다른 병원"],
    "ja": ["いいえ", "結構", "もういい", "嫌", "しつこい", "高い", "他の病院"],
    "en": ["no thanks", "not interested", "stop", "annoying", "expensive", "other clinic"],
    "zh": ["不要", "算了", "不需要", "烦", "太贵", "别的医院"],
}

_POSITIVE_KEYWORDS: dict[str, list[str]] = {
    "ko": ["좋아요", "감사", "궁금", "네", "언제", "예약", "하고 싶어"],
    "ja": ["いいですね", "ありがとう", "予約", "いつ", "お願い"],
    "en": ["great", "thanks", "interested", "when", "book", "please"],
    "zh": ["好的", "谢谢", "感兴趣", "预约", "什么时候"],
}

_FLOW_POSITIVE = ["예약", "book", "予約", "预约", "언제", "when", "いつ", "什么时候"]
_FLOW_NEGATIVE = ["생각해볼게", "think about", "考えます", "考虑", "다른 병원", "other clinic", "他の病院", "别的医院"]


@dataclass
class SignalResult:
    score: int
    details: dict = field(default_factory=dict)


@dataclass
class AnalysisResult:
    score: int
    level: str
    language_signals: dict
    behavior_signals: dict
    flow_signals: dict


def score_to_level(score: int) -> str:
    """Map satisfaction score (0-100) to alert level."""
    if score >= 90:
        return "green"
    elif score >= 70:
        return "yellow"
    elif score >= 50:
        return "orange"
    else:
        return "red"


class SatisfactionAnalyzer:
    """Analyzes real-time conversation satisfaction from message history."""

    def analyze(self, messages: list[dict]) -> AnalysisResult:
        """Analyze satisfaction from a list of message dicts.

        Each message dict should have: sender_type, content, created_at.
        Returns AnalysisResult with score (0-100) and level.
        """
        language = self._analyze_language_signals(messages)
        behavior = self._analyze_behavior_signals(messages)
        flow = self._analyze_flow_signals(messages)

        total = round(
            language.score * 0.40
            + behavior.score * 0.35
            + flow.score * 0.25
        )
        total = max(0, min(100, total))

        return AnalysisResult(
            score=total,
            level=score_to_level(total),
            language_signals=language.details,
            behavior_signals=behavior.details,
            flow_signals=flow.details,
        )

    def _analyze_language_signals(self, messages: list[dict]) -> SignalResult:
        """Analyze linguistic sentiment from customer messages."""
        customer_msgs = [m for m in messages if m.get("sender_type") == "customer"]
        if not customer_msgs:
            return SignalResult(score=70, details={"reason": "no_customer_messages"})

        latest = customer_msgs[-1]
        text = latest.get("content", "").lower()

        score = 70  # neutral baseline
        positive_hits = []
        negative_hits = []

        for lang, keywords in _POSITIVE_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    positive_hits.append(kw)

        for lang, keywords in _NEGATIVE_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text:
                    negative_hits.append(kw)

        score += len(positive_hits) * 8
        score -= len(negative_hits) * 12

        return SignalResult(
            score=max(0, min(100, score)),
            details={
                "positive_hits": positive_hits,
                "negative_hits": negative_hits,
                "base_score": 70,
            },
        )

    def _analyze_behavior_signals(self, messages: list[dict]) -> SignalResult:
        """Analyze behavioral patterns: message length changes, response gaps."""
        customer_msgs = [m for m in messages if m.get("sender_type") == "customer"]
        if len(customer_msgs) < 2:
            return SignalResult(score=70, details={"reason": "insufficient_messages"})

        score = 70
        details = {}

        # Message length trend
        recent_len = len(customer_msgs[-1].get("content", ""))
        prev_len = len(customer_msgs[-2].get("content", ""))

        if prev_len > 0 and recent_len < prev_len * 0.3:
            score -= 15
            details["length_drop"] = True
        elif recent_len > prev_len * 1.5:
            score += 5
            details["length_increase"] = True

        # Response gap analysis (if timestamps available)
        recent_ts = customer_msgs[-1].get("created_at")
        prev_ts = customer_msgs[-2].get("created_at")

        if recent_ts and prev_ts:
            gap = (recent_ts - prev_ts).total_seconds()
            if gap > 600:  # > 10 minutes
                score -= 10
                details["long_gap"] = True
            elif gap < 30:  # < 30 seconds (very engaged)
                score += 5
                details["quick_response"] = True
            details["gap_seconds"] = gap

        details["recent_length"] = recent_len
        details["prev_length"] = prev_len

        return SignalResult(score=max(0, min(100, score)), details=details)

    def _analyze_flow_signals(self, messages: list[dict]) -> SignalResult:
        """Analyze conversation flow direction."""
        customer_msgs = [m for m in messages if m.get("sender_type") == "customer"]
        if not customer_msgs:
            return SignalResult(score=70, details={"reason": "no_customer_messages"})

        score = 70
        details = {}

        # Check all recent customer messages for intent signals
        all_text = " ".join(m.get("content", "").lower() for m in customer_msgs[-3:])

        positive_flow = [kw for kw in _FLOW_POSITIVE if kw.lower() in all_text]
        negative_flow = [kw for kw in _FLOW_NEGATIVE if kw.lower() in all_text]

        if positive_flow:
            score += 20
            details["booking_intent"] = positive_flow
        if negative_flow:
            score -= 20
            details["exit_signals"] = negative_flow

        # Repeated questions detection (simple: same message appears twice)
        contents = [m.get("content", "").strip() for m in customer_msgs[-5:]]
        repeated = len(contents) - len(set(contents))
        if repeated > 0:
            score -= 10 * repeated
            details["repeated_messages"] = repeated

        return SignalResult(score=max(0, min(100, score)), details=details)
