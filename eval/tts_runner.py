import csv
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# Voices known to not support Kazakh synthesis
_UNSUPPORTED_LANGS = {"kk-KZ"}


def run_batch(texts_path, out_dir, client, voice: str = "alena", fmt: str = "mp3",
              dry_run: bool = False) -> tuple[list[dict], str]:
    out_dir = Path(out_dir)
    audio_out = out_dir / "tts_out"
    audio_out.mkdir(parents=True, exist_ok=True)

    log_rows = []
    rating_rows = []

    with open(texts_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        uid = row.get("id", "").strip()
        text = row.get("text", "").strip()
        lang = row.get("lang", "ru-RU").strip()
        category = row.get("category", "unknown").strip()

        log_entry = {
            "id": uid,
            "lang": lang,
            "category": category,
            "char_count": len(text),
            "latency_s": "",
            "status": "ok",
            "note": "",
        }

        if lang in _UNSUPPORTED_LANGS:
            log_entry["status"] = "skip"
            log_entry["note"] = f"TTS not supported for lang={lang}"
            logger.warning("Skipping TTS for %s: lang=%s not supported", uid, lang)
            log_rows.append(log_entry)
            continue

        audio_path = audio_out / f"{uid}.{fmt}"

        if dry_run:
            audio_path.write_bytes(b"")  # silent placeholder
            log_entry["latency_s"] = 0.0
        else:
            t0 = time.monotonic()
            try:
                audio_bytes = client.tts_synthesize(text, lang=lang, voice=voice, fmt=fmt)
            except Exception as exc:
                log_entry["status"] = "error"
                log_entry["note"] = str(exc)
                logger.error("TTS failed for %s: %s", uid, exc)
                log_rows.append(log_entry)
                continue
            log_entry["latency_s"] = round(time.monotonic() - t0, 3)
            audio_path.write_bytes(audio_bytes)

        log_rows.append(log_entry)
        rating_rows.append({
            "id": uid,
            "lang": lang,
            "category": category,
            "audio_file": str(audio_path),
            "naturalness_1_5": "",
            "intelligibility_1_5": "",
            "notes": "",
        })

    rating_sheet_path = out_dir / "tts_rating_sheet.csv"
    if rating_rows:
        with open(rating_sheet_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rating_rows[0].keys()))
            writer.writeheader()
            writer.writerows(rating_rows)

    log_path = out_dir / "tts_log.csv"
    if log_rows:
        with open(log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(log_rows[0].keys()))
            writer.writeheader()
            writer.writerows(log_rows)

    return log_rows, str(rating_sheet_path)
