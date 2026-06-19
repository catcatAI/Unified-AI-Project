#!/usr/bin/env python3
"""
Ingest Chinese activity logs from 我的活動 into VectorMemoryStore.
Reads *.txt files, splits into segments, stores via VectorMemoryStore.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "apps" / "backend" / "src"))

from ai.memory.vector_store import VectorMemoryStore

ACTIVITY_DIR = PROJECT_ROOT / "我的活動"
MAX_CHARS_PER_SEGMENT = 2000


def split_content(content: str) -> list[str]:
    raw = [s for s in content.split("\n\n") if s.strip()]
    segments: list[str] = []
    for seg in raw:
        if len(seg) > MAX_CHARS_PER_SEGMENT:
            current = ""
            for line in seg.splitlines(True):
                if len(current) + len(line) > MAX_CHARS_PER_SEGMENT:
                    if current.strip():
                        segments.append(current)
                    current = line
                else:
                    current += line
            if current.strip():
                segments.append(current)
        else:
            segments.append(seg)
    return [s for s in segments if s.strip()]


async def ingest_file(file_path: Path, store: VectorMemoryStore, existing_ids: set) -> None:
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[ERROR] Failed to read {file_path}: {e}")
        return

    segments = split_content(content)
    if not segments:
        print(f"[WARN] No content to ingest in {file_path}")
        return

    for idx, seg in enumerate(segments):
        relative = file_path.relative_to(PROJECT_ROOT)
        doc_id = f"{relative}#seg_{idx}"
        if doc_id in existing_ids:
            continue
        metadata = {
            "source": "我的活動",
            "filename": file_path.name,
            "segment_index": idx,
        }
        await store.add_memory(doc_id, seg, metadata)
        existing_ids.add(doc_id)

    print(f"[INFO] Ingested {len(segments)} segment(s) from {file_path.name}")


async def main() -> None:
    if not ACTIVITY_DIR.exists():
        print(f"[ERROR] Activity directory not found: {ACTIVITY_DIR}")
        return

    store = VectorMemoryStore()
    print(f"[INFO] Using vector store at {store.persist_directory}")

    existing_ids = set()
    if store.vector_count > 0:
        for m in store._numpy_backend.ids if store._numpy_backend else []:
            existing_ids.add(m)

    txt_files = list(ACTIVITY_DIR.rglob("*.txt"))
    if not txt_files:
        print("[INFO] No .txt files found.")
        return

    for f in txt_files:
        await ingest_file(f, store, existing_ids)

    store.persist()
    print("[DONE] All files processed and saved.")


if __name__ == "__main__":
    asyncio.run(main())
