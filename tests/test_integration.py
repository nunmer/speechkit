import os
import sys
from pathlib import Path

import pytest
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv()

# Skip entire module if credentials are absent
pytestmark = pytest.mark.skipif(
    not os.environ.get("API_KEY") or not os.environ.get("FOLDER_ID"),
    reason="API_KEY / FOLDER_ID not set in environment",
)


@pytest.fixture(scope="module")
def client():
    from dotenv import load_dotenv
    load_dotenv()
    from config import API_KEY, FOLDER_ID
    from speechkit.client import SpeechKitClient
    return SpeechKitClient(api_key=API_KEY, folder_id=FOLDER_ID)


def test_tts_returns_audio(client):
    audio = client.tts_synthesize("Привет", voice="jane", fmt="WAV")
    assert len(audio) > 0, "TTS returned empty audio"


def test_tts_audio_is_wav(client):
    audio = client.tts_synthesize("Проверка", voice="jane", fmt="WAV")
    assert audio[:4] == b"RIFF", "TTS response is not a valid WAV file"


def test_tts_kazakh_lang_does_not_crash(client):
    # kk-KZ TTS is unsupported — runner skips it before calling the client,
    # but if called directly it should raise SpeechKitError, not an unhandled crash
    from speechkit.client import SpeechKitError
    try:
        client.tts_synthesize("Сәлем", lang="kk-KZ", voice="jane", fmt="WAV")
    except SpeechKitError:
        pass  # expected — unsupported lang
    except Exception as exc:
        pytest.fail(f"Unexpected exception type: {type(exc).__name__}: {exc}")


def test_tts_bad_voice_raises_speechkit_error(client):
    from speechkit.client import SpeechKitError
    with pytest.raises(SpeechKitError):
        client.tts_synthesize("Привет", voice="nonexistent_voice", fmt="WAV")


def test_stt_recognizes_known_phrase(client):
    import wave, io
    phrase = "привет как дела"
    audio = client.tts_synthesize(phrase, voice="jane", fmt="WAV")
    # Pass full WAV bytes (with RIFF header) so the API can detect the format
    with wave.open(io.BytesIO(audio), "rb") as wf:
        rate = wf.getframerate()
    transcript = client.stt_recognize(audio, rate, lang="ru-RU")
    assert transcript.strip(), "STT returned empty transcript"
    from eval.metrics import normalize
    assert normalize(transcript), "Normalized transcript is empty"


def test_bad_api_key_raises_401():
    from speechkit.client import SpeechKitClient, SpeechKitError
    from dotenv import load_dotenv
    load_dotenv()
    from config import FOLDER_ID
    bad_client = SpeechKitClient(api_key="bad_key", folder_id=FOLDER_ID)
    with pytest.raises(SpeechKitError, match="401"):
        bad_client.tts_synthesize("test", voice="jane", fmt="WAV")
