from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_GREETINGS = {
    "ko": {
        "morning": "좋은 아침입니다!",
        "afternoon": "안녕하세요!",
        "evening": "좋은 저녁입니다!",
        "night": "늦은 시간에 감사합니다!",
    },
    "ja": {
        "morning": "おはようございます!",
        "afternoon": "こんにちは!",
        "evening": "こんばんは!",
        "night": "夜遅くにありがとうございます!",
    },
    "en": {
        "morning": "Good morning!",
        "afternoon": "Hello!",
        "evening": "Good evening!",
        "night": "Thanks for reaching out!",
    },
    "zh": {
        "morning": "早上好!",
        "afternoon": "你好!",
        "evening": "晚上好!",
        "night": "感谢您的联系!",
    },
    "vi": {
        "morning": "Chao buoi sang!",
        "afternoon": "Xin chao!",
        "evening": "Chao buoi toi!",
        "night": "Cam on ban da lien he!",
    },
}


def get_time_period(hour: int) -> str:
    """Determine time period from hour (0-23)."""
    if 6 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    elif 18 <= hour < 23:
        return "evening"
    else:
        return "night"


def _get_current_hour(tz_name: str | None) -> int:
    """Get current hour in the given timezone."""
    if tz_name:
        try:
            tz = ZoneInfo(tz_name)
        except (KeyError, ValueError):
            tz = timezone.utc
    else:
        tz = timezone.utc
    return datetime.now(tz).hour


def get_time_greeting(customer_timezone: str | None, language_code: str) -> str:
    """Return appropriate greeting based on customer timezone and language."""
    hour = _get_current_hour(customer_timezone)
    period = get_time_period(hour)
    greetings = _GREETINGS.get(language_code, _GREETINGS["en"])
    return greetings[period]
