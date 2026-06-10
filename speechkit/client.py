"""Yandex SpeechKit client over the REST API v3 (Kazakhstan region).

Pure HTTPS/REST — no gRPC — so it works through corporate HTTP proxies and
firewalls that block HTTP/2.

IMPORTANT (Kazakh recognition): the language list must be sent inside
``recognitionModel.languageRestriction`` with ``restrictionType=WHITELIST``.
Without WHITELIST the restriction type defaults to UNSPECIFIED, the language
codes are ignored, and Kazakh audio is silently mis-recognized as Russian.
"""
import base64
import io
import json
import os
import time
import wave
from typing import Iterator

import requests

from config import API_KEY, FOLDER_ID, STT_RECOGNIZE_URL, STT_GET_URL, TTS_URL

_TIMEOUT = int(os.environ.get("SPEECHKIT_TIMEOUT", "120"))
_POLL_ATTEMPTS = 30
_POLL_DELAY = 2.0


class SpeechKitError(Exception):
    pass


# ----------------------------------------------------------------- transport

def _headers() -> dict:
    return {
        "Authorization": f"Api-Key {API_KEY}",
        "x-folder-id": FOLDER_ID,
        "Content-Type": "application/json",
    }


def _proxies():
    """Pick up an HTTP(S) proxy from the environment, if configured."""
    proxy = (
        os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy") or ""
    ).strip()
    if proxy and "://" in proxy:
        return {"https": proxy, "http": proxy}
    return None


def _verify() -> bool:
    verify = os.environ.get("SSL_VERIFY", "true").lower() not in ("0", "false", "no")
    if not verify:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return verify


def _post(url: str, body: dict) -> requests.Response:
    try:
        resp = requests.post(
            url, headers=_headers(), data=json.dumps(body),
            timeout=_TIMEOUT, verify=_verify(), proxies=_proxies(),
        )
    except requests.RequestException as e:
        raise SpeechKitError(f"Request to {url} failed: {e}") from e
    if not resp.ok:
        raise SpeechKitError(f"API error {resp.status_code}: {resp.text}")
    return resp


def _iter_json_objects(text: str) -> Iterator[dict]:
    """Yield each JSON object from a streamed response body.

    SpeechKit v3 streams results as a sequence of JSON objects (newline- or
    whitespace-separated); ``raw_decode`` walks them regardless of delimiter.
    """
    decoder = json.JSONDecoder()
    i, n = 0, len(text)
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break
        obj, i = decoder.raw_decode(text, i)
        yield obj


# ----------------------------------------------------------------------- TTS

def tts_synthesize(text: str, voice: str = "jane", lang: str = "ru-RU",
                   fmt: str = "WAV") -> bytes:
    """Synthesize text to audio bytes (v3 utteranceSynthesis).

    ``lang`` is accepted for interface compatibility; the chosen ``voice``
    determines the language (e.g. ``madi``/``amira``/``saule`` are Kazakh).
    """
    body = {
        "text": text,
        "outputAudioSpec": {"containerAudio": {"containerAudioType": fmt}},
        "hints": [{"voice": voice}],
    }
    resp = _post(TTS_URL, body)
    audio = bytearray()
    for obj in _iter_json_objects(resp.text):
        chunk = (obj.get("result") or obj).get("audioChunk", {})
        data = chunk.get("data", "")
        if data:
            audio.extend(base64.b64decode(data))
    if not audio:
        raise SpeechKitError(f"TTS returned no audio: {resp.text[:300]}")
    return bytes(audio)


# ----------------------------------------------------------------------- STT

def _stt_body(audio: bytes, lang: str, speaker_labeling: bool) -> dict:
    model = {
        "audioFormat": {"containerAudio": {"containerAudioType": "WAV"}},
        "textNormalization": {"textNormalization": "TEXT_NORMALIZATION_ENABLED"},
        # WHITELIST is mandatory — see module docstring.
        "languageRestriction": {
            "restrictionType": "WHITELIST",
            "languageCode": [lang],
        },
    }
    body = {"content": base64.b64encode(audio).decode(), "recognitionModel": model}
    if speaker_labeling:
        body["speakerLabeling"] = {"speakerLabeling": "SPEAKER_LABELING_ENABLED"}
    return body


def _submit(audio: bytes, lang: str, speaker_labeling: bool) -> str:
    resp = _post(STT_RECOGNIZE_URL, _stt_body(audio, lang, speaker_labeling))
    op_id = resp.json().get("id")
    if not op_id:
        raise SpeechKitError(f"No operation id in STT response: {resp.text}")
    return op_id


