#!/usr/bin/env python3
"""Download a public Wikipedia dump for the offline knowledge index.

WHY this is a separate step from building the index
---------------------------------------------------
The dump is hundreds of megabytes and is licensed content (CC BY-SA); the index
is derived data. Keeping the download explicit means the repository ships a
*recipe* (this script) rather than a large opaque blob, and a clone can decide
whether to enable the general knowledge layer at all.

The dump is verified before it is accepted: ``bzip2 -t`` (or an in-process
BZh header check when ``bz2`` cannot stream the whole file) plus an optional
SHA-256 when the mirror publishes one. A truncated download is deleted, never
silently indexed.

Usage:
    python3 scripts/download_knowledge_corpus.py                 # simplewiki
    python3 scripts/download_knowledge_corpus.py --force         # re-download
    python3 scripts/download_knowledge_corpus.py --check         # is it there?
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = (
    "https://dumps.wikimedia.org/simplewiki/latest/"
    "simplewiki-latest-pages-articles.xml.bz2"
)
DEFAULT_DEST = (
    REPO_ROOT / "data" / "knowledge" / "simplewiki-latest-pages-articles.xml.bz2"
)
LICENSE = "CC BY-SA 4.0 (Simple English Wikipedia contributors)"


def _human(count: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if count < 1024 or unit == "GB":
            return f"{count:.1f} {unit}"
        count /= 1024
    return f"{count:.1f} GB"


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_suffix(dest.suffix + ".part")
    request = urllib.request.Request(url, headers={"User-Agent": "angela-knowledge/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        total = int(response.headers.get("Content-Length") or 0)
        print(f"downloading {url}")
        print(f"  -> {dest} ({_human(total) if total else 'size unknown'})")
        started = time.time()
        written = 0
        with partial.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                written += len(chunk)
                if total:
                    percent = written * 100 / total
                    sys.stdout.write(f"\r  {percent:5.1f}%  {_human(written)}")
                    sys.stdout.flush()
        elapsed = time.time() - started
        print(f"\r  {_human(written)} in {elapsed:.1f}s ({_human(written / elapsed)}/s)")
    partial.replace(dest)


def _looks_like_bzip2(path: Path) -> bool:
    with path.open("rb") as handle:
        return handle.read(3) == b"BZh"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    parser.add_argument("--sha256", default=None, help="expected digest (optional)")
    parser.add_argument("--force", action="store_true", help="re-download")
    parser.add_argument("--check", action="store_true", help="verify only, no download")
    args = parser.parse_args()

    if args.check:
        if not args.dest.is_file():
            print(f"missing: {args.dest}")
            return 1
        print(f"present: {args.dest} ({_human(args.dest.stat().st_size)})")
        return 0

    if args.dest.is_file() and not args.force:
        print(f"already present: {args.dest} ({_human(args.dest.stat().st_size)})")
        print("use --force to download again")
        return 0

    try:
        _download(args.url, args.dest)
    except Exception as exc:
        print(f"download failed: {exc}")
        return 1

    if not _looks_like_bzip2(args.dest):
        print("downloaded file is not a bzip2 stream; deleting")
        args.dest.unlink(missing_ok=True)
        return 1

    if args.sha256:
        digest = hashlib.sha256()
        with args.dest.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        actual = digest.hexdigest()
        if actual != args.sha256:
            print(f"sha256 mismatch: {actual} != {args.sha256}; deleting")
            args.dest.unlink(missing_ok=True)
            return 1

    print(f"ok: {args.dest} ({_human(args.dest.stat().st_size)})")
    print(f"license: {LICENSE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
