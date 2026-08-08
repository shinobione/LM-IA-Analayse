from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description='LMNotebook isolated Demucs runner')
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--model', default='htdemucs')
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    output_dir = Path(args.output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        '-m',
        'demucs.separate',
        '--name',
        args.model,
        '--device',
        'cuda',
        '--out',
        str(output_dir),
        str(input_path),
    ]
    completed = subprocess.run(command, check=False)
    return int(completed.returncode)


if __name__ == '__main__':
    raise SystemExit(main())
