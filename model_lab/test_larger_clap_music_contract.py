from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def main() -> int:
    runner = (ROOT / "run_larger_clap_music_benchmark.py").read_text(encoding="utf-8")
    setup_cmd = (REPO / "SONICTRACE_V4_LARGER_CLAP_MUSIC_SETUP.cmd").read_text(encoding="utf-8")
    bench_cmd = (REPO / "SONICTRACE_V4_LARGER_CLAP_MUSIC_BENCHMARK.cmd").read_text(encoding="utf-8")

    # Isolation / product boundary.
    assert 'set "VENV=%RUNTIME%\\larger_clap_venv"' in setup_cmd
    assert "DOES NOT MODIFY V3, CLAMP3, MUQ, MS-CLAP OR STUDIO" in setup_cmd
    assert "laion/larger_clap_music" in setup_cmd
    assert "a0b4534" in setup_cmd
    assert "Apache-2.0" in setup_cmd
    assert "torch==2.4.1" in setup_cmd and "torchaudio==2.4.1" in setup_cmd
    assert "transformers==4.46.3" in setup_cmd
    assert "numpy==1.26.4" in setup_cmd
    assert "ClapModel" in setup_cmd and "ClapProcessor" in setup_cmd
    assert 'set "LABPY=%RUNTIME%\\larger_clap_venv\\Scripts\\python.exe"' in bench_cmd
    assert '--engine-label "LAION Larger CLAP Music"' in bench_cmd
    assert "larger-clap-music-last-run.log" in bench_cmd
    assert "larger-clap-music-last-error.txt" in bench_cmd

    # Exact deterministic audio regime. The official processor advertises
    # rand_trunc for long audio, so only exact native 10-second arrays may reach it.
    assert 'MODEL_ID = "laion/larger_clap_music"' in runner
    assert 'MODEL_REVISION = "a0b4534"' in runner
    assert "SAMPLE_RATE = 48000" in runner
    assert "CLIP_SECONDS = 10.0" in runner
    assert "DEFAULT_CLIPS = 5" in runner
    assert "np.linspace(0, max_start, num=clips)" in runner
    assert "segment.size != clip_samples" in runner
    assert '"official_processor_rand_trunc_neutralized": True' in runner
    assert 'processor(\n            audios=segment,' in runner
    assert "F.normalize(stacked.mean(dim=0, keepdim=True), dim=-1)" in runner

    # Official Transformers model path, pinned revision and unchanged 4-axis taxonomy.
    assert "from transformers import ClapModel, ClapProcessor" in runner
    assert "ClapProcessor.from_pretrained(MODEL_ID, revision=MODEL_REVISION)" in runner
    assert "ClapModel.from_pretrained(MODEL_ID, revision=MODEL_REVISION)" in runner
    assert 'AXES = ("family", "style", "tradition", "form")' in runner
    assert '"weights_license": "Apache-2.0"' in runner

    # Critical anti-cheating contract: complete audio-only rankings happen before
    # benchmark/reference truth is loaded for that track.
    inference_pos = runner.index("axes = {")
    benchmark_pos = runner.index("benchmark = _load_benchmark")
    assert inference_pos < benchmark_pos
    assert '"audio_only": True' in runner
    assert '"declared_metadata_used_for_inference": False' in runner
    assert "declared_reference_evaluation_only" in runner

    print("SonicTrace V4 Candidate D Larger CLAP Music contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
