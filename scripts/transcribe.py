#!/usr/bin/env python3
"""Transcribe a WAV file using Yandex SpeechKit STT.

Usage:
  python scripts/transcribe.py audio.wav
  python scripts/transcribe.py audio.wav --lang kk-KZ
  python scripts/transcribe.py audio.wav --speakers   # speaker diarization
  python scripts/transcribe.py audio.wav --proxy http://headproxy03:8080
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv()


def main():
    parser = argparse.ArgumentParser(description="STT: WAV → text")
    parser.add_argument("file", help="Path to audio file")
    parser.add_argument("--lang", default="ru-RU")
    parser.add_argument("--speakers", action="store_true", help="Enable speaker diarization")
    parser.add_argument("--proxy", help="HTTP/HTTPS proxy URL (overrides env)")
    args = parser.parse_args()

    if args.proxy:
        os.environ["HTTPS_PROXY"] = args.proxy
        os.environ["HTTP_PROXY"] = args.proxy

    data = Path(args.file).read_bytes()

    from speechkit.client import stt_recognize, stt_transcribe

    if args.speakers:
        channels = stt_transcribe(data, lang=args.lang)
        for ch in channels:
            print(f"\n[Speaker {ch['speaker']}]")
            for utt in ch["utterances"]:
                print(f"  {utt['start_ms']}ms - {utt['end_ms']}ms: {utt['text']}")
    else:
        text = stt_recognize(data, lang=args.lang)
        print(text)


if __name__ == "__main__":
    main()
