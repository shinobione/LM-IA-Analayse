from __future__ import annotations

import json
import os
import threading
import urllib.request
from pathlib import Path
from typing import Any

from .config import settings

EXPERT_VERSION = '3.1'
EXPERT_MODE = os.getenv('LMN_MUSIC_EXPERT', 'auto').strip().lower()
MODEL_NAME = 'discogs-effnet-bsdynamic-1.onnx'
METADATA_NAME = 'discogs-effnet-bsdynamic-1.json'
MODEL_URL = f'https://essentia.upf.edu/models/feature-extractors/discogs-effnet/{MODEL_NAME}'
METADATA_URL = f'https://essentia.upf.edu/models/feature-extractors/discogs-effnet/{METADATA_NAME}'
MODEL_EXPECTED_BYTES = 18_027_718
SAMPLE_RATE = 16_000
FRAME_SIZE = 512
HOP_SIZE = 256
MEL_BANDS = 96
PATCH_SIZE = 128
PATCH_HOP = 62
MODEL_DIR = Path(os.getenv('LMN_MODEL_DIR') or (Path(__file__).resolve().parents[1] / 'models'))

_session: Any | None = None
_session_lock = threading.Lock()
_metadata: dict[str, Any] | None = None
_metadata_lock = threading.Lock()


def runtime_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        'enabled': EXPERT_MODE not in {'0', 'false', 'off', 'disabled'},
        'mode': EXPERT_MODE,
        'version': EXPERT_VERSION,
        'model': MODEL_NAME,
        'model_cached': (MODEL_DIR / MODEL_NAME).is_file(),
        'metadata_cached': (MODEL_DIR / METADATA_NAME).is_file(),
        'ready': False,
    }
    if not status['enabled']:
        status['reason'] = 'disabled by LMN_MUSIC_EXPERT'
        return status
    try:
        import onnxruntime as ort
    except Exception as exc:  # noqa: BLE001
        status['reason'] = f'onnxruntime unavailable: {exc}'
        return status
    status['onnxruntime_version'] = getattr(ort, '__version__', None)
    try:
        status['available_providers'] = list(ort.get_available_providers())
    except Exception:  # noqa: BLE001
        status['available_providers'] = []
    status['ready'] = True
    return status


def analyze_music_expert(
    segments: list[Any],
    offsets: list[float],
    *,
    input_sample_rate: int,
) -> dict[str, Any]:
    """Run a music-specialist Discogs400 expert without becoming a hard dependency.

    The caller may catch exceptions and continue with CLAP-only analysis. Model and
    metadata files are downloaded from the official Essentia model host on first use
    and cached under backend/models (gitignored).
    """
    if EXPERT_MODE in {'0', 'false', 'off', 'disabled'}:
        return {'status': 'disabled', 'engine': {'name': 'Discogs-EffNet', 'version': EXPERT_VERSION}}
    if not segments:
        raise RuntimeError('Discogs expert received no audio segments.')

    metadata = _load_metadata()
    classes = list(metadata.get('classes') or [])
    if len(classes) != 400:
        raise RuntimeError(f'Discogs metadata must expose 400 classes, found {len(classes)}.')

    session, provider = _load_session()
    input_name = session.get_inputs()[0].name
    output_meta = session.get_outputs()
    prediction_name = _find_output_name(output_meta, 400)
    embedding_name = _find_output_name(output_meta, 1280)

    import numpy as np
    import librosa

    segment_results: list[dict[str, Any]] = []
    all_predictions: list[Any] = []
    all_embeddings: list[Any] = []

    for index, source in enumerate(segments):
        audio = np.asarray(source, dtype=np.float32)
        if input_sample_rate != SAMPLE_RATE:
            audio = librosa.resample(audio, orig_sr=input_sample_rate, target_sr=SAMPLE_RATE, res_type='soxr_hq')
            audio = np.asarray(audio, dtype=np.float32)
        patches = _musicnn_patches(audio)
        if patches.shape[0] == 0:
            continue
        outputs = session.run([prediction_name, embedding_name], {input_name: patches})
        predictions = np.asarray(outputs[0], dtype=np.float32)
        embeddings = np.asarray(outputs[1], dtype=np.float32)
        if predictions.ndim != 2 or predictions.shape[1] != 400:
            raise RuntimeError(f'Unexpected Discogs prediction shape: {predictions.shape!r}')
        if embeddings.ndim != 2 or embeddings.shape[1] != 1280:
            raise RuntimeError(f'Unexpected Discogs embedding shape: {embeddings.shape!r}')

        mean_prediction = predictions.mean(axis=0)
        mean_embedding = embeddings.mean(axis=0)
        segment_results.append({
            'index': index,
            'offset_seconds': offsets[index] if index < len(offsets) else None,
            'patch_count': int(predictions.shape[0]),
            'top_styles': _rank_predictions(classes, mean_prediction, limit=5),
        })
        all_predictions.append(mean_prediction)
        all_embeddings.append(mean_embedding)

    if not all_predictions:
        raise RuntimeError('Discogs expert could not produce any valid patches.')

    track_prediction = np.stack(all_predictions, axis=0).mean(axis=0)
    track_embedding = np.stack(all_embeddings, axis=0).mean(axis=0)
    norm = float(np.linalg.norm(track_embedding))
    if norm > 1e-12:
        track_embedding = track_embedding / norm

    top_styles = _rank_predictions(classes, track_prediction, limit=20)
    families = _aggregate_families(classes, track_prediction)

    return {
        'status': 'ready',
        'engine': {
            'name': 'Discogs-EffNet',
            'version': EXPERT_VERSION,
            'provider': provider,
            'model': MODEL_NAME,
            'framework': 'ONNX Runtime',
            'class_count': len(classes),
            'sample_rate': SAMPLE_RATE,
            'frame_size': FRAME_SIZE,
            'hop_size': HOP_SIZE,
            'mel_bands': MEL_BANDS,
            'patch_size': PATCH_SIZE,
            'patch_hop': PATCH_HOP,
        },
        'top_styles': top_styles,
        'families': families[:12],
        'segments': segment_results,
        'embedding': {
            'model': 'discogs-effnet-bsdynamic-1',
            'dimension': 1280,
            'vector': [round(float(value), 7) for value in track_embedding.tolist()],
        },
        'provenance': {
            'type': 'music-specialist-neural',
            'dataset': str((metadata.get('dataset') or {}).get('name') or 'Discogs-4M'),
            'model_source': MODEL_URL,
            'metadata_source': METADATA_URL,
            'preprocessing': 'Essentia TensorflowInputMusiCNN-compatible: 16kHz, 512 frame, 256 hop, 96 Slaney mel bands, log10(1 + 10000*x), 128-frame patches / 62-frame hop',
            'score_note': 'Discogs style outputs are multi-label sigmoid model scores; they do not establish geographic/cultural metadata facts.',
        },
    }


