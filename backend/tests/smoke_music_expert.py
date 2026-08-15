from __future__ import annotations

import math

import numpy as np

from app.music_expert import PATCH_SIZE, MEL_BANDS, _musicnn_patches, analyze_music_expert


def main() -> None:
    sample_rate = 16_000
    duration = 4.0
    t = np.arange(int(sample_rate * duration), dtype=np.float32) / sample_rate
    # Deterministic multi-tone fixture: enough spectral content to exercise the
    # full preprocessing/model path without shipping an audio fixture in git.
    audio = (
        0.28 * np.sin(2.0 * math.pi * 110.0 * t)
        + 0.20 * np.sin(2.0 * math.pi * 220.0 * t)
        + 0.12 * np.sin(2.0 * math.pi * 440.0 * t)
    ).astype(np.float32)

    patches = _musicnn_patches(audio)
    assert patches.ndim == 3, patches.shape
    assert patches.shape[0] >= 1, patches.shape
    assert patches.shape[1:] == (PATCH_SIZE, MEL_BANDS), patches.shape
    assert np.isfinite(patches).all()

    result = analyze_music_expert([audio], [0.0], input_sample_rate=sample_rate)
    assert result['status'] == 'ready', result
    assert result['engine']['class_count'] == 400, result['engine']
    assert result['top_styles'], result
    assert result['embedding']['dimension'] == 1280, result['embedding'].get('dimension')
    assert len(result['embedding']['vector']) == 1280
    assert result['segments'][0]['patch_count'] >= 1
    print('Discogs-EffNet ONNX smoke: PASS')
    print('provider:', result['engine']['provider'])
    print('top style:', result['top_styles'][0]['label'])


if __name__ == '__main__':
    main()
