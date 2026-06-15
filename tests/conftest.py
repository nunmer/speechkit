import io
import wave

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_wav() -> bytes:
    """1-second 16kHz mono sine-wave WAV."""
    rate = 16000
    t = np.linspace(0, 1.0, rate, dtype=np.float32)
    samples = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()
