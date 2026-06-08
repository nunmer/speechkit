#!/usr/bin/env python3
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main():
    parser = argparse.ArgumentParser(description="Aggregate MOS scores from filled rating sheet.")
    parser.add_argument("--rating-sheet", default="out/tts_rating_sheet.csv")
    parser.add_argument("--out", default="out/tts_mos_summary.csv")
    args = parser.parse_args()

    with open(args.rating_sheet, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    from eval.report import mos_summary, write_csv, print_table

    summary = mos_summary(rows)
    write_csv(summary, args.out)
    print_table(summary)
    print(f"MOS summary written to {args.out}")


if __name__ == "__main__":
    main()
