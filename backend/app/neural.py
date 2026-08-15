from __future__ import annotations

import math
import os
import subprocess
import threading
from pathlib import Path
from typing import Any, Iterable

from .config import settings
from .neural_taxonomy import (
    GENRE_CANDIDATES,
    INSTRUMENT_LABELS,
    MOOD_LABELS,
    TAXONOMY_VERSION,
    confidence_policy,
)

MODEL_ID = os.getenv('LMN_NEURAL_MODEL', 'laion/clap-htsat-unfused')
SAMPLE_RATE = 48_000
SEGMENT_SECONDS = float(os.getenv('LMN_NEURAL_SEGMENT_SECONDS', '10'))
MAX_SEGMENTS = int(os.getenv('LMN_NEURAL_MAX_SEGMENTS', '5'))
UNKNOWN_MIN_SIMILARITY = float(os.getenv('LMN_NEURAL_UNKNOWN_MIN_SIMILARITY', '0.10'))
NEURAL_ANALYSIS_VERSION = '3.0'

TRAIT_AXES = {
    'electronic': ('electronic production', 'acoustic production'),
    'vocal': ('vocal music', 'instrumental music'),
    'energy': ('high energy music', 'calm low energy music'),
    'brightness': ('bright crisp music', 'dark warm music'),
    'danceability': ('danceable groove', 'non-danceable free rhythm'),
    'aggression': ('aggressive hard music', 'soft gentle music'),
    'space': ('spacious atmospheric production', 'dry close production'),
}

_model: Any | None = None
_processor: Any | None = None
_device: str | None = None
_load_lock = threading.Lock()
_text_cache_lock = threading.Lock()
_text_feature_cache: dict[tuple[str, ...], Any] = {}


def runtime_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        'installed': False,
        'ready': False,
        'cuda_available': False,
        'model_id': MODEL_ID,
        'model_loaded': _model is not None,
        'device': _device,
        'analysis_version': NEURAL_ANALYSIS_VERSION,
        'taxonomy_version': TAXONOMY_VERSION,
        'genre_candidate_count': len(GENRE_CANDIDATES),
        'supports_unknown_genre': True,
        'segment_consensus': True,
    }
    try:
        import torch
        import transformers
    except Exception as exc:  # noqa: BLE001
        status['error'] = f'Neural dependencies unavailable: {exc}'
        return status

    status['installed'] = True
    status['torch_version'] = torch.__version__
    status['transformers_version'] = transformers.__version__
    status['cuda_runtime'] = torch.version.cuda
    status['cuda_available'] = bool(torch.cuda.is_available())
    status['cuda_device_count'] = int(torch.cuda.device_count()) if torch.cuda.is_available() else 0
    if torch.cuda.is_available():
        status['device_name'] = torch.cuda.get_device_name(0)
        props = torch.cuda.get_device_properties(0)
        status['vram_total_gb'] = round(props.total_memory / (1024 ** 3), 1)
        status['ready'] = True
    else:
        status['error'] = 'PyTorch is installed but CUDA is not available.'
    return status


