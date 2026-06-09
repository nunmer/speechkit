from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import Literal

from config import API_KEY, FOLDER_ID
from speechkit.client import SpeechKitClient, SpeechKitError

router = APIRouter()

VOICES = ["jane", "madi", "amira", "saule", "zhanar"]
FORMATS = ["WAV", "MP3", "OGG_OPUS"]

client = SpeechKitClient(api_key=API_KEY, folder_id=FOLDER_ID)


class SynthesizeRequest(BaseModel):
    text: str
    voice: Literal["jane", "madi", "amira", "saule", "zhanar"] = "jane"
    lang: str = "ru-RU"
    format: Literal["WAV", "MP3", "OGG_OPUS"] = "WAV"


MIME = {
    "WAV": "audio/wav",
    "MP3": "audio/mpeg",
    "OGG_OPUS": "audio/ogg",
}


@router.get("/voices")
def list_voices():
    return {"voices": VOICES}


@router.post("/synthesize")
def synthesize(req: SynthesizeRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    try:
        audio = client.tts_synthesize(
            req.text,
            lang=req.lang,
            voice=req.voice,
            fmt=req.format,
        )
    except SpeechKitError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return Response(content=audio, media_type=MIME[req.format])
