import numpy as np
import logging
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)

class RAGManager:
    """
    Manages Retrieval-Augmented Generation by handling vector embeddings and similarity search.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.documents: Dict[int, str] = {}
        self.next_doc_id = 0
        self.faiss_available = False
        
        # 嘗試初始化Faiss索引，如果失敗則使用備用方案
        self._initialize_index()
    
    def _initialize_index(self):
        """初始化Faiss索引，如果失敗則使用備用的簡單向量存儲"""
        try:
            import faiss
            self.index = faiss.IndexFlatL2(self.embedding_dim)
            self.faiss_available = True
            logger.info("✅ Faiss索引初始化成功")
        except Exception as e:
            logger.warning(f"⚠️ Faiss初始化失敗，使用備用向量存儲: {e}")
            self.faiss_available = False
            # 使用簡單的列表作為備用存儲
            self.vectors = []
            self.index = None

    def add_document(self, text: str, doc_id: str = None):
        """Adds a document to the RAG manager and generates its vector embedding."""
        vector = self.model.encode([text])
        
        # Use provided doc_id or generate a new one
        if doc_id is None:
            doc_id = str(self.next_doc_id)
            self.next_doc_id += 1
        
        if self.faiss_available:
            # 使用Faiss索引
            import faiss
            faiss.normalize_L2(vector)
            self.index.add(vector)
            # Store the document content against the index position
            self.documents[self.index.ntotal - 1] = text
        else:
            # 使用備用向量存儲
            # 正規化向量
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
            
            # 存儲向量和文檔
            doc_index = len(self.vectors)
            self.vectors.append(vector[0])  # vector是2D數組，取第一個元素
            self.documents[doc_index] = text


    def search(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """Searches for the most similar documents to a given query."""
        if not self.documents:
            return []
        
        query_vector = self.model.encode([query])
        
        if self.faiss_available:
            # 使用Faiss搜索
            if self.index.ntotal == 0:
                return []
            
            import faiss
            faiss.normalize_L2(query_vector)
            distances, indices = self.index.search(query_vector, k)
            
            results = []
            for i in range(len(indices[0])):
                idx = indices[0][i]
                if idx != -1:
                    dist = distances[0][i]
                    doc = self.documents.get(idx, "Document not found")
                    results.append((doc, 1.0 - dist))  # Convert distance to similarity score
            return results
        else:
            # 使用備用向量搜索
            if not self.vectors:
                return []
            
            # 正規化查詢向量
            norm = np.linalg.norm(query_vector)
            if norm > 0:
                query_vector = query_vector / norm
            
            # 計算餘弦相似度
            similarities = []
            for i, doc_vector in enumerate(self.vectors):
                similarity = np.dot(query_vector[0], doc_vector)
                similarities.append((i, similarity))
            
            # 排序並返回前k個結果
            similarities.sort(key=lambda x: x[1], reverse=True)
            results = []
            for i, (doc_idx, similarity) in enumerate(similarities[:k]):
                doc = self.documents.get(doc_idx, "Document not found")
                results.append((doc, similarity))
            
            return results