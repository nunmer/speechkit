# speech-service

REST API + CLI wrapper around Yandex SpeechKit TTS and STT (Kazakhstan region).

Backed by the **SpeechKit REST API v3** over plain HTTPS — no gRPC. The
Kazakhstan region only exposes STT/TTS through API v3, and because this client
uses request/response HTTPS (not HTTP/2 streaming) it works through corporate
proxies and firewalls that block gRPC.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in your credentials
```

## Credentials (`.env`)

| Variable | Description |
|---|---|
| `API_KEY` | SpeechKit API key (Kazakhstan region) |
| `FOLDER_ID` | Yandex Cloud folder ID |
| `SSL_VERIFY` | Set to `false` on corporate networks that do TLS inspection |
| `HTTPS_PROXY` | Proxy URL, e.g. `http://headproxy03:8080` |
| `STT_URL` | _(optional)_ override the STT endpoint (defaults to KZ region) |
| `TTS_URL` | _(optional)_ override the TTS endpoint (defaults to KZ region) |
| `SPEECHKIT_TIMEOUT` | _(optional)_ per-request timeout in seconds (default `120`) |

Default endpoints (KZ region):
`https://stt.api.yandexcloud.kz/stt/v3/recognizeFileAsync` and
`https://tts.api.yandexcloud.kz/tts/v3/utteranceSynthesis`. For the Russia region,
override with the `stt.api.cloud.yandex.net` / `tts.api.cloud.yandex.net` hosts.

## Language

Pass the language code per request (`ru-RU`, `kk-KZ`, `en-US`, …). Internally the
code is sent as a `WHITELIST` language restriction — this is **required** for
Kazakh; without it the model silently falls back to Russian and mis-recognizes
Kazakh speech.

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

Voices: `jane`, `madi`, `amira`, `saule`, `zhanar` (the voice determines the
language — `madi`/`amira`/`saule`/`zhanar` are Kazakh).

**POST /tts/synthesize** — returns raw audio bytes (`WAV`/`MP3`/`OGG_OPUS`)

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
| `POST` | `/stt/transcribe` | Transcribe with timestamps + speaker diarization |

Both accept any audio `soundfile` can read; it is normalized to mono 16 kHz PCM
before being sent.

**POST /stt/recognize** — multipart form upload

```bash
curl -X POST http://localhost:8000/stt/recognize \
  -F "file=@audio.wav" \
  -F "lang=kk-KZ"
```

Response:
```json
{
  "text": "распознанный текст",
  "lang": "kk-KZ",
  "duration_seconds": 4.2
}
```

**POST /stt/transcribe** — multipart form upload, returns per-speaker utterances
with timestamps.

```bash
curl -X POST http://localhost:8000/stt/transcribe \
  -F "file=@call.wav" \
  -F "lang=ru-RU"
```

Response:
```json
{
  "lang": "ru-RU",
  "duration_seconds": 70.2,
  "speakers": [
    {
      "speaker": "0",
      "text": "...",
      "utterances": [
        {"text": "...", "start_ms": 0, "end_ms": 2620,
         "start": "00:00:00.000", "end": "00:00:02.620"}
      ]
    }
  ]
}
```

Diarization works two ways automatically:
- **Multi-channel audio** (e.g. a 2-channel call) — each channel is a speaker.
- **Mono audio** — in-channel speaker labeling separates speakers.

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

# STT with speaker diarization
python scripts/transcribe.py call.wav --lang ru-RU --speakers
```

## Structure

```
api/
  main.py          ← FastAPI app
  routers/
    tts.py         ← /tts endpoints
    stt.py         ← /stt endpoints (audio normalization + timestamps)
speechkit/
  client.py        ← REST API v3 client (tts_synthesize, stt_recognize, stt_transcribe)
config.py          ← credentials + REST endpoint URLs from .env
scripts/
  speak.py         ← TTS CLI
  transcribe.py    ← STT CLI
```
