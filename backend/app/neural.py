from __future__ import annotations

import math
import os
import subprocess
import threading
from pathlib import Path
from typing import Any

from .config import settings

MODEL_ID = os.getenv('LMN_NEURAL_MODEL', 'laion/clap-htsat-unfused')
SAMPLE_RATE = 48_000
SEGMENT_SECONDS = float(os.getenv('LMN_NEURAL_SEGMENT_SECONDS', '10'))
MAX_SEGMENTS = int(os.getenv('LMN_NEURAL_MAX_SEGMENTS', '5'))

GENRE_LABELS = [
    'hip hop', 'trap', 'drill', 'R&B', 'soul', 'pop', 'electronic pop',
    'house', 'techno', 'drum and bass', 'dubstep', 'future bass', 'synthwave',
    'ambient', 'lo-fi hip hop', 'rock', 'indie', 'jazz', 'funk', 'reggae',
    'dancehall', 'afrobeat', 'cinematic music', 'orchestral music',
]

MOOD_LABELS = [
    'energetic', 'dark', 'melancholic', 'dreamy', 'aggressive', 'euphoric',
    'romantic', 'relaxed', 'uplifting', 'tense', 'mysterious', 'confident',
    'nostalgic', 'intimate', 'playful',
]

INSTRUMENT_LABELS = [
    'male vocals', 'female vocals', 'rap vocals', 'drums', 'electronic drums',
    '808 bass', 'synth bass', 'bass guitar', 'synthesizer', 'ambient pads',
    'piano', 'electric guitar', 'acoustic guitar', 'strings', 'brass', 'flute',
    'percussion',
]

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


def runtime_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        'installed': False,
        'ready': False,
        'cuda_available': False,
        'model_id': MODEL_ID,
        'model_loaded': _model is not None,
        'device': _device,
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

    genre = _rank_labels(model, processor, track_embedding, GENRE_LABELS, device, 'music in the genre of {}')
    mood = _rank_labels(model, processor, track_embedding, MOOD_LABELS, device, 'music with a {} mood')
    instruments = _rank_labels(model, processor, track_embedding, INSTRUMENT_LABELS, device, 'music featuring {}')
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
        'genres': genre[:8],
        'moods': mood[:8],
        'instruments': instruments[:10],
        'traits': traits,
        'embedding': {
            'model': MODEL_ID,
            'dimension': len(embedding),
            'vector': [round(float(value), 7) for value in embedding],
        },
        'provenance': {
            'type': 'neural',
            'method': 'CLAP zero-shot audio/text similarity averaged across representative track segments',
            'calibration': 'relative-within-candidate-set; scores are not Spotify metrics or absolute probabilities',
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


def _rank_labels(
    model: Any,
    processor: Any,
    track_embedding: Any,
    labels: list[str],
    device: str,
    template: str,
) -> list[dict[str, Any]]:
    import torch
    import torch.nn.functional as F

    prompts = [template.format(label) for label in labels]
    text_inputs = processor(text=prompts, return_tensors='pt', padding=True)
    text_inputs = {key: value.to(device) if hasattr(value, 'to') else value for key, value in text_inputs.items()}

    with torch.inference_mode():
        text_features = _feature_tensor(model.get_text_features(**text_inputs))
        text_features = F.normalize(text_features.float(), dim=-1)
        similarities = track_embedding @ text_features.T
        scale = _logit_scale(model)
        probabilities = torch.softmax(similarities[0] * scale, dim=-1)

    values = probabilities.detach().cpu().tolist()
    ranked = sorted(zip(labels, values, strict=True), key=lambda item: item[1], reverse=True)
    return [
        {
            'label': label,
            'score': round(float(score), 5),
            'percent': round(float(score) * 100, 1),
            'provenance': 'neural-zero-shot',
        }
        for label, score in ranked
    ]


def _score_traits(model: Any, processor: Any, track_embedding: Any, device: str) -> dict[str, Any]:
    import torch
    import torch.nn.functional as F

    result: dict[str, Any] = {}
    for trait, pair in TRAIT_AXES.items():
        text_inputs = processor(text=list(pair), return_tensors='pt', padding=True)
        text_inputs = {key: value.to(device) if hasattr(value, 'to') else value for key, value in text_inputs.items()}
        with torch.inference_mode():
            text_features = _feature_tensor(model.get_text_features(**text_inputs))
            text_features = F.normalize(text_features.float(), dim=-1)
            similarities = track_embedding @ text_features.T
            probabilities = torch.softmax(similarities[0] * _logit_scale(model), dim=-1)
        positive = float(probabilities[0].detach().cpu())
        result[trait] = {
            'value': round(positive, 4),
            'percent': round(positive * 100, 1),
            'positive_label': pair[0],
            'negative_label': pair[1],
            'provenance': 'neural-zero-shot-relative',
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
