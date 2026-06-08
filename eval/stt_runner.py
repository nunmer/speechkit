import csv
import time
from pathlib import Path

from config import MAX_BYTES, MAX_SECONDS
from speechkit.audio import load_wav, validate
from eval.metrics import wer, cer, rtf


def run_batch(manifest_path, audio_dir, client, dry_run: bool = False) -> list[dict]:
    records = []
    audio_dir = Path(audio_dir)

    with open(manifest_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        filename = row.get("filename", "").strip()
        reference = row.get("reference", "").strip()
        lang = row.get("lang", "ru-RU").strip()
        condition = row.get("condition", "unknown").strip()
        audio_path = audio_dir / filename

        record = {
            "filename": filename,
            "condition": condition,
            "lang": lang,
            "reference": reference,
            "hypothesis": "",
            "wer": "",
            "cer": "",
            "rtf": "",
            "status": "ok",
            "note": "",
        }

        if not audio_path.exists():
            record["status"] = "skip"
            record["note"] = "file not found"
            records.append(record)
            continue

        try:
            pcm, rate, channels, sampwidth, duration = load_wav(audio_path)
        except Exception as exc:
            record["status"] = "error"
            record["note"] = f"load error: {exc}"
            records.append(record)
            continue

        warnings = validate(pcm, rate, channels, sampwidth, duration)
        fatal = [w for w in warnings if "exceeds" in w]
        if fatal:
            record["status"] = "skip"
            record["note"] = "; ".join(fatal)
            records.append(record)
            continue

        if dry_run:
            hypothesis = reference  # perfect mock
            proc_time = 0.1
        else:
            t0 = time.monotonic()
            try:
                hypothesis = client.stt_recognize(pcm, rate, lang)
            except Exception as exc:
                record["status"] = "error"
                record["note"] = str(exc)
                records.append(record)
                continue
            proc_time = time.monotonic() - t0

        record["hypothesis"] = hypothesis
        record["wer"] = round(wer(reference, hypothesis), 4)
        record["cer"] = round(cer(reference, hypothesis), 4)
        record["rtf"] = round(rtf(proc_time, duration), 4)
        if warnings:
            record["note"] = "; ".join(warnings)
        records.append(record)

    return records
