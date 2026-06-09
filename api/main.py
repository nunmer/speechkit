import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import tts, stt

app = FastAPI(title="SpeechKit API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tts.router, prefix="/tts", tags=["TTS"])
app.include_router(stt.router, prefix="/stt", tags=["STT"])


@app.get("/health")
def health():
    return {"status": "ok"}
