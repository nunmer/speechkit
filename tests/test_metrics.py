import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.metrics import normalize, wer, cer, rtf


def test_normalize_basic():
    assert normalize("Hello, World!") == "hello world"


def test_normalize_collapse_whitespace():
    assert normalize("  foo   bar  ") == "foo bar"


def test_normalize_unicode_nfc():
    # Cyrillic: same string in different normalization forms -> same output
    s = "привет"  # привет NFC
    assert normalize(s) == s


def test_normalize_kazakh():
    kk = "Сәлем, Әлем!"
    result = normalize(kk)
    assert "сәлем" in result
    assert "әлем" in result
    assert "," not in result
    assert "!" not in result


def test_wer_identical():
    assert wer("привет мир", "привет мир") == 0.0


def test_wer_one_substitution_in_five():
    ref = "один два три четыре пять"
    hyp = "один два три четыре шесть"
    assert abs(wer(ref, hyp) - 0.2) < 1e-6


def test_wer_completely_wrong():
    assert wer("один два", "три четыре") == 1.0


def test_cer_identical():
    assert cer("abc", "abc") == 0.0


def test_cer_nonzero():
    assert cer("abc", "axc") > 0.0


def test_rtf_basic():
    assert abs(rtf(1.0, 10.0) - 0.1) < 1e-9


def test_rtf_zero_duration():
    import math
    assert math.isnan(rtf(1.0, 0.0))
