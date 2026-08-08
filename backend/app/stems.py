from __future__ import annotations

import json
import math
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from .ffmpeg_analysis import analyze_levels, analyze_loudness, probe_audio
from .gpu import detect_nvidia_gpus

MODEL_NAME = 'htdemucs'
EXPECTED_STEMS = ('vocals', 'drums', 'bass', 'other')
BACKEND_ROOT = Path(__file__).resolve().parents[1]
STEMS_PYTHON = BACKEND_ROOT / '.venv-stems' / 'Scripts' / 'python.exe'
STEMS_RUNNER = BACKEND_ROOT / 'stems_runner.py'


def runtime_status() -> dict[str, Any]:
    if not STEMS_PYTHON.exists():
        return {
            'ready': False,
            'model': MODEL_NAME,
            'runtime': 'isolated',
            'error': 'backend/.venv-stems is not installed yet.',
        }

    code = (
        "import json,torch,torchaudio,demucs; "
        "cuda=bool(torch.cuda.is_available()); "
        "print(json.dumps({'ready':cuda,'torch_version':torch.__version__,"
        "'torchaudio_version':torchaudio.__version__,'cuda_runtime':torch.version.cuda,"
        "'device_name':torch.cuda.get_device_name(0) if cuda else None,"
        "'demucs_version':getattr(demucs,'__version__','4.x')}))"
    )
    try:
        completed = subprocess.run(
            [str(STEMS_PYTHON), '-c', code],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=20,
            check=False,
        )
        if completed.returncode != 0:
            tail = (completed.stderr or completed.stdout or '')[-2000:]
            raise RuntimeError(tail or f'stems runtime exited {completed.returncode}')
        payload = json.loads((completed.stdout or '').strip().splitlines()[-1])
        payload.update({'model': MODEL_NAME, 'runtime': 'isolated', 'python': str(STEMS_PYTHON)})
        if not payload.get('ready'):
            payload['error'] = 'CUDA is not available in the isolated Demucs runtime.'
        else:
            payload['error'] = None
        return payload
    except Exception as exc:  # noqa: BLE001
        return {
            'ready': False,
            'model': MODEL_NAME,
            'runtime': 'isolated',
            'python': str(STEMS_PYTHON),
            'error': str(exc),
        }


def separate_and_analyze(path: Path) -> dict[str, Any]:
    status = runtime_status()
    if not status.get('ready'):
        raise RuntimeError(status.get('error') or 'Demucs runtime is not ready.')
    if not STEMS_RUNNER.exists():
        raise RuntimeError(f'Isolated Demucs runner missing: {STEMS_RUNNER}')

    started = time.perf_counter()
    gpu = detect_nvidia_gpus()

    with tempfile.TemporaryDirectory(prefix='lmn-demucs-') as tmp_dir:
        out_dir = Path(tmp_dir)
        command = [
            str(STEMS_PYTHON),
            str(STEMS_RUNNER),
            '--input',
            str(path),
            '--output',
            str(out_dir),
            '--model',
            MODEL_NAME,
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
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
            'runtime': 'isolated',
            'device': status.get('device_name') or 'cuda',
            'torch_version': status.get('torch_version'),
            'torchaudio_version': status.get('torchaudio_version'),
            'cuda_runtime': status.get('cuda_runtime'),
            'gpu_snapshot': gpu,
            'elapsed_seconds': round(time.perf_counter() - started, 2),
            'stem_count': len(stems),
            'stems': stems,
            'provenance': 'DEMUCS GPU separation (isolated runtime) + FFmpeg per-stem measurements',
        }


def _find_stem_dir(out_dir: Path) -> Path:
    candidates = [
        p
        for p in out_dir.rglob('*')
        if p.is_dir() and any((p / f'{name}.wav').exists() for name in EXPECTED_STEMS)
    ]
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
