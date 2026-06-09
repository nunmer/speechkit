from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Literal

from speechkit.client import SpeechKitError, tts_synthesize

router = APIRouter()

VOICES = ["jane", "madi", "amira", "saule", "zhanar"]

MIME = {
    "WAV": "audio/wav",
    "MP3": "audio/mpeg",
    "OGG_OPUS": "audio/ogg",
}


class SynthesizeRequest(BaseModel):
    text: str
    voice: Literal["jane", "madi", "amira", "saule", "zhanar"] = "jane"
    lang: str = "ru-RU"
    format: Literal["WAV", "MP3", "OGG_OPUS"] = "WAV"


@router.get("/voices")
def list_voices():
    return {"voices": VOICES}


@router.post("/synthesize")
def synthesize(req: SynthesizeRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    try:
        audio = tts_synthesize(req.text, voice=req.voice, lang=req.lang, fmt=req.format)
    except SpeechKitError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=audio, media_type=MIME[req.format])
