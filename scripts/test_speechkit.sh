#!/usr/bin/env bash
# Тест Yandex SpeechKit v3: TTS (синтез) + STT (распознавание).
# Берёт креды из .env: API_KEY (секрет API-ключа), FOLDER_ID (каталог).
set -euo pipefail

cd "$(dirname "$0")"
set -a; . ./.env; set +a

: "${API_KEY:?нет API_KEY в .env}"
: "${FOLDER_ID:?нет FOLDER_ID в .env}"

# ВАЖНО: казахстанская инсталляция Yandex Cloud — домен *.yandexcloud.kz,
# отдельный IAM. Ключ из RU-региона (*.cloud.yandex.net) тут не работает и наоборот.
VOICE="${VOICE:-jane}"   # KZ-голоса: jane, madi, amira, saule, zhanar (alena недоступна)
AUTH=( -H "Authorization: Api-Key ${API_KEY}" -H "x-folder-id: ${FOLDER_ID}" )
TTS_URL="https://tts.api.yandexcloud.kz/tts/v3/utteranceSynthesis"
STT_URL="https://stt.api.yandexcloud.kz/stt/v3/recognizeFileAsync"

echo "== 1) TTS: синтез WAV =="
# v3 отдаёт stream JSON-чанков с base64 audioChunk.data; склеиваем и декодируем.
curl -sS -X POST "${AUTH[@]}" -H "Content-Type: application/json" \
  -d "{\"text\":\"Привет! Это проверка Yandex SpeechKit.\",
       \"outputAudioSpec\":{\"containerAudio\":{\"containerAudioType\":\"WAV\"}},
       \"hints\":[{\"voice\":\"${VOICE}\"}]}" \
  "$TTS_URL" \
| grep -o '"data":"[^"]*"' | sed 's/"data":"//;s/"//' \
| while read -r b64; do printf '%s' "$b64" | base64 -d; done > out.wav

if [ -s out.wav ]; then
  echo "OK: out.wav ($(wc -c < out.wav) байт)"
else
  echo "FAIL: пустой ответ TTS (скорее всего ключ/права)"; exit 1
fi

echo "== Готово. Синтез работает. =="
echo "STT-проверку добавим, если нужен async-распознаватель (нужен публичный URL аудио)."
