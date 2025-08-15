

import os

class VectorStoreError(Exception):
    """向量存儲錯誤"""
    pass

class VectorMemoryStore:
    """向量化記憶存儲"""
    
    def __init__(self, persist_directory="./chroma_db"):
        self.client = None
        self.collection = None
        try:
            import chromadb
            from chromadb.config import Settings
            import numpy as np # Import numpy here for the compatibility check
            _ = np.float_ # This line will raise AttributeError if numpy is 2.0+

            # Prefer in-memory client by default to avoid network dependency during tests
            use_http = os.environ.get("CHROMA_HTTP_CLIENT", "0") == "1"
            if use_http:
                try:
                    self.client = chromadb.HttpClient(
                        host=os.environ.get("CHROMA_HOST", "localhost"),
                        port=int(os.environ.get("CHROMA_PORT", "8000")),
                        settings=Settings(
                            anonymized_telemetry=False
                        )
                    )
                    print("VectorMemoryStore: Using HttpClient mode")
                except Exception as e:
                    print(f"VectorMemoryStore: HttpClient initialization failed: {e}. Falling back to EphemeralClient.")
                    self.client = chromadb.EphemeralClient(
                        settings=Settings(
                            anonymized_telemetry=False
                        )
                    )
            else:
                self.client = chromadb.EphemeralClient(
                    settings=Settings(
                        anonymized_telemetry=False
                    )
                )
                print("VectorMemoryStore: Using EphemeralClient (in-memory) mode")
            self.collection = self.client.get_or_create_collection(
                name="ham_memories",
                metadata={"hnsw:space": "cosine"}
            )
        except (AttributeError, ImportError) as e:
            # Handle both numpy 2.0 incompatibility and chromadb not found
            self.client = None
            self.collection = None
            print(f"VectorMemoryStore: Initialization failed due to dependency issue ({e}). Vector search will be disabled.")
        except Exception as e:
            self.client = None
            self.collection = None
            print(f"VectorMemoryStore: An unexpected error occurred during initialization ({e}). Vector search will be disabled.")
    
    async def add_memory(self, memory_id: str, content: str, metadata: dict):
        """添加記憶到向量存儲"""
        if not self.collection:
            raise VectorStoreError("Vector store is not initialized. Cannot add memory.")
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
        if not self.collection:
            raise VectorStoreError("Vector store is not initialized. Cannot perform semantic search.")
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
            return results
        except Exception as e:
            raise VectorStoreError(f"Semantic search failed: {e}")