from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .cluster import inspect_workers
from .config import settings
from .ffmpeg_analysis import analyze_levels, analyze_loudness, check_ffmpeg, probe_audio
from .gpu import detect_nvidia_gpus
from .neural import analyze_neural, runtime_status as neural_runtime_status
from .stems import runtime_status as stems_runtime_status, separate_and_analyze
from .task_router import route_task

API_SCHEMA = '2.2'
SUPPORTED_AUDIO = {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg'}

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description='LMNotebook Deep Audio V2 API — mastering, neural understanding and distributed GPU stem analysis.',
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=['GET', 'POST', 'OPTIONS'],
    allow_headers=['*'],
)


@app.get('/api/health')
def health() -> dict[str, Any]:
    tools = check_ffmpeg()
    gpus = detect_nvidia_gpus()
    neural = neural_runtime_status()
    stems = stems_runtime_status()
    return {
        'status': 'ok' if all(tools.values()) else 'degraded',
        'api_schema': API_SCHEMA,
        'service': settings.app_name,
        'version': settings.version,
        'node_name': settings.node_name,
        'node_role': settings.node_role,
        'ffmpeg': tools,
        'gpus': gpus,
        'gpu_ready': bool(gpus),
        'neural': neural,
        'stems': stems,
        'analysis_layers': {
            'v2a_mastering': True,
            'v2b_neural': bool(neural.get('ready')),
            'v2c_song_anatomy': False,
            'v2d_stems_vocals': bool(stems.get('ready')),
            'v2e_catalog': False,
        },
    }


@app.get('/api/neural/status')
def neural_status() -> dict[str, Any]:
    return neural_runtime_status()


@app.get('/api/stems/status')
def stems_status() -> dict[str, Any]:
    return stems_runtime_status()


@app.get('/api/cluster')
async def cluster() -> dict[str, Any]:
    local_gpu = detect_nvidia_gpus()
    workers = await inspect_workers()
    return {
        'coordinator': {
            'node_name': settings.node_name,
            'node_role': settings.node_role,
            'gpus': local_gpu,
            'stems': stems_runtime_status(),
        },
        'configured_workers': list(settings.worker_urls),
        'workers': workers,
        'online_gpu_count': len(local_gpu)
        + sum(len(worker.get('gpus', [])) for worker in workers if worker.get('online')),
    }


@app.get('/api/route/{task}')
async def route(task: str) -> dict[str, Any]:
    return await route_task(task)


@app.post('/api/analyze')
async def analyze(file: UploadFile = File(...), neural: bool = True) -> dict[str, Any]:
    filename, suffix = _validate_upload(file)
    ff = check_ffmpeg()
    if not all(ff.values()):
        raise HTTPException(status_code=503, detail='FFmpeg/ffprobe is not available on the V2 node.')

    temp_path: Path | None = None
    try:
        temp_path = await _save_upload(file, suffix)
        metadata = probe_audio(temp_path)
        loudness = analyze_loudness(temp_path)
        levels = analyze_levels(temp_path)

        neural_payload: dict[str, Any] | None = None
        neural_warning: str | None = None
        neural_status = neural_runtime_status()
        if neural:
            if neural_status.get('ready'):
                try:
                    neural_payload = await asyncio.to_thread(
                        analyze_neural,
                        temp_path,
                        metadata.get('duration_seconds'),
                    )
                except Exception as exc:  # noqa: BLE001
                    neural_warning = f'Neural analysis unavailable: {exc}'
            else:
                neural_warning = neural_status.get('error') or 'Neural runtime is not ready.'

        return {
            'schema_version': API_SCHEMA,
            'engine': _engine_snapshot(),
            'file': {'name': filename, **metadata},
            'mastering': {'loudness': loudness, 'levels': levels},
            'neural': neural_payload,
            'warnings': [neural_warning] if neural_warning else [],
            'provenance': {
                'file': 'measured',
                'mastering.loudness': 'measured',
                'mastering.levels': 'measured',
                'neural': 'neural' if neural_payload else 'unavailable',
            },
            'capabilities': {
                'v2a_mastering': 'active',
                'v2b_neural': 'active' if neural_payload else ('ready' if neural_status.get('ready') else 'unavailable'),
                'v2c_song_anatomy': 'planned',
                'v2d_stems_vocals': 'ready' if stems_runtime_status().get('ready') else 'cluster-optional',
                'v2e_catalog': 'embedding-ready' if neural_payload else 'planned',
            },
            'privacy': _privacy_payload(),
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f'V2 analysis failed: {exc}') from exc
    finally:
        await file.close()
        _delete_temp(temp_path)


