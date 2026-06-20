"""
ANGELA-MATRIX: [L2] [β] [B] [L1]
Vector Store Seed Script
=========================
Loads dictionary data from ``data/dictionaries/*.json`` into the
VectorMemoryStore.

Uses **batch** inserts (100 per batch) to chromadb — this is ~100× faster
than one-at-a-time insertion.  Re-running is safe: entries whose ``key``
already exists in the store are skipped.

Usage::

    python scripts/seed_vector_store.py                     # seed from all JSON files
    python scripts/seed_vector_store.py --limit 1000        # only import 1000 entries
    python scripts/seed_vector_store.py --source cedict     # only one file
    python scripts/seed_vector_store.py --dry-run --limit 10  # dry run
    python scripts/seed_vector_store.py --info              # list available sources
"""

import argparse
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Set, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "apps", "backend", "src"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed_vector_store")

BATCH_SIZE = 100  # chromadb batch size — 100 per call

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
# Batch insertion helper — works with chromadb or numpy backends
# ---------------------------------------------------------------------------


def _flush_batch(store, batch: List[Tuple[str, str, dict]]) -> int:
    """Insert a batch of (id, content, metadata) tuples into the store.

    Uses the store's underlying collection directly when available
    (chromadb path), or falls back to single-item ``add_memory()``
    (numpy path, which is fast anyway since it's in-memory).
    """
    ids = [b[0] for b in batch]
    docs = [b[1] for b in batch]
    metas = [b[2] for b in batch]

    # ChromaDB path — batch insert via collection.add()
    if store.collection is not None:
        store.collection.add(documents=docs, metadatas=metas, ids=ids)
        return len(batch)

    # Numpy path — single insert is fast (in-memory)
    import asyncio
    for mid, content, meta in batch:
        asyncio.run(store.add_memory(mid, content, meta))
    return len(batch)


# ---------------------------------------------------------------------------
# Main seeding logic
# ---------------------------------------------------------------------------


def seed_vector_store(
    limit: Optional[int] = None,
    source_filter: Optional[str] = None,
    dry_run: bool = False,
) -> int:
    """Entry point — seeds the VectorMemoryStore."""
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
    elif store.collection is not None:
        try:
            # ChromaDB: load all existing metadata (no limit to get all)
            existing = store.collection.get()
            if existing and existing.get("metadatas"):
                for m in existing["metadatas"]:
                    k = m.get("key", "") if isinstance(m, dict) else ""
                    if k:
                        seen_keys.add(k)
            logger.info("  Loaded %d existing keys from chromadb", len(seen_keys))
        except Exception as e:
            logger.warning("  Could not read existing keys: %s", e)

    total_imported = 0
    total_skipped = 0
    batch: List[Tuple[str, str, dict]] = []

    def _commit_batch():
        nonlocal batch
        if not batch:
            return
        size = _flush_batch(store, batch)
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

            if total_imported % 5000 == 0:
                logger.info("  Progress: %d entries", total_imported)

        # Commit remaining batch for this file
        _commit_batch()
        logger.info("  %s: %d entries %s", label, file_count,
                    "would be imported" if dry_run else "imported")

    if not dry_run:
        store.persist()
        logger.info("Seeding complete: %d new entries (skipped %d dups)",
                     total_imported, total_skipped)
        # Re-init store to get accurate count (chromadb doesn't expose count on VectorMemoryStore)
        store2 = VectorMemoryStore()
        logger.info("Total vectors now: %d (backend: %s)",
                     store2.vector_count, store2.backend_type)
    else:
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
