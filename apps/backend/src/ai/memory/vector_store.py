"""
Vector Memory Store
Handles vector storage and retrieval using ChromaDB.
"""

import logging
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

class VectorMemoryStore:
    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initializes the VectorMemoryStore.
        
        Args:
            persist_directory (Optional[str]): Directory to persist the ChromaDB data.
        """
        try:
            if persist_directory:
                self.client = chromadb.PersistentClient(path=persist_directory)
            else:
                self.client = chromadb.Client()
            
            # Create or get the collection
            self.collection = self.client.get_or_create_collection(
                name="ham_memories",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("VectorMemoryStore initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize VectorMemoryStore: {e}")
            self.client = None
            self.collection = None

    async def add_memory(self, memory_id: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Adds a memory to the vector store.
        
        Args:
            memory_id (str): Unique identifier for the memory.:
ontent (str): Content of the memory.
            metadata (Optional[Dict[str, Any]]): Metadata associated with the memory.:
""
        if not self.collection:
            logger.warning("VectorMemoryStore not initialized. Cannot add memory.")
            return
            
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata] if metadata else [{}],:
ds=[memory_id]
            )
            logger.debug(f"Added memory {memory_id} to vector store.")
        except Exception as e:
            logger.error(f"Error adding memory {memory_id} to vector store: {e}")

    async def semantic_search(self, query: str, limit: int = 10):
        """
        Performs semantic search on the vector store.
        
        Args:
            query (str): Query string to search for.
            limit (int): Maximum number of results to return.
            
        Returns:
            Search results from ChromaDB.
        """
        if not self.collection:
            logger.warning("VectorMemoryStore not initialized. Cannot perform semantic search.")
            return {}
            
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            logger.debug(f"Semantic search returned {len(results.get('ids', []))} results.")
            return results
        except Exception as e:
            logger.error(f"Error performing semantic search: {e}")
            return {}