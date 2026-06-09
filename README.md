# speech-service

REST API + CLI wrapper around Yandex SpeechKit TTS and STT (KZ region).

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in your credentials
```

## Credentials (`.env`)

| Variable | Description |
|---|---|
| `API_KEY` | SpeechKit API key |
| `FOLDER_ID` | Yandex Cloud folder ID |
| `SSL_VERIFY` | Set to `false` on corporate networks |
| `HTTPS_PROXY` | Proxy URL, e.g. `http://headproxy03:8080` |

## Run the API

```bash
uvicorn api.main:app --reload --port 8000
```

Interactive docs: http://localhost:8000/docs

## Endpoints

### TTS

| Method | Path | Description |
|---|---|---|
| `GET` | `/tts/voices` | List available voices |
| `POST` | `/tts/synthesize` | Synthesize text → audio |

**POST /tts/synthesize** — returns raw audio bytes (WAV/MP3/OGG_OPUS)

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
| `POST` | `/stt/recognize` | Transcribe WAV → text |

**POST /stt/recognize** — multipart form upload

```bash
curl -X POST http://localhost:8000/stt/recognize \
  -F "file=@audio.wav" \
  -F "lang=ru-RU"
```

Response:
```json
{
  "text": "распознанный текст",
  "lang": "ru-RU",
  "duration_seconds": 4.2,
  "warnings": []
}
```

### Health

```
GET /health  →  {"status": "ok"}
```

## CLI (quick tests without the server)

```bash
# TTS
python scripts/speak.py "Сәлем!" --voice madi --out out/madi.wav --proxy http://headproxy03:8080

# STT
python scripts/transcribe.py audio.wav --lang kk-KZ --proxy http://headproxy03:8080
```

## Structure

```
api/
  main.py          ← FastAPI app
  routers/
    tts.py         ← /tts endpoints
    stt.py         ← /stt endpoints
speechkit/
  client.py        ← SpeechKitClient (tts_synthesize, stt_recognize)
  audio.py         ← WAV load + validation helpers
config.py          ← credentials + API URLs from .env
scripts/
  speak.py         ← TTS CLI
  transcribe.py    ← STT CLI
```
