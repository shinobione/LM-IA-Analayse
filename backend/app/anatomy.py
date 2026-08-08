from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .config import settings

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ANATOMY_PYTHON = BACKEND_ROOT / ".venv-anatomy" / "Scripts" / "python.exe"
ANATOMY_RUNNER = BACKEND_ROOT / "anatomy_runner.py"
ANATOMY_READY_MARKER = BACKEND_ROOT / ".v2c-ready"


def runtime_status(deep: bool = False) -> dict[str, Any]:
    installed = ANATOMY_PYTHON.exists() and ANATOMY_RUNNER.exists()
    preflight_validated = ANATOMY_READY_MARKER.exists()
    status: dict[str, Any] = {
        "installed": installed,
        "preflight_validated": preflight_validated,
        "ready": False,
        "runtime": "isolated",
        "python": str(ANATOMY_PYTHON),
        "engine": "librosa/scipy structural DSP",
    }
    if not installed:
        status["error"] = "Song Anatomy runtime is not installed."
        return status
    if not preflight_validated:
        status["error"] = "Song Anatomy runtime exists but its dependency preflight has not passed."
        return status
    if not deep:
        status["ready"] = True
        status["status_source"] = "launcher-preflight-marker"
        return status

    code = (
        "import json,numpy,scipy,librosa,soundfile;"
        "print(json.dumps({'numpy':numpy.__version__,'scipy':scipy.__version__,"
        "'librosa':librosa.__version__,'soundfile':soundfile.__version__}))"
    )
    try:
        completed = subprocess.run(
            [str(ANATOMY_PYTHON), "-c", code],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            status["error"] = (completed.stderr or completed.stdout or "Song Anatomy import check failed.")[-2000:]
            return status
        details = json.loads(completed.stdout.strip().splitlines()[-1])
        status.update(details)
        status["ready"] = True
        status["status_source"] = "deep-diagnostics"
        return status
    except Exception as exc:  # noqa: BLE001
        status["error"] = f"Song Anatomy diagnostics failed: {exc}"
        return status


def analyze_anatomy(path: Path) -> dict[str, Any]:
    status = runtime_status(deep=False)
    if not status.get("ready"):
        raise RuntimeError(status.get("error") or "Song Anatomy runtime is not ready.")

    temp_wav: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            temp_wav = Path(tmp.name)

        convert = subprocess.run(
            [
                settings.ffmpeg_bin,
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-i",
                str(path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "22050",
                "-c:a",
                "pcm_s16le",
                str(temp_wav),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        if convert.returncode != 0:
            raise RuntimeError(f"FFmpeg anatomy decode failed: {(convert.stderr or convert.stdout)[-2000:]}")

        completed = subprocess.run(
            [str(ANATOMY_PYTHON), str(ANATOMY_RUNNER), str(temp_wav)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=420,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError((completed.stderr or completed.stdout or "Song Anatomy runner failed.")[-4000:])

        lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        if not lines:
            raise RuntimeError("Song Anatomy runner returned no JSON.")
        return json.loads(lines[-1])
    finally:
        if temp_wav and temp_wav.exists():
            try:
                os.remove(temp_wav)
            except OSError:
                pass
