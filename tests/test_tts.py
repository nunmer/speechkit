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
