from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .cluster import inspect_workers
from .config import settings
from .ffmpeg_analysis import analyze_levels, analyze_loudness, check_ffmpeg, probe_audio
from .gpu import detect_nvidia_gpus
from .task_router import route_task


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description='LMNotebook Deep Audio V2 API — mastering measurements and GPU-cluster foundation.',
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
    return {
        'status': 'ok' if all(tools.values()) else 'degraded',
        'service': settings.app_name,
        'version': settings.version,
        'node_name': settings.node_name,
        'node_role': settings.node_role,
        'ffmpeg': tools,
        'gpus': gpus,
        'gpu_ready': bool(gpus),
        'analysis_layers': {
            'v2a_mastering': True,
            'v2b_neural': False,
            'v2c_song_anatomy': False,
            'v2d_stems_vocals': False,
            'v2e_catalog': False,
        },
    }


@app.get('/api/cluster')
async def cluster() -> dict[str, Any]:
    local_gpu = detect_nvidia_gpus()
    workers = await inspect_workers()
    return {
        'coordinator': {
            'node_name': settings.node_name,
            'node_role': settings.node_role,
            'gpus': local_gpu,
        },
        'configured_workers': list(settings.worker_urls),
        'workers': workers,
        'online_gpu_count': len(local_gpu)
        + sum(len(worker.get('gpus', [])) for worker in workers if worker.get('online')),
    }


@app.get('/api/route/{task}')
async def route(task: str) -> dict[str, Any]:
    """Preview which GPU node should receive a future neural task."""
    return await route_task(task)


@app.post('/api/analyze')
async def analyze(file: UploadFile = File(...)) -> dict[str, Any]:
    filename = file.filename or 'audio.bin'
    suffix = Path(filename).suffix.lower() or '.bin'
    if suffix not in {'.mp3', '.wav', '.flac', '.m4a', '.aac', '.ogg'}:
        raise HTTPException(status_code=415, detail='Unsupported audio format.')

    ff = check_ffmpeg()
    if not all(ff.values()):
        raise HTTPException(status_code=503, detail='FFmpeg/ffprobe is not available on the V2 node.')

    max_bytes = settings.max_upload_mb * 1024 * 1024
    temp_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            temp_path = Path(tmp.name)
            total = 0
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f'File exceeds LMN_MAX_UPLOAD_MB={settings.max_upload_mb}.',
                    )
                tmp.write(chunk)

        metadata = probe_audio(temp_path)
        loudness = analyze_loudness(temp_path)
        levels = analyze_levels(temp_path)

        return {
            'schema_version': '2.0',
            'engine': {
                'name': settings.app_name,
                'version': settings.version,
                'node_name': settings.node_name,
                'node_role': settings.node_role,
                'gpu_snapshot': detect_nvidia_gpus(),
            },
            'file': {
                'name': filename,
                **metadata,
            },
            'mastering': {
                'loudness': loudness,
                'levels': levels,
            },
            'provenance': {
                'file': 'measured',
                'mastering.loudness': 'measured',
                'mastering.levels': 'measured',
            },
            'capabilities': {
                'v2a_mastering': 'active',
                'v2b_neural': 'planned-gpu',
                'v2c_song_anatomy': 'planned',
                'v2d_stems_vocals': 'planned-gpu',
                'v2e_catalog': 'planned',
            },
            'privacy': {
                'temporary_upload': True,
                'retained_on_server': False,
                'note': 'The temporary audio file is deleted after analysis.',
            },
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f'V2 analysis failed: {exc}') from exc
    finally:
        await file.close()
        if temp_path and temp_path.exists():
            try:
                os.remove(temp_path)
            except OSError:
                pass
