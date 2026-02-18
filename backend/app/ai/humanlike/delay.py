import random


class HumanLikeDelay:
    """Calculate human-like typing delay based on text length."""

    @staticmethod
    def calculate_delay(response_text: str) -> float:
        """Return delay in seconds proportional to text length.

        Range: 1.0 ~ 8.0 seconds.
        """
        char_count = len(response_text)

        # Base "reading time" (1~2s)
        reading_time = random.uniform(1.0, 2.0)

        # "Typing time" based on char count (~300 chars/min)
        typing_time = min(char_count / 300 * 60, 5.0)

        # Random jitter (±0.5s)
        jitter = random.uniform(-0.5, 0.5)

        total = reading_time + typing_time + jitter
        return max(1.0, min(total, 8.0))
