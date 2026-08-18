from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import re
import subprocess
import sys
import threading
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_RUNTIME = ROOT / ".runtime"
DEFAULT_TAXONOMY = ROOT / "taxonomy_v1.json"
DEFAULT_BENCHMARKS = ROOT / "benchmarks.json"
DEFAULT_RESULTS = ROOT / "results"
AXES = ("family", "style", "tradition", "form")
UPSTREAM_COMMIT = "3d0c4de9447c404a8d3f9f37e04f53bc902e09b3"
RELEASE_TAG = "v0.5.0"
MODEL_DIR_NAME = "m2d_clap_vit_base-80x1001p16x16p16kpBpTI-2025"
CHECKPOINT_FILE = "checkpoint-30.pth"
MODEL_NAME = "M2D-CLAP 2025"
SAMPLE_RATE = 16000
CLIP_SECONDS = 10.0
DEFAULT_CLIPS = 5
EMBED_DIM = 768


def _normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return re.sub(r"\s+", " ", value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    def __init__(self, interval: float = 0.35) -> None:
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

        self._thread = threading.Thread(target=worker, name="sonictrace-m2d-clap-gpu-sampler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)


def _load_taxonomy(path: Path) -> dict[str, list[dict[str, str]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    policy = payload.get("inference_policy", {})
    if policy.get("audio_only") is not True:
        raise RuntimeError("Taxonomy inference policy must be audio-only.")
    if policy.get("declared_metadata_used_for_inference") is not False:
        raise RuntimeError("Declared metadata must stay out of inference.")
    axes = payload.get("axes") or {}
    taxonomy = {axis: list(axes.get(axis) or []) for axis in AXES}
    if any(not taxonomy[axis] for axis in AXES):
        raise RuntimeError("M2D-CLAP benchmark requires all four taxonomy axes.")
    return taxonomy


def _load_portable(path: Path):
    spec = importlib.util.spec_from_file_location("sonictrace_m2d_portable", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load pinned PortableM2D source: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _clip_starts(total_samples: int, *, clips: int) -> list[int]:
    import numpy as np

    clip_samples = int(round(SAMPLE_RATE * CLIP_SECONDS))
    max_start = max(0, total_samples - clip_samples)
    if max_start == 0 or clips <= 1:
        return [0]
    return sorted({int(round(value)) for value in np.linspace(0, max_start, num=clips)})


def _l2_rows(values: Any) -> Any:
    import numpy as np

    if hasattr(values, "detach"):
        values = values.detach().float().cpu().numpy()
    array = np.asarray(values, dtype=np.float32)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    if not np.all(np.isfinite(norms)) or np.any(norms <= 1e-12):
        raise RuntimeError("M2D-CLAP produced invalid embedding norms.")
    return array / norms


def _encode_text_axes(model: Any, taxonomy: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    import torch

    encoded: dict[str, Any] = {}
    with torch.no_grad():
        for axis in AXES:
            rows = taxonomy[axis]
            prompts = [str(row["prompt"]) for row in rows]
            embeddings = model.encode_clap_text(prompts, truncate=True)
            normalized = _l2_rows(embeddings)
            if normalized.shape != (len(prompts), EMBED_DIM):
                raise RuntimeError(f"Unexpected M2D-CLAP text embedding batch for {axis}: {normalized.shape}")
            encoded[axis] = normalized
    return encoded


def _encode_audio_track(model: Any, audio: Path, *, clips: int, device: Any) -> tuple[Any, dict[str, Any]]:
    import librosa
    import numpy as np
    import torch

    waveform, _ = librosa.load(str(audio), sr=SAMPLE_RATE, mono=True, dtype=np.float32)
    waveform = np.asarray(waveform, dtype=np.float32)
    if waveform.size == 0:
        raise RuntimeError(f"Decoded audio is empty: {audio}")

    clip_samples = int(round(SAMPLE_RATE * CLIP_SECONDS))
    starts = _clip_starts(int(waveform.size), clips=clips)
    embeddings: list[Any] = []

    with torch.no_grad():
        for start in starts:
            segment = waveform[start : start + clip_samples]
            if segment.size < clip_samples:
                segment = np.pad(segment, (0, clip_samples - segment.size), mode="constant")
            segment = np.asarray(segment, dtype=np.float32)
            if segment.size != clip_samples:
                raise RuntimeError(f"M2D-CLAP staging produced non-exact clip length: {segment.size}")
            batch = torch.from_numpy(segment).unsqueeze(0).to(device=device, dtype=torch.float32)
            raw = model.encode_clap_audio(batch)
            normalized = _l2_rows(raw)
            if normalized.shape != (1, EMBED_DIM):
                raise RuntimeError(f"Unexpected M2D-CLAP audio embedding shape: {normalized.shape}")
            embeddings.append(normalized[0])

    if not embeddings:
        raise RuntimeError(f"No M2D-CLAP audio embedding produced for: {audio}")

    stacked = np.stack(embeddings, axis=0)
    aggregate = _l2_rows(stacked.mean(axis=0, keepdims=True))[0]
    meta = {
        "sample_rate": SAMPLE_RATE,
        "clip_seconds": CLIP_SECONDS,
        "clip_count": len(starts),
        "clip_start_seconds": [round(start / SAMPLE_RATE, 3) for start in starts],
        "duration_seconds": round(float(waveform.size) / SAMPLE_RATE, 3),
        "aggregation": "mean of per-clip L2-normalized embeddings, then L2-normalize",
        "staging": "five deterministic evenly-spaced exact 10-second mono float32 clips",
    }
    return aggregate, meta


def _rank_axis(audio_embedding: Any, text_embeddings: Any, rows: list[dict[str, str]], *, top_k: int) -> list[dict[str, Any]]:
    import numpy as np

    scores = np.asarray(text_embeddings, dtype=np.float32) @ np.asarray(audio_embedding, dtype=np.float32)
    ranked = sorted(
        [
            {"id": str(row["id"]), "label": str(row["label"]), "similarity": float(score)}
            for row, score in zip(rows, scores.tolist())
        ],
        key=lambda item: item["similarity"],
        reverse=True,
    )
    return ranked[:top_k]


def _match_benchmark(payload: dict[str, Any], audio_name: str) -> dict[str, Any] | None:
    stem = _normalize_name(Path(audio_name).stem)
    for row in payload.get("tracks") or []:
        keys = [row.get("key") or "", *(row.get("aliases") or [])]
        if stem in {_normalize_name(str(item)) for item in keys}:
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
    tradition_ok = not benchmark.get("acceptable_primary_tradition") or primary.get("tradition") in benchmark["acceptable_primary_tradition"]
    form_ok = not benchmark.get("acceptable_primary_form") or primary.get("form") in benchmark["acceptable_primary_form"]
    forbidden = primary.get("style") in (benchmark.get("forbidden_primary_style") or [])
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
        "SONICTRACE V4 MODEL LAB — M2D-CLAP 2025",
        "=" * 60,
        f"Generated: {payload['generated_at']}",
        f"Model: {payload['model']['name']} / {payload['model']['model_dir']} / {payload['model']['checkpoint_file']}",
        f"Upstream: nttcslab/m2d @ {payload['model']['upstream_commit']} / release {payload['model']['release_tag']}",
        f"Checkpoint SHA-256: {payload['model']['checkpoint_sha256']}",
        f"Audio policy: {payload['model']['audio_policy']}",
        f"License status: {payload['model']['license_status']}",
        "Declared TXT metadata used for inference: NO",
        "",
    ]
    for track in payload["tracks"]:
        sampling = track["audio_sampling"]
        lines.extend(
            [
                f"## {track['file']}",
                f"Benchmark: {track['benchmark']['status']}",
                f"Elapsed: {track['elapsed_seconds']:.1f}s | Peak GPU memory: {track['peak_gpu_memory_mib']} MiB",
                f"Clips: {sampling['clip_count']} x {sampling['clip_seconds']:.0f}s @ 16kHz | starts: {sampling['clip_start_seconds']}",
            ]
        )
        for axis in AXES:
            rows = track["axes"].get(axis) or []
            rendered = " | ".join(f"{row['label']} {row['similarity']:.4f}" for row in rows[:5])
            lines.append(f"{axis.upper()}: {rendered}")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SonicTrace V4 M2D-CLAP 2025 audio-only benchmark.")
    parser.add_argument("audio", nargs="+", type=Path, help="One or more WAV/MP3 files.")
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--benchmarks", type=Path, default=DEFAULT_BENCHMARKS)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--clips", type=int, default=DEFAULT_CLIPS)
    args = parser.parse_args()

    if args.clips < 1 or args.clips > 9:
        raise SystemExit("--clips must be between 1 and 9.")

    import numpy as np
    import torch

    if not torch.cuda.is_available():
        raise SystemExit("M2D-CLAP 2025 Model Lab requires an NVIDIA CUDA GPU.")
    device = torch.device("cuda:0")

    runtime = args.runtime.resolve()
    source = (runtime / "m2d_clap_2025_src" / "portable_m2d.py").resolve()
    checkpoint = (runtime / "m2d_clap_2025" / MODEL_DIR_NAME / CHECKPOINT_FILE).resolve()
    if not source.exists() or not checkpoint.exists():
        raise SystemExit("Candidate F assets are missing. Run SONICTRACE_V4_M2D_CLAP_2025_SETUP.cmd first.")

    local_lock = checkpoint.with_name(checkpoint.name + ".sha256")
    checkpoint_sha = _sha256(checkpoint)
    if local_lock.exists():
        expected = local_lock.read_text(encoding="ascii").strip().lower()
        if expected and expected != checkpoint_sha.lower():
            raise SystemExit(f"M2D-CLAP checkpoint local-lock mismatch: {checkpoint_sha}")

    taxonomy = _load_taxonomy(args.taxonomy.resolve())
    gpu = _gpu_info()
    if not gpu.get("available"):
        raise SystemExit(f"NVIDIA GPU not available through nvidia-smi: {gpu.get('error')}")

    module = _load_portable(source)
    print("\n=== SONICTRACE V4 MODEL LAB — M2D-CLAP 2025 ===")
    print(f"GPU: {gpu.get('name')} | VRAM: {gpu.get('memory_total_mib')} MiB")
    print(f"Model: {MODEL_DIR_NAME} / {CHECKPOINT_FILE} | 16 kHz | 5 deterministic exact 10s clips/track")
    print("Inference input: AUDIO ONLY. TXT metadata is benchmark-only.")
    print("License gate: custom LICENSE.pdf unresolved -> LAB ONLY.\n")

    print("[INIT] Loading M2D-CLAP 2025 checkpoint...")
    model = module.PortableM2D(weight_file=str(checkpoint), flat_features=True).to(device).eval()
    print("[OK] M2D-CLAP loaded. Precomputing generic taxonomy text embeddings...")
    text_axes = _encode_text_axes(model, taxonomy)
    print("[OK] Taxonomy embeddings ready (768D).")

    raw_tracks: list[dict[str, Any]] = []
    for audio_arg in args.audio:
        audio = audio_arg.resolve()
        if not audio.exists():
            raise SystemExit(f"Audio file not found: {audio}")

        print(f"\n--- {audio.name} ---")
        torch.cuda.empty_cache()
        sampler = GPUSampler()
        sampler.start()
        started = time.perf_counter()
        try:
            audio_embedding, sampling_meta = _encode_audio_track(model, audio, clips=args.clips, device=device)
            axes = {
                axis: _rank_axis(audio_embedding, text_axes[axis], taxonomy[axis], top_k=args.top_k)
                for axis in AXES
            }
        finally:
            elapsed = time.perf_counter() - started
            sampler.stop()

        for axis in AXES:
            rendered = " | ".join(f"{row['label']} {row['similarity']:.4f}" for row in axes[axis][:5])
            print(f"{axis:10s}: {rendered}")
        raw_tracks.append(
            {
                "file": audio.name,
                "path": str(audio),
                "elapsed_seconds": round(elapsed, 3),
                "peak_gpu_memory_mib": sampler.peak_mib,
                "audio_sampling": sampling_meta,
                "axes": axes,
            }
        )

    # Anti-cheating boundary: the benchmark/reference file is not opened until
    # EVERY selected track has completed audio embedding + all four rankings.
    benchmark_payload = json.loads(args.benchmarks.resolve().read_text(encoding="utf-8"))
    for track in raw_tracks:
        benchmark = _match_benchmark(benchmark_payload, track["file"])
        track["benchmark"] = _evaluate(benchmark, track["axes"])
        print(f"BENCHMARK {track['file']}: {track['benchmark']['status']}")

    results_dir = args.results.resolve()
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    json_path = results_dir / f"m2d-clap-2025-benchmark-{stamp}.json"
    txt_path = results_dir / f"m2d-clap-2025-benchmark-{stamp}.txt"

    package_versions = {}
    for package in ("timm", "nnAudio", "einops", "transformers", "librosa", "numpy"):
        try:
            package_versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            package_versions[package] = "missing"

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": {
            "name": MODEL_NAME,
            "model_dir": MODEL_DIR_NAME,
            "checkpoint_file": CHECKPOINT_FILE,
            "checkpoint_sha256": checkpoint_sha,
            "upstream_commit": UPSTREAM_COMMIT,
            "release_tag": RELEASE_TAG,
            "embedding_dimension": EMBED_DIM,
            "audio_policy": "5 deterministic evenly spaced exact 10-second clips; normalized embedding mean",
            "license_status": "custom upstream LICENSE.pdf unresolved; LAB ONLY; no product qualification",
            "declared_metadata_used_for_inference": False,
            "package_versions": package_versions,
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
        },
        "gpu": gpu,
        "taxonomy": str(args.taxonomy.resolve()),
        "benchmark_reference_loaded_after_all_inference": True,
        "tracks": raw_tracks,
    }

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_text_report(txt_path, payload)
    print(f"\n[OK] JSON: {json_path}")
    print(f"[OK] TXT : {txt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
