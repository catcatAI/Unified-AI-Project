import chromadb
from chromadb.config import Settings

class VectorStoreError(Exception):
    """向量存儲錯誤"""
    pass

class VectorMemoryStore:
    """向量化記憶存儲"""
    
    def __init__(self, persist_directory="./chroma_db"):
        # Use HttpClient to work with HTTP-only mode
        try:
            # 嘗試使用 HttpClient
            from chromadb.config import Settings
            self.client = chromadb.HttpClient(
                host="localhost",
                port=8000,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            print("VectorMemoryStore: Using HttpClient mode")
        except Exception as e:
            print(f"VectorMemoryStore: HttpClient initialization failed: {e}. Falling back to EphemeralClient.")
            # 如果 HttpClient 失敗，回退到 EphemeralClient
            self.client = chromadb.EphemeralClient(
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
        self.collection = self.client.get_or_create_collection(
            name="ham_memories",
            metadata={"hnsw:space": "cosine"}
        )
    
    async def add_memory(self, memory_id: str, content: str, metadata: dict):
        """添加記憶到向量存儲"""
        try:
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[memory_id]
            )
        except Exception as e:
            raise VectorStoreError(f"Failed to add memory: {e}")
    
    async def semantic_search(self, query: str, n_results: int = 10):
        """語義搜索"""
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            raise VectorStoreError(f"Semantic search failed: {e}")