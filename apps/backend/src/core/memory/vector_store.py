import chromadb
from chromadb.config import Settings
from typing import Dict, Any, List

class VectorStoreError(Exception):
    """Custom exception for VectorMemoryStore errors."""
    pass

class VectorMemoryStore:
    """向量化記憶存儲"""
    
    def __init__(self, persist_directory="./chroma_db"):
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="ham_memories",
            metadata={"hnsw:space": "cosine"}
        )
    
    async def add_memory(self, memory_id: str, content: str, metadata: Dict[str, Any]):
        """添加記憶到向量存儲"""
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[memory_id]
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to add memory: {e}")
    
    async def semantic_search(self, query: str, n_results: int = 10) -> List[Dict[str, Any]]:
        """語義搜索"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                include=['documents', 'metadatas', 'distances']
            )
            # Format results for consistency
            formatted_results = []
            if results and results['ids']:
                for i in range(len(results['ids'][0])):
                    formatted_results.append({
                        'id': results['ids'][0][i],
                        'document': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i]
                    })
            return formatted_results
        except Exception as e:
            raise VectorStoreError(f"Semantic search failed: {e}")
