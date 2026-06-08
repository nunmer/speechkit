# SpeechKit Beta Eval

Offline/cloud evaluation harness for Yandex SpeechKit STT and TTS. Answers one question: **does SpeechKit perform well enough on our audio?**

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# fill in your credentials in .env
```

## Credentials (`.env`)

| Variable | Description |
|---|---|
| `KEY_ID` | SpeechKit Key ID |
| `API_KEY` | SpeechKit API key secret |
| `FOLDER_ID` | Yandex Cloud folder ID |
| `SSL_VERIFY` | Set to `false` on corporate networks with proxy |

## Quick manual TTS test

Synthesize any text and hear it immediately — the WAV opens in your default player:

```bash
python scripts/speak.py "Привет, как дела?"
python scripts/speak.py "Добрый день" --voice madi
python scripts/speak.py "Тест голоса" --voice amira --out out/test.wav
```

Available KZ-region voices: `jane`, `madi`, `amira`, `saule`, `zhanar`

```bash
# List all voices
python scripts/speak.py --list-voices
```

## STT evaluation

```bash
# Dry run — no credentials needed, mocks API responses
python scripts/run_stt.py --dry-run

# Real run
python scripts/run_stt.py --manifest data/stt_manifest.csv --audio-dir data/audio --out out
```

Outputs:
- `out/stt_results.csv` — per-file WER/CER/RTF
- `out/stt_summary.csv` — mean metrics per condition + OVERALL

## TTS batch synthesis

```bash
# Dry run
python scripts/run_tts.py --dry-run

# Real run
python scripts/run_tts.py --texts data/tts_texts.csv --voice jane --out out
```

Outputs:
- `out/tts_out/<id>.wav` — synthesized audio files
- `out/tts_rating_sheet.csv` — blank sheet for human raters (fill in scores 1–5)
- `out/tts_log.csv` — latency + status per row

## MOS aggregation (after human rating)

Fill in `naturalness_1_5` and `intelligibility_1_5` in `out/tts_rating_sheet.csv`, then:

```bash
python scripts/score_mos.py --rating-sheet out/tts_rating_sheet.csv --out out/tts_mos_summary.csv
```

## Audio preparation

Convert any audio files to the required format (mono 16-bit WAV):

```bash
bash scripts/prep_audio.sh input_audio/ data/audio/
```

## Manifest format (`data/stt_manifest.csv`)

| Column | Description |
|---|---|
| `filename` | WAV filename relative to `--audio-dir` |
| `reference` | Ground-truth transcript |
| `lang` | Language code (`ru-RU`, `kk-KZ`) |
| `condition` | Label for grouping (e.g. `russian_clean`, `kazakh_noisy`) |

## TTS texts format (`data/tts_texts.csv`)

| Column | Description |
|---|---|
| `id` | Unique identifier |
| `text` | Text to synthesize |
| `lang` | Language code (`ru-RU`; `kk-KZ` is logged as skip — unsupported) |
| `category` | Label for MOS grouping |

## Tests

```bash
# Offline unit tests (no credentials needed)
pytest tests/test_metrics.py tests/test_audio.py -v

# Integration tests (requires .env with real credentials)
pytest tests/test_integration.py -v
```

## Output interpretation

- **WER** (Word Error Rate): lower is better; 0.0 = perfect, 1.0 = completely wrong
- **CER** (Character Error Rate): more granular than WER; useful for Kazakh
- **RTF** (Real-Time Factor): processing_time / audio_duration; <1.0 = faster than real-time
- **MOS** (Mean Opinion Score): 1–5 from human raters; ≥4.0 is generally acceptable

Results break down by `condition` so the Russian vs Kazakh gap is visible.

## Caveats

1. **Per-condition results are the product.** A blended number hides the Russian/Kazakh gap.
2. **Kazakh TTS is unsupported.** `kk-KZ` rows are logged as skips, never abort the batch.
3. **Number normalization is off by default.** "5000" vs "пять тысяч" scores as an error. Enable with `numbers_to_words=True` in `normalize()` — apply to both ref and hyp consistently.
4. **No secrets in code.** All credentials via `.env`; `data/audio/` and `out/` are gitignored.
