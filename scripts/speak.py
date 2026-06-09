#!/usr/bin/env python3
"""Synthesize text to WAV using Yandex SpeechKit TTS.

Usage:
  python scripts/speak.py "Сәлем, қалайсыз?"
  python scripts/speak.py "Привет" --voice madi --out out/madi.wav
  python scripts/speak.py "Текст" --proxy http://headproxy03:8080
  python scripts/speak.py --list-voices
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from dotenv import load_dotenv
load_dotenv()

VOICES = ["jane", "madi", "amira", "saule", "zhanar"]


def main():
    parser = argparse.ArgumentParser(description="TTS: text → WAV")
    parser.add_argument("text", nargs="?", help="Text to synthesize")
    parser.add_argument("--voice", default="jane", choices=VOICES)
    parser.add_argument("--lang", default="ru-RU")
    parser.add_argument("--out", default="out/speak.wav")
    parser.add_argument("--proxy", help="HTTP/HTTPS proxy URL (overrides env)")
    parser.add_argument("--list-voices", action="store_true")
    args = parser.parse_args()

    if args.list_voices:
        for v in VOICES:
            print(v)
        return

    if not args.text:
        parser.print_help()
        sys.exit(1)

    if args.proxy:
        os.environ["HTTPS_PROXY"] = args.proxy
        os.environ["HTTP_PROXY"] = args.proxy

    from config import API_KEY, FOLDER_ID
    from speechkit.client import SpeechKitClient

    client = SpeechKitClient(api_key=API_KEY, folder_id=FOLDER_ID)
    audio = client.tts_synthesize(args.text, lang=args.lang, voice=args.voice)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(audio)
    print(f"saved {len(audio)} bytes -> {out.resolve()}")

    if sys.platform == "win32":
        os.startfile(str(out.resolve()))
    elif sys.platform == "darwin":
        os.system(f"afplay '{out}'")
    else:
        os.system(f"aplay '{out}' 2>/dev/null || paplay '{out}' 2>/dev/null")


if __name__ == "__main__":
    main()
