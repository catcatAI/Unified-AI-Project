#!/usr/bin/env python3
# =============================================================================
# ANGELA-MATRIX: [L0] [α] [C] [L0]
# =============================================================================
"""
backup_checkpoints.py — 備份訓練檢查點（可排程）

WHY this exists
---------------
The trained checkpoints under ``data/checkpoints/`` are the *result* of every
training run (261 MB locally). They are git-ignored, so nothing in the
repository protects them: a re-training accident, a bad disk, or a cleanup
script can wipe hours of compute with no way back.

The task list carried "T-OPS-1: 字典/模型備份策略 — scripts/backup_checkpoints.py
+ cron/GitHub Action" as an open item. This is the script half: it copies the
checkpoints to a timestamped directory, prunes old backups, and reports what
it did. The scheduling half is a one-line cron entry (see --help).

Usage
    python3 scripts/backup_checkpoints.py                     # back up
    python3 scripts/backup_checkpoints.py --dry-run           # show what would happen
    python3 scripts/backup_checkpoints.py --dest /mnt/backups # custom destination
    python3 scripts/backup_checkpoints.py --keep 5            # keep the newest 5 backups
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "data" / "checkpoints"
DEFAULT_DEST = ROOT / "data" / "checkpoint_backups"
MANIFEST = "backup_manifest.json"


def _dir_size(path: Path) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                continue
    return total


def _human(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{size} B"
        size /= 1024
    return f"{size:.1f} GB"


def collect_backups(dest: Path) -> list:
    """Existing backup directories, oldest first."""
    if not dest.exists():
        return []
    return sorted(
        (p for p in dest.iterdir() if p.is_dir() and p.name.startswith("checkpoints-")),
        key=lambda p: p.name,
    )


def prune(dest: Path, keep: int) -> list:
    """Remove the oldest backups beyond *keep*; return what was removed."""
    backups = collect_backups(dest)
    removed = []
    for path in backups[:-keep] if keep > 0 else []:
        shutil.rmtree(path, ignore_errors=True)
        removed.append(path.name)
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", default=str(DEFAULT_DEST), help="backup destination")
    parser.add_argument("--keep", type=int, default=5, help="how many backups to keep")
    parser.add_argument("--dry-run", action="store_true", help="do not write anything")
    args = parser.parse_args()

    source = SOURCE
    if not source.exists():
        print(f"❌ no checkpoints at {source} — nothing to back up")
        return 1

    dest = Path(args.dest)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    target = dest / f"checkpoints-{stamp}"

    size = _dir_size(source)
    print(f"source : {source} ({_human(size)})")
    print(f"target : {target}")

    if args.dry_run:
        print("dry run — nothing was written")
        return 0

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target)
    except OSError as exc:
        print(f"❌ backup failed: {exc}")
        return 1

    manifest = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source": str(source),
        "target": str(target),
        "bytes": size,
        "files": sum(1 for _ in target.rglob("*") if _.is_file()),
    }
    try:
        (dest / MANIFEST).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        print(f"⚠️  manifest not written: {exc}")

    removed = prune(dest, args.keep)
    print(f"✅ backed up {_human(size)} → {target}")
    if removed:
        print(f"   pruned old backups: {', '.join(removed)}")
    print(f"   cron example: 0 3 * * * cd {ROOT} && {sys.executable} scripts/backup_checkpoints.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
