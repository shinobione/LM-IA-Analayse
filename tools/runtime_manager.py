from __future__ import annotations

import json
import os
import socket
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
API_HOST = "127.0.0.1"
API_PORT = 8000
FRONTEND_PORT = 8008
API_URL = f"http://{API_HOST}:{API_PORT}"
FRONTEND_URL = f"http://{API_HOST}:{FRONTEND_PORT}"
REQUIRED_API_SCHEMA = "2.2"


def _schema_tuple(value: Any) -> tuple[int, int] | None:
    try:
        major_text, minor_text, *_ = str(value).strip().split(".")
        return int(major_text), int(minor_text)
    except (TypeError, ValueError):
        return None


def _schema_compatible(value: Any) -> bool:
    current = _schema_tuple(value)
    required = _schema_tuple(REQUIRED_API_SCHEMA)
    if current is None or required is None:
        return False
    return current[0] == required[0] and current >= required


def _http_json(url: str, timeout: float = 2.0) -> dict[str, Any] | None:
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


def _port_open(port: int, timeout: float = 0.35) -> bool:
    try:
        with socket.create_connection((API_HOST, int(port)), timeout=timeout):
            return True
    except OSError:
        return False


def _parse_windows_netstat_listeners(output: str, port: int) -> set[int]:
    """Extract LISTENING PIDs for one local TCP port from Windows netstat output."""
    pids: set[int] = set()
    suffix = f":{int(port)}"
    for raw_line in str(output or "").splitlines():
        parts = raw_line.split()
        if len(parts) < 5 or parts[0].upper() != "TCP":
            continue
        local_endpoint = parts[1]
        state = parts[-2].upper()
        if state != "LISTENING" or not local_endpoint.endswith(suffix):
            continue
        try:
            pid = int(parts[-1])
        except ValueError:
            continue
        if pid > 0:
            pids.add(pid)
    return pids


def _listener_pids(port: int) -> set[int]:
    if os.name == "nt":
        try:
            completed = subprocess.run(
                ["netstat", "-ano", "-p", "tcp"],
                capture_output=True,
                text=True,
                check=False,
                timeout=8,
            )
        except (OSError, subprocess.SubprocessError):
            return set()
        return _parse_windows_netstat_listeners(completed.stdout, port)

    # Best-effort support for developer machines outside Windows. The production
    # desktop path is Windows; absence of lsof simply means tracked-PID cleanup.
    try:
        completed = subprocess.run(
            ["lsof", "-tiTCP:%d" % int(port), "-sTCP:LISTEN"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    pids: set[int] = set()
    for line in completed.stdout.splitlines():
        try:
            pid = int(line.strip())
        except ValueError:
            continue
        if pid > 0:
            pids.add(pid)
    return pids


def api_live() -> dict[str, Any] | None:
    return _http_json(f"{API_URL}/api/live")


def api_health() -> dict[str, Any] | None:
    return _http_json(f"{API_URL}/api/health")


def api_ready() -> bool:
    payload = api_live()
    return bool(
        payload
        and str(payload.get("service", "")).startswith("LMNotebook")
        and _schema_compatible(payload.get("api_schema"))
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
    live = api_live() or {}
    payload = {
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "api_pid": api_pid or previous.get("api_pid"),
        "frontend_pid": frontend_pid or previous.get("frontend_pid"),
        "api": API_URL,
        "frontend": FRONTEND_URL,
        "api_schema": live.get("api_schema") or REQUIRED_API_SCHEMA,
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
    if numeric_pid <= 0 or numeric_pid == os.getpid():
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


def _force_release_port(port: int) -> bool:
    """Release a SonicTrace-owned fixed port even when runtime PID tracking is stale."""
    if not _port_open(port):
        return True
    pids = _listener_pids(port)
    if pids:
        print(f"[runtime] Port {port} encore occupe; arret du/des listener(s) PID {', '.join(map(str, sorted(pids)))}...")
        for pid in pids:
            kill_pid(pid)
        time.sleep(0.8)
    return not _port_open(port)


def stop_spawned(api_pid: int | None, frontend_pid: int | None) -> None:
    kill_pid(api_pid)
    kill_pid(frontend_pid)


def stop_previous_runtime_if_incompatible() -> None:
    live = api_live()
    if live and _schema_compatible(live.get("api_schema")):
        return

    legacy = api_health()
    if not legacy:
        return

    print(
        f"[runtime] Ancienne API detectee (schema {legacy.get('api_schema') or 'legacy'}). "
        f"Redemarrage vers la facade health legere {REQUIRED_API_SCHEMA}+..."
    )
    runtime = read_runtime()
    kill_pid(runtime.get("api_pid"))
    time.sleep(1.0)
    _force_release_port(API_PORT)


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

    print(f"[runtime] Verification du backend V2 schema {REQUIRED_API_SCHEMA}+ (health leger)...")
    if api_ready():
        live = api_live() or {}
        print(f"[OK] API V2 deja active sur {API_HOST}:{API_PORT} (schema {live.get('api_schema') or '?'})")
    else:
        api_pid = spawn_process(
            [
                str(VENV_PYTHON),
                "-m",
                "uvicorn",
                "app.entrypoint:app",
                "--host",
                API_HOST,
                "--port",
                str(API_PORT),
            ],
            BACKEND,
            api_log,
        )
        print(f"[runtime] API lancee en arriere-plan (PID {api_pid})")
        if not wait_for(api_ready, 30):
            print(f"\n[ERREUR] Le ping leger /api/live du schema {REQUIRED_API_SCHEMA}+ n'a pas repondu dans les 30 secondes.")
            print("--- backend.log ---")
            print(tail(api_log))
            stop_spawned(api_pid, None)
            return 1
        live = api_live() or {}
        print(f"[OK] API V2 repond correctement (schema {live.get('api_schema') or '?'}).")

    print("[runtime] Verification du frontend local...")
    if frontend_ready():
        print(f"[OK] Frontend deja actif sur {API_HOST}:{FRONTEND_PORT}")
    else:
        frontend_pid = spawn_process(
            [
                str(VENV_PYTHON),
                "-m",
                "http.server",
                str(FRONTEND_PORT),
                "--bind",
                API_HOST,
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

    health = api_health() or api_live() or {}
    gpu_count = len(health.get("gpus") or [])
    ffmpeg = health.get("ffmpeg") or {}
    neural = health.get("neural") or {}
    stems = health.get("stems") or {}
    print(
        f"[OK] Deep Audio V2 ONLINE | schema {health.get('api_schema') or '?'} | GPU locales: {gpu_count} | "
        f"FFmpeg: {'READY' if ffmpeg.get('ffmpeg') and ffmpeg.get('ffprobe') else 'DEGRADED'}"
    )
    print(
        f"[OK] V2-B Neural: {'READY' if neural.get('ready') else 'WAIT'} | "
        f"V2-D Stems: {'READY' if stems.get('ready') else 'WAIT'} | health={health.get('health_mode') or 'light'}"
    )

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
    time.sleep(0.6)

    api_released = _force_release_port(API_PORT)
    frontend_released = _force_release_port(FRONTEND_PORT)

    try:
        RUNTIME_FILE.unlink(missing_ok=True)
    except OSError:
        pass

    if not api_released or not frontend_released:
        blocked = []
        if not api_released:
            blocked.append(str(API_PORT))
        if not frontend_released:
            blocked.append(str(FRONTEND_PORT))
        print(f"[ERREUR] Impossible de liberer le(s) port(s) {', '.join(blocked)}. Mise a jour/redemarrage annule.")
        return 1

    print("[OK] LMNotebook est arrete; ports 8000/8008 libres.")
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
