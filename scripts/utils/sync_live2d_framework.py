#!/usr/bin/env python3
import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

DEST_ROOT = Path(__file__).resolve().parents[2] / "apps" / "web-live2d-viewer" / "libs" / "live2dframework"
DEST_SRC = DEST_ROOT / "src"
PIN_FILE = DEST_ROOT / "version.json"

EXCLUDE_NAMES = {
    # Keep our local init wrapper intact
    "live2dcubism-init.js",
    # Node artifacts we don't want to vendor
    "node_modules",
    "dist",
    "build",
}


def copy_tree(src: Path, dst: Path):
    if not src.exists():
        raise FileNotFoundError(f"Source path not found: {src}")
    dst.mkdir(parents=True, exist_ok=True)

    for item in src.rglob("*"):
        rel = item.relative_to(src)
        if any(part in EXCLUDE_NAMES for part in rel.parts):
            continue
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Sync Live2D framework sources into web-live2d-viewer/libs/live2dframework")
    parser.add_argument("--src", required=True, help="Path to upstream live2d framework directory (containing src/)")
    parser.add_argument("--pin", default=None, help="Optional version string to pin (e.g., v5.0.0)")
    args = parser.parse_args(argv)

    src_path = Path(args.src).resolve()
    src_root = src_path
    if (src_root / "src").is_dir():
        src_path = src_root / "src"

    if not src_path.is_dir():
        raise SystemExit(f"Invalid --src. Expected a directory containing 'src/': {src_root}")

    print(f"Syncing Live2D framework from: {src_root}")
    print(f"Destination: {DEST_SRC}")

    # Clean existing src directory
    if DEST_SRC.exists():
        shutil.rmtree(DEST_SRC)
    DEST_SRC.mkdir(parents=True, exist_ok=True)

    # Copy over
    copy_tree(src_path, DEST_SRC)

    # Write pin metadata
    PIN_FILE.parent.mkdir(parents=True, exist_ok=True)
    pin_data = {
        "strategy": "vendored-sync",
        "source_path": str(src_root),
        "pinned_version": args.pin or "custom",
        "synced_at": datetime.utcnow().isoformat() + "Z",
    }
    with PIN_FILE.open("w", encoding="utf-8") as f:
        json.dump(pin_data, f, ensure_ascii=False, indent=2)

    print("Sync complete.")
    print(f"Pin written: {PIN_FILE}")


if __name__ == "__main__":
    main()
