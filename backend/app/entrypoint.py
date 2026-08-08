from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import File, Form, HTTPException, UploadFile

from . import main as main_module
from .anatomy import analyze_anatomy, runtime_status as anatomy_runtime_status
from .config import settings
from .ffmpeg_analysis import check_ffmpeg
from .fusion import fuse_anatomy_stems
from .gpu import detect_nvidia_gpus
from .studio_contract import build_analysis_envelope, parse_source_version, parse_track_id

app = main_module.app
API_SCHEMA = main_module.API_SCHEMA
BACKEND_ROOT = Path(__file__).resolve().parents[1]
NEURAL_PYTHON = BACKEND_ROOT / '.venv' / 'Scripts' / 'python.exe'
STEMS_PYTHON = BACKEND_ROOT / '.venv-stems' / 'Scripts' / 'python.exe'
ANATOMY_PYTHON = BACKEND_ROOT / '.venv-anatomy' / 'Scripts' / 'python.exe'

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

    neural_ready = gpu_ready and NEURAL_PYTHON.exists()
    stems_ready = gpu_ready and STEMS_PYTHON.exists()
    anatomy = anatomy_runtime_status(deep=False)
    anatomy_ready = bool(anatomy.get('ready')) and settings.node_role != 'gpu-worker'
    fusion_available = anatomy_ready and settings.node_role != 'gpu-worker'

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
        'fusion': {
            'available': fusion_available,
            'ready': fusion_available,
            'mode': 'V2-C x V2-D',
            'requires_stems_route': True,
            'status_source': 'anatomy-preflight; live stem route checked by /api/fusion/status',
        },
        'analysis_layers': {
            'v2a_mastering': True,
            'v2b_neural': neural_ready,
            'v2c_song_anatomy': anatomy_ready,
            'v2cd_fusion': fusion_available,
            'v2d_stems_vocals': stems_ready,
            'v2e_catalog': True,
        },
    }


_remove_route('/api/health')


@app.get('/api/live')
def live() -> dict[str, Any]:
    return _light_status()


@app.get('/api/health')
def health() -> dict[str, Any]:
    return _light_status()


@app.get('/api/diagnostics')
def diagnostics() -> dict[str, Any]:
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
    payload['analysis_layers']['v2cd_fusion'] = bool(anatomy.get('ready')) and settings.node_role != 'gpu-worker'
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


@app.get('/api/fusion/status')
async def fusion_status() -> dict[str, Any]:
    if settings.node_role == 'gpu-worker':
        return {
            'ready': False,
            'role': 'gpu-worker',
            'error': 'V2-CD Fusion runs on the coordinator.',
        }

    anatomy = anatomy_runtime_status(deep=False)
    route = await main_module.route_task('demucs')
    selected = route.get('selected')
    ready = bool(anatomy.get('ready')) and bool(selected)
    return {
        'ready': ready,
        'mode': 'V2-C x V2-D',
        'anatomy': anatomy,
        'stems_route': route,
        'selected_stems_node': selected,
        'error': None if ready else (
            anatomy.get('error')
            if not anatomy.get('ready')
            else 'No Demucs-capable GPU route is currently available.'
        ),
    }


