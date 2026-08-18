from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def main() -> int:
    runner = (ROOT / "run_m2d_clap_2025_benchmark.py").read_text(encoding="utf-8")
    helper = (ROOT / "setup_m2d_clap_2025.py").read_text(encoding="utf-8")
    setup = (REPO / "SONICTRACE_V4_M2D_CLAP_2025_SETUP.cmd").read_text(encoding="utf-8")
    bench = (REPO / "SONICTRACE_V4_M2D_CLAP_2025_BENCHMARK.cmd").read_text(encoding="utf-8")
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")

    # Candidate F must remain an isolated lab runtime with an unresolved license gate.
    assert 'set "VENV=%RUNTIME%\\m2d_clap_2025_venv"' in setup
    assert 'set "LABPY=%RUNTIME%\\m2d_clap_2025_venv\\Scripts\\python.exe"' in bench
    assert "model_lab/.runtime/" in gitignore
    assert "NO V3 / CATALOG / STUDIO CHANGE" in setup
    assert "LAB ONLY" in setup
    assert "custom LICENSE.pdf" in setup

    # Pin the exact official 2025 path documented by nttcslab/m2d.
    assert "3d0c4de9447c404a8d3f9f37e04f53bc902e09b3" in helper
    assert "releases/download/v0.5.0" in helper
    assert "m2d_clap_vit_base-80x1001p16x16p16kpBpTI-2025" in helper
    assert 'CHECKPOINT_FILE = "checkpoint-30.pth"' in helper
    assert "portable_m2d.py" in helper
    assert "class PortableM2D" in helper
    assert "encode_clap_audio" in helper
    assert "encode_clap_text" in helper

    # The Windows setup pins a reproducible CUDA/ABI stack and READY is gated by
    # a real checkpoint load + real audio and text embeddings.
    assert "torch==2.4.1" in setup
    assert "torchvision==0.19.1" in setup
    assert "torchaudio==2.4.1" in setup
    assert "transformers==4.46.3" in setup
    assert "numpy==1.26.4" in setup
    assert "timm==1.0.19" in setup
    assert "nnAudio==0.3.3" in setup
    assert "einops==0.8.1" in setup
    assert 'EXPECTED_TORCH_PREFIX = "2.4.1+cu118"' in helper
    assert 'EXPECTED_CUDA = "11.8"' in helper
    assert 'EXPECTED_NUMPY = "1.26.4"' in helper
    assert 'EXPECTED_TRANSFORMERS = "4.46.3"' in helper
    assert "model = module.PortableM2D" in helper
    assert "model.encode_clap_audio" in helper
    assert "model.encode_clap_text" in helper
    assert "(1, 768)" in helper
    assert "(2, 768)" in helper
    assert "M2D-CLAP 2025 CANDIDATE F PRET" in setup

    # Benchmark protocol is fixed before the first real result: 16 kHz, exact
    # 10-second windows, five evenly-spaced clips and 768D shared embeddings.
    assert "SAMPLE_RATE = 16000" in runner
    assert "CLIP_SECONDS = 10.0" in runner
    assert "DEFAULT_CLIPS = 5" in runner
    assert "EMBED_DIM = 768" in runner
    assert "np.linspace(0, max_start, num=clips)" in runner
    assert "model.encode_clap_audio" in runner
    assert "model.encode_clap_text" in runner
    assert '"declared_metadata_used_for_inference": False' in runner
    assert "custom upstream LICENSE.pdf unresolved; LAB ONLY" in runner

    # Stronger anti-cheating boundary than previous candidates: benchmark truth
    # is not opened until every selected track has completed all four rankings.
    inference_pos = runner.index("audio_embedding, sampling_meta = _encode_audio_track")
    axes_pos = runner.index("axes = {")
    raw_append_pos = runner.index("raw_tracks.append(")
    benchmark_read_pos = runner.index("benchmark_payload = json.loads")
    assert inference_pos < axes_pos < raw_append_pos < benchmark_read_pos
    assert '"benchmark_reference_loaded_after_all_inference": True' in runner

    print("SonicTrace V4 M2D-CLAP 2025 Candidate F contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
