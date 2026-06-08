import struct
import sys
import wave
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from speechkit.audio import load_wav, validate


def _write_wav(path, nchannels=1, sampwidth=2, framerate=16000, nframes=None, duration_s=1.0):
    if nframes is None:
        nframes = int(framerate * duration_s)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(nchannels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(b"\x00" * nframes * nchannels * sampwidth)


def test_load_wav_good():
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        path = tmp.name
    _write_wav(path, duration_s=2.0)
    pcm, rate, channels, sampwidth, duration = load_wav(path)
    assert rate == 16000
    assert channels == 1
    assert sampwidth == 2
    assert abs(duration - 2.0) < 0.01
    Path(path).unlink()


def test_validate_good_wav():
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        path = tmp.name
    _write_wav(path, duration_s=5.0)
    pcm, rate, channels, sampwidth, duration = load_wav(path)
    warnings = validate(pcm, rate, channels, sampwidth, duration)
    assert warnings == []
    Path(path).unlink()


def test_validate_non_mono():
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        path = tmp.name
    _write_wav(path, nchannels=2, duration_s=1.0)
    pcm, rate, channels, sampwidth, duration = load_wav(path)
    warnings = validate(pcm, rate, channels, sampwidth, duration)
    assert any("mono" in w for w in warnings)
    Path(path).unlink()


def test_validate_too_long():
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        path = tmp.name
    _write_wav(path, duration_s=35.0)
    pcm, rate, channels, sampwidth, duration = load_wav(path)
    warnings = validate(pcm, rate, channels, sampwidth, duration)
    assert any("duration" in w for w in warnings)
    Path(path).unlink()


def test_validate_too_large():
    from config import MAX_BYTES
    big_pcm = b"\x00" * (MAX_BYTES + 1)
    warnings = validate(big_pcm, 16000, 1, 2, 5.0)
    assert any("size" in w for w in warnings)