def analyze_neural(path: Path, duration_seconds: float | None = None) -> dict[str, Any]:
    status = runtime_status()
    if not status.get('ready'):
        raise RuntimeError(status.get('error') or 'Neural runtime is not ready.')

    model, processor, device = _load_model()
    segments, offsets = _decode_segments(path, duration_seconds)
    if not segments:
        raise RuntimeError('Could not decode neural analysis segments.')

    import torch
    import torch.nn.functional as F

    audio_inputs = processor(
        audios=segments,
        sampling_rate=SAMPLE_RATE,
        return_tensors='pt',
        padding=True,
    )
    audio_inputs = {key: value.to(device) if hasattr(value, 'to') else value for key, value in audio_inputs.items()}

    with torch.inference_mode():
        audio_features = _feature_tensor(model.get_audio_features(**audio_inputs))
        audio_features = F.normalize(audio_features.float(), dim=-1)
        track_embedding = F.normalize(audio_features.mean(dim=0, keepdim=True), dim=-1)

    genre_analysis = _analyze_genres_v3(model, processor, audio_features, offsets, device)
    moods = _rank_open_labels(model, processor, track_embedding, MOOD_LABELS, device, 'music with a {} mood')
    instruments = _rank_open_labels(model, processor, track_embedding, INSTRUMENT_LABELS, device, 'music featuring {}')
    traits = _score_traits(model, processor, track_embedding, device)

    embedding = track_embedding[0].detach().cpu().tolist()
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated(0)
        reserved = torch.cuda.memory_reserved(0)
    else:
        allocated = reserved = 0

    return {
        'engine': {
            'model': MODEL_ID,
            'model_family': 'CLAP',
            'analysis_version': NEURAL_ANALYSIS_VERSION,
            'taxonomy_version': TAXONOMY_VERSION,
            'device': device,
            'device_name': status.get('device_name'),
            'torch_version': status.get('torch_version'),
            'cuda_runtime': status.get('cuda_runtime'),
            'segment_count': len(segments),
            'segment_seconds': SEGMENT_SECONDS,
            'segment_offsets_seconds': offsets,
            'gpu_memory_allocated_mb': round(allocated / (1024 ** 2), 1),
            'gpu_memory_reserved_mb': round(reserved / (1024 ** 2), 1),
        },
        # Compatibility fields remain in place for SonicTrace UI, Catalog and
        # the current Studio envelope. They now come from the V3 taxonomy rather
        # than the old forced 24-way softmax.
        'genres': genre_analysis['styles'][:8],
        'moods': moods[:8],
        'instruments': instruments[:10],
        'traits': traits,
        # Additive V3 payload for future Studio integration.
        'genre_analysis': genre_analysis,
        'embedding': {
            'model': MODEL_ID,
            'dimension': len(embedding),
            'vector': [round(float(value), 7) for value in embedding],
        },
        'provenance': {
            'type': 'neural',
            'method': 'CLAP open-vocabulary audio/text similarity with per-segment hierarchical consensus',
            'calibration': 'cosine relevance + temporal consensus; scores are not Spotify metrics or absolute probabilities',
            'genre_taxonomy': TAXONOMY_VERSION,
            'unknown_policy': 'low-evidence or unstable classifications can resolve to Unknown / hybrid',
        },
    }


