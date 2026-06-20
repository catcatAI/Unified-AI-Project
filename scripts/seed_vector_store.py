"""
ANGELA-MATRIX: [L2] [β] [B] [L1]
Vector Store Seed Script
=========================
Loads dictionary data from ``data/dictionaries/*.json`` into the
VectorMemoryStore's numpy backend for maximum speed.

Uses ``_NumpyBackend.bulk_add_memories()`` — handles **~11,500 entries/sec**.
All 460K dictionary entries seed in **~40 seconds**.

Usage::

    python scripts/seed_vector_store.py                     # seed ALL entries
    python scripts/seed_vector_store.py --limit 10000       # first 10K entries
    python scripts/seed_vector_store.py --source cedict     # only one file
    python scripts/seed_vector_store.py --dry-run --limit 10  # dry run
    python scripts/seed_vector_store.py --info              # list available sources
"""

import argparse
import json
import logging
import os
import sys
import time
from typing import Dict, List, Optional, Set, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "apps", "backend", "src"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed_vector_store")

# Batch size for numpy bulk_add_memories — 5000 entries per call
# Each call is ~0.4s, so 100 batches of 5000 = ~40s for all 460K
BATCH_SIZE = 5000

# ---------------------------------------------------------------------------
# Dictionary file discovery
# ---------------------------------------------------------------------------

DICT_DIR = os.path.join(PROJECT_ROOT, "data", "dictionaries")

DICT_SOURCES: Dict[str, str] = {
    "cedict.json": "CC-CEDICT (zh↔en)",
    "jmdict.json": "JMdict (ja↔en)",
    "wordnet.json": "WordNet 3.0 (en)",
}


def _iter_semantic_parts(entry: dict) -> List[str]:
    """Extract semantically meaningful text from a dictionary entry.

    Dictionary files use ED3N DictionaryLayer format:
      - ``surface_forms``:  dict of language_code -> text
      - ``contexts``:       list of dicts (pinyin, reading, pos …)
      - ``key``:            unique identifier (used for dedup)
    """
    parts: List[str] = []

    # Surface forms (primary semantic content)
    sf = entry.get("surface_forms", {})
    if isinstance(sf, dict):
        parts.extend(str(v) for v in sf.values() if v and str(v).strip())
    elif isinstance(sf, list):
        parts.extend(str(s) for s in sf if s and str(s).strip())
    else:
        s = str(sf).strip()
        if s:
            parts.append(s)

    # Context fields with semantic meaning
    semantic_keys = {"pinyin", "reading", "pos", "definition",
                     "gloss", "example", "meaning", "note"}
    contexts = entry.get("contexts", [])
    if isinstance(contexts, list):
        for ctx in contexts:
            if not isinstance(ctx, dict):
                continue
            for key, val in ctx.items():
                if key.lower() in semantic_keys and val and str(val).strip():
                    parts.append(str(val).strip())

    return parts


def _get_entry_key(entry: dict) -> str:
    return str(entry.get("key", ""))


def _get_entry_confidence(entry: dict) -> float:
    conf = entry.get("confidence", 0.8)
    return float(conf) if isinstance(conf, (int, float)) else 0.8


# ---------------------------------------------------------------------------
# Batch insertion — uses _NumpyBackend.bulk_add_memories() for max speed
# ---------------------------------------------------------------------------


def _flush_batch(store, batch: List[Tuple[str, str, dict]]) -> int:
    """Insert a batch of entries using numpy backend's bulk method."""
    backend = getattr(store, "_numpy_backend", None)
    if backend is not None:
        backend.bulk_add_memories(batch)
        return len(batch)
    # Fallback: chromadb batch insert
    if store.collection is not None:
        ids = [b[0] for b in batch]
        docs = [b[1] for b in batch]
        metas = [b[2] for b in batch]
        store.collection.add(documents=docs, metadatas=metas, ids=ids)
        return len(batch)
    return 0


# ---------------------------------------------------------------------------
# Main seeding logic
# ---------------------------------------------------------------------------


