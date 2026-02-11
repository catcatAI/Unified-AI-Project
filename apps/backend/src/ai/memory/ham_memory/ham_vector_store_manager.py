import logging
import os
from typing import Any, Dict, Optional

from ai.memory.vector_store import VectorMemoryStore # Assuming vector_store is one level up

logger = logging.getLogger(__name__)

class HAMVectorStoreManager:
    def __init__(self, storage_dir: str, chroma_client: Optional[Any] = None):
        self.vector_store: Optional[VectorMemoryStore] = None
        self.chroma_collection: Optional[Any] = None

        if chroma_client is not None:
            try:
                self.chroma_collection = chroma_client.get_or_create_collection(
                    name="ham_memories",
                    metadata={"hnsw:space": "cosine"}
                )
                logger.info("ChromaDB collection initialized from external chroma_client.")
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB collection from external client: {e}")
                self.chroma_collection = None
        else:
            if os.environ.get("HAM_DISABLE_VECTOR_STORE", "0") == "1":
                logger.info("HAM: VectorMemoryStore disabled via HAM_DISABLE_VECTOR_STORE = 1")
            else:
                try:
                    self.vector_store = VectorMemoryStore(persist_directory=os.path.join(storage_dir, "chroma_db"))
                    logger.info("VectorMemoryStore initialized successfully.")

                    if self.vector_store and hasattr(self.vector_store, 'client') and self.vector_store.client:
                        try:
                            self.chroma_collection = self.vector_store.client.get_or_create_collection(
                                name="ham_memories",
                                metadata={"hnsw:space": "cosine"}
                            )
                            logger.info("ChromaDB collection initialized successfully via VectorMemoryStore.")
                        except Exception as e:
                            logger.error(f"Failed to initialize ChromaDB collection via VectorMemoryStore: {e}")
                            self.chroma_collection = None
                    else:
                        logger.warning("VectorMemoryStore client not available for direct ChromaDB collection access.")
                except Exception as e:
                    logger.warning(f"VectorMemoryStore initialization failed (likely due to chromadb / numpy issue): {e}. Vector search will be disabled.")
                    self.vector_store = None
                    self.chroma_collection = None

    async def add_semantic_vector(self, memory_id: str, content: str, metadata: Dict[str, Any]):
        try:
            if self.chroma_collection is not None:
                self.chroma_collection.add(
                    documents=[content],
                    metadatas=[metadata],
                    ids=[memory_id]
                )
                logger.debug(f"HAM: Stored semantic vector for {memory_id} in injected Chroma collection.")
            elif self.vector_store is not None:
                await self.vector_store.add_memory(
                    memory_id=memory_id,
                    content=content,
                    metadata=metadata
                )
                logger.debug(f"HAM: Stored semantic vector for {memory_id} in VectorMemoryStore.")
            else:
                logger.debug(f"HAM: Vector / Chroma store disabled, skipping semantic vector storage for {memory_id}.")
        except Exception as e:
            logger.error(f"Error storing semantic vector for {memory_id}: {e}")

    def close(self):
        if self.vector_store and hasattr(self.vector_store, 'client') and self.vector_store.client:
            try:
                self.vector_store.client = None
                logger.info("HAMVectorStoreManager: Vector store client dereferenced successfully.")
            except Exception as e:
                logger.error(f"HAMVectorStoreManager: Error dereferencing vector store client: {e}")