def _analyze_genres_v3(
    model: Any,
    processor: Any,
    audio_features: Any,
    offsets: list[float],
    device: str,
) -> dict[str, Any]:
    prompts: list[str] = []
    prompt_owners: list[int] = []
    for candidate_index, candidate in enumerate(GENRE_CANDIDATES):
        for prompt in candidate.prompts:
            prompts.append(prompt)
            prompt_owners.append(candidate_index)

    text_features = _cached_text_features(model, processor, prompts, device)
    similarities = audio_features @ text_features.T
    segment_prompt_values = similarities.detach().cpu().tolist()

    candidate_segment_scores: list[list[float]] = [
        [0.0 for _ in range(len(GENRE_CANDIDATES))]
        for _ in range(len(segment_prompt_values))
    ]
    owner_prompt_indices: list[list[int]] = [[] for _ in GENRE_CANDIDATES]
    for prompt_index, owner in enumerate(prompt_owners):
        owner_prompt_indices[owner].append(prompt_index)

    for segment_index, prompt_values in enumerate(segment_prompt_values):
        for candidate_index, indices in enumerate(owner_prompt_indices):
            values = sorted((float(prompt_values[index]) for index in indices), reverse=True)
            take = values[: min(2, len(values))]
            candidate_segment_scores[segment_index][candidate_index] = sum(take) / max(1, len(take))

    candidate_track_scores = [
        sum(segment[candidate_index] for segment in candidate_segment_scores) / max(1, len(candidate_segment_scores))
        for candidate_index in range(len(GENRE_CANDIDATES))
    ]
    ranked_indices = sorted(
        range(len(GENRE_CANDIDATES)),
        key=lambda index: candidate_track_scores[index],
        reverse=True,
    )

    def style_row(index: int) -> dict[str, Any]:
        candidate = GENRE_CANDIDATES[index]
        similarity = float(candidate_track_scores[index])
        relevance = max(0.0, min(1.0, similarity))
        return {
            'label': candidate.label,
            'family': candidate.family,
            'region': candidate.region,
            'similarity': round(similarity, 5),
            'score': round(relevance, 5),
            'percent': round(relevance * 100.0, 1),
            'score_kind': 'clap-cosine-relevance',
            'provenance': 'neural-zero-shot-open-vocabulary-v3',
        }

    styles = [style_row(index) for index in ranked_indices]
    primary_index = ranked_indices[0]
    second_index = ranked_indices[1] if len(ranked_indices) > 1 else primary_index
    primary_candidate = GENRE_CANDIDATES[primary_index]

    segment_rows: list[dict[str, Any]] = []
    style_winner_count = 0
    family_winner_count = 0
    for segment_index, values in enumerate(candidate_segment_scores):
        ranked_segment = sorted(range(len(GENRE_CANDIDATES)), key=lambda index: values[index], reverse=True)
        winner_index = ranked_segment[0]
        winner = GENRE_CANDIDATES[winner_index]
        if winner_index == primary_index:
            style_winner_count += 1
        if winner.family == primary_candidate.family:
            family_winner_count += 1

        top = []
        for index in ranked_segment[:3]:
            candidate = GENRE_CANDIDATES[index]
            similarity = float(values[index])
            top.append({
                'label': candidate.label,
                'family': candidate.family,
                'region': candidate.region,
                'similarity': round(similarity, 5),
            })
        segment_rows.append({
            'index': segment_index,
            'offset_seconds': offsets[segment_index] if segment_index < len(offsets) else None,
            'winner': top[0],
            'top_styles': top,
        })

    segment_count = max(1, len(candidate_segment_scores))
    style_consensus = style_winner_count / segment_count
    family_consensus = family_winner_count / segment_count
    confidence = confidence_policy(
        primary_similarity=float(candidate_track_scores[primary_index]),
        second_similarity=float(candidate_track_scores[second_index]),
        style_consensus=style_consensus,
        family_consensus=family_consensus,
        minimum_similarity=UNKNOWN_MIN_SIMILARITY,
    )

    family_best: dict[str, tuple[float, int]] = {}
    for index, candidate in enumerate(GENRE_CANDIDATES):
        score = float(candidate_track_scores[index])
        previous = family_best.get(candidate.family)
        if previous is None or score > previous[0]:
            family_best[candidate.family] = (score, index)
    family_rows = [
        {
            'label': family,
            'similarity': round(score, 5),
            'best_style': GENRE_CANDIDATES[index].label,
            'score': round(max(0.0, min(1.0, score)), 5),
            'percent': round(max(0.0, min(1.0, score)) * 100.0, 1),
            'score_kind': 'best-style-clap-cosine-relevance',
        }
        for family, (score, index) in sorted(family_best.items(), key=lambda item: item[1][0], reverse=True)
    ]

    regional_rows = [
        style_row(index)
        for index in ranked_indices
        if GENRE_CANDIDATES[index].region
    ][:8]

    candidate_primary = style_row(primary_index)
    if confidence['is_unknown']:
        primary = {
            'label': 'Unknown / hybrid',
            'candidate': candidate_primary,
            'reason': 'The model does not have enough stable evidence to force a single genre label.',
        }
    else:
        primary = candidate_primary

    return {
        'version': NEURAL_ANALYSIS_VERSION,
        'taxonomy_version': TAXONOMY_VERSION,
        'candidate_count': len(GENRE_CANDIDATES),
        'primary': primary,
        'families': family_rows[:8],
        'styles': styles[:16],
        'regional': regional_rows,
        'confidence': confidence,
        'consensus': {
            'segment_count': len(candidate_segment_scores),
            'style_winner_percent': round(style_consensus * 100.0, 1),
            'family_winner_percent': round(family_consensus * 100.0, 1),
            'primary_style': primary_candidate.label,
            'primary_family': primary_candidate.family,
        },
        'segments': segment_rows,
        'studio_contract': {
            'mode': 'additive',
            'legacy_genres_preserved': True,
            'preferred_future_field': 'neural.genre_analysis',
        },
        'provenance': {
            'method': 'multi-prompt CLAP cosine relevance aggregated per candidate and per representative segment',
            'score_note': 'Similarity/relevance values are not calibrated probabilities.',
            'regional_note': 'Regional labels are open-vocabulary evidence and should be treated as model inference, not metadata fact.',
        },
    }


def _load_model() -> tuple[Any, Any, str]:
    global _model, _processor, _device
    if _model is not None and _processor is not None and _device is not None:
        return _model, _processor, _device

    with _load_lock:
        if _model is not None and _processor is not None and _device is not None:
            return _model, _processor, _device

        import torch
        from transformers import ClapModel, ClapProcessor

        device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
        processor = ClapProcessor.from_pretrained(MODEL_ID)
        model = ClapModel.from_pretrained(MODEL_ID)
        model.eval()
        model.to(device)

        _model = model
        _processor = processor
        _device = device
        return model, processor, device


def _feature_tensor(value: Any) -> Any:
    """Normalize Transformers 4/5 feature return shapes to a projected tensor."""
    if hasattr(value, 'audio_embeds') and value.audio_embeds is not None:
        return value.audio_embeds
    if hasattr(value, 'text_embeds') and value.text_embeds is not None:
        return value.text_embeds
    if hasattr(value, 'pooler_output') and value.pooler_output is not None:
        return value.pooler_output
    if isinstance(value, (tuple, list)) and value:
        return value[0]
    return value


