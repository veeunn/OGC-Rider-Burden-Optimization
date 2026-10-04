"""Restore split OGC JSON files and verify them against manifest.json."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts-dir", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument(
        "--file",
        action="append",
        dest="files",
        help="Restore only this original filename. Repeat for multiple files.",
    )
    args = ap.parse_args()

    parts_dir = Path(args.parts_dir)
    output_dir = Path(args.output_dir)
    manifest_path = parts_dir / "manifest.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = {record["file"]: record for record in manifest}

    requested = args.files or list(records)
    missing = sorted(set(requested) - set(records))
    if missing:
        raise SystemExit(f"Not present in manifest: {', '.join(missing)}")

    output_dir.mkdir(parents=True, exist_ok=True)

    for filename in requested:
        record = records[filename]
        target = output_dir / Path(filename).name

        with target.open("wb") as dst:
            for part_info in record["parts"]:
                part_name = Path(part_info["name"]).name
                part = parts_dir / part_name
                if not part.is_file():
                    raise FileNotFoundError(f"Missing part: {part}")
                expected_part_size = part_info.get("size_bytes")
                if expected_part_size is not None and part.stat().st_size != expected_part_size:
                    raise ValueError(
                        f"Part size mismatch for {part_name}: "
                        f"{part.stat().st_size} != {expected_part_size}"
                    )
                with part.open("rb") as src:
                    shutil.copyfileobj(src, dst, length=1024 * 1024)

        actual_size = target.stat().st_size
        expected_size = record["size_bytes"]
        if actual_size != expected_size:
            raise ValueError(
                f"Restored size mismatch for {filename}: "
                f"{actual_size} != {expected_size}"
            )

        actual_hash = sha256(target)
        expected_hash = record["sha256"]
        if actual_hash != expected_hash:
            raise ValueError(
                f"SHA-256 mismatch for {filename}: "
                f"{actual_hash} != {expected_hash}"
            )

        print(
            f"RESTORED {filename} | "
            f"{actual_size / 1024 / 1024:.2f} MiB | sha256={actual_hash}"
        )


if __name__ == "__main__":
    main()
