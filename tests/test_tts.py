from unittest.mock import patch


def test_list_voices(client):
    r = client.get("/tts/voices")
    assert r.status_code == 200
    data = r.json()
    assert "voices" in data
    assert "engine" in data
    assert len(data["voices"]) > 0


def test_synthesize_empty_text(client):
    r = client.post("/tts/synthesize", json={"text": "   "})
    assert r.status_code == 400


def test_synthesize_invalid_engine(client):
    r = client.get("/tts/voices?engine=nonexistent")
    assert r.status_code == 400
    assert "Unknown" in r.json()["detail"]


def test_synthesize_returns_audio(client, sample_wav):
    fake_audio = b"RIFF" + b"\x00" * 36  # minimal fake WAV
    with patch("app.engines.yandex.tts.YandexTTSEngine.synthesize", return_value=fake_audio):
        r = client.post("/tts/synthesize", json={"text": "hello", "voice": "jane", "format": "WAV"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/wav"
    assert r.content == fake_audio


def test_resolve_voice_corrects_russian_voice_on_kazakh():
    """kk-KZ must never be spoken by a Russian voice — fall back to madi."""
    from app.engines.yandex.tts import YandexTTSEngine

    resolve = YandexTTSEngine._resolve_voice
    assert resolve("jane", "kk-KZ") == "amira"   # russian voice → kazakh default
    assert resolve("madi", "kk-KZ") == "madi"    # kazakh voice kept as-is
    assert resolve("amira", "ru-RU") == "marina"  # kazakh voice → russian default
    assert resolve("marina", "ru-RU") == "marina"  # russian voice kept for russian
    assert resolve("john", "en-US") == "john"    # no dedicated en voice → passthrough
