from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent


def main() -> int:
    taxonomy = json.loads((ROOT / "taxonomy_v1.json").read_text(encoding="utf-8"))
    benchmarks = json.loads((ROOT / "benchmarks.json").read_text(encoding="utf-8"))
    runner = (ROOT / "run_clamp3_benchmark.py").read_text(encoding="utf-8")
    launcher = (ROOT / "launch_benchmark.py").read_text(encoding="utf-8")
    setup = (ROOT / "setup_clamp3.py").read_text(encoding="utf-8")
    setup_cmd = (REPO / "SONICTRACE_V4_MODEL_LAB_SETUP.cmd").read_text(encoding="utf-8")
    bench_cmd = (REPO / "SONICTRACE_V4_MODEL_LAB_BENCHMARK.cmd").read_text(encoding="utf-8")
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

    print("SonicTrace V4 Model Lab contract PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
