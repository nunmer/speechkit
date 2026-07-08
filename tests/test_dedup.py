from app.services import dedup


def test_stt_hash_is_stable():
    a = dedup.stt_hash("recognize", "yandex", "ru-RU", b"audio-bytes")
    b = dedup.stt_hash("recognize", "yandex", "ru-RU", b"audio-bytes")
    assert a == b
    assert len(a) == 64


def test_stt_hash_varies_by_input():
    base = dedup.stt_hash("recognize", "yandex", "ru-RU", b"audio")
    assert base != dedup.stt_hash("transcribe", "yandex", "ru-RU", b"audio")
    assert base != dedup.stt_hash("recognize", "yandex", "kk-KZ", b"audio")
    assert base != dedup.stt_hash("recognize", "yandex", "ru-RU", b"other")


def test_tts_hash_varies_by_voice_and_format():
    base = dedup.tts_hash("hello", "jane", "ru-RU", "WAV")
    assert base == dedup.tts_hash("hello", "jane", "ru-RU", "WAV")
    assert base != dedup.tts_hash("hello", "madi", "ru-RU", "WAV")
    assert base != dedup.tts_hash("hello", "jane", "ru-RU", "MP3")
