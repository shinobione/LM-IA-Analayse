from __future__ import annotations

from typing import Any

from .cluster import inspect_workers
from .config import settings
from .gpu import detect_nvidia_gpus


TASKS: dict[str, dict[str, Any]] = {
    'genre-mood': {'min_vram_mb': 3500, 'preferred_vram_mb': 5500},
    'embeddings': {'min_vram_mb': 3000, 'preferred_vram_mb': 5000},
    'instruments': {'min_vram_mb': 3500, 'preferred_vram_mb': 5500},
    'demucs': {'min_vram_mb': 5500, 'preferred_vram_mb': 7000},
    'transcription': {'min_vram_mb': 5000, 'preferred_vram_mb': 8000},
    'large-model': {'min_vram_mb': 9500, 'preferred_vram_mb': 11000},
}


async def route_task(task: str) -> dict[str, Any]:
    if task not in TASKS:
        return {
            'task': task,
            'routable': False,
            'reason': f'Unknown task. Supported: {", ".join(sorted(TASKS))}',
        }

    requirement = TASKS[task]
    candidates: list[dict[str, Any]] = []

    for gpu in detect_nvidia_gpus():
        candidates.append(
            _candidate(
                task=task,
                node_name=settings.node_name,
                node_role=settings.node_role,
                url='local',
                gpu=gpu,
                requirement=requirement,
                local=True,
            )
        )

    workers = await inspect_workers()
    for worker in workers:
        if not worker.get('online'):
            continue
        for gpu in worker.get('gpus', []):
            candidates.append(
                _candidate(
                    task=task,
                    node_name=worker.get('node_name') or worker.get('url') or 'worker',
                    node_role=worker.get('node_role') or 'gpu-worker',
                    url=worker.get('url') or '',
                    gpu=gpu,
                    requirement=requirement,
                    local=False,
                )
            )

    viable = [candidate for candidate in candidates if candidate['fits']]
    viable.sort(key=lambda candidate: candidate['score'], reverse=True)

    return {
        'task': task,
        'requirement': requirement,
        'routable': bool(viable),
        'selected': viable[0] if viable else None,
        'candidates': candidates,
        'routing_policy': 'VRAM fit first; then free VRAM; coordinator locality is a small tie-breaker.',
    }


def _candidate(
    *,
    task: str,
    node_name: str,
    node_role: str,
    url: str,
    gpu: dict[str, Any],
    requirement: dict[str, Any],
    local: bool,
) -> dict[str, Any]:
    total = int(gpu.get('memory_total_mb') or 0)
    free = int(gpu.get('memory_free_mb') or 0)
    minimum = int(requirement['min_vram_mb'])
    preferred = int(requirement['preferred_vram_mb'])
    fits = total >= minimum and free >= min(minimum, int(total * 0.8))

    score = 0.0
    if fits:
        score += 100
        score += min(total / preferred, 1.5) * 25
        score += min(free / max(total, 1), 1.0) * 35
        if local:
            score += 4
        if task == 'large-model' and total >= 11000:
            score += 25
        if task == 'demucs' and total < 11000:
            # Keep the 12 GB card freer for larger models when an 8 GB worker fits.
            score += 8

    return {
        'node_name': node_name,
        'node_role': node_role,
        'url': url,
        'local': local,
        'gpu_index': gpu.get('index'),
        'gpu_name': gpu.get('name'),
        'memory_total_mb': total,
        'memory_free_mb': free,
        'fits': fits,
        'score': round(score, 2),
    }