def _poll(operation_id: str) -> str:
    """Fetch the recognition stream, retrying while the operation is pending."""
    params = {"operationId": operation_id}
    for _ in range(_POLL_ATTEMPTS):
        try:
            r = requests.get(
                STT_GET_URL, headers=_headers(), params=params,
                timeout=_TIMEOUT, verify=_verify(), proxies=_proxies(),
            )
        except requests.RequestException as e:
            raise SpeechKitError(f"getRecognition failed: {e}") from e
        if r.status_code == 404:  # result not ready yet
            time.sleep(_POLL_DELAY)
            continue
        if not r.ok:
            raise SpeechKitError(f"getRecognition error {r.status_code}: {r.text}")
        return r.text
    raise SpeechKitError(
        f"STT result not ready after {_POLL_ATTEMPTS} polls for {operation_id}"
    )


def _segment_index(result: dict) -> str:
    return result.get("audioCursors", {}).get("finalIndex", "0")


def _wav_channels(audio: bytes) -> int:
    """Number of channels in a WAV payload (defaults to 1 if unreadable)."""
    try:
        with wave.open(io.BytesIO(audio), "rb") as w:
            return w.getnchannels()
    except (wave.Error, EOFError):
        return 1


def stt_recognize(audio: bytes, lang: str = "ru-RU") -> str:
    """Recognize speech from WAV bytes; return the normalized transcript.

    ``audio`` should be a 16 kHz mono PCM WAV for best accuracy (the API reads
    the sample rate from the WAV header).
    """
    raw = _poll(_submit(audio, lang, speaker_labeling=False))
    normalized: dict[tuple, str] = {}
    fallback: dict[tuple, str] = {}
    order: list[tuple] = []

    for obj in _iter_json_objects(raw):
        result = obj.get("result", {})
        channel = str(result.get("channelTag", "0"))
        if "finalRefinement" in result:
            ref = result["finalRefinement"]
            alts = ref.get("normalizedText", {}).get("alternatives", [])
            if alts and alts[0].get("text"):
                key = (channel, ref.get("finalIndex", _segment_index(result)))
                normalized[key] = alts[0]["text"]
                if key not in order:
                    order.append(key)
        elif "final" in result:
            alts = result["final"].get("alternatives", [])
            if alts and alts[0].get("text"):
                key = (channel, _segment_index(result))
                fallback[key] = alts[0]["text"]
                if key not in order:
                    order.append(key)

    return " ".join(normalized.get(k) or fallback.get(k, "") for k in order).strip()


def stt_transcribe(audio: bytes, lang: str = "ru-RU") -> list:
    """Transcribe with per-utterance timestamps and channel/speaker grouping.

    Returns a list of channel dicts::

        {"speaker": str, "text": str,
         "utterances": [{"text": str, "start_ms": int, "end_ms": int}]}

    For multi-channel audio each channel is treated as a speaker. Speaker
    labeling (in-channel diarization) is enabled only for mono audio, since the
    API rejects it for multi-channel input.
    """
    raw = _poll(_submit(audio, lang, speaker_labeling=_wav_channels(audio) == 1))
    segments: dict[tuple, dict] = {}
    normalized: dict[tuple, str] = {}
    order: list[tuple] = []

    for obj in _iter_json_objects(raw):
        result = obj.get("result", {})
        channel = str(result.get("channelTag", "0"))
        if "final" in result:
            alts = result["final"].get("alternatives", [])
            if not alts:
                continue
            alt = alts[0]
            key = (channel, _segment_index(result))
            segments[key] = {
                "channel": channel,
                "text": alt.get("text", ""),
                "start_ms": int(alt.get("startTimeMs", 0)),
                "end_ms": int(alt.get("endTimeMs", 0)),
            }
            if key not in order:
                order.append(key)
        elif "finalRefinement" in result:
            ref = result["finalRefinement"]
            alts = ref.get("normalizedText", {}).get("alternatives", [])
            if alts:
                normalized[(channel, ref.get("finalIndex", "0"))] = alts[0].get("text", "")

    channels: dict[str, dict] = {}
    for key in order:
        seg = segments[key]
        channel = channels.setdefault(
            seg["channel"], {"speaker": seg["channel"], "text": "", "utterances": []}
        )
        channel["utterances"].append({
            "text": normalized.get(key, seg["text"]),
            "start_ms": seg["start_ms"],
            "end_ms": seg["end_ms"],
        })

    for channel in channels.values():
        channel["text"] = " ".join(u["text"] for u in channel["utterances"]).strip()
    return list(channels.values())
