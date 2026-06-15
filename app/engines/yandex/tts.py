import base64

from app.engines.base import TTSEngine, TTSEngineType, EngineError
from app.engines.yandex.client import YandexAPIError, post, iter_json_objects
from app.core.config import settings


VOICES = ["jane", "madi", "amira", "saule", "zhanar"]


class YandexTTSEngine(TTSEngine):
    @property
    def engine_type(self) -> TTSEngineType:
        return TTSEngineType.YANDEX

    def list_voices(self) -> list[str]:
        return VOICES

    def synthesize(self, text: str, voice: str = "jane", lang: str = "ru-RU",
                   fmt: str = "WAV") -> bytes:
        body = {
            "text": text,
            "outputAudioSpec": {"containerAudio": {"containerAudioType": fmt}},
            "hints": [{"voice": voice}],
        }
        try:
            resp = post(settings.YANDEX_TTS_URL, body)
        except YandexAPIError as e:
            raise EngineError(str(e)) from e

        audio = bytearray()
        for obj in iter_json_objects(resp.text):
            chunk = (obj.get("result") or obj).get("audioChunk", {})
            data = chunk.get("data", "")
            if data:
                audio.extend(base64.b64decode(data))
        if not audio:
            raise EngineError(f"TTS returned no audio: {resp.text[:300]}")
        return bytes(audio)
