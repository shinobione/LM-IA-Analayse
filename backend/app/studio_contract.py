from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

TRACK_ID_RE = re.compile(r'^[a-z0-9][a-z0-9-]{0,119}$')
CONTRACT_SCHEMA_VERSION = 1


def parse_track_id(value: str) -> str:
    track_id = str(value or '').strip()
    if not TRACK_ID_RE.fullmatch(track_id):
        raise ValueError('trackId must be the canonical lower-case kebab-case slug.')
    return track_id


def parse_source_version(value: str | dict[str, Any]) -> dict[str, Any]:
    payload: Any = value
    if isinstance(value, str):
        try:
            payload = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError('sourceVersion must be valid JSON.') from exc
    if not isinstance(payload, dict):
        raise ValueError('sourceVersion must be an object.')
    kind = str(payload.get('kind') or '').strip()
    revision = str(payload.get('value') or '').strip()
    size = payload.get('sizeBytes')
    if not kind or not revision or not isinstance(size, (int, float)) or int(size) < 1:
        raise ValueError('sourceVersion requires kind, value and positive sizeBytes.')
    return {
        'kind': kind,
        'value': revision,
        'sizeBytes': int(size),
        'filename': str(payload.get('filename') or ''),
        'uploadedAt': payload.get('uploadedAt'),
    }


def semantic_summary(neural: dict[str, Any] | None, structure: dict[str, Any] | None) -> dict[str, Any]:
    neural = neural or {}
    structure = structure or {}

    def ranked(name: str, limit: int) -> list[dict[str, Any]]:
        values = neural.get(name)
        return list(values[:limit]) if isinstance(values, list) else []

    summary = structure.get('summary') if isinstance(structure.get('summary'), dict) else {}
    genre_analysis = neural.get('genre_analysis') if isinstance(neural.get('genre_analysis'), dict) else None
    return {
        'topGenres': ranked('genres', 5),
        'topMoods': ranked('moods', 5),
        'topInstruments': ranked('instruments', 6),
        'genreAnalysis': genre_analysis,
        'traits': neural.get('traits') if isinstance(neural.get('traits'), dict) else {},
        'arrangement': summary,
        'hookCount': len(structure.get('hooks') or []),
        'climax': structure.get('climax'),
    }


def mastering_warnings(mastering: dict[str, Any] | None) -> list[str]:
    """Translate measurement-level degradation into durable, user-readable warnings."""
    if not isinstance(mastering, dict):
        return []
    warnings: list[str] = []
    for key, label in (('loudness', 'Mastering loudness'), ('levels', 'Mastering levels')):
        payload = mastering.get(key)
        if not isinstance(payload, dict) or payload.get('provenance') != 'unavailable':
            continue
        detail = str(payload.get('error') or 'measurement unavailable').strip()
        warnings.append(f'{label} unavailable: {detail}')
    return warnings


def normalize_mastering_provenance(mastering: dict[str, Any] | None, provenance: dict[str, Any]) -> None:
    if not isinstance(mastering, dict):
        return
    for key in ('loudness', 'levels'):
        payload = mastering.get(key)
        if isinstance(payload, dict) and payload.get('provenance'):
            provenance[f'mastering.{key}'] = str(payload['provenance'])


def build_analysis_envelope(
    *,
    track_id: str,
    source_version: dict[str, Any],
    engine_version: dict[str, Any],
    mastering: dict[str, Any] | None,
    neural: dict[str, Any] | None,
    structure: dict[str, Any] | None,
    stems_summary: dict[str, Any] | None,
    provenance: dict[str, Any],
    warnings: list[str],
) -> dict[str, Any]:
    track_id = parse_track_id(track_id)
    source_version = parse_source_version(source_version)
    embedding = neural.get('embedding') if isinstance(neural, dict) else None
    if embedding is not None:
        vector = embedding.get('vector') if isinstance(embedding, dict) else None
        if not isinstance(vector, list) or len(vector) != 512:
            warnings.append('Neural embedding was omitted because it is not exactly 512-dimensional.')
            embedding = None
    warnings.extend(mastering_warnings(mastering))
    normalize_mastering_provenance(mastering, provenance)
    return {
        'schemaVersion': CONTRACT_SCHEMA_VERSION,
        'analysisId': f'sta-{uuid4()}',
        'trackId': track_id,
        'sourceVersion': source_version,
        'analyzedAt': datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
        'engineVersion': engine_version,
        'dsp': None,
        'mastering': mastering,
        'neural': neural,
        'embedding': embedding,
        'structure': structure,
        'semanticSummary': semantic_summary(neural, structure),
        'stemsSummary': stems_summary,
        'provenance': provenance,
        'warnings': list(dict.fromkeys(str(item) for item in warnings if item)),
        'privacy': {
            'audioStored': False,
            'temporaryProcessingOnly': True,
        },
    }