@app.post('/api/stems/analyze')
async def analyze_stems_on_this_node(file: UploadFile = File(...)) -> dict[str, Any]:
    """Run Demucs on the node receiving this request. Used by LAN GPU workers."""
    filename, suffix = _validate_upload(file)
    status = stems_runtime_status()
    if not status.get('ready'):
        raise HTTPException(status_code=503, detail=status.get('error') or 'Demucs runtime is not ready on this node.')

    temp_path: Path | None = None
    try:
        temp_path = await _save_upload(file, suffix)
        result = await asyncio.to_thread(separate_and_analyze, temp_path)
        return {
            'schema_version': API_SCHEMA,
            'file': {'name': filename, **probe_audio(temp_path)},
            'compute': {
                'node_name': settings.node_name,
                'node_role': settings.node_role,
                'route': 'direct-node',
            },
            'separation': result,
            'privacy': _privacy_payload(),
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f'Stem analysis failed: {exc}') from exc
    finally:
        await file.close()
        _delete_temp(temp_path)


@app.post('/api/stems')
async def analyze_stems_routed(file: UploadFile = File(...)) -> dict[str, Any]:
    """Route Demucs to the best GPU, preferring the LAN worker when it fits."""
    filename, suffix = _validate_upload(file)
    temp_path: Path | None = None
    route_info = await route_task('demucs')
    selected = route_info.get('selected')
    if not selected:
        raise HTTPException(status_code=503, detail='No GPU currently satisfies the Demucs VRAM requirement.')

    try:
        temp_path = await _save_upload(file, suffix)
        selected_url = str(selected.get('url') or '')

        if not selected.get('local') and selected_url.startswith('http'):
            try:
                remote = await _forward_stems_to_worker(selected_url, temp_path, filename)
                remote['routing'] = route_info
                remote['compute']['route'] = 'lan-worker'
                return remote
            except Exception as exc:  # noqa: BLE001
                local_status = stems_runtime_status()
                if not local_status.get('ready'):
                    raise HTTPException(
                        status_code=502,
                        detail=f'LAN worker failed and local fallback is unavailable: {exc}',
                    ) from exc

                fallback = await asyncio.to_thread(separate_and_analyze, temp_path)
                return {
                    'schema_version': API_SCHEMA,
                    'file': {'name': filename, **probe_audio(temp_path)},
                    'compute': {
                        'node_name': settings.node_name,
                        'node_role': settings.node_role,
                        'route': 'local-fallback',
                        'worker_error': str(exc),
                    },
                    'routing': route_info,
                    'separation': fallback,
                    'privacy': _privacy_payload(),
                }

        local_status = stems_runtime_status()
        if not local_status.get('ready'):
            raise HTTPException(status_code=503, detail=local_status.get('error') or 'Local Demucs runtime is not ready.')
        local = await asyncio.to_thread(separate_and_analyze, temp_path)
        return {
            'schema_version': API_SCHEMA,
            'file': {'name': filename, **probe_audio(temp_path)},
            'compute': {
                'node_name': settings.node_name,
                'node_role': settings.node_role,
                'route': 'local',
            },
            'routing': route_info,
            'separation': local,
            'privacy': _privacy_payload(),
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f'Routed stem analysis failed: {exc}') from exc
    finally:
        await file.close()
        _delete_temp(temp_path)


async def _forward_stems_to_worker(worker_url: str, path: Path, filename: str) -> dict[str, Any]:
    timeout = httpx.Timeout(connect=5.0, read=1800.0, write=1800.0, pool=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        with path.open('rb') as audio:
            response = await client.post(
                f'{worker_url.rstrip("/")}/api/stems/analyze',
                files={'file': (filename, audio, 'application/octet-stream')},
            )
        if response.status_code >= 400:
            detail = response.text[-2000:]
            raise RuntimeError(f'Worker HTTP {response.status_code}: {detail}')
        return response.json()


def _validate_upload(file: UploadFile) -> tuple[str, str]:
    filename = file.filename or 'audio.bin'
    suffix = Path(filename).suffix.lower() or '.bin'
    if suffix not in SUPPORTED_AUDIO:
        raise HTTPException(status_code=415, detail='Unsupported audio format.')
    return filename, suffix


async def _save_upload(file: UploadFile, suffix: str) -> Path:
    max_bytes = settings.max_upload_mb * 1024 * 1024
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        path = Path(tmp.name)
        total = 0
        while chunk := await file.read(1024 * 1024):
            total += len(chunk)
            if total > max_bytes:
                _delete_temp(path)
                raise HTTPException(
                    status_code=413,
                    detail=f'File exceeds LMN_MAX_UPLOAD_MB={settings.max_upload_mb}.',
                )
            tmp.write(chunk)
    return path


def _engine_snapshot() -> dict[str, Any]:
    return {
        'name': settings.app_name,
        'version': settings.version,
        'node_name': settings.node_name,
        'node_role': settings.node_role,
        'gpu_snapshot': detect_nvidia_gpus(),
    }


def _privacy_payload() -> dict[str, Any]:
    return {
        'temporary_upload': True,
        'retained_on_server': False,
        'note': 'Temporary audio and generated stems are deleted after measurements. Model weights remain cached locally.',
    }


def _delete_temp(path: Path | None) -> None:
    if path and path.exists():
        try:
            os.remove(path)
        except OSError:
            pass
