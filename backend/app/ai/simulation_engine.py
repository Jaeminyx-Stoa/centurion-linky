"""Simulation engine for AI vs AI consultation testing.

The actual LLM-driven simulation is a Celery task. This module provides:
- Customer persona definitions
- Conversation ending detection
- Result analysis from message logs
"""

CUSTOMER_PERSONAS = [
    {
        "name": "유코",
        "profile": "일본인 30대 여성, 신중, 질문 많음, 가격 민감",
        "behavior": "3번 이상 확인해야 예약, 한국 미용 처음",
        "language": "ja",
        "country": "JP",
    },
    {
        "name": "웨이",
        "profile": "중국인 40대 남성, 직접적, 결과 중심",
        "behavior": "VIP 대우 기대, Before/After 요구, 빠른 결정",
        "language": "zh",
        "country": "CN",
    },
    {
        "name": "제시카",
        "profile": "미국인 20대 여성, 적극적, SNS 영향",
        "behavior": "리뷰 중시, 자연스러움 추구, 예산 있음",
        "language": "en",
        "country": "US",
    },
    {
        "name": "린",
        "profile": "베트남인 30대 여성, 친근, 가성비 추구",
        "behavior": "패키지 선호, 친구 추천, 가격 협상",
        "language": "vi",
        "country": "VN",
    },
]

# Keywords indicating conversation has ended
_BOOKING_KEYWORDS = [
    "예약", "book", "reserve", "予約", "预约", "đặt lịch",
]
_EXIT_KEYWORDS = [
    "됐어요", "no thanks", "not interested", "結構です",
    "不需要", "thôi", "bye", "이만", "다음에",
]


def is_conversation_ended(message: str) -> tuple[bool, str | None]:
    """Check if the customer message indicates conversation end.

    Returns (ended, reason) where reason is 'booked', 'abandoned', or None.
    """
    lower = message.lower()

    for kw in _BOOKING_KEYWORDS:
        if kw in lower:
            return True, "booked"

    for kw in _EXIT_KEYWORDS:
        if kw in lower:
            return True, "abandoned"

    return False, None


def analyze_simulation(messages: list[dict]) -> dict:
    """Analyze a completed simulation conversation.

    Args:
        messages: List of {"role": "customer"|"ai", "content": "...", "round": int}

    Returns:
        Analysis dict with booked, abandoned, satisfaction estimate, etc.
    """
    if not messages:
        return {
            "booked": False,
            "abandoned": True,
            "total_rounds": 0,
            "exit_reason": "no_messages",
            "satisfaction_estimate": 0,
        }

    total_rounds = max(m.get("round", 0) for m in messages)
    customer_msgs = [m for m in messages if m.get("role") == "customer"]

    # Check last customer message for booking or exit
    booked = False
    abandoned = False
    exit_reason = None

    if customer_msgs:
        last_msg = customer_msgs[-1].get("content", "")
        ended, reason = is_conversation_ended(last_msg)
        if reason == "booked":
            booked = True
            exit_reason = "booked"
        elif reason == "abandoned":
            abandoned = True
            exit_reason = "abandoned"
        else:
            # Conversation reached max rounds without clear ending
            abandoned = True
            exit_reason = "max_rounds"

    # Simple satisfaction estimate based on conversation length and outcome
    if booked:
        satisfaction = min(70 + total_rounds * 2, 95)
    elif total_rounds >= 10:
        satisfaction = 50  # Long conversation without booking = mediocre
    else:
        satisfaction = max(30, 70 - (10 - total_rounds) * 5)

    return {
        "booked": booked,
        "abandoned": abandoned,
        "total_rounds": total_rounds,
        "exit_reason": exit_reason,
        "satisfaction_estimate": satisfaction,
        "customer_message_count": len(customer_msgs),
    }
