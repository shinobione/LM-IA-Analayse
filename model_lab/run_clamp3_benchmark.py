from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from prepare_refs import build_reference_banks


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
DEFAULT_RUNTIME = ROOT / ".runtime"
DEFAULT_TAXONOMY = ROOT / "taxonomy_v1.json"
DEFAULT_BENCHMARKS = ROOT / "benchmarks.json"
DEFAULT_RESULTS = ROOT / "results"
AXES = ("family", "style", "tradition", "form")
RESULT_RE = re.compile(r"^([A-Za-z0-9_-]+)\s+(-?\d+(?:\.\d+)?)\s*$")


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return re.sub(r"\s+", " ", value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )


def _git_sha(repo: Path) -> str | None:
    completed = _run(["git", "rev-parse", "HEAD"], cwd=repo)
    return completed.stdout.strip() if completed.returncode == 0 else None


def _gpu_info() -> dict[str, Any]:
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version,memory.total,memory.used",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip().splitlines()[0]
        name, driver, total, used = [part.strip() for part in out.split(",", 3)]
        return {
            "available": True,
            "name": name,
            "driver": driver,
            "memory_total_mib": int(float(total)),
            "memory_used_mib_at_start": int(float(used)),
        }
    except Exception as exc:  # pragma: no cover - hardware dependent
        return {"available": False, "error": str(exc)}


def _gpu_memory_used() -> int | None:
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
            text=True,
            encoding="utf-8",
            errors="replace",
            stderr=subprocess.DEVNULL,
        ).strip().splitlines()[0]
        return int(float(out.strip()))
    except Exception:  # pragma: no cover - hardware dependent
        return None


