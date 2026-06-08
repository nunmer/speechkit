#!/usr/bin/env python3
"""Quick manual test: synthesize text and save/play the result.

Usage:
  python scripts/speak.py "Привет мир"
  python scripts/speak.py "Привет мир" --voice madi
  python scripts/speak.py "Привет мир" --voice jane --lang ru-RU --out out/test.wav
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
    parser = argparse.ArgumentParser(description="TTS quick test")
    parser.add_argument("text", nargs="?", help="Text to synthesize")
    parser.add_argument("--voice", default="jane", choices=VOICES)
    parser.add_argument("--lang", default="ru-RU")
    parser.add_argument("--out", default="out/speak_test.wav")
    parser.add_argument("--list-voices", action="store_true", help="List available voices")
    args = parser.parse_args()

    if args.list_voices:
        print("Available KZ-region voices:")
        for v in VOICES:
            print(f"  {v}")
        return

    if not args.text:
        parser.print_help()
        sys.exit(1)

    from config import API_KEY, FOLDER_ID
    from speechkit.client import SpeechKitClient

    client = SpeechKitClient(api_key=API_KEY, folder_id=FOLDER_ID)

    print(f"Synthesizing: '{args.text.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)}'  voice={args.voice}  lang={args.lang}")
    audio = client.tts_synthesize(args.text, lang=args.lang, voice=args.voice, fmt="WAV")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(audio)
    print(f"Saved {len(audio)} bytes -> {out_path.resolve()}")

    # Try to play it
    if sys.platform == "win32":
        os.startfile(str(out_path.resolve()))
    elif sys.platform == "darwin":
        os.system(f"afplay '{out_path}'")
    else:
        os.system(f"aplay '{out_path}' 2>/dev/null || paplay '{out_path}' 2>/dev/null")

if __name__ == "__main__":
    main()
