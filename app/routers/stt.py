import logging

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.engines import create_stt_engine
from app.engines.base import EngineError
from app.utils.audio import to_pcm_wav, wav_duration, ms_to_timestamp
from app.core.metrics import ENGINE_ERRORS, AUDIO_DURATION

logger = logging.getLogger("speech_service.stt")

router = APIRouter()


@router.post("/recognize")
async def recognize(
    file: UploadFile = File(..., description="Audio file"),
    lang: str = Form("ru-RU", description="Language code, e.g. ru-RU or kk-KZ"),
    engine: str = Form(default=None, description="STT engine (default from config)"),
):
    data = await file.read()
    try:
        data = to_pcm_wav(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not decode audio: {e}")

    try:
        stt = create_stt_engine(engine)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    duration = wav_duration(data)
    try:
        text = stt.recognize(data, lang=lang)
    except EngineError as e:
        ENGINE_ERRORS.labels(engine=stt.engine_type.value, operation="recognize").inc()
        logger.error("STT recognize error [%s]: %s", stt.engine_type.value, e)
        raise HTTPException(status_code=502, detail=str(e))

    AUDIO_DURATION.labels(operation="recognize", engine=stt.engine_type.value).observe(duration)
    return {
        "text": text,
        "lang": lang,
        "engine": stt.engine_type.value,
        "duration_seconds": round(duration, 2),
    }


@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(..., description="Audio file"),
    lang: str = Form("ru-RU", description="Language code, e.g. ru-RU or kk-KZ"),
    engine: str = Form(default=None, description="STT engine (default from config)"),
):
    data = await file.read()
    try:
        data = to_pcm_wav(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not decode audio: {e}")

    try:
        stt = create_stt_engine(engine)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    duration = wav_duration(data)
    try:
        channels = stt.transcribe(data, lang=lang)
    except EngineError as e:
        ENGINE_ERRORS.labels(engine=stt.engine_type.value, operation="transcribe").inc()
        logger.error("STT transcribe error [%s]: %s", stt.engine_type.value, e)
        raise HTTPException(status_code=502, detail=str(e))

    for ch in channels:
        for utt in ch["utterances"]:
            utt["start"] = ms_to_timestamp(utt["start_ms"])
            utt["end"] = ms_to_timestamp(utt["end_ms"])

    AUDIO_DURATION.labels(operation="transcribe", engine=stt.engine_type.value).observe(duration)
    return {
        "lang": lang,
        "engine": stt.engine_type.value,
        "duration_seconds": round(duration, 2),
        "speakers": channels,
    }