@app.post('/api/studio/analyze')
async def analyze_for_studio(
    file: UploadFile = File(...),
    track_id: str = Form(...),
    source_version: str = Form(...),
) -> dict[str, Any]:
    """Build the PHASE 5 envelope without retaining the canonical audio."""
    if settings.node_role == 'gpu-worker':
        raise HTTPException(status_code=409, detail='Studio analysis must run on the coordinator.')
    try:
        canonical_track_id = parse_track_id(track_id)
        canonical_source_version = parse_source_version(source_version)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    filename, suffix = main_module._validate_upload(file)
    if not all(main_module.check_ffmpeg().values()):
        raise HTTPException(status_code=503, detail='FFmpeg/ffprobe is not available on the SonicTrace coordinator.')

    temp_path: Path | None = None
    warnings: list[str] = []
    mastering: dict[str, Any] | None = None
    neural: dict[str, Any] | None = None
    structure: dict[str, Any] | None = None
    stems_summary: dict[str, Any] | None = None
    provenance: dict[str, Any] = {}
    fusion_version: str | None = None
    try:
        temp_path = await main_module._save_upload(file, suffix)
        metadata = await asyncio.to_thread(main_module.probe_audio, temp_path)
        loudness, levels = await asyncio.gather(
            asyncio.to_thread(main_module.analyze_loudness, temp_path),
            asyncio.to_thread(main_module.analyze_levels, temp_path),
        )
        mastering = {'file': {'name': filename, **metadata}, 'loudness': loudness, 'levels': levels}
        provenance.update({'mastering.file': 'measured', 'mastering.loudness': 'measured', 'mastering.levels': 'measured'})

        neural_status = main_module.neural_runtime_status()
        if neural_status.get('ready'):
            try:
                neural = await asyncio.to_thread(main_module.analyze_neural, temp_path, metadata.get('duration_seconds'))
                provenance['neural'] = 'neural'
            except Exception as exc:  # noqa: BLE001
                warnings.append(f'Neural layer unavailable: {exc}')
                provenance['neural'] = 'unavailable'
        else:
            warnings.append(str(neural_status.get('error') or 'Neural runtime is not ready.'))
            provenance['neural'] = 'unavailable'

        anatomy_status = anatomy_runtime_status(deep=False)
        anatomy_result: dict[str, Any] | None = None
        if anatomy_status.get('ready'):
            try:
                anatomy_result = await asyncio.to_thread(analyze_anatomy, temp_path)
                structure = anatomy_result
                provenance['structure'] = 'signal-derived+heuristic-labels'
            except Exception as exc:  # noqa: BLE001
                warnings.append(f'Song Anatomy layer unavailable: {exc}')
        else:
            warnings.append(str(anatomy_status.get('error') or 'Song Anatomy runtime is not ready.'))

        if anatomy_result is not None:
            try:
                route_info = await main_module.route_task('demucs')
                if route_info.get('selected'):
                    stems_payload = await _run_routed_stems(temp_path, filename, route_info)
                    separation = stems_payload.get('separation') or {}
                    structure = await asyncio.to_thread(fuse_anatomy_stems, anatomy_result, separation)
                    fusion_version = str(structure.get('engine', {}).get('version') or '') or None
                    stems_summary = {
                        'model': separation.get('model'),
                        'stemCount': separation.get('stem_count'),
                        'activityFormat': separation.get('activity_format'),
                        'compute': stems_payload.get('compute') or {},
                    }
                    provenance['structure'] = 'V2-C signal + V2-D Demucs fusion'
                    provenance['stemsSummary'] = 'measured-from-temporary-stems'
                else:
                    warnings.append('No Demucs-capable GPU route is online; V2-C structure was retained without stem fusion.')
            except Exception as exc:  # noqa: BLE001
                warnings.append(f'Stem/fusion layer unavailable: {exc}')

        return build_analysis_envelope(
            track_id=canonical_track_id,
            source_version=canonical_source_version,
            engine_version={
                'apiSchema': API_SCHEMA,
                'appVersion': settings.version,
                'nodeName': settings.node_name,
                'nodeRole': settings.node_role,
                'neuralModel': neural.get('engine', {}).get('model') if neural else None,
                'fusionVersion': fusion_version,
            },
            mastering=mastering,
            neural=neural,
            structure=structure,
            stems_summary=stems_summary,
            provenance=provenance,
            warnings=warnings,
        )
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f'Studio SonicTrace analysis failed: {exc}') from exc
    finally:
        await file.close()
        main_module._delete_temp(temp_path)


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


