import os
from dotenv import load_dotenv

load_dotenv()

KEY_ID = os.environ.get("KEY_ID")
API_KEY = os.environ.get("API_KEY")
FOLDER_ID = os.environ.get("FOLDER_ID")


def require_credentials():
    """Call this before making API requests. Raises clearly if credentials are absent."""
    if not API_KEY:
        raise EnvironmentError("API_KEY is not set. Add it to your .env file.")
    if not FOLDER_ID:
        raise EnvironmentError("FOLDER_ID is not set. Add it to your .env file.")


STT_URL = "https://stt.api.yandexcloud.kz/stt/v3/recognizeFileAsync"
TTS_URL = "https://tts.api.yandexcloud.kz/tts/v3/utteranceSynthesis"

MAX_BYTES = 1_048_576   # 1 MB
MAX_SECONDS = 30

DEFAULT_VOICE = "jane"   # KZ-available voices: jane, madi, amira, saule, zhanar
DEFAULT_TTS_FORMAT = "WAV"
DEFAULT_STT_LANG = "ru-RU"
