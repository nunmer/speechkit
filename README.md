# speech-service

Minimal wrapper around Yandex SpeechKit TTS and STT (KZ region).

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

## TTS — synthesize text to WAV

```bash
python scripts/speak.py "Сәлем, қалайсыз?" --voice madi --out out/madi.wav
python scripts/speak.py "Привет" --proxy http://headproxy03:8080
python scripts/speak.py --list-voices
```

Available voices: `jane`, `madi`, `amira`, `saule`, `zhanar`

## STT — transcribe WAV to text

```bash
python scripts/transcribe.py audio.wav
python scripts/transcribe.py audio.wav --lang kk-KZ --proxy http://headproxy03:8080
```

## Structure

```
speechkit/
  client.py   — SpeechKitClient (tts_synthesize, stt_recognize)
  audio.py    — WAV loading + validation helpers
config.py     — credentials + API URLs from .env
scripts/
  speak.py      — TTS CLI
  transcribe.py — STT CLI
```