@app.post('/api/fusion')
async def analyze_song_fusion(file: UploadFile = File(...)) -> dict[str, Any]:
    if settings.node_role == 'gpu-worker':
        raise HTTPException(status_code=409, detail='V2-CD Fusion must run on the coordinator.')

    filename, suffix = main_module._validate_upload(file)
    anatomy_status = anatomy_runtime_status(deep=False)
    if not anatomy_status.get('ready'):
        raise HTTPException(status_code=503, detail=anatomy_status.get('error') or 'Song Anatomy runtime is not ready.')

    route_info = await main_module.route_task('demucs')
    if not route_info.get('selected'):
        raise HTTPException(status_code=503, detail='No Demucs-capable GPU is currently available for V2-CD Fusion.')

    temp_path: Path | None = None
    try:
        temp_path = await main_module._save_upload(file, suffix)
        metadata = main_module.probe_audio(temp_path)

        anatomy_task = asyncio.to_thread(analyze_anatomy, temp_path)
        stems_task = _run_routed_stems(temp_path, filename, route_info)
        anatomy_result, stems_payload = await asyncio.gather(anatomy_task, stems_task)

        separation = stems_payload.get('separation') or {}
        fusion = await asyncio.to_thread(fuse_anatomy_stems, anatomy_result, separation)

        return {
            'schema_version': API_SCHEMA,
            'fusion_schema_version': fusion.get('engine', {}).get('version', '2.4'),
            'file': {'name': filename, **metadata},
            'compute': {
                'coordinator': settings.node_name,
                'anatomy_route': 'local-coordinator',
                'stems_node': stems_payload.get('compute', {}).get('node_name'),
                'stems_device': separation.get('device'),
                'stems_route': stems_payload.get('compute', {}).get('route'),
                'stems_elapsed_seconds': separation.get('elapsed_seconds'),
            },
            'routing': stems_payload.get('routing') or route_info,
            'fusion': fusion,
            'source_summary': {
                'anatomy': anatomy_result.get('summary') or {},
                'stems': {
                    'model': separation.get('model'),
                    'stem_count': separation.get('stem_count'),
                    'activity_format': separation.get('activity_format'),
                },
            },
            'privacy': main_module._privacy_payload(),
        }
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f'V2-CD Fusion failed: {exc}') from exc
    finally:
        await file.close()
        main_module._delete_temp(temp_path)


async def _run_routed_stems(path: Path, filename: str, route_info: dict[str, Any]) -> dict[str, Any]:
    selected = route_info.get('selected') or {}
    selected_url = str(selected.get('url') or '')

    if not selected.get('local') and selected_url.startswith('http'):
        try:
            remote = await main_module._forward_stems_to_worker(selected_url, path, filename)
            remote['routing'] = route_info
            remote.setdefault('compute', {})['route'] = 'lan-worker'
            return remote
        except Exception as exc:  # noqa: BLE001
            local_status = main_module.stems_runtime_status()
            if not local_status.get('ready'):
                raise RuntimeError(f'LAN worker failed and local fallback is unavailable: {exc}') from exc
            fallback = await asyncio.to_thread(main_module.separate_and_analyze, path)
            return {
                'schema_version': API_SCHEMA,
                'file': {'name': filename, **main_module.probe_audio(path)},
                'compute': {
                    'node_name': settings.node_name,
                    'node_role': settings.node_role,
                    'route': 'local-fallback',
                    'worker_error': str(exc),
                },
                'routing': route_info,
                'separation': fallback,
                'privacy': main_module._privacy_payload(),
            }

    local_status = main_module.stems_runtime_status()
    if not local_status.get('ready'):
        raise RuntimeError(local_status.get('error') or 'Local Demucs runtime is not ready.')
    local = await asyncio.to_thread(main_module.separate_and_analyze, path)
    return {
        'schema_version': API_SCHEMA,
        'file': {'name': filename, **main_module.probe_audio(path)},
        'compute': {
            'node_name': settings.node_name,
            'node_role': settings.node_role,
            'route': 'local',
        },
        'routing': route_info,
        'separation': local,
        'privacy': main_module._privacy_payload(),
    }
