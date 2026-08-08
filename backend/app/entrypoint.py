from __future__ import annotations

from pathlib import Path
from typing import Any

from . import main as main_module
from .config import settings
from .ffmpeg_analysis import check_ffmpeg
from .gpu import detect_nvidia_gpus

app = main_module.app
API_SCHEMA = main_module.API_SCHEMA
BACKEND_ROOT = Path(__file__).resolve().parents[1]
NEURAL_PYTHON = BACKEND_ROOT / '.venv' / 'Scripts' / 'python.exe'
STEMS_PYTHON = BACKEND_ROOT / '.venv-stems' / 'Scripts' / 'python.exe'


def _remove_route(path: str) -> None:
    app.router.routes[:] = [
        route for route in app.router.routes if getattr(route, 'path', None) != path
    ]


def _light_status() -> dict[str, Any]:
    tools = check_ffmpeg()
    gpus = detect_nvidia_gpus()
    gpu_ready = bool(gpus)
    device_name = gpus[0].get('name') if gpus else None

    # START/WORKER_START validate the real CUDA imports before launching the API.
    # The health endpoint therefore only needs installation/runtime hints here;
    # it must never import Torch/Demucs just to answer a liveness probe.
    neural_ready = gpu_ready and NEURAL_PYTHON.exists()
    stems_ready = gpu_ready and STEMS_PYTHON.exists()

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
        'analysis_layers': {
            'v2a_mastering': True,
            'v2b_neural': neural_ready,
            'v2c_song_anatomy': False,
            'v2d_stems_vocals': stems_ready,
            'v2e_catalog': False,
        },
    }


# Replace the old expensive health route from app.main. FastAPI resolves routes
# in registration order, so removing it explicitly avoids accidental fallback.
_remove_route('/api/health')


@app.get('/api/live')
def live() -> dict[str, Any]:
    """Fast liveness probe. Never imports Torch, Transformers, Torchaudio or Demucs."""
    return _light_status()


@app.get('/api/health')
def health() -> dict[str, Any]:
    """Backward-compatible lightweight health endpoint used by the UI and LAN cluster."""
    return _light_status()


@app.get('/api/diagnostics')
def diagnostics() -> dict[str, Any]:
    """Explicit deep diagnostics. This endpoint is allowed to load GPU runtimes."""
    payload = _light_status()
    neural = main_module.neural_runtime_status()
    stems = main_module.stems_runtime_status()
    payload['health_mode'] = 'deep-diagnostics'
    payload['neural'] = neural
    payload['stems'] = stems
    payload['analysis_layers']['v2b_neural'] = bool(neural.get('ready'))
    payload['analysis_layers']['v2d_stems_vocals'] = bool(stems.get('ready'))
    return payload
