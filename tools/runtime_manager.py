from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
VENV_PYTHON = BACKEND / ".venv" / "Scripts" / "python.exe"
LOGS = ROOT / "logs"
RUNTIME_FILE = ROOT / ".lmn-runtime.json"
API_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:8008"
EXPECTED_API_SCHEMA = "2.1"


def _http_json(url: str, timeout: float = 1.5) -> dict[str, Any] | None:
    try:
        request = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                return None
            return json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError):
        return None


def _http_ok(url: str, timeout: float = 1.5) -> bool:
    try:
        request = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


def api_health() -> dict[str, Any] | None:
    return _http_json(f"{API_URL}/api/health")


def api_ready() -> bool:
    payload = api_health()
    return bool(
        payload
        and str(payload.get("service", "")).startswith("LMNotebook")
        and str(payload.get("api_schema", "")) == EXPECTED_API_SCHEMA
    )


def frontend_ready() -> bool:
    return _http_ok(FRONTEND_URL)


def wait_for(check: Callable[[], bool], timeout_seconds: float) -> bool:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if check():
            return True
        time.sleep(0.5)
    return check()


def _creation_flags() -> int:
    if os.name != "nt":
        return 0
    return subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW


def spawn_process(args: list[str], cwd: Path, log_path: Path) -> int:
    LOGS.mkdir(parents=True, exist_ok=True)
    log_handle = open(log_path, "a", encoding="utf-8", buffering=1)
    log_handle.write(f"\n\n===== LMNotebook launch {time.strftime('%Y-%m-%d %H:%M:%S')} =====\n")
    process = subprocess.Popen(
        args,
        cwd=str(cwd),
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        creationflags=_creation_flags(),
        close_fds=True,
    )
    return process.pid


def read_runtime() -> dict[str, Any]:
    try:
        return json.loads(RUNTIME_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}


def write_runtime(api_pid: int | None, frontend_pid: int | None) -> None:
    previous = read_runtime()
    payload = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "api_pid": api_pid or previous.get("api_pid"),
        "frontend_pid": frontend_pid or previous.get("frontend_pid"),
        "api": API_URL,
        "frontend": FRONTEND_URL,
        "api_schema": EXPECTED_API_SCHEMA,
    }
    RUNTIME_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def tail(path: Path, lines: int = 35) -> str:
    try:
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return "(aucun log disponible)"
    return "\n".join(content[-lines:]) or "(log vide)"


def kill_pid(pid: Any) -> None:
    try:
        numeric_pid = int(pid)
    except (TypeError, ValueError):
        return
    if numeric_pid <= 0:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(numeric_pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        try:
            os.kill(numeric_pid, 15)
        except OSError:
            pass


def stop_spawned(api_pid: int | None, frontend_pid: int | None) -> None:
    kill_pid(api_pid)
    kill_pid(frontend_pid)


def stop_previous_runtime_if_incompatible() -> None:
    current = api_health()
    if not current or str(current.get("api_schema", "")) == EXPECTED_API_SCHEMA:
        return
    print(
        f"[runtime] Ancienne API detectee (schema {current.get('api_schema') or 'legacy'}). "
        f"Redemarrage vers {EXPECTED_API_SCHEMA}..."
    )
    runtime = read_runtime()
    kill_pid(runtime.get("api_pid"))
    time.sleep(1.0)


def start() -> int:
    if not VENV_PYTHON.exists():
        print("[ERREUR] Python prive LMNotebook introuvable.")
        return 1

    LOGS.mkdir(parents=True, exist_ok=True)
    api_log = LOGS / "backend.log"
    frontend_log = LOGS / "frontend.log"

    api_pid: int | None = None
    frontend_pid: int | None = None

    stop_previous_runtime_if_incompatible()

    print(f"[runtime] Verification du backend V2 schema {EXPECTED_API_SCHEMA}...")
    if api_ready():
        print("[OK] API V2 deja active sur 127.0.0.1:8000")
    else:
        api_pid = spawn_process(
            [
                str(VENV_PYTHON),
                "-m",
                "uvicorn",
                "app.main:app",
                "--host",
                "127.0.0.1",
                "--port",
                "8000",
            ],
            BACKEND,
            api_log,
        )
        print(f"[runtime] API lancee en arriere-plan (PID {api_pid})")
        if not wait_for(api_ready, 30):
            print("\n[ERREUR] L'API V2.1 n'a pas repondu dans les 30 secondes.")
            print("--- backend.log ---")
            print(tail(api_log))
            stop_spawned(api_pid, None)
            return 1
        print("[OK] API V2.1 repond correctement.")

    print("[runtime] Verification du frontend local...")
    if frontend_ready():
        print("[OK] Frontend deja actif sur 127.0.0.1:8008")
    else:
        frontend_pid = spawn_process(
            [
                str(VENV_PYTHON),
                "-m",
                "http.server",
                "8008",
                "--bind",
                "127.0.0.1",
            ],
            ROOT,
            frontend_log,
        )
        print(f"[runtime] Frontend lance en arriere-plan (PID {frontend_pid})")
        if not wait_for(frontend_ready, 12):
            print("\n[ERREUR] Le frontend local n'a pas repondu.")
            print("--- frontend.log ---")
            print(tail(frontend_log))
            stop_spawned(api_pid, frontend_pid)
            return 1
        print("[OK] Frontend local repond correctement.")

    write_runtime(api_pid, frontend_pid)

    health = api_health() or {}
    gpu_count = len(health.get("gpus") or [])
    ffmpeg = health.get("ffmpeg") or {}
    neural = health.get("neural") or {}
    print(
        f"[OK] Deep Audio V2 ONLINE | GPU locales: {gpu_count} | "
        f"FFmpeg: {'READY' if ffmpeg.get('ffmpeg') and ffmpeg.get('ffprobe') else 'DEGRADED'}"
    )
    if neural.get("ready"):
        print(
            f"[OK] V2-B NEURAL CUDA READY | {neural.get('device_name') or 'GPU'} | "
            f"Torch {neural.get('torch_version') or '?'} | CUDA {neural.get('cuda_runtime') or '?'}"
        )
    else:
        print(f"[INFO] V2-B Neural non active: {neural.get('error') or 'runtime optionnel indisponible'}")

    local_url = f"{FRONTEND_URL}/?runtime=local-v2"
    print(f"[runtime] Ouverture de {local_url}")
    webbrowser.open(local_url)
    print("[OK] LMNotebook local V2 est pret.")
    return 0


def stop() -> int:
    runtime = read_runtime()
    print("Arret des processus LMNotebook geres...")
    kill_pid(runtime.get("api_pid"))
    kill_pid(runtime.get("frontend_pid"))
    try:
        RUNTIME_FILE.unlink(missing_ok=True)
    except OSError:
        pass
    print("[OK] LMNotebook est arrete.")
    return 0


def main() -> int:
    action = (sys.argv[1] if len(sys.argv) > 1 else "start").lower()
    if action == "start":
        return start()
    if action == "stop":
        return stop()
    print("Usage: runtime_manager.py [start|stop]")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
