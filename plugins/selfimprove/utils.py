from typing import Optional


def word_count(text: Optional[str] = None) -> int:
    if text is None:
        return 0
    try:
        return len(text.split())
    except Exception:
        return 0


def char_count(text: Optional[str] = None) -> int:
    if text is None:
        return 0
    try:
        return len(text)
    except Exception:
        return 0


def summarize_text(text: Optional[str] = None, max_words: int = 20) -> str:
    if text is None:
        return ""
    try:
        words = text.split()
        return ' '.join(words[:max_words])
    except Exception:
        return ""