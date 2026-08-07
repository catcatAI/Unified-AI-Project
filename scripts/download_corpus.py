#!/usr/bin/env python3
"""
Streaming corpus downloader that fills the disk corpus toward the ~10GB target.

Pulls real, openly-licensed multilingual text into
``apps/backend/data/raw_datasets/corpus/{source}/``:

  * wiki-zh, wiki-ja, wiki-en   Wikipedia pages-articles dumps (CC BY-SA 4.0)
  * tatoeba                     Tatoeba sentence/translation export (CC BY 2.0 FR)

Design (matches the data-eng streaming/resume plan):
  * Resumable: each source tracks its global byte offset in a small state.json;
    a re-run issues an HTTP Range request from that offset instead of starting
    over.
  * Lightweight: raw bytes are rolled into segment files of SEGMENT_BYTES
    (1 GB) named ``{slug}-NNN``. On disk each segment stays <=1GB and the
    writer only ever buffers one 64KB request chunk.
  * Target: downloading stops once the accumulated global offset reaches the
    target bytes. "all" walks source priority z->ja->en->tatoeba to fill.

Deferred on purpose (not this script's job): decompressing .bz2 / .tar.bz2 and
extracting clean paragraphs. That is the corpus -> samples transform and lives
in the training ingest step so the raw dumps stay reusable.

Writes zero placeholder data: on any network failure it records the offset and
the next run resumes from there.

Usage:
    python scripts/download_corpus.py [source ...] [--target-gb N] [--dry-run]
    source: wiki_zh | wiki_ja | wiki_en | tatoeba | all   (default: all)
"""

import argparse
import json
import logging
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
try:  # project config authority for the dataset volume target (graceful)
    sys.path.insert(0, str(ROOT / "apps" / "backend" / "src"))
    from core.system.config import magic_numbers as _mn  # noqa: E402
except Exception:  # noqa: BLE001
    _mn = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("download_corpus")

CORPUS_DIR = ROOT / "apps" / "backend" / "data" / "raw_datasets" / "corpus"
SEGMENT_BYTES = 1024 * 1024 * 1024  # 1 GB per on-disk segment file
_DEFAULT_TARGET_GB = 10

SOURCES = {
    "wiki_zh": (
        "Wikipedia zh",
        "https://dumps.wikimedia.org/zhwiki/latest/zhwiki-latest-pages-articles-multistream.xml.bz2",
        3_559_343_816,
    ),
    "wiki_ja": (
        "Wikipedia ja",
        "https://dumps.wikimedia.org/jawiki/latest/jawiki-latest-pages-articles-multistream.xml.bz2",
        4_827_732_824,
    ),
    "wiki_en": (
        "Wikipedia en",
        "https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2",
        26_668_484_995,
    ),
    "tatoeba": (
        "Tatoeba",
        "https://downloads.tatoeba.org/exports/sentences.tar.bz2",
        217_621_211,
    ),
}
_ALL_PRIORITY = ["wiki_zh", "wiki_ja", "wiki_en", "tatoeba"]


def _default_target_bytes() -> int:
    """Dataset volume target from the capacity config, else 10 GiB."""
    if _mn is not None:
        try:
            cfg = _mn._get("system.capacity.capacity.dataset", {})  # noqa: SLF001
            mb = cfg.get("target_volume_mb")
            if mb:
                return int(mb) * 1024 * 1024
        except Exception:  # noqa: BLE001
            pass
    return _DEFAULT_TARGET_GB * 1024 * 1024 * 1024


def _state_path(slug: str) -> Path:
    return CORPUS_DIR / slug / "state.json"


def _load_state(slug: str) -> dict:
    p = _state_path(slug)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001 - corrupt state restarts cleanly
            logger.warning("Corrupt state for %s; restarting from 0", slug)
    return {"offset": 0, "segments": [], "downloaded": 0}


