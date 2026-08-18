from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path


UPSTREAM_COMMIT = "3d0c4de9447c404a8d3f9f37e04f53bc902e09b3"
MODEL_DIR_NAME = "m2d_clap_vit_base-80x1001p16x16p16kpBpTI-2025"
CHECKPOINT_FILE = "checkpoint-30.pth"
RELEASE_URL = (
    "https://github.com/nttcslab/m2d/releases/download/v0.5.0/"
    "m2d_clap_vit_base-80x1001p16x16p16kpBpTI-2025.zip"
)
PORTABLE_URL = (
    "https://raw.githubusercontent.com/nttcslab/m2d/"
    f"{UPSTREAM_COMMIT}/examples/portable_m2d.py"
)


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    if partial.exists():
        partial.unlink()

    request = urllib.request.Request(url, headers={"User-Agent": "SonicTrace-V4-Model-Lab/1.0"})
    print(f"[DOWNLOAD] {url}")
    with urllib.request.urlopen(request, timeout=90) as response, partial.open("wb") as handle:
        total_raw = response.headers.get("Content-Length")
        total = int(total_raw) if total_raw and total_raw.isdigit() else 0
        read = 0
        last_bucket = -1
        while True:
            chunk = response.read(4 * 1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)
            read += len(chunk)
            if total:
                bucket = int((read * 20) / total)
                if bucket != last_bucket:
                    last_bucket = bucket
                    print(f"  {min(100, int(read * 100 / total)):3d}%  {read / (1024**2):.1f}/{total / (1024**2):.1f} MiB")
            elif read % (64 * 1024 * 1024) < len(chunk):
                print(f"  {read / (1024**2):.1f} MiB")
    partial.replace(destination)
    print(f"[OK] Downloaded: {destination}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _prepare_assets(runtime: Path) -> tuple[Path, Path, str]:
    asset_root = runtime / "m2d_clap_2025"
    source_root = runtime / "m2d_clap_2025_src"
    model_dir = asset_root / MODEL_DIR_NAME
    checkpoint = model_dir / CHECKPOINT_FILE
    archive = asset_root / f"{MODEL_DIR_NAME}.zip"
    portable = source_root / "portable_m2d.py"

    asset_root.mkdir(parents=True, exist_ok=True)
    source_root.mkdir(parents=True, exist_ok=True)

    # The source URL includes the exact upstream commit, so refreshing this tiny
    # file makes the runtime reproducible without cloning the entire repository.
    _download(PORTABLE_URL, portable)
    text = portable.read_text(encoding="utf-8")
    if "class PortableM2D" not in text or "def encode_clap_audio" not in text or "def encode_clap_text" not in text:
        raise RuntimeError("Pinned portable_m2d.py does not expose the expected M2D-CLAP runtime API.")

    if not checkpoint.exists():
        if not archive.exists():
            _download(RELEASE_URL, archive)
        try:
            with zipfile.ZipFile(archive, "r") as zipped:
                bad_member = zipped.testzip()
                if bad_member:
                    raise RuntimeError(f"Corrupt M2D-CLAP release archive member: {bad_member}")
                print(f"[EXTRACT] {archive.name}")
                zipped.extractall(asset_root)
        except zipfile.BadZipFile as exc:
            raise RuntimeError(f"Invalid M2D-CLAP release archive: {archive}") from exc

    if not checkpoint.exists():
        matches = [p for p in asset_root.rglob(CHECKPOINT_FILE) if p.is_file()]
        if len(matches) != 1:
            raise RuntimeError(f"Expected exactly one {CHECKPOINT_FILE}, found {len(matches)} under {asset_root}")
        model_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(matches[0], checkpoint)

    checkpoint_hash = _sha256(checkpoint)
    lock = checkpoint.with_name(checkpoint.name + ".sha256")
    if lock.exists():
        previous = lock.read_text(encoding="ascii").strip().lower()
        if previous and previous != checkpoint_hash.lower():
            raise RuntimeError(
                "Local M2D-CLAP checkpoint changed since first successful download: "
                f"expected {previous}, got {checkpoint_hash}"
            )
    else:
        lock.write_text(checkpoint_hash + "\n", encoding="ascii")

    print(f"[OK] Checkpoint: {checkpoint}")
    print(f"[OK] Checkpoint SHA-256 (local lock): {checkpoint_hash}")
    print(f"[OK] Portable source: upstream {UPSTREAM_COMMIT}")
    return checkpoint, portable, checkpoint_hash


def _load_portable(portable: Path):
    spec = importlib.util.spec_from_file_location("sonictrace_m2d_portable", portable)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load portable M2D source: {portable}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _verify_runtime(checkpoint: Path, portable: Path) -> None:
    import numpy as np
    import torch
    import transformers

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is not available. Candidate F requires an NVIDIA CUDA GPU.")

    module = _load_portable(portable)
    device = torch.device("cuda:0")
    print("[VERIFY] Loading real M2D-CLAP 2025 checkpoint on CUDA...")
    model = module.PortableM2D(weight_file=str(checkpoint), flat_features=True).to(device).eval()

    # Exercise BOTH official CLAP paths before allowing READY. The 10-second
    # deterministic ramp is only a setup smoke input, never a benchmark sample.
    with torch.no_grad():
        audio = torch.linspace(-0.08, 0.08, steps=16000 * 10, dtype=torch.float32, device=device).unsqueeze(0)
        audio_emb = model.encode_clap_audio(audio)
        text_emb = model.encode_clap_text(
            ["This audio is a rock song.", "This audio is a classical song."],
            truncate=True,
        )

    if tuple(audio_emb.shape) != (1, 768):
        raise RuntimeError(f"Unexpected M2D-CLAP audio embedding shape: {tuple(audio_emb.shape)}")
    if tuple(text_emb.shape) != (2, 768):
        raise RuntimeError(f"Unexpected M2D-CLAP text embedding shape: {tuple(text_emb.shape)}")
    if not torch.isfinite(audio_emb).all() or not torch.isfinite(text_emb).all():
        raise RuntimeError("M2D-CLAP produced non-finite setup embeddings.")
    if float(torch.linalg.vector_norm(audio_emb[0]).item()) <= 1e-8:
        raise RuntimeError("M2D-CLAP produced a zero-norm audio embedding.")
    if float(torch.linalg.vector_norm(text_emb[0]).item()) <= 1e-8:
        raise RuntimeError("M2D-CLAP produced a zero-norm text embedding.")

    try:
        timm_version = importlib.metadata.version("timm")
        nnaudio_version = importlib.metadata.version("nnAudio")
        einops_version = importlib.metadata.version("einops")
    except importlib.metadata.PackageNotFoundError as exc:
        raise RuntimeError(f"Missing pinned M2D-CLAP dependency: {exc}") from exc

    print(f"[OK] GPU: {torch.cuda.get_device_name(0)}")
    print(f"[OK] Torch {torch.__version__} CUDA {torch.version.cuda} NumPy {np.__version__}")
    print(f"[OK] Transformers {transformers.__version__} timm {timm_version} nnAudio {nnaudio_version} einops {einops_version}")
    print(f"[OK] Real M2D-CLAP audio/text embeddings active: {tuple(audio_emb.shape)} / {tuple(text_emb.shape)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare and verify the isolated SonicTrace M2D-CLAP 2025 runtime.")
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()

    runtime = args.runtime.resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    checkpoint, portable, _ = _prepare_assets(runtime)
    _verify_runtime(checkpoint, portable)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
