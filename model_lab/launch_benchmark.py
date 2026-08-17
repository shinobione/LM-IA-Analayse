from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SUPPORTED_AUDIO = {".wav", ".mp3"}


def _read_file_list(path: Path) -> list[Path]:
    if not path.exists():
        raise FileNotFoundError(f"Selection file not found: {path}")
    files: list[Path] = []
    for raw in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
        value = raw.strip().strip('"')
        if not value:
            continue
        audio = Path(value).expanduser().resolve()
        if not audio.exists():
            raise FileNotFoundError(f"Selected audio file not found: {audio}")
        if audio.suffix.lower() not in SUPPORTED_AUDIO:
            raise ValueError(f"Unsupported CLaMP3 audio type: {audio.suffix} ({audio})")
        files.append(audio)
    if not files:
        raise ValueError("The Windows picker returned an empty audio selection.")
    return files


def _write_error(path: Path, message: str, log_path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tail = ""
    try:
        if log_path.exists():
            tail = log_path.read_text(encoding="utf-8", errors="replace")[-16000:]
    except Exception:
        tail = ""
    path.write_text(
        "SONICTRACE V4 MODEL LAB - LAST ERROR\n"
        f"Time: {datetime.now().isoformat(timespec='seconds')}\n"
        f"{message}\n\n"
        "---- LAST RUN LOG TAIL ----\n"
        f"{tail}\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Stable Windows launcher for the SonicTrace V4 Model Lab benchmark.")
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--file-list", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--error-log", type=Path, required=True)
    args = parser.parse_args()

    runner = args.runner.resolve()
    file_list = args.file_list.resolve()
    log_path = args.log.resolve()
    error_path = args.error_log.resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    error_path.unlink(missing_ok=True)

    try:
        files = _read_file_list(file_list)
        if not runner.exists():
            raise FileNotFoundError(f"Benchmark runner not found: {runner}")

        venv_scripts = Path(sys.executable).resolve().parent
        venv_root = venv_scripts.parent
        env = os.environ.copy()
        # CLaMP3's official helpers launch nested commands with the literal
        # executable name `python`. Put this isolated venv first so those
        # children cannot fall back to a global Windows Python installation.
        env["PATH"] = str(venv_scripts) + os.pathsep + env.get("PATH", "")
        env["VIRTUAL_ENV"] = str(venv_root)
        env["PYTHONNOUSERSITE"] = "1"
        env["PYTHONUTF8"] = "1"

        command = [sys.executable, str(runner), *(str(path) for path in files)]
        header = [
            "SONICTRACE V4 MODEL LAB - WINDOWS LAUNCHER",
            "=" * 58,
            f"Time: {datetime.now().isoformat(timespec='seconds')}",
            f"Python: {sys.executable}",
            f"VIRTUAL_ENV: {env['VIRTUAL_ENV']}",
            f"PATH first entry: {env['PATH'].split(os.pathsep)[0]}",
            f"Runner: {runner}",
            f"Selected files: {len(files)}",
            *[f"  - {path}" for path in files],
            "",
            "[STEP] Starting CLaMP3 benchmark...",
            "[INFO] Nested CLaMP3 `python` commands are pinned to the Model Lab venv.",
            "",
        ]

        with log_path.open("w", encoding="utf-8", buffering=1) as log:
            for line in header:
                print(line, flush=True)
                print(line, file=log, flush=True)

            process = subprocess.Popen(
                command,
                cwd=str(runner.parent),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            assert process.stdout is not None
            for line in process.stdout:
                print(line, end="", flush=True)
                print(line, end="", file=log, flush=True)
            return_code = process.wait()
            print(f"\n[STEP] Benchmark process exited with code {return_code}.", flush=True)
            print(f"\n[STEP] Benchmark process exited with code {return_code}.", file=log, flush=True)

        if return_code != 0:
            _write_error(error_path, f"Benchmark process failed with exit code {return_code}.", log_path)
            return return_code

        error_path.unlink(missing_ok=True)
        return 0
    except Exception as exc:
        message = f"Launcher failure: {type(exc).__name__}: {exc}"
        print(f"\n[ERREUR] {message}", file=sys.stderr, flush=True)
        _write_error(error_path, message, log_path)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
