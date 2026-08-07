from __future__ import annotations

import asyncio
from typing import Any

import httpx

from .config import settings


async def inspect_workers() -> list[dict[str, Any]]:
    if not settings.worker_urls:
        return []

    async with httpx.AsyncClient(timeout=settings.worker_timeout_seconds) as client:
        results = await asyncio.gather(
            *[_inspect_worker(client, url) for url in settings.worker_urls],
            return_exceptions=False,
        )
    return results


async def _inspect_worker(client: httpx.AsyncClient, url: str) -> dict[str, Any]:
    try:
        response = await client.get(f'{url}/api/health')
        response.raise_for_status()
        payload = response.json()
        return {
            'url': url,
            'online': True,
            'node_name': payload.get('node_name'),
            'node_role': payload.get('node_role'),
            'gpus': payload.get('gpus', []),
            'version': payload.get('version'),
        }
    except Exception as exc:  # noqa: BLE001 - surfaced as worker health state
        return {
            'url': url,
            'online': False,
            'error': str(exc),
            'gpus': [],
        }
