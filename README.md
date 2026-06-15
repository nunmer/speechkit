# speech-service

Multi-engine speech service — REST API + CLI for TTS and STT.

Supports pluggable engines via an abstract base class. Currently implemented:
- **Yandex SpeechKit** (REST API v3, Kazakhstan region)

Adding a new engine (e.g. a local Whisper model, Google Cloud Speech, etc.) requires
implementing `STTEngine` and/or `TTSEngine` from `app/engines/base.py` and adding a
branch to the factory.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in your credentials
```

## Configuration (`.env`)

| Variable | Description |
|---|---|
| `DEFAULT_STT_ENGINE` | Default STT engine (`yandex`) |
| `DEFAULT_TTS_ENGINE` | Default TTS engine (`yandex`) |
| `YANDEX_API_KEY` | SpeechKit API key |
| `YANDEX_FOLDER_ID` | Yandex Cloud folder ID |
| `YANDEX_SSL_VERIFY` | Set to `false` for corporate TLS inspection |
| `YANDEX_HTTPS_PROXY` | Proxy URL, e.g. `http://headproxy03:8080` |
| `YANDEX_TIMEOUT` | Per-request timeout in seconds (default `120`) |

## Run the API

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs

## Endpoints

All endpoints accept an optional `engine` query/form parameter to override
the default engine at request time.

### TTS

| Method | Path | Description |
|---|---|---|
| `GET` | `/tts/voices?engine=yandex` | List available voices |
| `POST` | `/tts/synthesize?engine=yandex` | Synthesize text → audio |

**POST /tts/synthesize**

```json
{
  "text": "Сәлем, қалайсыз?",
  "voice": "madi",
  "lang": "ru-RU",
  "format": "WAV"
}
```

### STT

| Method | Path | Description |
|---|---|---|
| `POST` | `/stt/recognize` | Transcribe audio → text |
| `POST` | `/stt/transcribe` | Transcribe with timestamps + speaker diarization |

Both accept any audio format `soundfile` can read; it is normalized to mono 16 kHz PCM
before processing.

```bash
curl -X POST http://localhost:8000/stt/recognize \
  -F "file=@audio.wav" \
  -F "lang=kk-KZ" \
  -F "engine=yandex"
```

### Health

```
GET /health  →  {"status": "ok"}
```

## CLI

```bash
# TTS
python scripts/speak.py "Сәлем!" --voice madi --engine yandex

# STT
python scripts/transcribe.py audio.wav --lang kk-KZ --engine yandex

# STT with speaker diarization
python scripts/transcribe.py call.wav --speakers
```

## Structure

```
app/
  main.py              ← FastAPI application
  core/
    config.py          ← Pydantic Settings (env-driven)
  engines/
    base.py            ← ABC: STTEngine, TTSEngine
    factory.py         ← create_stt_engine(), create_tts_engine()
    yandex/
      client.py        ← HTTP transport for SpeechKit REST v3
      tts.py           ← YandexTTSEngine
      stt.py           ← YandexSTTEngine
  routers/
    tts.py             ← /tts endpoints
    stt.py             ← /stt endpoints
  utils/
    audio.py           ← Audio normalization (→ mono 16kHz PCM WAV)
scripts/
  speak.py             ← TTS CLI
  transcribe.py        ← STT CLI
```

## Adding a New Engine

1. Add a value to `STTEngineType` / `TTSEngineType` in `app/engines/base.py`
2. Create `app/engines/<name>/stt.py` (and/or `tts.py`) implementing the ABC
3. Add the engine's config variables to `app/core/config.py`
4. Add a branch in `app/engines/factory.py`
