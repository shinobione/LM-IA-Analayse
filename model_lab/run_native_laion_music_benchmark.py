from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import re
import subprocess
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
MODEL_NAME = "LAION CLAP native music_audioset"
MODEL_PACKAGE = "laion-clap"
MODEL_PACKAGE_VERSION = "1.1.7"
AUDIO_MODEL = "HTSAT-base"
CHECKPOINT_REPO = "lukewys/laion_clap"
CHECKPOINT_FILE = "music_audioset_epoch_15_esc_90.14.pt"
CHECKPOINT_SHA256 = "fae3e9c087f2909c28a09dc31c8dfcdacbc42ba44c70e972b58c1bd1caf6dedd"
SAMPLE_RATE = 48000
CLIP_SECONDS = 10.0
DEFAULT_CLIPS = 5


def _normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return re.sub(r"\s+", " ", value)


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

        self._thread = threading.Thread(target=worker, name="sonictrace-native-laion-gpu-sampler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(8 * 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _load_taxonomy(path: Path) -> dict[str, list[dict[str, str]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    policy = payload.get("inference_policy", {})
    if policy.get("audio_only") is not True:
        raise RuntimeError("Taxonomy inference policy must be audio-only.")
    if policy.get("declared_metadata_used_for_inference") is not False:
        raise RuntimeError("Declared metadata must stay out of inference.")
    axes = payload.get("axes") or {}
    return {axis: list(axes.get(axis) or []) for axis in AXES}


def _load_benchmark(path: Path, audio: Path) -> dict[str, Any] | None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    stem = _normalize_name(audio.stem)
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


def _clip_starts(total_samples: int, *, clips: int) -> list[int]:
    import numpy as np

    clip_samples = int(round(SAMPLE_RATE * CLIP_SECONDS))
    max_start = max(0, total_samples - clip_samples)
    if max_start == 0 or clips <= 1:
        return [0]
    return sorted({int(round(value)) for value in np.linspace(0, max_start, num=clips)})


def _l2_rows(values: Any) -> Any:
    import numpy as np

    array = np.asarray(values, dtype=np.float32)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    if not np.all(np.isfinite(norms)) or np.any(norms <= 1e-12):
        raise RuntimeError("Native LAION CLAP produced invalid embedding norms.")
    return array / norms


def _encode_text_axes(model: Any, taxonomy: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    encoded: dict[str, Any] = {}
    for axis in AXES:
        rows = taxonomy[axis]
        prompts = [str(row["prompt"]) for row in rows]
        embeddings = model.get_text_embedding(prompts, use_tensor=False)
        normalized = _l2_rows(embeddings)
        if normalized.shape[0] != len(prompts):
            raise RuntimeError(f"Unexpected native LAION text embedding batch for {axis}: {normalized.shape}")
        encoded[axis] = normalized
    return encoded


def _encode_audio_track(model: Any, audio: Path, *, clips: int) -> tuple[Any, dict[str, Any]]:
    import librosa
    import numpy as np

    waveform, _ = librosa.load(str(audio), sr=SAMPLE_RATE, mono=True, dtype=np.float32)
    waveform = np.asarray(waveform, dtype=np.float32)
    if waveform.size == 0:
        raise RuntimeError(f"Decoded audio is empty: {audio}")

    clip_samples = int(round(SAMPLE_RATE * CLIP_SECONDS))
    starts = _clip_starts(int(waveform.size), clips=clips)
    embeddings: list[Any] = []

    for start in starts:
        segment = waveform[start : start + clip_samples]
        if segment.size < clip_samples:
            segment = np.pad(segment, (0, clip_samples - segment.size), mode="constant")
        segment = np.asarray(segment, dtype=np.float32)
        if segment.size != clip_samples:
            raise RuntimeError(f"Native LAION staging produced non-exact clip length: {segment.size}")

        # Native LAION's non-fusion helper uses rand_trunc only when input is
        # longer than 480000 samples. Exact 10-second arrays therefore keep the
        # benchmark deterministic while still using the official audio path.
        raw = model.get_audio_embedding_from_data(
            np.expand_dims(segment, axis=0),
            use_tensor=False,
        )
        normalized = _l2_rows(raw)
        if normalized.shape[0] != 1:
            raise RuntimeError(f"Unexpected native LAION audio embedding shape: {normalized.shape}")
        embeddings.append(normalized[0])

    if not embeddings:
        raise RuntimeError(f"No native LAION audio embedding produced for: {audio}")

    stacked = np.stack(embeddings, axis=0)
    aggregate = _l2_rows(stacked.mean(axis=0, keepdims=True))[0]
    meta = {
        "sample_rate": SAMPLE_RATE,
        "clip_seconds": CLIP_SECONDS,
        "clip_count": len(starts),
        "clip_start_seconds": [round(start / SAMPLE_RATE, 3) for start in starts],
        "duration_seconds": round(float(waveform.size) / SAMPLE_RATE, 3),
        "aggregation": "mean of per-clip L2-normalized embeddings, then L2-normalize",
        "native_rand_trunc_neutralized": True,
        "staging": "exact deterministic native 10-second float32 arrays",
    }
    return aggregate, meta


def _rank_axis(audio_embedding: Any, text_embeddings: Any, rows: list[dict[str, str]], *, top_k: int) -> list[dict[str, Any]]:
    import numpy as np

    scores = np.asarray(text_embeddings, dtype=np.float32) @ np.asarray(audio_embedding, dtype=np.float32)
    ranked = sorted(
        [
            {
                "id": str(row["id"]),
                "label": str(row["label"]),
                "similarity": float(score),
            }
            for row, score in zip(rows, scores.tolist())
        ],
        key=lambda item: item["similarity"],
        reverse=True,
    )
    return ranked[:top_k]


def _write_text_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "SONICTRACE V4 MODEL LAB — Native LAION CLAP Music",
        "=" * 60,
        f"Generated: {payload['generated_at']}",
        f"Model: {payload['model']['name']} / {payload['model']['checkpoint_file']}",
        f"Package: laion-clap {payload['model']['package_version']}",
        f"Checkpoint SHA-256: {payload['model']['checkpoint_sha256']}",
        f"Audio policy: {payload['model']['audio_policy']}",
        f"Licenses: code {payload['model']['code_license']} | checkpoint repo {payload['model']['weights_license']}",
        "Declared TXT metadata used for inference: NO",
        "",
    ]
    for track in payload["tracks"]:
        sampling = track["audio_sampling"]
        lines.extend([
            f"## {track['file']}",
            f"Benchmark: {track['benchmark']['status']}",
            f"Elapsed: {track['elapsed_seconds']:.1f}s | Peak GPU memory: {track['peak_gpu_memory_mib']} MiB",
            f"Clips: {sampling['clip_count']} x {sampling['clip_seconds']:.0f}s @ 48kHz | starts: {sampling['clip_start_seconds']}",
        ])
        for axis in AXES:
            rows = track["axes"].get(axis) or []
            rendered = " | ".join(f"{row['label']} {row['similarity']:.4f}" for row in rows[:5])
            lines.append(f"{axis.upper()}: {rendered}")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SonicTrace V4 native LAION CLAP music audio-only benchmark.")
    parser.add_argument("audio", nargs="+", type=Path, help="One or more WAV/MP3 files.")
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--benchmarks", type=Path, default=DEFAULT_BENCHMARKS)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument("--clips", type=int, default=DEFAULT_CLIPS)
    args = parser.parse_args()

    if args.clips < 1 or args.clips > 9:
        raise SystemExit("--clips must be between 1 and 9.")

    import numpy as np
    import torch
    import laion_clap

    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    if not device.startswith("cuda"):
        raise SystemExit("Native LAION CLAP Model Lab requires an NVIDIA CUDA GPU for this benchmark.")

    runtime_dir = args.runtime.resolve()
    checkpoint = (
        args.checkpoint.resolve()
        if args.checkpoint is not None
        else (runtime_dir / "native_laion_music" / CHECKPOINT_FILE).resolve()
    )
    if not checkpoint.exists():
        raise SystemExit(
            f"Native LAION checkpoint not found: {checkpoint}\n"
            "Run SONICTRACE_V4_NATIVE_LAION_MUSIC_SETUP.cmd first."
        )

    print("[VERIFY] Checking native LAION checkpoint SHA-256...")
    checkpoint_sha = _sha256(checkpoint)
    if checkpoint_sha.lower() != CHECKPOINT_SHA256:
        raise SystemExit(f"Checkpoint SHA-256 mismatch: {checkpoint_sha}")

    taxonomy = _load_taxonomy(args.taxonomy.resolve())
    gpu = _gpu_info()
    if not gpu.get("available"):
        raise SystemExit(f"NVIDIA GPU not available through nvidia-smi: {gpu.get('error')}")

    package_version = importlib.metadata.version(MODEL_PACKAGE)
    if package_version != MODEL_PACKAGE_VERSION:
        raise SystemExit(f"Unexpected laion-clap version: {package_version}")

    print("\n=== SONICTRACE V4 MODEL LAB — Native LAION CLAP Music ===")
    print(f"GPU: {gpu.get('name')} | VRAM: {gpu.get('memory_total_mib')} MiB")
    print(f"Model: {AUDIO_MODEL} / {CHECKPOINT_FILE} | 48 kHz | {args.clips} deterministic exact 10s clips/track")
    print(f"Checkpoint SHA-256: {checkpoint_sha}")
    print("License boundary: Apache-2.0 code | CC0-1.0 checkpoint repository | product legal review before shipping")
    print("Inference input: AUDIO ONLY. TXT metadata is benchmark-only.\n")
    print("[INIT] Loading native LAION HTSAT-base music checkpoint...")

    model = laion_clap.CLAP_Module(enable_fusion=False, device=device, amodel=AUDIO_MODEL)
    model.load_ckpt(str(checkpoint), verbose=False)
    print("[OK] Native LAION checkpoint loaded. Precomputing generic taxonomy text embeddings...")
    text_embeddings = _encode_text_axes(model, taxonomy)
    dimension = int(next(iter(text_embeddings.values())).shape[-1])
    print(f"[OK] Taxonomy embeddings ready ({dimension}D).")

    args.results.mkdir(parents=True, exist_ok=True)
    tracks: list[dict[str, Any]] = []

    for audio in args.audio:
        audio = audio.resolve()
        if not audio.exists():
            raise FileNotFoundError(audio)

        print(f"\n--- {audio.name} ---")
        sampler = GPUSampler()
        sampler.start()
        started = time.perf_counter()
        try:
            audio_embedding, sampling_meta = _encode_audio_track(model, audio, clips=args.clips)
            axes = {
                axis: _rank_axis(audio_embedding, text_embeddings[axis], taxonomy[axis], top_k=args.top_k)
                for axis in AXES
            }
            # Critical no-cheating boundary: benchmark/reference truth is loaded
            # only after all four audio-only rankings are complete.
            benchmark = _load_benchmark(args.benchmarks.resolve(), audio)
            evaluation = _evaluate(benchmark, axes)
        finally:
            sampler.stop()

        elapsed = time.perf_counter() - started
        peak_mib = sampler.peak_mib
        for axis in AXES:
            rows = axes.get(axis) or []
            rendered = " | ".join(f"{row['label']} {row['similarity']:.4f}" for row in rows[:5])
            print(f"{axis:<10}: {rendered}")
        print(f"BENCHMARK : {evaluation['status']} | {elapsed:.1f}s | peak VRAM {peak_mib} MiB")

        tracks.append({
            "file": audio.name,
            "path": str(audio),
            "elapsed_seconds": round(elapsed, 3),
            "peak_gpu_memory_mib": peak_mib,
            "audio_sampling": sampling_meta,
            "embedding_dimension": int(audio_embedding.shape[-1]),
            "axes": axes,
            "benchmark": evaluation,
        })

    generated_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema": "sonictrace-v4-model-lab-native-laion-music-result-v1",
        "generated_at": generated_at,
        "inference": {
            "audio_only": True,
            "declared_metadata_used_for_inference": False,
        },
        "model": {
            "name": MODEL_NAME,
            "package": MODEL_PACKAGE,
            "package_version": package_version,
            "audio_model": AUDIO_MODEL,
            "checkpoint_repo": CHECKPOINT_REPO,
            "checkpoint_file": CHECKPOINT_FILE,
            "checkpoint_sha256": checkpoint_sha,
            "embedding_dimension": dimension,
            "sample_rate": SAMPLE_RATE,
            "clip_seconds": CLIP_SECONDS,
            "audio_policy": "5 deterministic evenly spaced exact 10-second clips; normalized embedding mean",
            "code_license": "Apache-2.0",
            "weights_license": "CC0-1.0 (checkpoint repository metadata)",
            "license_gate": "Commercially plausible; perform product legal review before shipping.",
        },
        "gpu": gpu,
        "tracks": tracks,
    }

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = args.results / f"native-laion-music-benchmark-{stamp}.json"
    txt_path = args.results / f"native-laion-music-benchmark-{stamp}.txt"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _write_text_report(txt_path, payload)
    print(f"\n[OK] JSON: {json_path}")
    print(f"[OK] TXT : {txt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