def _cached_text_features(
    model: Any,
    processor: Any,
    prompts: Iterable[str],
    device: str,
) -> Any:
    import torch
    import torch.nn.functional as F

    key = tuple(str(prompt) for prompt in prompts)
    with _text_cache_lock:
        cached = _text_feature_cache.get(key)
    if cached is not None:
        return cached

    text_inputs = processor(text=list(key), return_tensors='pt', padding=True)
    text_inputs = {name: value.to(device) if hasattr(value, 'to') else value for name, value in text_inputs.items()}
    with torch.inference_mode():
        text_features = _feature_tensor(model.get_text_features(**text_inputs))
        text_features = F.normalize(text_features.float(), dim=-1)

    with _text_cache_lock:
        _text_feature_cache[key] = text_features
    return text_features


def _rank_open_labels(
    model: Any,
    processor: Any,
    track_embedding: Any,
    labels: Iterable[str],
    device: str,
    template: str,
) -> list[dict[str, Any]]:
    labels = tuple(labels)
    prompts = [template.format(label) for label in labels]
    text_features = _cached_text_features(model, processor, prompts, device)
    similarities = (track_embedding @ text_features.T)[0].detach().cpu().tolist()
    ranked = sorted(zip(labels, similarities, strict=True), key=lambda item: item[1], reverse=True)
    return [
        {
            'label': label,
            'similarity': round(float(similarity), 5),
            'score': round(max(0.0, min(1.0, float(similarity))), 5),
            'percent': round(max(0.0, min(1.0, float(similarity))) * 100.0, 1),
            'score_kind': 'clap-cosine-relevance',
            'provenance': 'neural-zero-shot-open-vocabulary-v3',
        }
        for label, similarity in ranked
    ]


def _score_traits(model: Any, processor: Any, track_embedding: Any, device: str) -> dict[str, Any]:
    import torch

    result: dict[str, Any] = {}
    for trait, pair in TRAIT_AXES.items():
        text_features = _cached_text_features(model, processor, pair, device)
        with torch.inference_mode():
            similarities = track_embedding @ text_features.T
            probabilities = torch.softmax(similarities[0] * _logit_scale(model), dim=-1)
        positive = float(probabilities[0].detach().cpu())
        result[trait] = {
            'value': round(positive, 4),
            'percent': round(positive * 100, 1),
            'positive_label': pair[0],
            'negative_label': pair[1],
            'provenance': 'neural-zero-shot-relative-axis',
            'score_note': 'Relative bipolar trait axis, not an absolute probability.',
        }
    return result


def _logit_scale(model: Any) -> float:
    try:
        value = float(model.logit_scale_a.exp().detach().cpu())
        if math.isfinite(value):
            return max(1.0, min(value, 100.0))
    except Exception:  # noqa: BLE001
        pass
    return 14.285714


def _decode_segments(path: Path, duration_seconds: float | None) -> tuple[list[Any], list[float]]:
    import numpy as np

    duration = float(duration_seconds or 0.0)
    if duration <= 0:
        offsets = [0.0]
    elif duration <= SEGMENT_SECONDS * 1.25:
        offsets = [0.0]
    else:
        fractions = [0.12, 0.32, 0.52, 0.72, 0.88][: max(1, MAX_SEGMENTS)]
        max_start = max(0.0, duration - SEGMENT_SECONDS)
        offsets = [max(0.0, min(max_start, duration * fraction - SEGMENT_SECONDS / 2)) for fraction in fractions]
        offsets = list(dict.fromkeys(round(value, 3) for value in offsets))

    segments: list[Any] = []
    successful_offsets: list[float] = []
    ffmpeg = settings.ffmpeg_bin or 'ffmpeg'
    for offset in offsets:
        command = [
            ffmpeg,
            '-hide_banner', '-loglevel', 'error',
            '-ss', f'{offset:.3f}',
            '-i', str(path),
            '-t', f'{SEGMENT_SECONDS:.3f}',
            '-vn', '-ac', '1', '-ar', str(SAMPLE_RATE),
            '-f', 'f32le', '-acodec', 'pcm_f32le', 'pipe:1',
        ]
        try:
            proc = subprocess.run(command, capture_output=True, check=True, timeout=45)
        except (subprocess.SubprocessError, OSError):
            continue
        audio = np.frombuffer(proc.stdout, dtype='<f4').astype(np.float32, copy=False)
        if audio.size < SAMPLE_RATE:
            continue
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        if peak > 1.5:
            audio = audio / peak
        segments.append(audio)
        successful_offsets.append(offset)
    return segments, successful_offsets
