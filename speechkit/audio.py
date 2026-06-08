import io
import subprocess
import wave
from pathlib import Path

from config import MAX_BYTES, MAX_SECONDS


def load_wav(path) -> tuple:
    """Returns (pcm_bytes, sample_rate, channels, sampwidth, duration_seconds)."""
    with wave.open(str(path), "rb") as wf:
        params = wf.getparams()
        frames = wf.readframes(params.nframes)
        duration = params.nframes / params.framerate
    return frames, params.framerate, params.nchannels, params.sampwidth, duration


def validate(pcm: bytes, rate: int, channels: int, sampwidth: int, duration: float) -> list:
    warnings = []
    if channels != 1:
        warnings.append(f"not mono: {channels} channels")
    if sampwidth != 2:
        warnings.append(f"not 16-bit: sampwidth={sampwidth}")
    if duration > MAX_SECONDS:
        warnings.append(f"duration {duration:.1f}s exceeds {MAX_SECONDS}s limit")
    if len(pcm) > MAX_BYTES:
        warnings.append(f"size {len(pcm)} bytes exceeds {MAX_BYTES} byte limit")
    return warnings


def to_mono_wav(input_path, output_path):
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path),
         "-ac", "1", "-ar", "16000", "-sample_fmt", "s16", str(output_path)],
        check=True,
        capture_output=True,
    )


def segment(input_path, output_dir, segment_seconds: int = 30):
    """Split audio into fixed-length segments, writing them to output_dir."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(input_path).stem
    pattern = str(output_dir / f"{stem}_%03d.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(input_path),
         "-f", "segment", "-segment_time", str(segment_seconds),
         "-ac", "1", "-ar", "16000", "-sample_fmt", "s16",
         "-reset_timestamps", "1", pattern],
        check=True,
        capture_output=True,
    )
