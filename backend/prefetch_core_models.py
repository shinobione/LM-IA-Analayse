from __future__ import annotations

import gc
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, TypeVar

BACKEND_ROOT = Path(__file__).resolve().parent
MODEL_ROOT = BACKEND_ROOT / "models"
HF_HOME = Path(os.getenv("HF_HOME") or (MODEL_ROOT / "huggingface"))
READY_MANIFEST = MODEL_ROOT / "core-models-ready.json"
CLAP_MODEL_ID = os.getenv("LMN_NEURAL_MODEL", "laion/clap-htsat-unfused")
DOWNLOAD_ATTEMPTS = max(1, int(os.getenv("LMN_MODEL_PREFETCH_ATTEMPTS", "3")))

# Hugging Face Hub reads these at import/runtime. Increase the file-transfer timeout
# so a cold Windows cache does not strand a Studio request at 90% while a large
# checkpoint is being fetched over the default short CDN timeout.
os.environ.setdefault("HF_HOME", str(HF_HOME))
os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "300")
os.environ.setdefault("HF_HUB_ETAG_TIMEOUT", "30")
os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")

T = TypeVar("T")


def _retry(label: str, action: Callable[[], T]) -> T:
    last: Exception | None = None
    for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
        try:
            print(f"[..] {label} (attempt {attempt}/{DOWNLOAD_ATTEMPTS})")
            return action()
        except Exception as exc:  # noqa: BLE001
            last = exc
            print(f"[WARN] {label} failed: {type(exc).__name__}: {exc}")
            if attempt < DOWNLOAD_ATTEMPTS:
                time.sleep(min(10, attempt * 3))
    assert last is not None
    raise last


def _prefetch_clap() -> dict[str, object]:
    from huggingface_hub import snapshot_download
    from transformers import ClapModel, ClapProcessor

    HF_HOME.mkdir(parents=True, exist_ok=True)

    # Download/resume the repository first without constructing the model. This
    # keeps a cold-cache transfer out of Studio's POST /api/studio/analyze path.
    snapshot = _retry(
        "CLAP repository download/cache",
        lambda: snapshot_download(repo_id=CLAP_MODEL_ID),
    )

    # The only model construction is deliberately offline-only. If this fails,
    # the local cache cannot satisfy a real analysis and SonicTrace must not start
    # as READY. On a warm cache this also avoids any network dependency.
    print("[..] Validating CLAP from local cache only...")
    processor = ClapProcessor.from_pretrained(CLAP_MODEL_ID, local_files_only=True)
    model = ClapModel.from_pretrained(CLAP_MODEL_ID, local_files_only=True)
    parameter_count = sum(int(param.numel()) for param in model.parameters())
    del processor, model
    gc.collect()

    print(f"[OK] CLAP local cache validated: {CLAP_MODEL_ID}")
    return {
        "model_id": CLAP_MODEL_ID,
        "parameter_count": parameter_count,
        "hf_home": str(HF_HOME),
        "snapshot": str(snapshot),
    }


def _prefetch_discogs() -> dict[str, object]:
    # Reuse SonicTrace's production downloader/size validation instead of
    # duplicating URLs or model metadata in this bootstrap helper.
    from app import music_expert

    metadata = _retry("Discogs-EffNet metadata download/cache", music_expert._load_metadata)
    session, provider = _retry("Discogs-EffNet ONNX download/cache", music_expert._load_session)

    model_path = music_expert.MODEL_DIR / music_expert.MODEL_NAME
    metadata_path = music_expert.MODEL_DIR / music_expert.METADATA_NAME
    if not model_path.is_file() or model_path.stat().st_size != music_expert.MODEL_EXPECTED_BYTES:
        raise RuntimeError("Discogs-EffNet model cache did not pass the production size contract.")
    if not metadata_path.is_file() or metadata_path.stat().st_size < 10_000:
        raise RuntimeError("Discogs-EffNet metadata cache did not pass the production size contract.")
    classes = list(metadata.get("classes") or [])
    if len(classes) != 400:
        raise RuntimeError(f"Discogs metadata must expose 400 classes, found {len(classes)}.")

    # Touch the session metadata so a corrupt ONNX file cannot be marked ready.
    inputs = session.get_inputs()
    outputs = session.get_outputs()
    if not inputs or len(outputs) < 2:
        raise RuntimeError("Discogs-EffNet ONNX session exposes an invalid I/O contract.")

    print(f"[OK] Discogs-EffNet cache validated: {model_path.name} | provider {provider}")
    return {
        "model": music_expert.MODEL_NAME,
        "model_bytes": model_path.stat().st_size,
        "metadata": music_expert.METADATA_NAME,
        "metadata_bytes": metadata_path.stat().st_size,
        "provider": provider,
        "class_count": len(classes),
    }


def main() -> int:
    print("============================================================")
    print(" SonicTrace core model asset prefetch")
    print("============================================================")
    print(f"HF_HOME: {HF_HOME}")
    print("This runs before the local API is declared ready.")
    print()

    MODEL_ROOT.mkdir(parents=True, exist_ok=True)
    READY_MANIFEST.unlink(missing_ok=True)

    try:
        clap = _prefetch_clap()
        discogs = _prefetch_discogs()
    except Exception as exc:  # noqa: BLE001
        print()
        print(f"[ERROR] Core model assets are NOT ready: {type(exc).__name__}: {exc}")
        print("[ERROR] SonicTrace will not be started as READY with an incomplete cold cache.")
        return 1

    payload = {
        "schema": 1,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "clap": clap,
        "discogs_effnet": discogs,
        "policy": "prefetched-and-local-cache-validated-before-api-start",
    }
    READY_MANIFEST.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print()
    print(f"[OK] Ready manifest: {READY_MANIFEST}")
    print("[OK] SONICTRACE CORE MODEL ASSETS READY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
