from __future__ import annotations

import math
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from .ffmpeg_analysis import analyze_levels, analyze_loudness, probe_audio
from .gpu import detect_nvidia_gpus

MODEL_NAME = 'htdemucs'
EXPECTED_STEMS = ('vocals', 'drums', 'bass', 'other')


def runtime_status() -> dict[str, Any]:
    try:
        import demucs  # type: ignore
        import torch
        import torchaudio  # noqa: F401

        cuda_ready = bool(torch.cuda.is_available())
        return {
            'ready': cuda_ready,
            'model': MODEL_NAME,
            'demucs_version': getattr(demucs, '__version__', '4.x'),
            'torch_version': torch.__version__,
            'cuda_runtime': torch.version.cuda,
            'device_name': torch.cuda.get_device_name(0) if cuda_ready else None,
            'error': None if cuda_ready else 'CUDA is not available for Demucs.',
        }
    except Exception as exc:  # noqa: BLE001
        return {
            'ready': False,
            'model': MODEL_NAME,
            'error': str(exc),
        }


def separate_and_analyze(path: Path) -> dict[str, Any]:
    status = runtime_status()
    if not status.get('ready'):
        raise RuntimeError(status.get('error') or 'Demucs runtime is not ready.')

    started = time.perf_counter()
    gpu = detect_nvidia_gpus()

    with tempfile.TemporaryDirectory(prefix='lmn-demucs-') as tmp_dir:
        out_dir = Path(tmp_dir)
        command = [
            sys.executable,
            '-m',
            'demucs.separate',
            '--name',
            MODEL_NAME,
            '--device',
            'cuda',
            '--out',
            str(out_dir),
            str(path),
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            tail = (completed.stderr or completed.stdout or '')[-4000:]
            raise RuntimeError(f'Demucs failed with exit code {completed.returncode}: {tail}')

        stem_dir = _find_stem_dir(out_dir)
        stems: list[dict[str, Any]] = []
        raw_weights: dict[str, float] = {}

        for name in EXPECTED_STEMS:
            stem_path = stem_dir / f'{name}.wav'
            if not stem_path.exists():
                continue
            metadata = probe_audio(stem_path)
            loudness = analyze_loudness(stem_path)
            levels = analyze_levels(stem_path)
            mean_db = levels.get('mean_volume_db')
            raw_weights[name] = _db_to_power(mean_db)
            stems.append(
                {
                    'name': name,
                    'file_name': stem_path.name,
                    'metadata': metadata,
                    'loudness': loudness,
                    'levels': levels,
                }
            )

        total_weight = sum(raw_weights.values()) or 1.0
        for stem in stems:
            weight = raw_weights.get(stem['name'], 0.0)
            stem['relative_energy_percent'] = round((weight / total_weight) * 100.0, 1)

        return {
            'ready': True,
            'model': MODEL_NAME,
            'device': status.get('device_name') or 'cuda',
            'gpu_snapshot': gpu,
            'elapsed_seconds': round(time.perf_counter() - started, 2),
            'stem_count': len(stems),
            'stems': stems,
            'provenance': 'DEMUCS GPU separation + FFmpeg per-stem measurements',
        }


def _find_stem_dir(out_dir: Path) -> Path:
    candidates = [p for p in out_dir.rglob('*') if p.is_dir() and any((p / f'{name}.wav').exists() for name in EXPECTED_STEMS)]
    if not candidates:
        raise RuntimeError('Demucs finished but no stem directory was found.')
    candidates.sort(key=lambda p: len(p.parts))
    return candidates[0]


def _db_to_power(value: Any) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0
    if not math.isfinite(numeric):
        return 0.0
    return 10.0 ** (numeric / 10.0)
