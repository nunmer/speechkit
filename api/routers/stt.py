from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from config import API_KEY, FOLDER_ID
from speechkit.client import SpeechKitClient, SpeechKitError
from speechkit.audio import load_wav, validate

import io
import wave

router = APIRouter()

client = SpeechKitClient(api_key=API_KEY, folder_id=FOLDER_ID)


def _parse_wav(data: bytes) -> tuple:
    buf = io.BytesIO(data)
    with wave.open(buf, "rb") as wf:
        params = wf.getparams()
        pcm = wf.readframes(params.nframes)
        duration = params.nframes / params.framerate
    return pcm, params.framerate, params.nchannels, params.sampwidth, duration


@router.post("/recognize")
async def recognize(
    file: UploadFile = File(..., description="WAV audio file"),
    lang: str = Form("ru-RU", description="Language code, e.g. ru-RU or kk-KZ"),
):
    if not file.filename.lower().endswith(".wav"):
        raise HTTPException(status_code=400, detail="Only WAV files are supported")

    data = await file.read()
    try:
        pcm, rate, channels, sampwidth, duration = _parse_wav(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid WAV file: {e}")

    warnings = validate(pcm, rate, channels, sampwidth, duration)

    try:
        text = client.stt_recognize(pcm, rate, lang=lang)
    except SpeechKitError as e:
        raise HTTPException(status_code=502, detail=str(e))

    return {
        "text": text,
        "lang": lang,
        "duration_seconds": round(duration, 2),
        "warnings": warnings,
    }
