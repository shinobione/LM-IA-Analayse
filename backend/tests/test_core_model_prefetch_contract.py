from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"Missing {label}: {needle!r}")


def main() -> None:
    helper = (BACKEND / "prefetch_core_models.py").read_text(encoding="utf-8")
    repair = (ROOT / "SONICTRACE_REPAIR_MODELS.cmd").read_text(encoding="utf-8")
    launcher = (ROOT / "LMNotebook_START.cmd").read_text(encoding="utf-8")
    requirements = (BACKEND / "requirements-neural.txt").read_text(encoding="utf-8")

    require(requirements, "hf-xet>=1.1,<2", "Xet transport dependency")

    require(helper, 'CLAP_MODEL_ID = os.getenv("LMN_NEURAL_MODEL", "laion/clap-htsat-unfused")', "production CLAP identity")
    require(helper, 'os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "300")', "bounded large-file timeout")
    require(helper, "DOWNLOAD_ATTEMPTS", "bounded retry policy")
    require(helper, "local_files_only=True", "offline cache validation")
    require(helper, "music_expert._load_metadata", "production Discogs metadata loader")
    require(helper, "music_expert._load_session", "production Discogs ONNX loader")
    require(helper, "MODEL_EXPECTED_BYTES", "Discogs exact-size validation")
    require(helper, "SONICTRACE CORE MODEL ASSETS READY", "explicit ready gate")
    require(helper, "READY_MANIFEST", "durable prefetch evidence")

    require(launcher, "prefetch_core_models.py", "launcher prefetch before API start")
    require(launcher, "goto :model_assets_fail", "fail-closed cold-cache gate")
    require(launcher, "V2-B Neural CUDA + MODELS PRETS", "post-prefetch readiness wording")
    if "decho " in launcher:
        raise AssertionError("Launcher contains a malformed 'decho' command.")

    require(repair, "LMNotebook_STOP.cmd", "active-runtime stop before model repair")
    require(repair, "requirements-neural.txt", "repair transport dependency sync")
    require(repair, "prefetch_core_models.py", "repair prefetch helper")
    require(repair, "SONICTRACE_START.cmd", "canonical restart after repair")
    if "wsl" in repair.lower():
        raise AssertionError("Core model repair must never invoke or configure WSL.")
    if "model_lab" in repair.lower():
        raise AssertionError("Core model repair must stay isolated from V4 Model Lab.")

    print("Core model prefetch contract: PASS")


if __name__ == "__main__":
    main()
