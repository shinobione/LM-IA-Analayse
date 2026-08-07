from __future__ import annotations

import os
from dataclasses import dataclass


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip().rstrip('/') for item in value.split(',') if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv('LMN_APP_NAME', 'LMNotebook Deep Audio API')
    version: str = os.getenv('LMN_VERSION', '2.0.0-alpha')
    node_name: str = os.getenv('LMN_NODE_NAME', 'RTX3060-PRIMARY')
    node_role: str = os.getenv('LMN_NODE_ROLE', 'coordinator')
    allowed_origins: tuple[str, ...] = tuple(
        _csv(os.getenv('LMN_ALLOWED_ORIGINS'))
        or [
            'https://shinobione.github.io',
            'http://127.0.0.1:5500',
            'http://localhost:5500',
            'http://127.0.0.1:8008',
            'http://localhost:8008',
        ]
    )
    worker_urls: tuple[str, ...] = tuple(_csv(os.getenv('LMN_WORKERS')))
    max_upload_mb: int = int(os.getenv('LMN_MAX_UPLOAD_MB', '250'))
    ffmpeg_bin: str = os.getenv('LMN_FFMPEG_BIN', 'ffmpeg')
    ffprobe_bin: str = os.getenv('LMN_FFPROBE_BIN', 'ffprobe')
    worker_timeout_seconds: float = float(os.getenv('LMN_WORKER_TIMEOUT_SECONDS', '2.5'))


settings = Settings()
