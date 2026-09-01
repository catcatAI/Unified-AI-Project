"""
Vector Memory Store
Handles vector storage and retrieval with automatic backend selection:
- ChromaDB when available (default persist_directory)
- Pure numpy + JSON fallback (stdlib-only, cross-platform)
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import asyncio
import atexit
import importlib
import json
import logging
import os
import time
import zlib
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from core.system.config.magic_numbers import cache_value, timing_value

logger = logging.getLogger(__name__)

_chromadb = None

# Default storage directory
_DEFAULT_PERSIST_DIR = os.path.join(os.environ.get("VECTOR_STORE_PATH", "data/vector_store"))

# Embedding dimension for numpy backend (hashing trick)
_NUMPY_EMBED_DIM = 512

# Bump when _embed() changes: persisted vectors computed with a different
# embedding are incompatible (similarity would be garbage) and are discarded
# on load instead of silently poisoning retrieval.
# v2: crc32 stable hashing (was salted hash()).
# v3: added word-level unigram signal (weight 2.0) on top of char bigrams.
_EMBED_VERSION = 3

# =============================================================================
# Lazy chromadb import (60s timeout, existing behavior)
# =============================================================================


def _lazy_chromadb():
    global _chromadb
    if _chromadb is None:
        try:
            from concurrent.futures import ThreadPoolExecutor, TimeoutError

            with ThreadPoolExecutor(max_workers=1) as ex:
                _chromadb = ex.submit(importlib.import_module, "chromadb").result(timeout=60)
        except (ImportError, TimeoutError):
            logger.warning("chromadb not available (timed out); using numpy backend")
            _chromadb = False
    return _chromadb if _chromadb else None


# =============================================================================
# Numpy backend: stdlib-only vector storage with character bigram embedding
# =============================================================================


class _NumpyBackend:
    def __init__(self, persist_dir: str):
        self.persist_dir = persist_dir
        self.vectors: np.ndarray = np.empty((0, _NUMPY_EMBED_DIM), dtype=np.float32)
        self.ids: List[str] = []
        self.documents: List[str] = []
        self.metadatas: List[Dict[str, Any]] = []
        self._dirty = False
        # Amortized-O(1) inserts: new vectors queue in a small buffer and are
        # compacted into the matrix in bulk (was: full np.vstack per insert).
        self._pending_vecs: List[np.ndarray] = []
        self._flush_interval = max(1, cache_value("vector_store.flush_interval", 32))
        # Debounced durability: add_memory marks dirty and only hits disk when
        # the debounce window has elapsed; persist() always forces a save.
        self._save_debounce = timing_value("vector_store.save_debounce", 30.0)
        self._last_save_ts = time.time()
        # Durability backstop: no production code calls persist() on a
        # schedule, so without this a clean exit inside the debounce window
        # would silently drop recently learned memories.
        self._atexit_registered = False
        os.makedirs(persist_dir, exist_ok=True)
        self._load()
        self._register_atexit()

    def _register_atexit(self) -> None:
        if self._atexit_registered:
            return
        atexit.register(self._atexit_save)
        self._atexit_registered = True

    def _atexit_save(self) -> None:
        try:
            if self._dirty and os.path.isdir(self.persist_dir):
                self._save()
        except Exception as e:  # pragma: no cover - best-effort on shutdown
            logger.warning("Vector store atexit save failed: %s", e)

    # ------------------------------------------------------------------
    # Embedding: character bigram hashing trick (STABLE across processes)
    # ------------------------------------------------------------------

    @staticmethod
    def _embed(text: str) -> np.ndarray:
        text = text.lower().strip()
        vec = np.zeros(_NUMPY_EMBED_DIM, dtype=np.float32)
        if not text:
            return vec
        seen_bg = set()
        # Word-level unigrams first: char bigrams smear across Latin word
        # boundaries ("quantum" ↔ "antum"), exact-word hits restore that
        # signal at negligible cost. CJK has no whitespace words, so this
        # only fires on Latin/digit runs.
        import re as _re

        seen_word = set()
        for w in _re.split(r"[^a-z0-9]+", text):
            if len(w) >= 2 and w not in seen_word:
                seen_word.add(w)
                idx = zlib.crc32(("w:" + w).encode("utf-8")) % _NUMPY_EMBED_DIM
                vec[idx] += 2.0
        if len(text) < 2:
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            return vec
        for i in range(len(text) - 1):
            bg = text[i : i + 2]
            if bg not in seen_bg:
                seen_bg.add(bg)
                # zlib.crc32 is deterministic across processes. Built-in
                # hash() is salted per process (PYTHONHASHSEED), which made
                # persisted vectors permanently incompatible with query
                # embeddings after every restart.
                idx = zlib.crc32(bg.encode("utf-8")) % _NUMPY_EMBED_DIM
                vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def _flush_pending(self) -> None:
        """Compact queued rows into the vector matrix in one operation."""
        if not self._pending_vecs:
            return
        new_vecs = np.stack(self._pending_vecs)
        self._pending_vecs.clear()
        base = self.vectors.shape[0]
        grown = np.zeros((base + new_vecs.shape[0], _NUMPY_EMBED_DIM), dtype=np.float32)
        grown[:base] = self.vectors
        grown[base:] = new_vecs
        self.vectors = grown

    async def add_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._pending_vecs.append(self._embed(content))
        if len(self._pending_vecs) >= self._flush_interval:
            self._flush_pending()
        self.ids.append(memory_id)
        self.documents.append(content)
        self.metadatas.append(metadata or {})
        if len(self.ids) > 10000:
            self._flush_pending()
            self.ids.pop(0)
            self.documents.pop(0)
            self.metadatas.pop(0)
            self.vectors = self.vectors[1:]
        self._dirty = True
        now = time.time()
        if now - self._last_save_ts >= self._save_debounce:
            self._save()

    def bulk_add_memories(
        self,
        entries: List[Tuple[str, str, Optional[Dict[str, Any]]]],
    ) -> None:
        """Add multiple memories in a single batch.

        Avoids O(n²) ``vstack`` and per-insert ``_save()``
        that make sequential ``add_memory`` calls extremely slow.
        Chunked at 4096 to keep peak allocation bounded (100k×512×4=195MB
        would otherwise double to ~390MB transient).
        """
        if not entries:
            return
        # Chunk to bound peak memory (4096×512×4=8MB per chunk)
        chunk = 4096
        for start in range(0, len(entries), chunk):
            part = entries[start : start + chunk]
            n = len(part)
            new_vecs = np.zeros((n, _NUMPY_EMBED_DIM), dtype=np.float32)
            for i, (mid, content, meta) in enumerate(part):
                new_vecs[i] = self._embed(content)
                self.ids.append(mid)
                self.documents.append(content)
                self.metadatas.append(meta or {})
            base = self.vectors.shape[0]
            grown = np.zeros((base + n, _NUMPY_EMBED_DIM), dtype=np.float32)
            grown[:base] = self.vectors
            grown[base:] = new_vecs
            self.vectors = grown
        self._dirty = True

    async def semantic_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        self._flush_pending()
        if len(self.ids) == 0:
            return {}
        qvec = self._embed(query)
        sims = self.vectors @ qvec
        n = min(limit, len(sims))
        if n == 0:
            return {}
        indices = np.argpartition(-sims, n - 1)[:n]
        sorted_idx = indices[np.argsort(-sims[indices])]
        return {
            "ids": [[self.ids[i] for i in sorted_idx]],
            "documents": [[self.documents[i] for i in sorted_idx]],
            "distances": [[float(1.0 - sims[i]) for i in sorted_idx]],
        }

    def __len__(self) -> int:
        return len(self.ids)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def persist(self) -> None:
        if self._dirty:
            self._save()

    def _save(self) -> None:
        self._flush_pending()
        np.save(os.path.join(self.persist_dir, "vectors.npy"), self.vectors)
        meta_path = os.path.join(self.persist_dir, "metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "embed_version": _EMBED_VERSION,
                    "ids": self.ids,
                    "documents": self.documents,
                    "metadatas": self.metadatas,
                },
                f,
                ensure_ascii=False,
            )
        self._dirty = False
        self._last_save_ts = time.time()

    def _load(self) -> None:
        vec_path = os.path.join(self.persist_dir, "vectors.npy")
        meta_path = os.path.join(self.persist_dir, "metadata.json")
        if os.path.exists(vec_path) and os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                stored_version = int(data.get("embed_version", 1))
                if stored_version != _EMBED_VERSION:
                    # Vectors from an incompatible embedding would match
                    # queries only by accident — discard rather than poison
                    # retrieval (pre-salt-fix stores are garbage anyway).
                    logger.warning(
                        "Vector store embed_version mismatch (stored=%d, current=%d) "
                        "at %s; discarding stale vectors",
                        stored_version,
                        _EMBED_VERSION,
                        self.persist_dir,
                    )
                    return
                self.vectors = np.load(vec_path, allow_pickle=False)
                self.ids = data.get("ids", [])
                self.documents = data.get("documents", [])
                self.metadatas = data.get("metadatas", [])
                n = len(self.ids)
                if self.vectors.shape[0] != n:
                    logger.warning(
                        "Vector/metadata count mismatch (vec=%d, meta=%d); truncating",
                        self.vectors.shape[0],
                        n,
                    )
                    min_n = min(self.vectors.shape[0], n)
                    self.vectors = self.vectors[:min_n]
                    self.ids = self.ids[:min_n]
                    self.documents = self.documents[:min_n]
                    self.metadatas = self.metadatas[:min_n]
                logger.info("Loaded %d vectors from %s", len(self.ids), self.persist_dir)
            except Exception as e:
                logger.warning(
                    "Failed to load vector store from %s: %s; starting fresh", self.persist_dir, e
                )
                self.vectors = np.empty((0, _NUMPY_EMBED_DIM), dtype=np.float32)
                self.ids = []
                self.documents = []
                self.metadatas = []
        else:
            logger.info("No existing vector store found at %s; starting fresh", self.persist_dir)


# =============================================================================
# ChromaDB backend
# =============================================================================


class _ChromadbBackend:
    def __init__(self, persist_dir: str):
        chromadb = _lazy_chromadb()
        if chromadb is None:
            raise RuntimeError("chromadb not available")
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="ham_memories", metadata={"hnsw:space": "cosine"}
        )

    async def add_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        # chromadb's collection.add is a blocking I/O call. Run it in a worker
        # thread so it yields the event loop (lets wait_for / timeouts work and
        # keeps the request path responsive).
        await asyncio.to_thread(
            self.collection.add,
            documents=[content],
            metadatas=[metadata or {}],
            ids=[memory_id],
        )

    async def semantic_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        # chromadb's collection.query is a blocking I/O call — offload to a
        # worker thread so the caller's asyncio.wait_for can actually bound it.
        result = await asyncio.to_thread(
            self.collection.query, query_texts=[query], n_results=limit
        )
        return result


# =============================================================================
# Public VectorMemoryStore — automatic backend selection
# =============================================================================


class VectorMemoryStore:
    def __init__(self, persist_directory: Optional[str] = None):
        self.persist_directory = persist_directory or _DEFAULT_PERSIST_DIR
        self.client: Optional[Any] = None
        self.collection: Optional[Any] = None
        self._numpy_backend: Optional[_NumpyBackend] = None
        os.makedirs(self.persist_directory, exist_ok=True)

        # Deployment flag: force the pure-numpy backend even when chromadb is
        # installed. Some environments (e.g. Windows with onnxruntime-backed
        # embeddings) make chromadb's PersistentClient pathologically slow
        # (multi-second queries), and vector search here is enrichment-only —
        # correctness never depends on chromadb, only on recall quality.
        force_numpy = os.environ.get("ANGELA_VECTOR_BACKEND", "").strip().lower() == "numpy"

        chromadb = None if force_numpy else _lazy_chromadb()
        if chromadb is not None:
            try:
                _cb = _ChromadbBackend(self.persist_directory)
                self.client = _cb.client
                self.collection = _cb.collection
                self.add_memory = _cb.add_memory
                self.semantic_search = _cb.semantic_search
                logger.info(
                    "VectorMemoryStore: using chromadb backend at %s",
                    self.persist_directory,
                )
                return
            except Exception as e:
                logger.warning(
                    "ChromaDB backend init failed (%s); falling back to numpy",
                    e,
                )

        self._numpy_backend = _NumpyBackend(self.persist_directory)
        logger.info(
            "VectorMemoryStore: using numpy backend at %s",
            self.persist_directory,
        )

    async def add_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self._numpy_backend is not None:
            await self._numpy_backend.add_memory(memory_id, content, metadata)

    async def semantic_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        if self._numpy_backend is not None:
            return await self._numpy_backend.semantic_search(query, limit)
        return {}

    def persist(self) -> None:
        if self._numpy_backend is not None:
            self._numpy_backend.persist()

    @property
    def vector_count(self) -> int:
        if self._numpy_backend is not None:
            return len(self._numpy_backend)
        if self.collection is not None:
            try:
                return self.collection.count()
            except Exception as err:
                logger.warning("ChromaDB count failed: %s", err, exc_info=True)
                return 0
        return 0

    @property
    def backend_type(self) -> str:
        """Return the active backend type: 'chromadb', 'numpy', or 'none'."""
        if self.client is not None and self.collection is not None:
            return "chromadb"
        if self._numpy_backend is not None:
            return "numpy"
        return "none"

    def __bool__(self) -> bool:
        return True
