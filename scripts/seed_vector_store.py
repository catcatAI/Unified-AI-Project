"""
ANGELA-MATRIX: [L2] [β] [B] [L1]
Vector Store Seed Script
=========================
Loads dictionary data from ``data/dictionaries/*.json`` into the
VectorMemoryStore (supports both chromadb and numpy backends).

Usage::

    python scripts/seed_vector_store.py                     # seed from all JSON files
    python scripts/seed_vector_store.py --dry-run            # show what would be imported
    python scripts/seed_vector_store.py --limit 100          # only import 100 entries
    python scripts/seed_vector_store.py --source cedict      # only one file
    python scripts/seed_vector_store.py --info               # list available sources

The script uses the public ``VectorMemoryStore.add_memory()`` API so it
works identically with chromadb and numpy backends.  Re-running is safe;
entries with the same ``key`` field are skipped.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Dict, List, Optional, Set

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "apps", "backend", "src"))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed_vector_store")


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
    """Extract semantically meaningful text parts from a dictionary entry.

    The dictionary files use the ED3N DictionaryLayer format:
      - ``surface_forms``: dict of language_code -> text
      - ``contexts``: list of dicts with fields like pinyin, reading, pos
      - ``key``: unique identifier (not semantic, used for dedup)
    """
    parts: List[str] = []

    # Surface forms (the primary semantic content)
    sf = entry.get("surface_forms", {})
    if isinstance(sf, dict):
        parts.extend(str(v) for v in sf.values() if v and str(v).strip())
    elif isinstance(sf, list):
        parts.extend(str(s) for s in sf if s and str(s).strip())
    else:
        s = str(sf).strip()
        if s:
            parts.append(s)

    # Context fields with semantic meaning (skip IDs, timestamps, etc.)
    semantic_context_keys = {"pinyin", "reading", "pos", "definition",
                             "gloss", "example", "meaning", "note"}
    contexts = entry.get("contexts", [])
    if isinstance(contexts, list):
        for ctx in contexts:
            if not isinstance(ctx, dict):
                continue
            for key, val in ctx.items():
                if key.lower() in semantic_context_keys and val and str(val).strip():
                    parts.append(str(val).strip())

    return parts


def _get_entry_key(entry: dict) -> str:
    """Return a unique key for deduplication."""
    return entry.get("key", "")


def _get_entry_confidence(entry: dict) -> float:
    conf = entry.get("confidence", 0.8)
    return float(conf) if isinstance(conf, (int, float)) else 0.8


# ---------------------------------------------------------------------------
# Async seeding logic — single event loop for all inserts
# ---------------------------------------------------------------------------


async def _seed_all(
    store,
    limit: Optional[int],
    source_filter: Optional[str],
    dry_run: bool,
) -> int:
    """Seed the store asynchronously, returning total inserted count."""
    # Track already-seen keys to avoid duplicates
    seen_keys: Set[str] = set()

    # If store already has data, load existing keys
    backend = getattr(store, "_numpy_backend", None)
    if backend is not None:
        for meta in backend.metadatas:
            k = meta.get("key", "")
            if k:
                seen_keys.add(k)
    elif store.collection is not None:
        try:
            all_meta = store.collection.get(limit=100_000)
            if all_meta and all_meta.get("metadatas"):
                for m in all_meta["metadatas"]:
                    k = m.get("key", "") if isinstance(m, dict) else ""
                    if k:
                        seen_keys.add(k)
        except Exception as e:
            logger.warning("Could not read existing keys from chromadb: %s", e)

    total_imported = 0
    total_skipped = 0

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

            entry_id = f"dict_{entry_key[:32] if entry_key else hash(content) % 10**10}"

            if dry_run:
                logger.info("[DRY-RUN] %s — %s", entry_id, content[:80])
            else:
                await store.add_memory(entry_id, content, metadata)

            file_count += 1
            total_imported += 1

            if total_imported % 5000 == 0:
                logger.info("  Progress: %d entries", total_imported)

        logger.info("  %s: %d entries %s", label, file_count,
                    "would be imported (dry-run)" if dry_run else "imported")

    if not dry_run:
        store.persist()
        count = store.vector_count
        logger.info("Seeding complete: %d new entries (skipped %d dups)",
                     total_imported, total_skipped)
        logger.info("Total vectors now: %d", count)
    else:
        logger.info("Dry-run: %d would be imported, %d skipped",
                     total_imported, total_skipped)

    return total_imported


def seed_vector_store(
    limit: Optional[int] = None,
    source_filter: Optional[str] = None,
    dry_run: bool = False,
) -> int:
    """Entry point — creates event loop and runs seeding."""
    from ai.memory.vector_store import VectorMemoryStore

    store = VectorMemoryStore()
    logger.info("Backend: %s (existing vectors: %d)",
                store.backend_type, store.vector_count)

    return asyncio.run(_seed_all(store, limit, source_filter, dry_run))


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
