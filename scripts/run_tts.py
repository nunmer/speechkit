#!/usr/bin/env python3
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    parser = argparse.ArgumentParser(description="Run TTS synthesis batch.")
    parser.add_argument("--texts", default="data/tts_texts.csv")
    parser.add_argument("--voice", default="alena")
    parser.add_argument("--format", dest="fmt", default="mp3")
    parser.add_argument("--out", default="out")
    parser.add_argument("--dry-run", action="store_true",
                        help="Mock API calls; no credentials required.")
    args = parser.parse_args()

    if args.dry_run:
        client = None
    else:
        from config import API_KEY, FOLDER_ID
        from speechkit.client import SpeechKitClient
        client = SpeechKitClient(api_key=API_KEY, folder_id=FOLDER_ID)

    from eval.tts_runner import run_batch

    log_rows, rating_sheet = run_batch(
        args.texts, args.out, client,
        voice=args.voice, fmt=args.fmt,
        dry_run=args.dry_run,
    )

    ok = sum(1 for r in log_rows if r["status"] == "ok")
    skipped = sum(1 for r in log_rows if r["status"] == "skip")
    errors = sum(1 for r in log_rows if r["status"] == "error")
    print(f"Done: {ok} synthesized, {skipped} skipped, {errors} errors.")
    print(f"Rating sheet: {rating_sheet}")


if __name__ == "__main__":
    main()
