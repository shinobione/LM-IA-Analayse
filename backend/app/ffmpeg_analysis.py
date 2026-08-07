from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import settings


LOUDNORM_JSON_RE = re.compile(r'\{\s*"input_i".*?\}', re.DOTALL)


def check_ffmpeg() -> dict[str, bool]:
    return {
        'ffmpeg': bool(shutil.which(settings.ffmpeg_bin)),
        'ffprobe': bool(shutil.which(settings.ffprobe_bin)),
    }


def probe_audio(path: Path) -> dict[str, Any]:
    command = [
        settings.ffprobe_bin,
        '-v', 'error',
        '-show_entries',
        'format=duration,size,bit_rate,format_name:stream=index,codec_name,codec_type,sample_rate,channels,channel_layout,bits_per_sample,bit_rate',
        '-of', 'json',
        str(path),
    ]
    proc = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30)
    raw = json.loads(proc.stdout or '{}')
    fmt = raw.get('format', {})
    audio_stream = next((s for s in raw.get('streams', []) if s.get('codec_type') == 'audio'), {})

    duration = _float(fmt.get('duration'))
    size_bytes = _int(fmt.get('size'))
    bitrate = _int(audio_stream.get('bit_rate')) or _int(fmt.get('bit_rate'))
    sample_rate = _int(audio_stream.get('sample_rate'))

    return {
        'format': fmt.get('format_name'),
        'codec': audio_stream.get('codec_name'),
        'duration_seconds': round(duration, 3) if duration is not None else None,
        'size_bytes': size_bytes,
        'size_mb': round(size_bytes / 1048576, 2) if size_bytes is not None else None,
        'bit_rate_bps': bitrate,
        'bit_rate_kbps': round(bitrate / 1000, 1) if bitrate is not None else None,
        'sample_rate_hz': sample_rate,
        'channels': _int(audio_stream.get('channels')),
        'channel_layout': audio_stream.get('channel_layout'),
        'bits_per_sample': _int(audio_stream.get('bits_per_sample')),
    }


def analyze_loudness(path: Path) -> dict[str, Any]:
    """Measure integrated LUFS, LRA and true peak with FFmpeg loudnorm."""
    command = [
        settings.ffmpeg_bin,
        '-hide_banner',
        '-nostats',
        '-i', str(path),
        '-af', 'loudnorm=I=-14:LRA=11:TP=-1:print_format=json',
        '-f', 'null',
        '-',
    ]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=180)
    stderr = proc.stderr or ''
    match = LOUDNORM_JSON_RE.search(stderr)
    if not match:
        raise RuntimeError('FFmpeg loudnorm did not return a measurement block.')
    payload = json.loads(match.group(0))

    integrated = _float(payload.get('input_i'))
    true_peak = _float(payload.get('input_tp'))
    lra = _float(payload.get('input_lra'))
    threshold = _float(payload.get('input_thresh'))

    return {
        'integrated_lufs': integrated,
        'loudness_range_lu': lra,
        'true_peak_dbtp': true_peak,
        'relative_threshold_lufs': threshold,
        'target_offset_lu': _float(payload.get('target_offset')),
        'normalization_type': payload.get('normalization_type'),
        'provenance': 'measured',
        'standard': 'ITU-R BS.1770 / EBU R128 via FFmpeg loudnorm',
    }


def analyze_levels(path: Path) -> dict[str, Any]:
    """Get simple mean/max level measurements for cross-checking browser DSP."""
    command = [
        settings.ffmpeg_bin,
        '-hide_banner',
        '-nostats',
        '-i', str(path),
        '-af', 'volumedetect',
        '-f', 'null',
        '-',
    ]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=180)
    stderr = proc.stderr or ''
    mean_match = re.search(r'mean_volume:\s*(-?inf|-?[0-9.]+) dB', stderr)
    max_match = re.search(r'max_volume:\s*(-?inf|-?[0-9.]+) dB', stderr)
    return {
        'mean_volume_db': _db(mean_match.group(1)) if mean_match else None,
        'max_volume_db': _db(max_match.group(1)) if max_match else None,
        'provenance': 'measured',
    }


def _db(value: str) -> float | None:
    if value == '-inf':
        return None
    return _float(value)


def _float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return None if not math.isfinite(result) else round(result, 4)


def _int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
