"""
Vector Memory Store
Handles vector storage and retrieval using ChromaDB.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_chromadb = None


def _lazy_chromadb():
    global _chromadb
    if _chromadb is None:
        try:
            from concurrent.futures import ThreadPoolExecutor, TimeoutError

            with ThreadPoolExecutor(max_workers=1) as ex:
                _chromadb = ex.submit(__import__, "chromadb").result(timeout=60)
        except (ImportError, TimeoutError):
            logger.warning("chromadb not available (timed out); vector store disabled")
            _chromadb = False
    return _chromadb if _chromadb else None


class VectorMemoryStore:
    def __init__(self, persist_directory: Optional[str] = None):
        self.client: Optional[Any] = None
        self.collection: Optional[Any] = None
        chromadb = _lazy_chromadb()
        if chromadb is None:
            return
        try:
            if persist_directory:
                self.client = chromadb.PersistentClient(path=persist_directory)
            else:
                self.client = chromadb.Client()
            self.collection = self.client.get_or_create_collection(
                name="ham_memories", metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            logger.error(f"VectorMemoryStore init failed: {e}")
            self.client = None
            self.collection = None

    async def add_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if self.collection is None:
            return
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata or {}],
                ids=[memory_id],
            )
        except Exception as e:
            logger.error(f"add_memory failed: {e}")

    async def semantic_search(self, query: str, limit: int = 10) -> Dict[str, Any]:
        if self.collection is None:
            return {}
        try:
            return self.collection.query(query_texts=[query], n_results=limit)
        except Exception as e:
            logger.error(f"semantic_search failed: {e}")
            return {}