def _musicnn_patches(audio: Any) -> Any:
    """Reproduce the documented MusiCNN input geometry used by EffNetDiscogs."""
    import numpy as np
    import librosa

    y = np.asarray(audio, dtype=np.float32)
    if y.ndim != 1:
        y = np.mean(y, axis=-1, dtype=np.float32)
    if y.size < FRAME_SIZE:
        return np.empty((0, PATCH_SIZE, MEL_BANDS), dtype=np.float32)

    stft = librosa.stft(
        y,
        n_fft=FRAME_SIZE,
        hop_length=HOP_SIZE,
        win_length=FRAME_SIZE,
        window='hann',
        center=True,
        pad_mode='constant',
    )
    magnitude = np.abs(stft).astype(np.float32, copy=False)
    mel_filter = librosa.filters.mel(
        sr=SAMPLE_RATE,
        n_fft=FRAME_SIZE,
        n_mels=MEL_BANDS,
        fmin=0.0,
        fmax=SAMPLE_RATE / 2,
        htk=False,
        norm='slaney',
        dtype=np.float32,
    )
    mel = mel_filter @ magnitude
    bands = np.log10(1.0 + 10000.0 * np.maximum(mel, 0.0)).T.astype(np.float32, copy=False)

    starts = range(0, max(0, bands.shape[0] - PATCH_SIZE + 1), PATCH_HOP)
    patches = [bands[start:start + PATCH_SIZE] for start in starts]
    if not patches:
        return np.empty((0, PATCH_SIZE, MEL_BANDS), dtype=np.float32)
    return np.stack(patches, axis=0).astype(np.float32, copy=False)


def _rank_predictions(classes: list[str], values: Any, *, limit: int) -> list[dict[str, Any]]:
    indexed = sorted(enumerate(values), key=lambda item: float(item[1]), reverse=True)
    result: list[dict[str, Any]] = []
    for class_index, value in indexed[:limit]:
        label = classes[class_index]
        family, style = _split_discogs_label(label)
        score = max(0.0, min(1.0, float(value)))
        result.append({
            'label': label,
            'discogs_family': family,
            'style': style,
            'family': _map_discogs_family(family),
            'score': round(score, 5),
            'percent': round(score * 100.0, 1),
            'score_kind': 'discogs400-sigmoid',
        })
    return result


