import os
from dotenv import load_dotenv
load_dotenv(override=True)

import yandex_ai_studio_sdk as sdk_module

_sdk_instance = None


def _get_sdk():
    global _sdk_instance
    if _sdk_instance is None:
        from config import API_KEY, FOLDER_ID
        _sdk_instance = sdk_module.AIStudio(
            auth=API_KEY,
            folder_id=FOLDER_ID,
            endpoint=os.environ.get("YANDEX_ENDPOINT", "api.cloud.yandex.net:443"),
        )
    return _sdk_instance


class SpeechKitError(Exception):
    pass


def tts_synthesize(text: str, voice: str = "jane", lang: str = "ru-RU", fmt: str = "WAV") -> bytes:
    """Synthesize text to audio bytes using the official SDK."""
    try:
        sdk = _get_sdk()
        audio_format = sdk_module.AIStudio.speechkit.AudioFormat  # noqa — accessed below
        tts = sdk.speechkit.tts(
            audio_format="WAV" if fmt == "WAV" else fmt.lower(),
            voice=voice,
        )
        result = tts.run(text)
        return result.audio_bytes
    except Exception as e:
        raise SpeechKitError(str(e)) from e


def stt_recognize(audio: bytes, lang: str = "ru-RU") -> str:
    """Recognize speech from raw audio bytes, return plain text."""
    try:
        sdk = _get_sdk()
        stt = sdk.speechkit.stt(
            audio_format="WAV",
            language_codes=lang,
            text_normalization=True,
        )
        result = stt.run(audio)
        return result.text
    except Exception as e:
        raise SpeechKitError(str(e)) from e


def stt_transcribe(audio: bytes, lang: str = "ru-RU") -> list:
    """Transcribe audio with word timestamps and speaker diarization (deferred/async mode).

    Returns list of channel dicts:
      {
        "speaker": str,           # channel tag, e.g. "1", "2"
        "text": str,
        "utterances": [
          {
            "text": str,
            "start_ms": int,
            "end_ms": int,
          }
        ]
      }
    """
    try:
        sdk = _get_sdk()
        stt = sdk.speechkit.stt(
            audio_format="WAV",
            language_codes=lang,
            text_normalization=True,
            speaker_labeling=True,
        )
        operation = stt.run_deferred(audio)
        result = operation.wait()

        channels = []
        for channel in result:
            utterances = []
            for utt in channel.utterances:
                utterances.append({
                    "text": utt.text,
                    "start_ms": utt.timespan.start_time_ms,
                    "end_ms": utt.timespan.end_time_ms,
                })
            channels.append({
                "speaker": channel.tag,
                "text": channel.text,
                "utterances": utterances,
            })
        return channels
    except Exception as e:
        raise SpeechKitError(str(e)) from e
