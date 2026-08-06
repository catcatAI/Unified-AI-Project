#!/usr/bin/env python3
"""
Download the real everyday-dialogue / commonsense dataset used by training.

This is NOT a synthetic generator. It fetches a real open instruction-dialogue
corpus — the Stanford Alpaca dataset (52K human-written instruction -> output
turns covering everyday chat, commonsense, and open knowledge) — into
``apps/backend/data/raw_datasets/alpaca_data.json``, exactly where
``train_pipeline.load_alpaca_data()`` reads it.

Why Alpaca:
  * real, human-curated, open-domain — everyday dialogue + commonsense +
    open QA, i.e. exactly the data the deterministic engines do NOT answer
    (they only cover math/logic/closed-facts), so it survives the
    ``is_deterministic_match`` filter and actually trains the neural layers;
  * reachable from a stable raw URL with Python stdlib only (no HF/torch dep);
  * disk space is plentiful, so the full corpus is kept by default.

Usage:
    python scripts/download_daily_data.py [--max-entries N] [--force] [--dry-run]

    --max-entries N   Keep at most the first N entries (default: all).
    --force           Re-download even if the file already exists.
    --dry-run         Check connectivity + print what would happen, download nothing.

Idempotent: skips when the file already exists and looks valid (unless --force).
On any download/parse failure it prints a clear error and returns a non-zero
exit code — it NEVER fabricates or writes placeholder data.
"""

import argparse
import json
import logging
import os
import sys
import time
import urllib.request

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("download_daily_data")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(ROOT, "apps", "backend", "data", "raw_datasets")
OUT_PATH = os.path.join(DATA_DIR, "alpaca_data.json")

# Stanford Alpaca — real instruction-dialogue corpus (CC BY-NC 4.0, 52K turns).
ALPACA_URL = "https://raw.githubusercontent.com/tatsu-lab/stanford_alpaca/main/alpaca_data.json"

# Alpaca-Data-Cleaned — a cleaned/respell of the same format (CC BY-NC 4.0, 51K
# turns). Merging the two grows the real daily-dialogue/commonsense pool while
# keeping the same instruction/input/output schema that train_pipeline reads.
CLEANED_URL = "https://raw.githubusercontent.com/gururise/AlpacaDataCleaned/main/alpaca_data_cleaned.json"

CORPORA = (("alpaca", ALPACA_URL), ("cleaned", CLEANED_URL))

TIMEOUT = 300
MIN_VALID_BYTES = 500_000  # a truncated/empty response below this is treated as invalid


def _urlretrieve(url: str, dest: str) -> int:
    """Download *url* to *dest*; return byte count."""
    logger.info("Downloading %s", url)
    req = urllib.request.Request(url, headers={"User-Agent": "ED3N-DailyData/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        chunk_size = 64 * 1024
        downloaded = 0
        with open(dest, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total:
                    pct = downloaded * 100 // total
                    sys.stdout.write(f"\r  {downloaded // 1024}KB/{total // 1024}KB ({pct}%)")
                    sys.stdout.flush()
    print()
    logger.info("Downloaded %s (%.1fMB)", os.path.basename(dest), downloaded / (1024 * 1024))
    return downloaded


def _validate(path: str) -> int:
    """Return entry count if *path* is a valid list of Alpaca-style items, else raise."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("dataset root is not a JSON array")
    required = ("instruction", "output")
    for item in data:
        if not isinstance(item, dict) or not all(k in item for k in required):
            raise ValueError("entry missing instruction/output keys")
        break
    logger.info("Validated %d entries from %s", len(data), os.path.basename(path))
    return len(data)


def _cap_entries(path: str, max_entries: int) -> None:
    """Trim *path* in place to the first ``max_entries`` entries (defensive cap)."""
    if max_entries is None or max_entries <= 0:
        return
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if len(data) <= max_entries:
        return
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data[:max_entries], f, ensure_ascii=False)
    logger.info("Capped dataset to first %d entries", max_entries)


def _load_valid(path: str) -> list:
    """Load a JSON-array dataset, raising if schema is wrong. No fabrication."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"{os.path.basename(path)} root is not a JSON array")
    if data:
        required = ("instruction", "output")
        if any(not isinstance(i, dict) or not all(k in i for k in required) for i in data):
            raise ValueError(f"{os.path.basename(path)} entry missing instruction/output keys")
    return data


def _build_merged(parts: list) -> None:
    """Merge per-corpus part files into OUT_PATH, dedup by instruction.

    All corpora share the instruction/input/output schema, so entries can be
    concatenated. Dedup is by exact instruction text (keeps the first), so the
    overlapping Stanford/Cleaned Alpaca don't double-count.
    """
    seen = set()
    merged = []
    for part in parts:
        for item in _load_valid(part):
            inst = item.get("instruction", "")
            if inst in seen:
                continue
            seen.add(inst)
            merged.append(item)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False)
    logger.info("Merged %d unique real turns from %d corpora -> %s", len(merged), len(parts), OUT_PATH)
    return len(merged)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-entries", type=int, default=None, help="cap to N entries")
    parser.add_argument("--force", action="store_true", help="re-download even if file exists")
    parser.add_argument("--dry-run", action="store_true", help="check connectivity only")
    args = parser.parse_args()

    os.makedirs(DATA_DIR, exist_ok=True)
    exists = os.path.exists(OUT_PATH)

    if args.dry_run:
        ok = True
        for _name, url in CORPORA:
            try:
                req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "ED3N/1.0"})
                with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                    logger.info(
                        "Dry-run OK: %s reachable (status %s, ~%sMB)",
                        _name,
                        resp.status,
                        round(int(resp.headers.get("Content-Length", 0)) / (1024 * 1024), 1),
                    )
            except Exception as e:  # noqa: BLE001 - connectivity probe is intentionally broad
                logger.error("Dry-run FAILED: %s (%s)", _name, e)
                ok = False
        return 0 if ok else 1

    if exists and not args.force:
        try:
            n = _validate(OUT_PATH)
        except Exception as e:  # noqa: BLE001 - corrupt local file -> re-download
            logger.warning("Existing file invalid (%s); re-downloading.", e)
            os.remove(OUT_PATH)
        else:
            logger.info("Merged dataset already present (%d entries). Use --force to re-download.", n)
            return 0

    parts = []
    try:
        for _name, url in CORPORA:
            part = os.path.join(DATA_DIR, f"download-daily-{_name}.part-{os.getpid()}")
            size = _urlretrieve(url, part)
            if size < MIN_VALID_BYTES:
                raise ValueError(f"{_name} response too small ({size} bytes); refusing to use it")
            _load_valid(part)
            parts.append(part)
        n = _build_merged(parts)
        _cap_entries(OUT_PATH, args.max_entries)
        n = _validate(OUT_PATH)
    except Exception as e:  # noqa: BLE001 - any failure means: no data, clear error
        logger.error("Download FAILED — no data written: %s", e)
        for part in parts:
            if os.path.exists(part):
                os.remove(part)
        return 1

    for part in parts:
        if os.path.exists(part):
            os.remove(part)

    final_mb = round(os.path.getsize(OUT_PATH) / (1024 * 1024), 2)
    logger.info("READY: %d real dialogue/commonsense turns -> %s (%.1fMB)", n, OUT_PATH, final_mb)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
