import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("API_KEY")
FOLDER_ID = os.environ.get("FOLDER_ID")

if not API_KEY:
    raise EnvironmentError("API_KEY is not set. Add it to your .env file.")
if not FOLDER_ID:
    raise EnvironmentError("FOLDER_ID is not set. Add it to your .env file.")

# Yandex SpeechKit REST API v3 (Kazakhstan region). Pure HTTPS — no gRPC — so it
# passes through HTTP proxies/firewalls that block HTTP/2. Override via env for
# other regions (e.g. https://stt.api.cloud.yandex.net/... for Russia).
STT_RECOGNIZE_URL = os.environ.get(
    "STT_URL", "https://stt.api.yandexcloud.kz/stt/v3/recognizeFileAsync"
)
STT_GET_URL = STT_RECOGNIZE_URL.replace("recognizeFileAsync", "getRecognition")
TTS_URL = os.environ.get(
    "TTS_URL", "https://tts.api.yandexcloud.kz/tts/v3/utteranceSynthesis"
)
