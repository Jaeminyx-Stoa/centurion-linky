AI_DISCLOSURE = {
    "ko": "AI 상담사가 도와드리고 있으며, 필요시 전문 상담사가 연결됩니다.",
    "ja": "AIアシスタントがご対応しております。必要に応じて専門スタッフにお繋ぎいたします。",
    "en": "You are chatting with an AI assistant. A specialist can be connected if needed.",
    "zh": "AI助手正在为您服务。如需要，可以为您转接专业顾问。",
    "vi": "Tro ly AI dang ho tro ban. Chuyen gia co the ket noi khi can thiet.",
}


def get_ai_disclosure(language_code: str) -> str:
    """Return AI disclosure message for the given language."""
    return AI_DISCLOSURE.get(language_code, AI_DISCLOSURE["en"])
