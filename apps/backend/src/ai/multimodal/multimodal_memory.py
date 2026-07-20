# =============================================================================
# ANGELA-MATRIX: [L3] [γδ] [C] [L3]
# =============================================================================
"""
MultimodalMemoryStore — persistent storage for multimodal encoding results.

Analogous to HAMMemoryManager for the chat pipeline.
Stores encoded latents with metadata, supports similarity search,
time-based recall, TTL-based compaction, and JSON persistence.

Key features:
  - store(): Save a (modality, latent, metadata) tuple with auto-ID
  - search(): Find top-k similar latents via cosine similarity
  - recall_by_time(): Query by time window
  - compact(): Compress old entries (keep only latent + summary)
  - cleanup(): Remove expired entries
  - save/load: JSON persistence to disk
"""

import json
import logging
from core.system.config.async_io import async_json_load
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np

logger = logging.getLogger(__name__)


class MultimodalMemoryStore:
    """Persistent store for multimodal encoding results.

    Attributes:
        store_dir: Directory for JSON persistence
        max_entries: Maximum entries before compaction (default 5000)
        ttl_days: Time-to-live for full entries in days (default 7)
        ttl_compact_days: Time-to-live for compacted entries in days (default 30)
    """

    def __init__(
        self,
        store_dir: Optional[str] = None,
        max_entries: int = 5000,
        ttl_days: int = 7,
        ttl_compact_days: int = 30,
    ):
        self.store_dir = store_dir
        self.max_entries = max_entries
        self.ttl_seconds = ttl_days * 86400
        self.ttl_compact_seconds = ttl_compact_days * 86400

        self._entries: Dict[str, Dict[str, Any]] = {}
        self._lock = None  # asyncio lock for thread safety

    def _get_lock(self):
        if self._lock is None:
            import asyncio

            self._lock = asyncio.Lock()
        return self._lock

    # --- Store ---

    async def store(
        self, modality: str, latent: List[float], metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a multimodal encoding result.

        Args:
            modality: "vision" or "audio"
            latent: 64-dim latent vector
            metadata: Optional metadata dict

        Returns:
            entry_id: Unique identifier for the stored entry
        """
        async with self._get_lock():
            entry_id = f"{modality}_{uuid4().hex[:12]}"
            self._entries[entry_id] = {
                "modality": modality,
                "latent": latent,
                "metadata": metadata or {},
                "timestamp": time.time(),
                "compacted": False,
            }

            # Auto-compact if over limit
            if len(self._entries) > self.max_entries:
                await self._compact_impl()

            # Auto-save if store_dir configured
            if self.store_dir:
                self._save_impl()

            return entry_id

    async def store_from_item(self, item_id: str, item: Dict[str, Any]) -> Optional[str]:
        """Store from a MultimodalService registered item.

        Args:
            item_id: The item's ID in MultimodalService
            item: The item dict from MultimodalService

        Returns:
            Memory entry ID, or None if storage failed
        """
        latent = item.get("latent")
        modality = item.get("modality")
        if not latent or not modality:
            return None
        return await self.store(
            modality=modality,
            latent=latent,
            metadata={"source_item_id": item_id, "timestamp": item.get("timestamp", 0)},
        )

    # --- Search ---

    async def search(
        self, query_latent: List[float], top_k: int = 5, modality_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for top-k similar latents via cosine similarity.

        Args:
            query_latent: 64-dim query latent vector
            top_k: Number of results to return
            modality_filter: Optional modality filter

        Returns:
            List of {entry_id, score, modality, metadata, timestamp}
        """
        q = np.array(query_latent, dtype=np.float32)
        q_norm = np.linalg.norm(q)
        if q_norm < 1e-10:
            return []
        q = q / q_norm

        results: List[Tuple[float, str, Dict]] = []

        async with self._get_lock():
            for eid, entry in self._entries.items():
                if modality_filter and entry.get("modality") != modality_filter:
                    continue

                latent = np.array(entry["latent"], dtype=np.float32)
                latent_norm = np.linalg.norm(latent)
                if latent_norm < 1e-10:
                    continue
                latent = latent / latent_norm

                score = float(np.dot(q, latent))
                results.append((score, eid, entry))

        results.sort(key=lambda x: x[0], reverse=True)
        top = results[:top_k]

        return [
            {
                "entry_id": eid,
                "score": round(score, 6),
                "modality": entry.get("modality"),
                "metadata": entry.get("metadata", {}),
                "timestamp": entry.get("timestamp", 0),
                "compacted": entry.get("compacted", False),
            }
            for score, eid, entry in top
        ]

    async def recall_by_time(
        self, hours: float = 24, modality_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Recall entries within a time window.

        Args:
            hours: Time window in hours
            modality_filter: Optional modality filter

        Returns:
            List of entry dicts within the time window
        """
        cutoff = time.time() - hours * 3600
        results = []

        async with self._get_lock():
            for eid, entry in self._entries.items():
                if entry.get("timestamp", 0) < cutoff:
                    continue
                if modality_filter and entry.get("modality") != modality_filter:
                    continue
                results.append(
                    {
                        "entry_id": eid,
                        "modality": entry.get("modality"),
                        "latent": entry.get("latent"),
                        "metadata": entry.get("metadata", {}),
                        "timestamp": entry.get("timestamp", 0),
                        "compacted": entry.get("compacted", False),
                    }
                )

        results.sort(key=lambda x: x["timestamp"], reverse=True)
        return results

    async def get_entry(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Get a single entry by ID."""
        async with self._get_lock():
            entry = self._entries.get(entry_id)
            if entry is None:
                return None
            return {
                "entry_id": entry_id,
                "modality": entry["modality"],
                "latent": entry["latent"],
                "metadata": entry.get("metadata", {}),
                "timestamp": entry.get("timestamp", 0),
                "compacted": entry.get("compacted", False),
            }

    async def count(self) -> int:
        """Return total number of entries."""
        async with self._get_lock():
            return len(self._entries)

    # --- Compaction & Cleanup ---

    async def compact(self) -> Dict[str, Any]:
        """Compress entries older than TTL (keep only latent + summary metadata)."""
        async with self._get_lock():
            return await self._compact_impl()

    async def _compact_impl(self) -> Dict[str, Any]:
        """Internal compaction implementation (lock must be held)."""
        now = time.time()
        compacted_count = 0
        deleted_count = 0

        eids_to_delete = []
        for eid, entry in self._entries.items():
            age = now - entry.get("timestamp", now)

            if age > self.ttl_compact_seconds:
                eids_to_delete.append(eid)
            elif age > self.ttl_seconds and not entry.get("compacted"):
                # Compact: keep only latent + summary metadata
                metadata = entry.get("metadata", {})
                summary_metadata = {
                    k: v for k, v in metadata.items() if isinstance(v, (str, int, float, bool))
                }
                entry["metadata"] = summary_metadata
                entry["compacted"] = True
                compacted_count += 1

        for eid in eids_to_delete:
            del self._entries[eid]
            deleted_count += 1

        if compacted_count > 0 or deleted_count > 0:
            logger.info("Memory compacted: %d entries, %d deleted", compacted_count, deleted_count)

        return {
            "compacted": compacted_count,
            "deleted": deleted_count,
            "remaining": len(self._entries),
        }

    async def cleanup(self) -> Dict[str, Any]:
        """Remove all expired entries."""
        return await self.compact()

    # --- Stats ---

    async def stats(self) -> Dict[str, Any]:
        """Return memory store statistics."""
        async with self._get_lock():
            vision_count = sum(1 for e in self._entries.values() if e.get("modality") == "vision")
            audio_count = sum(1 for e in self._entries.values() if e.get("modality") == "audio")
            compacted_count = sum(1 for e in self._entries.values() if e.get("compacted"))

            now = time.time()
            ages = [now - e.get("timestamp", now) for e in self._entries.values()]
            avg_age = sum(ages) / max(len(ages), 1)

            return {
                "total_entries": len(self._entries),
                "vision_entries": vision_count,
                "audio_entries": audio_count,
                "compacted_entries": compacted_count,
                "avg_age_hours": round(avg_age / 3600, 1),
                "max_entries": self.max_entries,
            }

    # --- Persistence ---

    def _save_impl(self) -> None:
        """Save all entries to JSON (lock must be held externally).

        Note: For very large memory stores (>10000 entries), consider
        splitting into multiple files or using a database backend.
        """
        if not self.store_dir:
            return
        try:
            path = Path(self.store_dir)
            path.mkdir(parents=True, exist_ok=True)

            # Save all entries (limit safeguard at 10000 to prevent OOM)
            entries_to_save = dict(list(self._entries.items())[-10000:])
            if len(self._entries) > 10000:
                logger.warning(
                    "Memory store saving %d/%d entries (truncated at 10000)",
                    len(entries_to_save),
                    len(self._entries),
                )
            data = {
                "entries": {
                    eid: {
                        "modality": e["modality"],
                        "latent": e["latent"],
                        "metadata": e.get("metadata", {}),
                        "timestamp": e.get("timestamp", 0),
                        "compacted": e.get("compacted", False),
                    }
                    for eid, e in entries_to_save.items()
                },
                "saved_at": time.time(),
            }
            save_path = path / "multimodal_memory.json"
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            logger.warning("Memory save failed: %s", e)

    async def save(self) -> Optional[str]:
        """Save entries to JSON file (async version).

        Returns:
            Path to saved file, or None if save failed
        """
        if not self.store_dir:
            return None
        async with self._get_lock():
            self._save_impl()
            return str(Path(self.store_dir) / "multimodal_memory.json")

    async def load(self) -> bool:
        """Load entries from JSON file.

        Returns:
            True if loaded successfully
        """
        if not self.store_dir:
            return False
        try:
            load_path = Path(self.store_dir) / "multimodal_memory.json"
            if not load_path.exists():
                return False

            async with self._get_lock():
                with open(load_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                entries_data = data.get("entries", {})
                self._entries = {}
                for eid, entry in entries_data.items():
                    self._entries[eid] = {
                        "modality": entry.get("modality", "unknown"),
                        "latent": entry.get("latent", []),
                        "metadata": entry.get("metadata", {}),
                        "timestamp": entry.get("timestamp", 0),
                        "compacted": entry.get("compacted", False),
                    }

            logger.info("Memory loaded %d entries from %s", len(self._entries), load_path)
            return True
        except Exception as e:
            logger.warning("Memory load failed: %s", e)
            return False
