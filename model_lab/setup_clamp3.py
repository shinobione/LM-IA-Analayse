from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_RUNTIME = ROOT / ".runtime"
CLAMP3_REPO = "https://github.com/sanderwood/clamp3.git"
CLAMP3_COMMIT = "9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8"


def run(command: list[str], cwd: Path | None = None) -> None:
    print("[RUN]", " ".join(command))
    subprocess.run(command, cwd=str(cwd) if cwd else None, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare pinned CLaMP3 source checkout for SonicTrace V4 Model Lab.")
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    args = parser.parse_args()

    runtime = args.runtime.resolve()
    clamp_dir = runtime / "clamp3"
    runtime.mkdir(parents=True, exist_ok=True)

    if shutil.which("git") is None:
        raise SystemExit("git.exe is required. SonicTrace normally installs Git automatically.")

    if not (clamp_dir / ".git").exists():
        if clamp_dir.exists():
            shutil.rmtree(clamp_dir)
        run(["git", "clone", "--filter=blob:none", CLAMP3_REPO, str(clamp_dir)])
    else:
        run(["git", "remote", "set-url", "origin", CLAMP3_REPO], cwd=clamp_dir)

    run(["git", "fetch", "--depth", "1", "origin", CLAMP3_COMMIT], cwd=clamp_dir)
    run(["git", "checkout", "--detach", CLAMP3_COMMIT], cwd=clamp_dir)
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(clamp_dir), text=True).strip()
    if actual != CLAMP3_COMMIT:
        raise SystemExit(f"CLaMP3 checkout mismatch: expected {CLAMP3_COMMIT}, got {actual}")

    (runtime / "CLAMP3_PIN.txt").write_text(
        f"repository={CLAMP3_REPO}\ncommit={CLAMP3_COMMIT}\n",
        encoding="utf-8",
    )
    print(f"[OK] CLaMP3 pinned at {CLAMP3_COMMIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
