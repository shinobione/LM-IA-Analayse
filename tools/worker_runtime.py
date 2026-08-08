from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
VENV_PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
LOGS = ROOT / "logs"
RUNTIME_FILE = ROOT / ".lmn-worker-runtime.json"
PORT = int(os.getenv("LMN_WORKER_PORT", "8001"))
HOST = os.getenv("LMN_WORKER_HOST", "0.0.0.0")


def _creation_flags() -> int:
    if os.name != "nt":
        return 0
    return subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW


def _read_runtime() -> dict:
    try:
        return json.loads(RUNTIME_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _kill_pid(pid: object) -> None:
    try:
        numeric = int(pid)
    except (TypeError, ValueError):
        return
    if numeric <= 0:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(numeric), "/T", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    else:
        try:
            os.kill(numeric, 15)
        except OSError:
            pass


def start() -> int:
    if not VENV_PYTHON.exists():
        print("[ERREUR] Environnement Python LMNotebook introuvable.")
        return 1

    LOGS.mkdir(parents=True, exist_ok=True)
    log_path = LOGS / "worker.log"
    log = open(log_path, "a", encoding="utf-8", buffering=1)
    log.write(f"\n===== worker launch {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")

    env = os.environ.copy()
    env.setdefault("LMN_NODE_NAME", os.getenv("COMPUTERNAME", "RTX3070TI-WORKER"))
    env["LMN_NODE_ROLE"] = "gpu-worker"
    env["LMN_WORKERS"] = ""
    env["LMN_DISCOVER_WORKERS"] = "0"

    process = subprocess.Popen(
        [str(VENV_PYTHON), "-m", "uvicorn", "app.main:app", "--host", HOST, "--port", str(PORT)],
        cwd=str(BACKEND),
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        env=env,
        creationflags=_creation_flags(),
        close_fds=True,
    )
    RUNTIME_FILE.write_text(json.dumps({"pid": process.pid, "port": PORT, "started_at": time.strftime('%Y-%m-%dT%H:%M:%S')}, indent=2), encoding="utf-8")
    print(f"[OK] Worker LMNotebook lancé sur le port {PORT} (PID {process.pid}).")
    return 0


def stop() -> int:
    runtime = _read_runtime()
    _kill_pid(runtime.get("pid"))
    try:
        RUNTIME_FILE.unlink(missing_ok=True)
    except OSError:
        pass
    print("[OK] Worker LMNotebook arrêté.")
    return 0


def main() -> int:
    action = (sys.argv[1] if len(sys.argv) > 1 else "start").lower()
    if action == "start":
        return start()
    if action == "stop":
        return stop()
    print("Usage: worker_runtime.py [start|stop]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
