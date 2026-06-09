#!/usr/bin/env python3
"""Transcribe a WAV file using Yandex SpeechKit STT.

Usage:
  python scripts/transcribe.py audio.wav
  python scripts/transcribe.py audio.wav --lang kk-KZ
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
    parser.add_argument("file", help="Path to WAV file")
    parser.add_argument("--lang", default="ru-RU")
    parser.add_argument("--proxy", help="HTTP/HTTPS proxy URL (overrides env)")
    args = parser.parse_args()

    if args.proxy:
        os.environ["HTTPS_PROXY"] = args.proxy
        os.environ["HTTP_PROXY"] = args.proxy

    from config import API_KEY, FOLDER_ID
    from speechkit.client import SpeechKitClient
    from speechkit.audio import load_wav, validate

    pcm, rate, channels, sampwidth, duration = load_wav(args.file)
    warnings = validate(pcm, rate, channels, sampwidth, duration)
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)

    client = SpeechKitClient(api_key=API_KEY, folder_id=FOLDER_ID)
    text = client.stt_recognize(pcm, rate, lang=args.lang)
    print(text)


if __name__ == "__main__":
    main()