class GPUSampler:
    def __init__(self, interval: float = 0.4) -> None:
        self.interval = interval
        self.peak_mib: int | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        def worker() -> None:
            while not self._stop.is_set():
                used = _gpu_memory_used()
                if used is not None:
                    self.peak_mib = used if self.peak_mib is None else max(self.peak_mib, used)
                self._stop.wait(self.interval)

        self._thread = threading.Thread(target=worker, name="sonictrace-gpu-sampler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)


def _invalidate_reference_cache_if_needed(clamp_dir: Path, runtime_dir: Path, taxonomy_path: Path) -> None:
    current = _sha256(taxonomy_path)
    marker = runtime_dir / "taxonomy.sha256"
    previous = marker.read_text(encoding="utf-8").strip() if marker.exists() else ""
    if previous == current:
        return
    cache = clamp_dir / "cache"
    for axis in AXES:
        shutil.rmtree(cache / f"txt-{axis}", ignore_errors=True)
    marker.write_text(current + "\n", encoding="utf-8")


def _clear_query_cache(clamp_dir: Path, audio: Path) -> None:
    cache_file = clamp_dir / "cache" / "query" / f"audio-{audio.stem}.npy"
    cache_file.unlink(missing_ok=True)


def _parse_rankings(stdout: str, label_map: dict[str, str], top_k: int) -> list[dict[str, Any]]:
    rankings: list[dict[str, Any]] = []
    for raw_line in stdout.splitlines():
        match = RESULT_RE.match(raw_line.strip())
        if not match:
            continue
        slug, value = match.groups()
        if slug not in label_map:
            continue
        rankings.append({"id": slug, "label": label_map[slug], "similarity": float(value)})
    return rankings[:top_k]


def _classify_axis(
    *,
    python: Path,
    clamp_dir: Path,
    audio: Path,
    refs_dir: Path,
    label_map: dict[str, str],
    top_k: int,
    env: dict[str, str],
) -> tuple[list[dict[str, Any]], float, str]:
    started = time.perf_counter()
    completed = _run(
        [str(python), "clamp3_search.py", str(audio), str(refs_dir), "--top_k", str(top_k)],
        cwd=clamp_dir,
        env=env,
    )
    elapsed = time.perf_counter() - started
    combined_log = (completed.stdout or "") + "\n" + (completed.stderr or "")
    if completed.returncode != 0:
        raise RuntimeError(
            f"CLaMP3 failed for axis {refs_dir.name} on {audio.name} (exit {completed.returncode}).\n{combined_log[-8000:]}"
        )
    rankings = _parse_rankings(completed.stdout or "", label_map, top_k)
    if not rankings:
        raise RuntimeError(
            f"CLaMP3 returned no parseable rankings for axis {refs_dir.name} on {audio.name}.\n{combined_log[-8000:]}"
        )
    return rankings, elapsed, combined_log


def _load_benchmark(path: Path, audio: Path) -> dict[str, Any] | None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    stem = _normalize(audio.stem)
    for row in payload.get("tracks") or []:
        keys = [row.get("key") or "", *(row.get("aliases") or [])]
        if stem in {_normalize(str(item)) for item in keys}:
            return row
    return None


def _evaluate(benchmark: dict[str, Any] | None, axes: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    if not benchmark:
        return {"status": "UNBENCHMARKED", "note": "No matching real-track benchmark entry."}

    primary = {axis: (rows[0]["label"] if rows else None) for axis, rows in axes.items()}
    style_top5 = [row["label"] for row in axes.get("style", [])[:5]]
    family_ok = not benchmark.get("acceptable_family") or primary.get("family") in benchmark["acceptable_family"]
    primary_style_ok = not benchmark.get("acceptable_primary_style") or primary.get("style") in benchmark["acceptable_primary_style"]
    top5_style_ok = not benchmark.get("acceptable_top5_style") or any(
        label in benchmark["acceptable_top5_style"] for label in style_top5
    )
    forbidden = primary.get("style") in (benchmark.get("forbidden_primary_style") or [])
    tradition_ok = not benchmark.get("acceptable_primary_tradition") or primary.get("tradition") in benchmark["acceptable_primary_tradition"]
    form_ok = not benchmark.get("acceptable_primary_form") or primary.get("form") in benchmark["acceptable_primary_form"]
    discouraged = primary.get("style") in (benchmark.get("discouraged_primary_style") or [])

    if family_ok and primary_style_ok and tradition_ok and form_ok and not forbidden:
        status = "PASS"
    elif family_ok and top5_style_ok and tradition_ok and form_ok and not forbidden:
        status = "NEAR"
    else:
        status = "FAIL"

    return {
        "status": status,
        "display_name": benchmark.get("display_name"),
        "primary": primary,
        "style_top5": style_top5,
        "checks": {
            "family_ok": family_ok,
            "primary_style_ok": primary_style_ok,
            "top5_style_ok": top5_style_ok,
            "tradition_ok": tradition_ok,
            "form_ok": form_ok,
            "forbidden_primary": forbidden,
            "discouraged_primary": discouraged,
        },
        "declared_reference_evaluation_only": benchmark.get("declared_reference"),
    }


def _write_text_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "SONICTRACE V4 MODEL LAB — CLaMP3 / MERT95M",
        "=" * 58,
        f"Generated: {payload['generated_at']}",
        f"CLaMP3 commit: {payload['model']['clamp3_commit']}",
        f"MERT: {payload['model']['audio_encoder']}",
        "Declared TXT metadata used for inference: NO",
        "",
    ]
    for track in payload["tracks"]:
        lines.extend([
            f"## {track['file']}",
            f"Benchmark: {track['benchmark']['status']}",
            f"Elapsed: {track['elapsed_seconds']:.1f}s | Peak GPU memory: {track['peak_gpu_memory_mib']} MiB",
        ])
        for axis in AXES:
            rows = track["axes"].get(axis) or []
            if not rows:
                continue
            rendered = " | ".join(f"{row['label']} {row['similarity']:.4f}" for row in rows[:5])
            lines.append(f"{axis.upper()}: {rendered}")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SonicTrace V4 Model Lab CLaMP3 audio-only benchmark.")
    parser.add_argument("audio", nargs="+", type=Path, help="One or more WAV/MP3 files.")
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--benchmarks", type=Path, default=DEFAULT_BENCHMARKS)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--axes", nargs="+", choices=AXES, default=list(AXES))
    args = parser.parse_args()

    runtime_dir = args.runtime.resolve()
    taxonomy_path = args.taxonomy.resolve()
    clamp_dir = runtime_dir / "clamp3"
    python = runtime_dir / "venv" / "Scripts" / "python.exe" if os.name == "nt" else runtime_dir / "venv" / "bin" / "python"
    if not clamp_dir.exists() or not python.exists():
        raise SystemExit("Model Lab runtime missing. Run SONICTRACE_V4_MODEL_LAB_SETUP.cmd first.")

    label_maps = build_reference_banks(taxonomy_path, runtime_dir)
    _invalidate_reference_cache_if_needed(clamp_dir, runtime_dir, taxonomy_path)

    env = os.environ.copy()
    env["HF_HOME"] = str(runtime_dir / "huggingface")
    env["TRANSFORMERS_CACHE"] = str(runtime_dir / "huggingface" / "transformers")
    env["TOKENIZERS_PARALLELISM"] = "false"

    gpu = _gpu_info()
    if not gpu.get("available"):
        raise SystemExit(f"NVIDIA GPU not available through nvidia-smi: {gpu.get('error')}")

    report: dict[str, Any] = {
        "schema": "sonictrace-v4-model-lab-result-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inference": {"audio_only": True, "declared_metadata_used_for_inference": False},
        "model": {
            "name": "CLaMP 3 SAAS",
            "clamp3_commit": _git_sha(clamp_dir),
            "audio_encoder": "m-a-p/MERT-v1-95M",
            "embedding_dimension": 768,
        },
        "gpu": gpu,
        "tracks": [],
    }

    print("\n=== SONICTRACE V4 MODEL LAB — CLaMP3 / MERT95M ===")
    print(f"GPU: {gpu.get('name')} | VRAM: {gpu.get('memory_total_mib')} MiB")
    print("Inference input: AUDIO ONLY. TXT metadata is benchmark-only.\n")

    for requested in args.audio:
        audio = requested.resolve()
        if not audio.exists():
            print(f"[SKIP] Missing file: {audio}")
            continue
        if audio.suffix.lower() not in {".wav", ".mp3", ".flac", ".ogg"}:
            print(f"[SKIP] Unsupported audio type: {audio}")
            continue

        print(f"--- {audio.name} ---")
        _clear_query_cache(clamp_dir, audio)
        sampler = GPUSampler()
        sampler.start()
        started = time.perf_counter()
        axis_results: dict[str, list[dict[str, Any]]] = {}
        axis_seconds: dict[str, float] = {}
        try:
            for axis in args.axes:
                rankings, elapsed, _log = _classify_axis(
                    python=python,
                    clamp_dir=clamp_dir,
                    audio=audio,
                    refs_dir=runtime_dir / "refs" / axis,
                    label_map=label_maps[axis],
                    top_k=args.top_k,
                    env=env,
                )
                axis_results[axis] = rankings
                axis_seconds[axis] = round(elapsed, 3)
                print(f"{axis:10s}: " + " | ".join(f"{row['label']} {row['similarity']:.4f}" for row in rankings[:5]))
        finally:
            sampler.stop()
        elapsed_total = time.perf_counter() - started
        benchmark = _load_benchmark(args.benchmarks.resolve(), audio)
        evaluation = _evaluate(benchmark, axis_results)
        print(f"BENCHMARK : {evaluation['status']} | {elapsed_total:.1f}s | peak VRAM {sampler.peak_mib} MiB\n")
        report["tracks"].append({
            "file": audio.name,
            "path": str(audio),
            "elapsed_seconds": round(elapsed_total, 3),
            "axis_seconds": axis_seconds,
            "peak_gpu_memory_mib": sampler.peak_mib,
            "axes": axis_results,
            "benchmark": evaluation,
        })

    if not report["tracks"]:
        raise SystemExit("No audio file was benchmarked.")

    results_dir = args.results.resolve()
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = results_dir / f"clamp3-benchmark-{stamp}.json"
    txt_path = results_dir / f"clamp3-benchmark-{stamp}.txt"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_text_report(txt_path, report)
    print(f"[OK] JSON: {json_path}")
    print(f"[OK] TXT : {txt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
