from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import File, HTTPException, UploadFile

from . import main as main_module
from .anatomy import analyze_anatomy, runtime_status as anatomy_runtime_status
from .config import settings
from .ffmpeg_analysis import check_ffmpeg
from .gpu import detect_nvidia_gpus

app = main_module.app
API_SCHEMA = main_module.API_SCHEMA
BACKEND_ROOT = Path(__file__).resolve().parents[1]
NEURAL_PYTHON = BACKEND_ROOT / '.venv' / 'Scripts' / 'python.exe'
STEMS_PYTHON = BACKEND_ROOT / '.venv-stems' / 'Scripts' / 'python.exe'
ANATOMY_PYTHON = BACKEND_ROOT / '.venv-anatomy' / 'Scripts' / 'python.exe'

# Do the cheap executable/GPU probes once while Uvicorn imports the app. Every
# subsequent /api/live and /api/health request is then pure in-memory JSON.
_BOOT_TOOLS = check_ffmpeg()
_BOOT_GPUS = detect_nvidia_gpus()


def _remove_route(path: str) -> None:
    app.router.routes[:] = [
        route for route in app.router.routes if getattr(route, 'path', None) != path
    ]


def _light_status() -> dict[str, Any]:
    tools = dict(_BOOT_TOOLS)
    gpus = [dict(gpu) for gpu in _BOOT_GPUS]
    gpu_ready = bool(gpus)
    device_name = gpus[0].get('name') if gpus else None

    # START/WORKER_START validate the real CUDA imports before launching the API.
    # Health only reports those bootstrap-validated runtime hints and never
    # imports Torch/Demucs itself. V2-C is isolated too and only checks its venv.
    neural_ready = gpu_ready and NEURAL_PYTHON.exists()
    stems_ready = gpu_ready and STEMS_PYTHON.exists()
    anatomy = anatomy_runtime_status(deep=False)
    anatomy_ready = bool(anatomy.get('ready')) and settings.node_role != 'gpu-worker'

    return {
        'status': 'ok' if all(tools.values()) else 'degraded',
        'health_mode': 'lightweight-bootstrap-validated',
        'api_schema': API_SCHEMA,
        'service': settings.app_name,
        'version': settings.version,
        'node_name': settings.node_name,
        'node_role': settings.node_role,
        'ffmpeg': tools,
        'gpus': gpus,
        'gpu_ready': gpu_ready,
        'neural': {
            'ready': neural_ready,
            'installed': NEURAL_PYTHON.exists(),
            'device_name': device_name,
            'status_source': 'launcher-preflight',
        },
        'stems': {
            'ready': stems_ready,
            'installed': STEMS_PYTHON.exists(),
            'runtime': 'isolated',
            'model': 'htdemucs',
            'device_name': device_name,
            'status_source': 'launcher-preflight',
        },
        'anatomy': {
            **anatomy,
            'ready': anatomy_ready,
            'role': 'coordinator-only',
        },
        'analysis_layers': {
            'v2a_mastering': True,
            'v2b_neural': neural_ready,
            'v2c_song_anatomy': anatomy_ready,
            'v2d_stems_vocals': stems_ready,
            'v2e_catalog': False,
        },
    }


# Replace the old expensive health route from app.main. FastAPI resolves routes
# in registration order, so removing it explicitly avoids accidental fallback.
_remove_route('/api/health')


@app.get('/api/live')
def live() -> dict[str, Any]:
    """Instant liveness probe: pure cached JSON, no subprocess or ML import."""
    return _light_status()


@app.get('/api/health')
def health() -> dict[str, Any]:
    """Backward-compatible lightweight health endpoint used by UI and LAN cluster."""
    return _light_status()


@app.get('/api/diagnostics')
def diagnostics() -> dict[str, Any]:
    """Explicit deep diagnostics. This endpoint is allowed to load GPU/DSP runtimes."""
    payload = _light_status()
    neural = main_module.neural_runtime_status()
    stems = main_module.stems_runtime_status()
    anatomy = anatomy_runtime_status(deep=True) if settings.node_role != 'gpu-worker' else anatomy_runtime_status(deep=False)
    payload['health_mode'] = 'deep-diagnostics'
    payload['neural'] = neural
    payload['stems'] = stems
    payload['anatomy'] = anatomy
    payload['analysis_layers']['v2b_neural'] = bool(neural.get('ready'))
    payload['analysis_layers']['v2c_song_anatomy'] = bool(anatomy.get('ready')) and settings.node_role != 'gpu-worker'
    payload['analysis_layers']['v2d_stems_vocals'] = bool(stems.get('ready'))
    return payload


@app.get('/api/anatomy/status')
def anatomy_status() -> dict[str, Any]:
    if settings.node_role == 'gpu-worker':
        return {
            'installed': ANATOMY_PYTHON.exists(),
            'ready': False,
            'role': 'gpu-worker',
            'error': 'Song Anatomy runs on the coordinator; this worker is reserved for GPU jobs.',
        }
    return anatomy_runtime_status(deep=True)


@app.post('/api/anatomy')
async def analyze_song_anatomy(file: UploadFile = File(...)) -> dict[str, Any]:
    if settings.node_role == 'gpu-worker':
        raise HTTPException(status_code=409, detail='Song Anatomy V2-C must run on the coordinator.')

    filename, suffix = main_module._validate_upload(file)
    status = anatomy_runtime_status(deep=False)
    if not status.get('ready'):
        raise HTTPException(status_code=503, detail=status.get('error') or 'Song Anatomy runtime is not ready.')

    temp_path: Path | None = None
    try:
        temp_path = await main_module._save_upload(file, suffix)
        result = await asyncio.to_thread(analyze_anatomy, temp_path)
        return {
            'schema_version': API_SCHEMA,
            'file': {'name': filename, **main_module.probe_audio(temp_path)},
            'compute': {
                'node_name': settings.node_name,
                'node_role': settings.node_role,
                'route': 'local-coordinator',
                'runtime': 'isolated-anatomy',
            },
            'anatomy': result,
            'privacy': main_module._privacy_payload(),
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f'Song Anatomy failed: {exc}') from exc
    finally:
        await file.close()
        main_module._delete_temp(temp_path)