def _aggregate_families(classes: list[str], values: Any) -> list[dict[str, Any]]:
    by_family: dict[str, list[float]] = {}
    for label, value in zip(classes, values, strict=True):
        discogs_family, _ = _split_discogs_label(label)
        family = _map_discogs_family(discogs_family)
        by_family.setdefault(family, []).append(float(value))

    rows: list[dict[str, Any]] = []
    for family, scores in by_family.items():
        top = sorted(scores, reverse=True)[:3]
        score = sum(top) / max(1, len(top))
        rows.append({
            'label': family,
            'score': round(score, 5),
            'percent': round(max(0.0, min(1.0, score)) * 100.0, 1),
            'score_kind': 'mean-top3-discogs400-sigmoid',
        })
    rows.sort(key=lambda item: float(item['score']), reverse=True)
    return rows


def _split_discogs_label(label: str) -> tuple[str, str]:
    if '---' not in label:
        return label, label
    family, style = label.split('---', 1)
    return family, style


def _map_discogs_family(family: str) -> str:
    return {
        'Hip Hop': 'Hip-Hop / Rap',
        'Funk / Soul': 'R&B / Soul / Funk',
        'Electronic': 'Electronic',
        'Pop': 'Pop',
        'Folk, World, & Country': 'Folk / World',
        'Reggae': 'Reggae / Caribbean',
        'Latin': 'Latin',
        'Rock': 'Rock / Metal',
        'Jazz': 'Jazz / Blues',
        'Blues': 'Jazz / Blues',
        'Classical': 'Classical / Screen',
        'Stage & Screen': 'Classical / Screen',
        'Brass & Military': 'Folk / World',
        'Non-Music': 'Non-Music',
        "Children's": 'Other',
    }.get(family, family)


def _load_session() -> tuple[Any, str]:
    global _session
    if _session is not None:
        providers = getattr(_session, 'get_providers', lambda: [])()
        return _session, providers[0] if providers else 'unknown'

    with _session_lock:
        if _session is not None:
            providers = getattr(_session, 'get_providers', lambda: [])()
            return _session, providers[0] if providers else 'unknown'

        model_path = _ensure_cached_file(MODEL_URL, MODEL_DIR / MODEL_NAME, expected_bytes=MODEL_EXPECTED_BYTES)
        import onnxruntime as ort

        # ORT can reuse CUDA/cuDNN DLLs shipped with the existing PyTorch install.
        preload = getattr(ort, 'preload_dlls', None)
        if callable(preload):
            try:
                preload(directory='')
            except Exception:  # noqa: BLE001
                pass
        available = list(ort.get_available_providers())
        preferred = [name for name in ('CUDAExecutionProvider', 'CPUExecutionProvider') if name in available]
        if not preferred:
            preferred = available or ['CPUExecutionProvider']
        _session = ort.InferenceSession(str(model_path), providers=preferred)
        active = _session.get_providers()
        return _session, active[0] if active else 'unknown'


def _load_metadata() -> dict[str, Any]:
    global _metadata
    if _metadata is not None:
        return _metadata
    with _metadata_lock:
        if _metadata is not None:
            return _metadata
        path = _ensure_cached_file(METADATA_URL, MODEL_DIR / METADATA_NAME, minimum_bytes=10_000)
        payload = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(payload, dict):
            raise RuntimeError('Discogs metadata payload is not an object.')
        _metadata = payload
        return payload


def _ensure_cached_file(
    url: str,
    path: Path,
    *,
    expected_bytes: int | None = None,
    minimum_bytes: int | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_file() and _valid_size(path, expected_bytes=expected_bytes, minimum_bytes=minimum_bytes):
        return path

    temporary = path.with_suffix(path.suffix + '.download')
    if temporary.exists():
        temporary.unlink()
    request = urllib.request.Request(url, headers={'User-Agent': f'SonicTrace/{EXPERT_VERSION}'})
    try:
        with urllib.request.urlopen(request, timeout=90) as response, temporary.open('wb') as output:  # noqa: S310
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                output.write(chunk)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    if not _valid_size(temporary, expected_bytes=expected_bytes, minimum_bytes=minimum_bytes):
        size = temporary.stat().st_size if temporary.exists() else 0
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f'Downloaded model asset has unexpected size: {size} bytes.')
    temporary.replace(path)
    return path


def _valid_size(path: Path, *, expected_bytes: int | None, minimum_bytes: int | None) -> bool:
    try:
        size = path.stat().st_size
    except OSError:
        return False
    if expected_bytes is not None and size != expected_bytes:
        return False
    if minimum_bytes is not None and size < minimum_bytes:
        return False
    return size > 0


def _find_output_name(outputs: list[Any], final_dimension: int) -> str:
    for output in outputs:
        shape = list(getattr(output, 'shape', []) or [])
        if shape and shape[-1] == final_dimension:
            return str(output.name)
    raise RuntimeError(f'Discogs ONNX model has no output ending in dimension {final_dimension}.')
