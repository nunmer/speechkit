#!/usr/bin/env bash
# Convert audio files to mono 16kHz 16-bit WAV, then segment to 30s chunks.
# Usage: bash prep_audio.sh <input_dir> <output_dir>
set -euo pipefail

INPUT_DIR="${1:?Usage: $0 <input_dir> <output_dir>}"
OUTPUT_DIR="${2:?Usage: $0 <input_dir> <output_dir>}"

mkdir -p "$OUTPUT_DIR"

for f in "$INPUT_DIR"/*.{wav,mp3,ogg,flac,m4a} 2>/dev/null; do
    [[ -f "$f" ]] || continue
    stem=$(basename "${f%.*}")
    mono_wav="$OUTPUT_DIR/${stem}_mono.wav"

    echo "Converting $f -> $mono_wav"
    ffmpeg -y -i "$f" -ac 1 -ar 16000 -sample_fmt s16 "$mono_wav"

    duration=$(ffprobe -v error -show_entries format=duration \
        -of default=noprint_wrappers=1:nokey=1 "$mono_wav")
    if (( $(echo "$duration > 30" | bc -l) )); then
        echo "Segmenting $mono_wav (${duration}s) into 30s chunks"
        ffmpeg -y -i "$mono_wav" -f segment -segment_time 30 \
            -ac 1 -ar 16000 -sample_fmt s16 -reset_timestamps 1 \
            "$OUTPUT_DIR/${stem}_%03d.wav"
        rm "$mono_wav"
    fi
done

echo "Done. Output in $OUTPUT_DIR"
