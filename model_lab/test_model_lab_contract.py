from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def main() -> int:
    taxonomy = json.loads((ROOT / "taxonomy_v1.json").read_text(encoding="utf-8"))
    benchmarks = json.loads((ROOT / "benchmarks.json").read_text(encoding="utf-8"))
    runner = (ROOT / "run_clamp3_benchmark.py").read_text(encoding="utf-8")
    muq_runner = (ROOT / "run_muq_mulan_benchmark.py").read_text(encoding="utf-8")
    msclap_runner = (ROOT / "run_ms_clap_benchmark.py").read_text(encoding="utf-8")
    launcher = (ROOT / "launch_benchmark.py").read_text(encoding="utf-8")
    setup = (ROOT / "setup_clamp3.py").read_text(encoding="utf-8")
    setup_cmd = (REPO / "SONICTRACE_V4_MODEL_LAB_SETUP.cmd").read_text(encoding="utf-8")
    bench_cmd = (REPO / "SONICTRACE_V4_MODEL_LAB_BENCHMARK.cmd").read_text(encoding="utf-8")
    muq_setup_cmd = (REPO / "SONICTRACE_V4_MUQ_MULAN_SETUP.cmd").read_text(encoding="utf-8")
    muq_bench_cmd = (REPO / "SONICTRACE_V4_MUQ_MULAN_BENCHMARK.cmd").read_text(encoding="utf-8")
    msclap_setup_cmd = (REPO / "SONICTRACE_V4_MS_CLAP_SETUP.cmd").read_text(encoding="utf-8")
    msclap_bench_cmd = (REPO / "SONICTRACE_V4_MS_CLAP_BENCHMARK.cmd").read_text(encoding="utf-8")
    gitignore = (REPO / ".gitignore").read_text(encoding="utf-8")

    assert taxonomy["inference_policy"]["audio_only"] is True
    assert taxonomy["inference_policy"]["declared_metadata_used_for_inference"] is False
    assert set(taxonomy["axes"]) == {"family", "style", "tradition", "form"}
    for axis, rows in taxonomy["axes"].items():
        assert rows, axis
        ids = [row["id"] for row in rows]
        labels = [row["label"] for row in rows]
        assert len(ids) == len(set(ids)), f"duplicate ids in {axis}"
        assert len(labels) == len(set(labels)), f"duplicate labels in {axis}"
        assert all(row.get("prompt", "").strip() for row in rows)

    styles = {row["label"] for row in taxonomy["axes"]["style"]}
    for required in {
        "Vietnamese Bolero",
        "Dancehall Pop",
        "Eurodance",
        "Cyber Trap",
        "Industrial Hip-Hop",
        "Glitch Hop",
        "Drift Phonk",
        "Electronic Drill",
        "Grime",
    }:
        assert required in styles

    assert benchmarks["policy"]["declared_metadata_used_for_inference"] is False
    benchmark_names = {row["display_name"] for row in benchmarks["tracks"]}
    assert {"THICK", "Tachy Psychia", "Stick to You", "Tinh Bolero Cho Trân"}.issubset(benchmark_names)

    # Guard the critical no-cheating boundary: benchmark truth is loaded only
    # after all axis inference is complete for a track.
    classify_pos = runner.index("for axis in args.axes:")
    benchmark_pos = runner.index("benchmark = _load_benchmark")
    assert classify_pos < benchmark_pos
    assert '"declared_metadata_used_for_inference": False' in runner

    # Official CLaMP3 source is pinned and kept outside tracked product runtime.
    assert "9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8" in setup
    assert "model_lab/.runtime/" in gitignore
    assert "model_lab/results/" in gitignore
    assert 'set "VENV=%RUNTIME%\\venv"' in setup_cmd
    assert "%ROOT%backend\\.venv\\Scripts\\python.exe" not in setup_cmd
    assert "studio" in setup_cmd.lower() and "does not modify" in setup_cmd.lower()

    # Windows launcher hardening: no second PowerShell is allowed to forward
    # selected audio paths into Python. The stable stdlib launcher reads the
    # selection file itself and pins every nested `python` command to the lab venv.
    assert "launch_benchmark.py" in bench_cmd
    assert 'set "PATH=%RUNTIME%\\venv\\Scripts;%PATH%"' in bench_cmd
    assert "--file-list" in bench_cmd
    assert "$files=Get-Content" not in bench_cmd
    assert "last-run.log" in bench_cmd
    assert "last-error.txt" in bench_cmd
    assert 'env["PATH"] = str(venv_scripts) + os.pathsep + env.get("PATH", "")' in launcher
    assert 'env["VIRTUAL_ENV"] = str(venv_root)' in launcher
    assert 'env["PYTHONNOUSERSITE"] = "1"' in launcher
    assert 'stderr=subprocess.STDOUT' in launcher
    assert "Selected files:" in launcher
    assert "--engine-label" in launcher

    # Upstream CLaMP3 builds an unquoted nested search command from the generated
    # query embedding filename. Real user files may contain spaces/Unicode, so
    # inference must use a disposable ASCII/no-space staging name while benchmark
    # matching and reports retain the original source filename/path.
    assert "def _stage_audio_for_clamp3" in runner
    assert 'stage_dir = runtime_dir / "staged_audio"' in runner
    assert 'staged = stage_dir / f"track-{token}{suffix}"' in runner
    assert "audio=staged_audio" in runner
    assert "_clear_query_cache(clamp_dir, staged_audio)" in runner
    assert "staged_audio.unlink(missing_ok=True)" in runner
    assert "benchmark = _load_benchmark(args.benchmarks.resolve(), audio)" in runner
    assert '"file": audio.name' in runner and '"path": str(audio)' in runner

    # MuQ-MuLan challenger is isolated from the CLaMP3 venv and V3. It must use
    # the official 24 kHz / 10-second audio regime, fp32, generic taxonomy text,
    # deterministic song coverage and the same post-inference benchmark truth.
    assert 'set "VENV=%RUNTIME%\\muq_venv"' in muq_setup_cmd
    assert "muq==0.1.0" in muq_setup_cmd
    assert "transformers==4.46.3" in muq_setup_cmd
    assert "torch==2.4.1" in muq_setup_cmd and "torchaudio==2.4.1" in muq_setup_cmd
    assert "from transformers.utils import is_torch_available" in muq_setup_cmd
    assert "assert is_torch_available()" in muq_setup_cmd
    assert "from muq import MuQMuLan" in muq_setup_cmd
    assert "OpenMuQ/MuQ-MuLan-large" in muq_setup_cmd
    assert "CC-BY-NC-4.0" in muq_setup_cmd
    assert "DOES NOT MODIFY V3, CLAMP3 OR STUDIO" in muq_setup_cmd
    assert 'set "LABPY=%RUNTIME%\\muq_venv\\Scripts\\python.exe"' in muq_bench_cmd
    assert '--engine-label "MuQ-MuLan"' in muq_bench_cmd
    assert "muq-last-run.log" in muq_bench_cmd and "muq-last-error.txt" in muq_bench_cmd
    assert 'MODEL_ID = "OpenMuQ/MuQ-MuLan-large"' in muq_runner
    assert "SAMPLE_RATE = 24000" in muq_runner
    assert "CLIP_SECONDS = 10.0" in muq_runner
    assert "DEFAULT_CLIPS = 5" in muq_runner
    assert "np.linspace(0, max_start, num=clips)" in muq_runner
    assert "F.normalize(stacked.mean(dim=0, keepdim=True), dim=-1)" in muq_runner
    assert 'model = model.float()' in muq_runner
    muq_inference_pos = muq_runner.index("audio_embedding, sampling_meta = _encode_audio_track")
    muq_benchmark_pos = muq_runner.index("benchmark = _load_benchmark")
    assert muq_inference_pos < muq_benchmark_pos
    assert '"declared_metadata_used_for_inference": False' in muq_runner
    assert '"weights_license": "CC-BY-NC-4.0"' in muq_runner

    # Candidate C: official Microsoft CLAP 2023 is kept in a third isolated venv.
    # Its upstream wrapper randomly crops long files, so the Model Lab must first
    # stage deterministic exact-duration 7s clips and only then call msclap.
    # The checkpoint is MS-PL (not MIT like the code repo), and the runner must
    # preserve that distinction instead of declaring an unconditional product pass.
    assert 'set "VENV=%RUNTIME%\\msclap_venv"' in msclap_setup_cmd
    assert "msclap==1.3.3" in msclap_setup_cmd
    assert "transformers==4.46.3" in msclap_setup_cmd
    assert "torch==2.4.1" in msclap_setup_cmd and "torchaudio==2.4.1" in msclap_setup_cmd
    assert "from msclap import CLAP" in msclap_setup_cmd
    assert "e8a6467b87cd85716e20c6a008126150d9740be0" in msclap_setup_cmd
    assert "MIT" in msclap_setup_cmd and "MS-PL" in msclap_setup_cmd
    assert "DOES NOT MODIFY V3, CLAMP3, MUQ OR STUDIO" in msclap_setup_cmd
    assert 'set "LABPY=%RUNTIME%\\msclap_venv\\Scripts\\python.exe"' in msclap_bench_cmd
    assert '--engine-label "Microsoft CLAP 2023"' in msclap_bench_cmd
    assert "msclap-last-run.log" in msclap_bench_cmd and "msclap-last-error.txt" in msclap_bench_cmd
    assert 'MODEL_REPO = "microsoft/msclap"' in msclap_runner
    assert 'MODEL_VERSION = "2023"' in msclap_runner
    assert 'WEIGHTS_FILE = "CLAP_weights_2023.pth"' in msclap_runner
    assert "SAMPLE_RATE = 44100" in msclap_runner
    assert "CLIP_SECONDS = 7.0" in msclap_runner
    assert "DEFAULT_CLIPS = 5" in msclap_runner
    assert "np.linspace(0, max_start, num=clips)" in msclap_runner
    assert 'stage_dir = runtime_dir / "msclap_staged"' in msclap_runner
    assert 'staged = stage_dir / f"clip-{token}-{index:02d}.wav"' in msclap_runner
    assert 'sf.write(str(staged)' in msclap_runner
    assert 'model.get_audio_embeddings([str(staged)], resample=True)' in msclap_runner
    assert "staged.unlink(missing_ok=True)" in msclap_runner
    assert "F.normalize(stacked.mean(dim=0, keepdim=True), dim=-1)" in msclap_runner
    assert 'model = CLAP(version=MODEL_VERSION, use_cuda=True)' in msclap_runner
    msclap_inference_pos = msclap_runner.index("audio_embedding, sampling_meta = _encode_audio_track")
    msclap_benchmark_pos = msclap_runner.index("benchmark = _load_benchmark")
    assert msclap_inference_pos < msclap_benchmark_pos
    assert '"declared_metadata_used_for_inference": False' in msclap_runner
    assert '"code_license": "MIT"' in msclap_runner
    assert '"weights_license": "MS-PL"' in msclap_runner
    assert "product legal review before shipping" in msclap_runner

    print("SonicTrace V4 Model Lab contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
