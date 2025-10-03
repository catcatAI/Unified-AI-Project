#!/usr/bin/env python3
# -*- coding utf-8 -*-

# 使用我们的兼容性模块
try:
    from apps.backend.src.compat.transformers_compat import import_sentence_transformers
    SentenceTransformer, SENTENCE_TRANSFORMERS_AVAILABLE = import_sentence_transformers
    if not SENTENCE_TRANSFORMERS_AVAILABLE:

    print("Warning: Could not import sentence_transformers")
except ImportError as e:
    print(f"Warning: Could not import transformers_compat: {e}")
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

import faiss
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict

class RAGManager:
    """
    Manages Retrieval-Augmented Generation by handling vector embeddings and similarity search.
    """
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2') -> None:
    self.model = SentenceTransformer(model_name)
    self.embedding_dim = self.model.get_sentence_embedding_dimension
    self.index = faiss.IndexFlatL2(self.embedding_dim)
    self.documents: Dict[int, str] =
    self.next_doc_id = 0

    def add_document(self, text: str, doc_id: str = None)
    """Adds a document to the RAG manager and generates its vector embedding."""
    vector = self.model.encode([text])
    faiss.normalize_L2(vector)
    self.index.add(vector)

    # Use provided doc_id or generate a new one
        if doc_id is None:

    doc_id = str(self.next_doc_id)
            self.next_doc_id += 1

    # Store the document content against the index position
    # The index position is self.index.ntotal - 1 after adding
    self.documents[self.index.ntotal - 1] = text


    def search(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """Searches for the most similar documents to a given query.""":
    if self.index.ntotal == 0:

    return

    query_vector = self.model.encode([query])
    faiss.normalize_L2(query_vector)
    distances, indices = self.index.search(query_vector, k)

    results =
        for i in range(len(indices[0])):

    idx = indices[0][i]
            if idx != -1:

    dist = distances[0][i]
                doc = self.documents.get(idx, "Document not found")
                results.append((doc, 1.0 - dist)) # Convert distance to similarity score
    return results