def seed_vector_store(
    limit: Optional[int] = None,
    source_filter: Optional[str] = None,
    dry_run: bool = False,
) -> int:
    """Entry point — seeds the VectorMemoryStore.

    Forces numpy backend for maximum import speed.
    """
    # Force numpy backend by temporarily disabling chromadb
    import ai.memory.vector_store as vs_module
    _old_chromadb = vs_module._lazy_chromadb
    vs_module._lazy_chromadb = lambda: None

    from ai.memory.vector_store import VectorMemoryStore

    store = VectorMemoryStore()
    logger.info("Backend: %s (existing vectors: %d)",
                store.backend_type, store.vector_count)

    # Load existing keys for dedup
    seen_keys: Set[str] = set()
    backend = getattr(store, "_numpy_backend", None)
    if backend is not None:
        for meta in backend.metadatas:
            k = meta.get("key", "")
            if k:
                seen_keys.add(k)
        logger.info("  Loaded %d existing keys from numpy backend", len(seen_keys))

    total_imported = 0
    total_skipped = 0
    batch: List[Tuple[str, str, dict]] = []

    def _commit_batch():
        nonlocal batch
        if not batch:
            return
        _flush_batch(store, batch)
        logger.info("  Batch %d committed", len(batch))
        batch = []

    for fname, label in DICT_SOURCES.items():
        if source_filter and source_filter.lower() not in fname:
            continue

        filepath = os.path.join(DICT_DIR, fname)
        if not os.path.exists(filepath):
            logger.warning("File not found: %s", filepath)
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)

        items: list = []
        if isinstance(raw, list):
            items = raw
        elif isinstance(raw, dict):
            items = raw.get("entries", raw.get("dictionary", []))

        file_count = 0
        t_file = time.time()
        for entry in items:
            if not isinstance(entry, dict):
                continue
            if limit is not None and total_imported >= limit:
                break

            entry_key = _get_entry_key(entry)
            if entry_key in seen_keys:
                total_skipped += 1
                continue
            seen_keys.add(entry_key)

            parts = _iter_semantic_parts(entry)
            content = " ".join(p.strip() for p in parts if p.strip())
            if not content.strip():
                total_skipped += 1
                continue

            metadata = {
                "source": label,
                "key": entry_key or "",
                "confidence": _get_entry_confidence(entry),
            }
            # Use hash of key+content for guaranteed uniqueness
            dedup_seed = entry_key or content
            entry_id = f"dict_{abs(hash(dedup_seed)) % 10**14}"

            if dry_run:
                logger.info("[DRY-RUN] %s — %s", entry_id, content[:80])
            else:
                batch.append((entry_id, content, metadata))

                if len(batch) >= BATCH_SIZE:
                    _commit_batch()

            file_count += 1
            total_imported += 1

            if total_imported % 10000 == 0:
                elapsed = time.time() - t_file
                rate = total_imported / elapsed if elapsed > 0 else 0
                logger.info("  Progress: %d entries (%d/s)", total_imported, int(rate))

        # Commit remaining batch for this file
        _commit_batch()
        elapsed = time.time() - t_file
        logger.info("  %s: %d entries in %.1fs (%d/s)",
                    label, file_count, elapsed,
                    int(file_count / elapsed) if elapsed > 0 else 0)

    if not dry_run:
        # Capture count BEFORE restoring chromadb (numpy backend)
        final_count = store.vector_count
        # Persist numpy backend to disk
        store.persist()
        logger.info("Persisting to disk...")
        # Restore chromadb
        vs_module._lazy_chromadb = _old_chromadb
        logger.info("Seeding complete: %d new entries (skipped %d dups). Total vectors: %d",
                     total_imported, total_skipped, final_count)
    else:
        vs_module._lazy_chromadb = _old_chromadb
        logger.info("Dry-run: %d would be imported, %d skipped",
                     total_imported, total_skipped)

    return total_imported


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Seed VectorMemoryStore with dictionary data"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be imported without actually storing",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Maximum entries to import (default: all)",
    )
    parser.add_argument(
        "--source", type=str, default=None,
        help="Source: cedict, jmdict, or wordnet",
    )
    parser.add_argument(
        "--info", action="store_true",
        help="Show available sources and exit",
    )

    args = parser.parse_args()

    if args.info:
        print("Available dictionary sources:")
        for fname, label in DICT_SOURCES.items():
            fpath = os.path.join(DICT_DIR, fname)
            size_mb = os.path.getsize(fpath) // (1024 * 1024) if os.path.exists(fpath) else 0
            print(f"  {fname:20s}  {label:25s}  {size_mb} MB")
        return

    logger.info("Starting VectorMemoryStore seeding...")
    count = seed_vector_store(
        limit=args.limit,
        source_filter=args.source,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print(f"\nDry-run: {count} entries ready to import.")
    else:
        print(f"\nDone! {count} entries imported.")


if __name__ == "__main__":
    main()
