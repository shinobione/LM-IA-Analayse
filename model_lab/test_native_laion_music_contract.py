from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def main() -> int:
    runner = (ROOT / "run_native_laion_music_benchmark.py").read_text(encoding="utf-8")
    setup = (REPO / "SONICTRACE_V4_NATIVE_LAION_MUSIC_SETUP.cmd").read_text(encoding="utf-8")
    bench = (REPO / "SONICTRACE_V4_NATIVE_LAION_MUSIC_BENCHMARK.cmd").read_text(encoding="utf-8")
    verdict = (ROOT / "BENCHMARK-VERDICT-2026-08-18-CANDIDATE-D.md").read_text(encoding="utf-8")
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")

    # Candidate E must stay completely isolated from product runtimes.
    assert 'set "VENV=%RUNTIME%\\native_laion_music_venv"' in setup
    assert 'set "LABPY=%RUNTIME%\\native_laion_music_venv\\Scripts\\python.exe"' in bench
    assert "model_lab/.runtime/" in gitignore
    assert "DOES NOT MODIFY V3 OR STUDIO" in setup

    # Native LAION path: do not accidentally fall back to the unreliable HF conversion.
    assert "laion-clap==1.1.7" in setup
    assert "transformers==4.51.3" in setup
    assert "torch==2.4.1" in setup
    assert "torchvision==0.19.1" in setup
    assert "torchaudio==2.4.1" in setup
    assert "numpy==1.26.4" in setup
    assert "HTSAT-base" in setup
    assert "music_audioset_epoch_15_esc_90.14.pt" in setup
    assert "fae3e9c087f2909c28a09dc31c8dfcdacbc42ba44c70e972b58c1bd1caf6dedd" in setup
    assert "model.load_ckpt" in setup
    assert "get_text_embedding" in setup
    assert "NATIVE LAION CLAP MUSIC CANDIDATE E PRET" in setup

    assert 'AUDIO_MODEL = "HTSAT-base"' in runner
    assert 'CHECKPOINT_FILE = "music_audioset_epoch_15_esc_90.14.pt"' in runner
    assert 'CHECKPOINT_SHA256 = "fae3e9c087f2909c28a09dc31c8dfcdacbc42ba44c70e972b58c1bd1caf6dedd"' in runner
    assert "SAMPLE_RATE = 48000" in runner
    assert "CLIP_SECONDS = 10.0" in runner
    assert "DEFAULT_CLIPS = 5" in runner
    assert "np.linspace(0, max_start, num=clips)" in runner
    assert "get_audio_embedding_from_data" in runner
    assert "get_text_embedding" in runner
    assert "native_rand_trunc_neutralized" in runner
    assert '"declared_metadata_used_for_inference": False' in runner
    assert '"weights_license": "CC0-1.0 (checkpoint repository metadata)"' in runner

    # Benchmark truth is post-inference only.
    inference_pos = runner.index("audio_embedding, sampling_meta = _encode_audio_track")
    axes_pos = runner.index("axes = {")
    benchmark_pos = runner.index("benchmark = _load_benchmark")
    assert inference_pos < axes_pos < benchmark_pos

    # Candidate D must be documented as an upstream conversion reliability failure,
    # not rescued by prompt/threshold changes.
    assert "upstream Hugging Face conversion is known to be unreliable" in verdict
    assert "Do not tune taxonomy prompts" in verdict
    assert "huggingface.co/laion/larger_clap_music/discussions/2" in verdict
    assert "huggingface/transformers/issues/26362" in verdict

    print("SonicTrace V4 Native LAION Music Candidate E contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
