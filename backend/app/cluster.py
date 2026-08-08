from __future__ import annotations

import asyncio
import ipaddress
import socket
import time
from typing import Any

import httpx

from .config import settings

_DISCOVERY_CACHE: tuple[float, list[str]] = (0.0, [])


async def inspect_workers() -> list[dict[str, Any]]:
    urls = list(settings.worker_urls)
    if settings.discover_workers and settings.node_role != 'gpu-worker':
        urls.extend(await discover_worker_urls())

    urls = list(dict.fromkeys(url.rstrip('/') for url in urls if url))
    if not urls:
        return []

    timeout = httpx.Timeout(max(settings.worker_timeout_seconds, 2.5))
    async with httpx.AsyncClient(timeout=timeout) as client:
        results = await asyncio.gather(
            *[_inspect_worker(client, url, configured=url in settings.worker_urls) for url in urls],
            return_exceptions=False,
        )
    return results


async def discover_worker_urls(force: bool = False) -> list[str]:
    global _DISCOVERY_CACHE
    now = time.monotonic()
    cached_at, cached_urls = _DISCOVERY_CACHE
    if not force and cached_urls and now - cached_at < settings.discovery_cache_seconds:
        return list(cached_urls)

    local_ips = _private_ipv4_addresses()
    if not local_ips:
        _DISCOVERY_CACHE = (now, [])
        return []

    network = ipaddress.ip_network(f'{local_ips[0]}/24', strict=False)
    own = set(local_ips)
    semaphore = asyncio.Semaphore(64)

    async def probe(ip: str) -> str | None:
        if ip in own:
            return None
        async with semaphore:
            try:
                _reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, settings.worker_port),
                    timeout=settings.discovery_connect_timeout_seconds,
                )
                writer.close()
                await writer.wait_closed()
                return f'http://{ip}:{settings.worker_port}'
            except (OSError, asyncio.TimeoutError):
                return None

    probes = await asyncio.gather(*(probe(str(host)) for host in network.hosts()))
    candidates = [url for url in probes if url]

    verified: list[str] = []
    # /api/live deliberately avoids Torch/Demucs imports, so a sub-second
    # discovery timeout is realistic again even on a busy GPU worker.
    timeout = httpx.Timeout(max(settings.discovery_http_timeout_seconds, 0.9))
    async with httpx.AsyncClient(timeout=timeout) as client:
        checks = await asyncio.gather(*[_is_lmn_worker(client, url) for url in candidates])
    for url, valid in zip(candidates, checks, strict=True):
        if valid:
            verified.append(url)

    _DISCOVERY_CACHE = (now, verified)
    return verified


async def _is_lmn_worker(client: httpx.AsyncClient, url: str) -> bool:
    try:
        response = await client.get(f'{url}/api/live')
        if response.status_code != 200:
            return False
        payload = response.json()
        return (
            str(payload.get('service', '')).startswith('LMNotebook')
            and payload.get('node_role') == 'gpu-worker'
        )
    except Exception:  # noqa: BLE001
        return False


async def _inspect_worker(client: httpx.AsyncClient, url: str, configured: bool) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        response = await client.get(f'{url}/api/live')
        response.raise_for_status()
        payload = response.json()
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {
            'url': url,
            'online': True,
            'source': 'configured' if configured else 'autodiscovered',
            'latency_ms': latency_ms,
            'node_name': payload.get('node_name'),
            'node_role': payload.get('node_role'),
            'gpus': payload.get('gpus', []),
            'version': payload.get('version'),
            'api_schema': payload.get('api_schema'),
            'neural': payload.get('neural'),
            'stems': payload.get('stems'),
            'health_mode': payload.get('health_mode'),
        }
    except Exception as exc:  # noqa: BLE001
        return {
            'url': url,
            'online': False,
            'source': 'configured' if configured else 'autodiscovered',
            'latency_ms': None,
            'error': str(exc),
            'gpus': [],
        }


def _private_ipv4_addresses() -> list[str]:
    addresses: list[str] = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            address = info[4][0]
            ip = ipaddress.ip_address(address)
            if ip.is_private and not ip.is_loopback and address not in addresses:
                addresses.append(address)
    except OSError:
        pass
    return addresses