def _save_state(slug: str, state: dict) -> None:
    (CORPUS_DIR / slug).mkdir(parents=True, exist_ok=True)
    _state_path(slug).write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _resume_read(url: str, path: Path, offset: int, max_bytes: int, seg_boundary: bool) -> int:
    """Write *url* bytes starting at global *offset* into *path*; return bytes written.

    ``offset`` is the GLOBAL byte offset (must equal this segment's position +
    what it already holds), used for the HTTP Range request. ``seg_boundary``
    tells whether this is the very start of a fresh segment (write) vs. a
    mid-segment resume (append). Reads at most *max_bytes* so one network stream
    rolls over into fresh segment files. Returns 0 when the server has nothing
    beyond *offset* (HTTP 416 = already complete).
    """
    headers = {"User-Agent": "ED3N-Corpus-Downloader/1.0", "Range": f"bytes={offset}-"}
    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as e:
        if e.code == 416:  # Range beyond end of file -> nothing left to fetch
            logger.info("  already complete at byte %d (416); nothing more to fetch", offset)
            return 0
        raise
    with resp:
        total = int(resp.headers.get("Content-Length", 0))
        available = max(0, total - offset) if total > offset else max_bytes
        remaining = min(max_bytes, available)
        written = 0
        with open(path, "wb" if seg_boundary else "ab") as f:
            while written < remaining:
                want = min(64 * 1024, remaining - written)
                chunk = resp.read(want)
                if not chunk:
                    break
                f.write(chunk)
                written += len(chunk)
                sys.stdout.write(
                    f"\r  seg@+{offset//1024//1024}MB +{written//1024}KB/{max(remaining,1)//1024}KB ({written*100//max(remaining,1)}%)"
                )
                sys.stdout.flush()
    print()
    return written


def download_source(slug: str, target: int) -> dict:
    """Resume the download for *slug* up to the global *target* bytes."""
    kind, url, _ = SOURCES[slug]
    state = _load_state(slug)
    (CORPUS_DIR / slug).mkdir(parents=True, exist_ok=True)
    offset = int(state.get("offset", 0))
    segments = list(state.get("segments", []))
    done = offset >= target

    if done:
        logger.info("%s: already at %d bytes, skip", kind, offset)
        return {"slug": slug, "name": kind, "bytes": offset, "segments": len(segments), "done": True}

    logger.info(
        "%s: resume global byte %d, %d segment(s) on disk, target %d",
        kind, offset, len(segments), target,
    )
    t0 = time.time()
    while offset < target:
        seg_index = offset // SEGMENT_BYTES
        seg_name = f"{slug}-{seg_index:03d}"
        seg_path = CORPUS_DIR / slug / seg_name
        seg_offset = offset % SEGMENT_BYTES  # where within this segment we resume
        seg_cap = SEGMENT_BYTES - seg_offset  # bytes still allowed in this segment

        received = _resume_read(url, seg_path, offset, seg_cap, seg_offset == 0)
        if received == 0:
            logger.warning("%s: no new bytes; server may reject Range — stopping.", kind)
            break
        offset += received
        if seg_name not in segments:
            segments.append(seg_name)
        _save_state(
            slug,
            {
                "offset": offset,
                "segments": segments,
                "downloaded": offset,
                "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        )
        logger.info(
            "%s: segment %s -> +%d bytes (now %d)",
            kind, seg_name, received, offset,
        )

    done = offset >= target
    logger.info(
        "%s: done=%s total %d bytes in %.1fs (target %d)",
        kind, done, offset, time.time() - t0, target,
    )
    return {"slug": slug, "name": kind, "bytes": offset, "segments": len(segments), "done": done}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sources", nargs="*", help="wiki_zh|wiki_ja|wiki_en|tatoeba|all")
    parser.add_argument("--target-gb", type=float, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    target = int(args.target_gb * 1024**3) if args.target_gb else _default_target_bytes()

    picks = args.sources or ["all"]
    unknown = [p for p in picks if p != "all" and p not in SOURCES]
    if unknown:
        parser.error(f"unknown sources: {', '.join(unknown)}")
    if "all" in picks:
        picks = list(_ALL_PRIORITY)
    else:
        picks = [p for p in picks if p in SOURCES]

    if args.dry_run:
        ok = True
        for slug in picks:
            kind, url, fallback = SOURCES[slug]
            try:
                req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ED3N/1.0"})
                with urllib.request.urlopen(req, timeout=30) as resp:
                    size = int(resp.headers.get("Content-Length", 0)) or fallback
                    logger.info("dry-run OK: %s (%s MB) -> %s", kind, round(size / 1024**2, 1), slug)
            except Exception as e:  # noqa: BLE001 - connectivity probe
                logger.error("dry-run FAILED: %s (%s)", slug, e)
                ok = False
        return 0 if ok else 1

    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    report = []
    for slug in picks:
        report.append(download_source(slug, target))
        if sum(r["bytes"] for r in report) >= target:
            logger.info("Reached target volume (>=%d bytes); stopping.", target)
            break

    total = sum(r["bytes"] for r in report)
    print()
    logger.info("=== Summary ===")
    for r in report:
        logger.info(
            "  %-8s %7.1f MB  %s",
            r["slug"], r["bytes"] / 1024**2, "full" if r["done"] else "partial",
        )
    logger.info("  TOTAL     %6.2f GB (target %.1f GB)", total / 1024**3, target / 1024**3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())