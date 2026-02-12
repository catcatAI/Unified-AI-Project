#!/usr/bin/env python3
"""
Ingest Chinese activity logs from the folder "我的活動" into the AI memory system.
The script reads all *.txt files, optionally splits large files according to
per‑file rules, generates embeddings using the HybridBrain provider, and stores
them in the vector store for later retrieval.
"""
import os
import sys
import asyncio
from pathlib import Path
import logging
logger = logging.getLogger(__name__)

# Adjust import paths for the project structure
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT / "apps" / "backend" / "src"))

from core.llm.hybrid_brain import HybridBrain
from ai.memory.vector_store import VectorStore as VectorMemoryStore

# Directory containing the txt files (Chinese activity logs)
ACTIVITY_DIR = PROJECT_ROOT / "我的活動"

# ---------------------------------------------------------------------------
# Splitting utilities
# ---------------------------------------------------------------------------
# Default maximum characters per segment (adjustable). Files larger than this
# will be split into multiple segments so that each embedding stays within a
# reasonable size for the LLM.
MAX_CHARS_PER_SEGMENT = 2000

# Per‑file custom split rules – map a filename (or stem) to a callable that
# receives the raw text and returns a list of segment strings.  Add entries
# here when a specific file requires a special rule.
CUSTOM_SPLIT_RULES = {
    # Example: "chatlog.txt": lambda txt: [s for s in txt.split("\n\n") if s.strip()],
    # Add more custom rules as needed.
}

def split_content(file_path: Path, content: str) -> list[str]:
    """Return a list of text segments for *content*.

    The function first checks for a custom rule based on the file name. If none
    is found, it falls back to a generic splitter that respects
    ``MAX_CHARS_PER_SEGMENT``.
    """
    # 1️⃣ Custom rule based on file name (case‑insensitive)
    rule = CUSTOM_SPLIT_RULES.get(file_path.name.lower()) or CUSTOM_SPLIT_RULES.get(file_path.stem.lower())
    if rule:
        segments = rule(content)
    else:
        # 2️⃣ Generic splitter – split on double newlines first
        raw_segments = [s for s in content.split("\n\n") if s.strip()]
        segments: list[str] = []
        for seg in raw_segments:
            # If a segment is still too long, further split on single newline
            if len(seg) > MAX_CHARS_PER_SEGMENT:
                sub_parts = []
                current = ""
                for line in seg.splitlines(True):
                    if len(current) + len(line) > MAX_CHARS_PER_SEGMENT:
                        sub_parts.append(current)
                        current = line
                    else:
                        current += line
                if current:
                    sub_parts.append(current)
                segments.extend([p for p in sub_parts if p.strip()])
            else:
                segments.append(seg)
    return [s for s in segments if s.strip()]

async def ingest_file(file_path: Path, brain: HybridBrain, store: VectorMemoryStore, existing_ids: set):
    """Read *file_path*, split it if necessary, generate embeddings for each
    segment, and store them in the vector store.
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[ERROR] Failed to read {file_path}: {e}")
        return

    segments = split_content(file_path, content)
    if not segments:
        print(f"[WARN] No content to ingest in {file_path}")
        return

    batch_contents = []
    batch_metadatas = []
    batch_ids = []
    BATCH_SIZE = 100

    for idx, seg in enumerate(segments):
        # Use a composite doc_id that includes the segment index
        relative = file_path.relative_to(PROJECT_ROOT)
        doc_id = f"{relative}#seg_{idx}"

        if doc_id in existing_ids:
            continue

        metadata = {
            "source": "我的活動",
            "filename": file_path.name,
            "segment_index": idx,
            "segment_length": len(seg),
        }
        
        batch_contents.append(seg)
        batch_metadatas.append(metadata)
        batch_ids.append(doc_id)
        existing_ids.add(doc_id) # Optimistically mark as added

        if len(batch_contents) >= BATCH_SIZE:
            await store.add_memories(
                contents=batch_contents,
                metadatas=batch_metadatas,
                ids=batch_ids,
                auto_save=False  # Disable auto-save for performance
            )
            print(f"[INFO] Ingested batch of {len(batch_contents)} segments from {file_path.name} (upto {idx + 1}/{len(segments)})")
            batch_contents = []
            batch_metadatas = []
            batch_ids = []

    # Process remaining
    if batch_contents:
        await store.add_memories(
            contents=batch_contents,
            metadatas=batch_metadatas,
            ids=batch_ids,
            auto_save=False
        )
        print(f"[INFO] Ingested final batch of {len(batch_contents)} segments from {file_path.name}")

async def main():
    if not ACTIVITY_DIR.exists():
        print(f"[ERROR] Activity directory not found: {ACTIVITY_DIR}")
        return
    brain = HybridBrain()
    # Ensure providers (skipped in mock mode)
    store = VectorMemoryStore()
    
    # Load existing IDs to support resume
    if hasattr(store, 'memories'):
        existing_ids = {m['id'] for m in store.memories}
        print(f"[INFO] Found {len(existing_ids)} existing memories. Resuming ingestion...")
    else:
        existing_ids = set()

    txt_files = list(ACTIVITY_DIR.rglob("*.txt"))
    if not txt_files:
        print("[INFO] No .txt files found in 我的活動.")
        return
    tasks = [ingest_file(p, brain, store, existing_ids) for p in txt_files]
    await asyncio.gather(*tasks)
    
    print("[INFO] Saving Vector Store to disk...")
    store._save_to_disk()
    print("[DONE] All files processed and saved.")

if __name__ == "__main__":
    asyncio.run(main())
