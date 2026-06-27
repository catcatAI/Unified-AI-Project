# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================

import logging
import os
from typing import Any, Dict, List, Optional

import numpy as np
from ai.memory.vector_store import VectorMemoryStore

logger = logging.getLogger(__name__)


class HAMVectorStoreManager:
    def __init__(self, storage_dir: str, chroma_client: Optional[Any] = None):
        self.vector_store: Optional[VectorMemoryStore] = None
        self.chroma_collection: Optional[Any] = None

        if chroma_client is not None:
            try:
                self.chroma_collection = chroma_client.get_or_create_collection(
                    name="ham_memories", metadata={"hnsw:space": "cosine"}
                )
                logger.info("ChromaDB collection initialized from external chroma_client.")
            except Exception as e:  # broad exception acceptable: external client initialization should not crash the system
                logger.error(f"Failed to initialize ChromaDB collection from external client: {e}", exc_info=True)
                self.chroma_collection = None
        else:
            if os.environ.get("HAM_DISABLE_VECTOR_STORE", "0") == "1":
                logger.info("HAM: VectorMemoryStore disabled via HAM_DISABLE_VECTOR_STORE = 1")
            else:
                try:
                    self.vector_store = VectorMemoryStore(
                        persist_directory=os.path.join(storage_dir, "chroma_db")
                    )
                    logger.info("VectorMemoryStore initialized successfully.")

                    if (
                        self.vector_store
                        and hasattr(self.vector_store, "client")
                        and self.vector_store.client
                    ):
                        try:
                            self.chroma_collection = (
                                self.vector_store.client.get_or_create_collection(
                                    name="ham_memories", metadata={"hnsw:space": "cosine"}
                                )
                            )
                            logger.info(
                                "ChromaDB collection initialized successfully via VectorMemoryStore."
                            )
                        except Exception as e:  # broad exception acceptable: collection initialization should not crash the manager
                            logger.error(
                                f"Failed to initialize ChromaDB collection via VectorMemoryStore: {e}"
                                , exc_info=True
                            )
                            self.chroma_collection = None
                    else:
                        logger.warning(
                            "VectorMemoryStore client not available for direct ChromaDB collection access."
                            , exc_info=True
                        )
                except Exception as e:  # broad exception acceptable: initialization failure should disable vector store gracefully
                    logger.warning(
                        f"VectorMemoryStore initialization failed (likely due to chromadb / numpy issue): {e}. Vector search will be disabled."
                        , exc_info=True
                    )
                    self.vector_store = None
                    self.chroma_collection = None

    async def add_semantic_vector(self, memory_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """Add a semantic vector."""
        try:
            if self.chroma_collection is not None:
                self.chroma_collection.add(
                    documents=[content], metadatas=[metadata], ids=[memory_id]
                )
                logger.debug(
                    f"HAM: Stored semantic vector for {memory_id} in injected Chroma collection."
                )
            elif self.vector_store is not None:
                await self.vector_store.add_memory(
                    memory_id=memory_id, content=content, metadata=metadata
                )
                logger.debug(f"HAM: Stored semantic vector for {memory_id} in VectorMemoryStore.")
            else:
                logger.debug(
                    f"HAM: Vector / Chroma store disabled, skipping semantic vector storage for {memory_id}."
                )
        except Exception as e:  # broad exception acceptable: storage failure should be logged gracefully
            logger.error(f"Error storing semantic vector for {memory_id}: {e}", exc_info=True)

    async def embed_text(self, text: str) -> Optional[np.ndarray]:
        """Generate an embedding vector for text using the numpy hashing trick.

        Falls back to the same algorithm used by ``_NumpyBackend._embed``.
        Returns ``None`` if the vector store is not available.
        """
        if self.vector_store and self.vector_store._numpy_backend is not None:
            from ai.memory.vector_store import _NumpyBackend
            return _NumpyBackend._embed(text)
        if self.chroma_collection is not None:
            from ai.memory.ham_utils import generate_embedding
            return generate_embedding(text)
        return None

    async def query_similar(
        self, query_embedding: np.ndarray, n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Query similar vectors by embedding.

        Returns a list of dicts with keys ``id``, ``document``, ``distance``.
        Returns an empty list when the store is unavailable.
        """
        if self.vector_store and self.vector_store._numpy_backend is not None:
            backend = self.vector_store._numpy_backend
            n = len(backend)
            if n == 0:
                return []
            sims = backend.vectors @ query_embedding
            topk = min(n_results, n)
            indices = np.argpartition(-sims, topk - 1)[:topk]
            sorted_idx = indices[np.argsort(-sims[indices])]
            return [
                {
                    "id": backend.ids[i],
                    "document": backend.documents[i],
                    "distance": float(1.0 - sims[i]),
                }
                for i in sorted_idx
            ]
        if self.chroma_collection is not None:
            try:
                raw = self.chroma_collection.query(
                    query_embeddings=[query_embedding.tolist()], n_results=n_results
                )
                results = []
                for i in range(len(raw.get("ids", [[]])[0])):
                    results.append({
                        "id": raw["ids"][0][i],
                        "document": raw["documents"][0][i] if raw.get("documents") else "",
                        "distance": raw["distances"][0][i] if raw.get("distances") else 0.0,
                    })
                return results
            except Exception as e:
                logger.warning("ChromaDB query_similar failed: %s", e)
                return []
        return []

    def close(self) -> None:
        """Close and release resources."""
        if self.vector_store and hasattr(self.vector_store, "client") and self.vector_store.client:
            try:
                self.vector_store.client = None
                logger.info("HAMVectorStoreManager: Vector store client dereferenced successfully.")
            except Exception as e:  # broad exception acceptable: cleanup should not crash the system
                logger.error(f"HAMVectorStoreManager: Error dereferencing vector store client: {e}", exc_info=True)
