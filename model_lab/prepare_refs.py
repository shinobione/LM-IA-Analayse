from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_TAXONOMY = ROOT / "taxonomy_v1.json"
DEFAULT_RUNTIME = ROOT / ".runtime"


def build_reference_banks(taxonomy_path: Path, runtime_dir: Path) -> dict[str, dict[str, str]]:
    taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    axes = taxonomy.get("axes") or {}
    refs_root = runtime_dir / "refs"
    refs_root.mkdir(parents=True, exist_ok=True)

    label_map: dict[str, dict[str, str]] = {}
    for axis, entries in axes.items():
        axis_dir = refs_root / axis
        axis_dir.mkdir(parents=True, exist_ok=True)
        # Remove stale generated prompts so taxonomy edits cannot leave ghosts.
        for old in axis_dir.glob("*.txt"):
            old.unlink()

        axis_map: dict[str, str] = {}
        for item in entries:
            slug = str(item["id"]).strip()
            label = str(item["label"]).strip()
            prompt = str(item["prompt"]).strip()
            if not slug or not label or not prompt:
                raise ValueError(f"Invalid taxonomy entry in axis {axis!r}: {item!r}")
            (axis_dir / f"{slug}.txt").write_text(prompt + "\n", encoding="utf-8")
            axis_map[slug] = label
        label_map[axis] = axis_map

    (runtime_dir / "label_map.json").write_text(
        json.dumps(label_map, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return label_map


def main() -> int:
    parser = argparse.ArgumentParser(description="Build CLaMP3 text reference banks for SonicTrace V4 Model Lab.")
    parser.add_argument("--taxonomy", type=Path, default=DEFAULT_TAXONOMY)
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    args = parser.parse_args()

    label_map = build_reference_banks(args.taxonomy.resolve(), args.runtime.resolve())
    print("[OK] CLaMP3 reference banks generated:")
    for axis, rows in label_map.items():
        print(f"  - {axis}: {len(rows)} candidates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
