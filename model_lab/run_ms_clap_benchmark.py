from __future__ import annotations

import argparse
import hashlib
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
MODEL_REPO = "microsoft/msclap"
MODEL_VERSION = "2023"
WEIGHTS_FILE = "CLAP_weights_2023.pth"
OFFICIAL_CODE_COMMIT = "e8a6467b87cd85716e20c6a008126150d9740be0"
WEIGHTS_SHA256 = "2cef4016d47d00eb28d153d522f397222057f95000e9bad6b9583c631284a1e6"
SAMPLE_RATE = 44100
CLIP_SECONDS = 7.0
DEFAULT_CLIPS = 5
TEXT_BATCH = 12


def _normalize(value: str) -> str:
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

        self._thread = threading.Thread(target=worker, name="sonictrace-msclap-gpu-sampler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)


def _load_taxonomy(path: Path) -> dict[str, list[dict[str, str]]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("inference_policy", {}).get("declared_metadata_used_for_inference") is not False:
        raise RuntimeError("Taxonomy inference policy must keep declared metadata out of inference.")
    axes = payload.get("axes") or {}
    return {axis: list(axes.get(axis) or []) for axis in AXES}


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


def _clip_starts(total_samples: int, *, clips: int) -> list[int]:
    import numpy as np

    clip_samples = int(round(SAMPLE_RATE * CLIP_SECONDS))
    max_start = max(0, total_samples - clip_samples)
    if max_start == 0 or clips <= 1:
        return [0]
    # Model Lab policy: deterministic whole-song coverage. The official msclap
    # wrapper normally random-crops long sources, so we stage exact 7-second
    # clips ourselves and never let benchmark truth influence clip selection.
    return sorted({int(round(value)) for value in np.linspace(0, max_start, num=clips)})


def _coerce_embeddings(value: Any, *, expected_batch: int, torch_module: Any) -> Any:
    if not torch_module.is_tensor(value):
        raise TypeError(f"Microsoft CLAP returned unsupported embedding type: {type(value).__name__}")
    tensor = value.float()
    if tensor.ndim == 1:
        tensor = tensor.unsqueeze(0)
    if tensor.ndim != 2 or tensor.shape[0] != expected_batch:
        raise RuntimeError(f"Unexpected Microsoft CLAP embedding shape: {tuple(tensor.shape)}")
    return tensor


def _encode_text_axes(model: Any, taxonomy: dict[str, list[dict[str, str]]], device: str) -> dict[str, Any]:
    import torch
    import torch.nn.functional as F

    encoded: dict[str, Any] = {}
    for axis in AXES:
        rows = taxonomy[axis]
        prompts = [str(row["prompt"]) for row in rows]
        chunks = []
        for start in range(0, len(prompts), TEXT_BATCH):
            batch = prompts[start : start + TEXT_BATCH]
            with torch.no_grad():
                raw = model.get_text_embeddings(batch)
            emb = _coerce_embeddings(raw, expected_batch=len(batch), torch_module=torch)
            chunks.append(F.normalize(emb, dim=-1).detach().cpu())
        encoded[axis] = torch.cat(chunks, dim=0)
        if device == "cuda":
            torch.cuda.empty_cache()
    return encoded


def _encode_audio_track(
    model: Any,
    audio: Path,
    *,
    clips: int,
    device: str,
    stage_dir: Path,
) -> tuple[Any, dict[str, Any]]:
    import librosa
    import numpy as np
    import soundfile as sf
    import torch
    import torch.nn.functional as F

    waveform, _ = librosa.load(str(audio), sr=SAMPLE_RATE, mono=True, dtype=np.float32)
    waveform = np.asarray(waveform, dtype=np.float32)
    if waveform.size == 0:
        raise RuntimeError(f"Decoded audio is empty: {audio}")

    clip_samples = int(round(SAMPLE_RATE * CLIP_SECONDS))
    starts = _clip_starts(int(waveform.size), clips=clips)
    stage_dir.mkdir(parents=True, exist_ok=True)
    token = hashlib.sha1(str(audio).encode("utf-8", errors="replace")).hexdigest()[:12]
    embeddings = []
    staged_paths: list[Path] = []

    try:
        for index, start in enumerate(starts):
            segment = waveform[start : start + clip_samples]
            if segment.size < clip_samples:
                segment = np.pad(segment, (0, clip_samples - segment.size), mode="constant")
            staged = stage_dir / f"clip-{token}-{index:02d}.wav"
            # Exact 7-second WAVs neutralize msclap's random long-file trim:
            # its >= duration branch repeats by factor 1 and slices deterministically.
            sf.write(str(staged), np.asarray(segment, dtype=np.float32), SAMPLE_RATE, subtype="FLOAT")
            staged_paths.append(staged)
            with torch.no_grad():
                raw = model.get_audio_embeddings([str(staged)], resample=True)
            emb = _coerce_embeddings(raw, expected_batch=1, torch_module=torch)
            embeddings.append(F.normalize(emb, dim=-1).squeeze(0).detach().cpu())
            del raw, emb
            if device == "cuda":
                torch.cuda.empty_cache()
    finally:
        for staged in staged_paths:
            staged.unlink(missing_ok=True)

    if not embeddings:
        raise RuntimeError(f"No Microsoft CLAP audio embedding produced for: {audio}")

    stacked = torch.stack(embeddings, dim=0)
    aggregate = F.normalize(stacked.mean(dim=0, keepdim=True), dim=-1).squeeze(0)
    meta = {
        "sample_rate": SAMPLE_RATE,
        "clip_seconds": CLIP_SECONDS,
        "clip_count": len(starts),
        "clip_start_seconds": [round(start / SAMPLE_RATE, 3) for start in starts],
        "duration_seconds": round(float(waveform.size) / SAMPLE_RATE, 3),
        "aggregation": "mean of per-clip L2-normalized embeddings, then L2-normalize",
        "official_wrapper_random_crop_neutralized": True,
        "staging": "exact deterministic 7-second WAV clips",
    }
    return aggregate, meta


def _rank_axis(audio_embedding: Any, text_embeddings: Any, rows: list[dict[str, str]], *, top_k: int) -> list[dict[str, Any]]:
    import torch

    scores = torch.matmul(text_embeddings, audio_embedding).detach().cpu().tolist()
    ranked = sorted(
        [
            {
                "id": str(row["id"]),
                "label": str(row["label"]),
                "similarity": float(score),
            }
            for row, score in zip(rows, scores)
        ],
        key=lambda item: item["similarity"],
        reverse=True,
    )
    return ranked[:top_k]


def _write_text_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "SONICTRACE V4 MODEL LAB — Microsoft CLAP 2023",
        "=" * 60,
        f"Generated: {payload['generated_at']}",
        f"Model: {payload['model']['id']} / {payload['model']['weights_file']}",
        f"Official code commit: {payload['model']['official_code_commit']}",
        f"Audio policy: {payload['model']['audio_policy']}",
        f"Licenses: code {payload['model']['code_license']} | weights {payload['model']['weights_license']}",
        "Declared TXT metadata used for inference: NO",
        "",
    ]
    for track in payload["tracks"]:
        segment = track["audio_sampling"]
        lines.extend([
            f"## {track['file']}",
            f"Benchmark: {track['benchmark']['status']}",
            f"Elapsed: {track['elapsed_seconds']:.1f}s | Peak GPU memory: {track['peak_gpu_memory_mib']} MiB",
            f"Clips: {segment['clip_count']} x {segment['clip_seconds']:.0f}s @ 44.1kHz | starts: {segment['clip_start_seconds']}",
        ])
        for axis in AXES:
            rows = track["axes"].get(axis) or []
            rendered = " | ".join(f"{row['label']} {row['similarity']:.4f}" for row in rows[:5])
            lines.append(f"{axis.upper()}: {rendered}")
        lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SonicTrace V4 Model Lab Microsoft CLAP 2023 audio-only benchmark.")
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

    import torch
    from msclap import CLAP

    runtime_dir = args.runtime.resolve()
    taxonomy_path = args.taxonomy.resolve()
    stage_dir = runtime_dir / "msclap_staged"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if device != "cuda":
        raise SystemExit("Microsoft CLAP Model Lab requires an NVIDIA CUDA GPU for this benchmark.")

    taxonomy = _load_taxonomy(taxonomy_path)
    gpu = _gpu_info()
    if not gpu.get("available"):
        raise SystemExit(f"NVIDIA GPU not available through nvidia-smi: {gpu.get('error')}")

    print("\n=== SONICTRACE V4 MODEL LAB — Microsoft CLAP 2023 ===")
    print(f"GPU: {gpu.get('name')} | VRAM: {gpu.get('memory_total_mib')} MiB")
    print(f"Model: {MODEL_REPO} / {WEIGHTS_FILE} | 44.1 kHz | {args.clips} deterministic 7s clips/track")
    print("License boundary: MIT code | MS-PL weights | product legal review before shipping")
    print("Inference input: AUDIO ONLY. TXT metadata is benchmark-only.\n")
    print("[INIT] Loading Microsoft CLAP 2023. First run may download checkpoint + GPT-2...")

    torch.set_grad_enabled(False)
    model = CLAP(version=MODEL_VERSION, use_cuda=True)
    print("[OK] Microsoft CLAP loaded. Precomputing generic taxonomy text embeddings...")
    text_embeddings = _encode_text_axes(model, taxonomy, device)
    embedding_dimension = int(next(iter(text_embeddings.values())).shape[-1])
    print(f"[OK] Taxonomy embeddings ready ({embedding_dimension}D).\n")

    report: dict[str, Any] = {
        "schema": "sonictrace-v4-model-lab-msclap-result-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inference": {"audio_only": True, "declared_metadata_used_for_inference": False},
        "model": {
            "name": "Microsoft CLAP",
            "id": MODEL_REPO,
            "version": MODEL_VERSION,
            "weights_file": WEIGHTS_FILE,
            "weights_sha256": WEIGHTS_SHA256,
            "official_code_commit": OFFICIAL_CODE_COMMIT,
            "embedding_dimension": embedding_dimension,
            "sample_rate": SAMPLE_RATE,
            "clip_seconds": CLIP_SECONDS,
            "audio_policy": f"{args.clips} deterministic evenly spaced native 7-second clips; normalized embedding mean",
            "code_license": "MIT",
            "weights_license": "MS-PL",
            "license_gate": "Commercial use is not marked non-commercial; comply with MS-PL terms and perform product legal review before shipping.",
        },
        "gpu": gpu,
        "tracks": [],
    }

    for requested in args.audio:
        audio = requested.resolve()
        if not audio.exists():
            print(f"[SKIP] Missing file: {audio}")
            continue
        if audio.suffix.lower() not in {".wav", ".mp3"}:
            print(f"[SKIP] Unsupported audio type: {audio}")
            continue

        print(f"--- {audio.name} ---")
        sampler = GPUSampler()
        sampler.start()
        started = time.perf_counter()
        try:
            audio_embedding, sampling_meta = _encode_audio_track(
                model,
                audio,
                clips=args.clips,
                device=device,
                stage_dir=stage_dir,
            )
            axis_results: dict[str, list[dict[str, Any]]] = {}
            for axis in AXES:
                rankings = _rank_axis(
                    audio_embedding,
                    text_embeddings[axis],
                    taxonomy[axis],
                    top_k=args.top_k,
                )
                axis_results[axis] = rankings
                print(f"{axis:10s}: " + " | ".join(f"{row['label']} {row['similarity']:.4f}" for row in rankings[:5]))
        except torch.cuda.OutOfMemoryError as exc:
            torch.cuda.empty_cache()
            raise RuntimeError("Microsoft CLAP ran out of RTX VRAM during deterministic clip inference.") from exc
        finally:
            sampler.stop()

        elapsed_total = time.perf_counter() - started
        # Critical anti-cheating boundary: artist-declared/reference truth is loaded
        # only AFTER audio embedding and all four axis rankings are complete.
        benchmark = _load_benchmark(args.benchmarks.resolve(), audio)
        evaluation = _evaluate(benchmark, axis_results)
        print(f"BENCHMARK : {evaluation['status']} | {elapsed_total:.1f}s | peak VRAM {sampler.peak_mib} MiB\n")
        report["tracks"].append({
            "file": audio.name,
            "path": str(audio),
            "elapsed_seconds": round(elapsed_total, 3),
            "peak_gpu_memory_mib": sampler.peak_mib,
            "audio_sampling": sampling_meta,
            "axes": axis_results,
            "benchmark": evaluation,
        })
        torch.cuda.empty_cache()

    if not report["tracks"]:
        raise SystemExit("No audio file was benchmarked.")

    results_dir = args.results.resolve()
    results_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    json_path = results_dir / f"msclap-benchmark-{stamp}.json"
    txt_path = results_dir / f"msclap-benchmark-{stamp}.txt"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_text_report(txt_path, report)
    print(f"[OK] JSON: {json_path}")
    print(f"[OK] TXT : {txt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
