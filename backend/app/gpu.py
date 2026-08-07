from __future__ import annotations

import shutil
import subprocess
from typing import Any


def detect_nvidia_gpus() -> list[dict[str, Any]]:
    """Return NVIDIA GPU capabilities without requiring PyTorch."""
    if not shutil.which('nvidia-smi'):
        return []

    command = [
        'nvidia-smi',
        '--query-gpu=index,name,memory.total,memory.free,driver_version',
        '--format=csv,noheader,nounits',
    ]

    try:
        proc = subprocess.run(command, capture_output=True, text=True, check=True, timeout=5)
    except (subprocess.SubprocessError, OSError):
        return []

    gpus: list[dict[str, Any]] = []
    for line in proc.stdout.splitlines():
        parts = [part.strip() for part in line.split(',')]
        if len(parts) != 5:
            continue
        index, name, total_mb, free_mb, driver = parts
        try:
            total = int(float(total_mb))
            free = int(float(free_mb))
        except ValueError:
            continue
        gpus.append(
            {
                'index': int(index),
                'name': name,
                'memory_total_mb': total,
                'memory_free_mb': free,
                'memory_total_gb': round(total / 1024, 1),
                'memory_free_gb': round(free / 1024, 1),
                'driver': driver,
                'recommended_roles': _recommended_roles(total),
            }
        )
    return gpus


def _recommended_roles(total_mb: int) -> list[str]:
    roles = ['dsp', 'embeddings', 'genre-mood']
    if total_mb >= 7000:
        roles.extend(['demucs', 'transcription'])
    if total_mb >= 11000:
        roles.extend(['large-models', 'primary-neural-worker'])
    return roles
