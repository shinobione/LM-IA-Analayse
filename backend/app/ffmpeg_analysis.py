from __future__ import annotations

import json
import math
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import settings


LOUDNORM_KEYS = {'input_i', 'input_tp', 'input_lra', 'input_thresh'}
JSON_OBJECT_RE = re.compile(r'\{(?:[^{}]|"(?:\\.|[^"\\])*")*\}', re.DOTALL)


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
    """Measure integrated LUFS, LRA and true peak without aborting later Deep Audio layers."""
    command = [
        settings.ffmpeg_bin,
        '-hide_banner',
        '-nostats',
        '-i', str(path),
        '-map', '0:a:0',
        '-vn',
        '-sn',
        '-dn',
        '-af', 'loudnorm=I=-14:LRA=11:TP=-1:print_format=json',
        '-f', 'null',
        '-',
    ]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=180)
    payload = _parse_loudnorm_payload(proc.stdout, proc.stderr)
    if payload is not None:
        return _loudnorm_result(payload)

    fallback = _analyze_loudness_ebur128(path)
    if fallback is not None:
        fallback['fallback_reason'] = 'loudnorm JSON measurement block was unavailable'
        return fallback

    diagnostic = _diagnostic_tail(proc.stderr or proc.stdout or '')
    return _unavailable_loudness(
        'FFmpeg produced neither loudnorm JSON nor an EBU R128 summary'
        f' (loudnorm exit {proc.returncode}).{diagnostic}'
    )


def analyze_levels(path: Path) -> dict[str, Any]:
    """Get simple mean/max level measurements for cross-checking browser DSP."""
    command = [
        settings.ffmpeg_bin,
        '-hide_banner',
        '-nostats',
        '-i', str(path),
        '-map', '0:a:0',
        '-vn',
        '-sn',
        '-dn',
        '-af', 'volumedetect',
        '-f', 'null',
        '-',
    ]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=180)
    stderr = proc.stderr or ''
    mean_match = re.search(r'mean_volume:\s*(-?inf|-?[0-9.]+) dB', stderr)
    max_match = re.search(r'max_volume:\s*(-?inf|-?[0-9.]+) dB', stderr)
    if not (mean_match or max_match):
        diagnostic = _diagnostic_tail(stderr or proc.stdout or '')
        return {
            'mean_volume_db': None,
            'max_volume_db': None,
            'provenance': 'unavailable',
            'error': f'FFmpeg volumedetect returned no measurement (exit {proc.returncode}).{diagnostic}',
        }
    return {
        'mean_volume_db': _db(mean_match.group(1)) if mean_match else None,
        'max_volume_db': _db(max_match.group(1)) if max_match else None,
        'provenance': 'measured',
    }


def _parse_loudnorm_payload(*streams: str) -> dict[str, Any] | None:
    """Find the actual loudnorm object without depending on FFmpeg log spacing/order."""
    text = '\n'.join(stream for stream in streams if stream)
    candidates = list(JSON_OBJECT_RE.finditer(text))
    for match in reversed(candidates):
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and LOUDNORM_KEYS.issubset(payload):
            return payload
    return None


def _loudnorm_result(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        'integrated_lufs': _float(payload.get('input_i')),
        'loudness_range_lu': _float(payload.get('input_lra')),
        'true_peak_dbtp': _float(payload.get('input_tp')),
        'relative_threshold_lufs': _float(payload.get('input_thresh')),
        'target_offset_lu': _float(payload.get('target_offset')),
        'normalization_type': payload.get('normalization_type'),
        'provenance': 'measured-loudnorm-json',
        'standard': 'ITU-R BS.1770 / EBU R128 via FFmpeg loudnorm',
    }


def _unavailable_loudness(error: str) -> dict[str, Any]:
    return {
        'integrated_lufs': None,
        'loudness_range_lu': None,
        'true_peak_dbtp': None,
        'relative_threshold_lufs': None,
        'target_offset_lu': None,
        'normalization_type': None,
        'provenance': 'unavailable',
        'standard': 'ITU-R BS.1770 / EBU R128 via FFmpeg',
        'error': error,
    }


def _analyze_loudness_ebur128(path: Path) -> dict[str, Any] | None:
    """Fallback measurement when loudnorm ran but its JSON summary cannot be recovered."""
    command = [
        settings.ffmpeg_bin,
        '-hide_banner',
        '-nostats',
        '-i', str(path),
        '-map', '0:a:0',
        '-vn',
        '-sn',
        '-dn',
        '-af', 'ebur128=peak=true:framelog=verbose',
        '-f', 'null',
        '-',
    ]
    proc = subprocess.run(command, capture_output=True, text=True, timeout=180)
    return _parse_ebur128_summary(proc.stderr or proc.stdout or '')


def _parse_ebur128_summary(text: str) -> dict[str, Any] | None:
    summaries = list(re.finditer(r'Summary:\s*(.*)', text, re.DOTALL | re.IGNORECASE))
    if not summaries:
        return None
    summary = summaries[-1].group(1)
    integrated = re.search(r'Integrated loudness:.*?\bI:\s*(-?inf|-?[0-9.]+)\s+LUFS', summary, re.DOTALL | re.IGNORECASE)
    lra = re.search(r'Loudness range:.*?\bLRA:\s*(-?inf|-?[0-9.]+)\s+LU', summary, re.DOTALL | re.IGNORECASE)
    threshold = re.search(r'Integrated loudness:.*?Threshold:\s*(-?inf|-?[0-9.]+)\s+LUFS', summary, re.DOTALL | re.IGNORECASE)
    peak = re.search(r'True peak:.*?\bPeak:\s*(-?inf|-?[0-9.]+)\s+dB(?:FS|TP)', summary, re.DOTALL | re.IGNORECASE)
    if not integrated:
        return None
    return {
        'integrated_lufs': _db(integrated.group(1)),
        'loudness_range_lu': _db(lra.group(1)) if lra else None,
        'true_peak_dbtp': _db(peak.group(1)) if peak else None,
        'relative_threshold_lufs': _db(threshold.group(1)) if threshold else None,
        'target_offset_lu': None,
        'normalization_type': 'measurement-only-fallback',
        'provenance': 'measured-ebur128-fallback',
        'standard': 'EBU R128 via FFmpeg ebur128 fallback',
    }


def _diagnostic_tail(value: str, limit: int = 900) -> str:
    compact = ' '.join(str(value or '').split())
    if not compact:
        return ''
    return f' FFmpeg tail: {compact[-limit:]}'


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
