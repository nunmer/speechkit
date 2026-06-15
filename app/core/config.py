from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )

    # App
    APP_ENV: str = "production"
    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True
    WORKERS: int = 4

    # Engine selection
    DEFAULT_STT_ENGINE: str = "yandex"
    DEFAULT_TTS_ENGINE: str = "yandex"

    # Yandex SpeechKit
    YANDEX_API_KEY: str = ""
    YANDEX_FOLDER_ID: str = ""
    YANDEX_STT_URL: str = "https://stt.api.yandexcloud.kz/stt/v3/recognizeFileAsync"
    YANDEX_TTS_URL: str = "https://tts.api.yandexcloud.kz/tts/v3/utteranceSynthesis"
    YANDEX_TIMEOUT: int = 120
    YANDEX_SSL_VERIFY: bool = True
    YANDEX_HTTPS_PROXY: str = ""
    YANDEX_HTTP_PROXY: str = ""


settings = Settings()
