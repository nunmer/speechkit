#!/usr/bin/env python3
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    parser = argparse.ArgumentParser(description="Run STT evaluation batch.")
    parser.add_argument("--manifest", default="data/stt_manifest.csv")
    parser.add_argument("--audio-dir", default="data/audio")
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

    from eval.stt_runner import run_batch
    from eval.report import aggregate, write_csv, print_table

    records = run_batch(args.manifest, args.audio_dir, client, dry_run=args.dry_run)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    results_path = out / "stt_results.csv"
    if records:
        with open(results_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)
        print(f"Results written to {results_path}")

    summary = aggregate(records)
    write_csv(summary, str(out / "stt_summary.csv"))
    print_table(summary)
    print(f"Summary written to {out / 'stt_summary.csv'}")


if __name__ == "__main__":
    main()
