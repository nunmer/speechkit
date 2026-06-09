from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from speechkit.client import SpeechKitError, stt_recognize, stt_transcribe

import io
import wave
import numpy as np
import soundfile as sf

router = APIRouter()

TARGET_RATE = 16000


def _to_pcm_wav(data: bytes) -> bytes:
    """Normalize any audio soundfile can read to mono 16-bit 16kHz PCM WAV."""
    samples, rate = sf.read(io.BytesIO(data), dtype="int16", always_2d=True)

    if samples.shape[1] > 1:
        samples = samples.mean(axis=1).astype(np.int16)
    else:
        samples = samples[:, 0]

    if rate != TARGET_RATE:
        ratio = TARGET_RATE / rate
        new_len = int(len(samples) * ratio)
        indices = (np.arange(new_len) / ratio).astype(np.float64)
        idx0 = indices.astype(int)
        idx1 = np.clip(idx0 + 1, 0, len(samples) - 1)
        frac = indices - idx0
        samples = (samples[idx0] * (1 - frac) + samples[idx1] * frac).astype(np.int16)

    out = io.BytesIO()
    with wave.open(out, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(TARGET_RATE)
        wf.writeframes(samples.tobytes())
    return out.getvalue()


def _duration(wav_bytes: bytes) -> float:
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        return wf.getnframes() / wf.getframerate()


def _ms_to_ts(ms: int) -> str:
    s, ms = divmod(ms, 1000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"


@router.post("/recognize")
async def recognize(
    file: UploadFile = File(..., description="Audio file"),
    lang: str = Form("ru-RU", description="Language code, e.g. ru-RU or kk-KZ"),
):
    data = await file.read()
    try:
        data = _to_pcm_wav(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not decode audio: {e}")

    try:
        text = stt_recognize(data, lang=lang)
    except SpeechKitError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {
        "text": text,
        "lang": lang,
        "duration_seconds": round(_duration(data), 2),
    }


@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(..., description="Audio file"),
    lang: str = Form("ru-RU", description="Language code, e.g. ru-RU or kk-KZ"),
):
    data = await file.read()
    try:
        data = _to_pcm_wav(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not decode audio: {e}")

    try:
        channels = stt_transcribe(data, lang=lang)
    except SpeechKitError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Add human-readable timestamps to utterances
    for ch in channels:
        for utt in ch["utterances"]:
            utt["start"] = _ms_to_ts(utt["start_ms"])
            utt["end"] = _ms_to_ts(utt["end_ms"])

    return {
        "lang": lang,
        "duration_seconds": round(_duration(data), 2),
        "speakers": channels,
    }
