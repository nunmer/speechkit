import re
import unicodedata

import jiwer


def normalize(text: str, numbers_to_words: bool = False) -> str:
    text = text.lower()
    # Unicode normalize (NFC) for consistent Cyrillic/Kazakh handling
    text = unicodedata.normalize("NFC", text)
    if numbers_to_words:
        # Basic digit->word substitution for Russian; extend as needed
        _RU_ONES = ["ноль", "один", "два", "три", "четыре",
                    "пять", "шесть", "семь", "восемь", "девять"]
        text = re.sub(r"\d", lambda m: _RU_ONES[int(m.group())], text)
    # Strip punctuation (keep letters, digits, spaces)
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def wer(ref: str, hyp: str) -> float:
    ref_n = normalize(ref)
    hyp_n = normalize(hyp)
    if not ref_n:
        return 0.0 if not hyp_n else 1.0
    return jiwer.wer(ref_n, hyp_n)


def cer(ref: str, hyp: str) -> float:
    ref_n = normalize(ref)
    hyp_n = normalize(hyp)
    if not ref_n:
        return 0.0 if not hyp_n else 1.0
    return jiwer.cer(ref_n, hyp_n)


def rtf(processing_seconds: float, audio_duration: float) -> float:
    if audio_duration <= 0:
        return float("nan")
    return processing_seconds / audio_duration
