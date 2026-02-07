#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import List, Tuple, Dict, Optional, Any

# Attempt to import sentence-transformers and faiss
try:
    from src.compat.transformers_compat import import_sentence_transformers
    SentenceTransformer, SENTENCE_TRANSFORMERS_AVAILABLE = import_sentence_transformers()
except ImportError as e:
    logging.error(f"Could not import transformers_compat: {e}")
    SentenceTransformer = None
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    logging.error("faiss module not found. Vector search will be unavailable.")
    FAISS_AVAILABLE = False

logger = logging.getLogger(__name__)

class RAGManager:
    """
    Manages Retrieval-Augmented Generation by handling vector embeddings and 
    similarity search.
    """

    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model = None
        self.embedding_dim = 0
        self.index = None
        self.documents: Dict[int, str] = {}
        self.next_doc_id = 0
        
        if SENTENCE_TRANSFORMERS_AVAILABLE and SentenceTransformer:
            try:
                self.model = SentenceTransformer(model_name)
                self.embedding_dim = self.model.get_sentence_embedding_dimension()
                if FAISS_AVAILABLE:
                    self.index = faiss.IndexFlatL2(self.embedding_dim)
            except Exception as e:
                logger.error(f"Error initializing RAG model or index: {e}")
        else:
            logger.warning("RAGManager initialized without a functional embedding model.")

    def add_document(self, text: str, doc_id: Optional[str] = None):
        """Adds a document to the RAG manager and generates its vector embedding."""
        if not self.model or not self.index:
            logger.error("RAGManager: Model or Index not available.")
            return

        try:
            vector = self.model.encode([text])
            if FAISS_AVAILABLE:
                faiss.normalize_L2(vector)
                self.index.add(vector)

            # Use provided doc_id or generate a new one
            current_pos = self.index.ntotal - 1
            self.documents[current_pos] = text
            logger.info(f"RAGManager: Document added at position {current_pos}.")
        except Exception as e:
            logger.error(f"Error adding document to RAG: {e}")

    def search(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """Searches for the most similar documents to a given query."""
        if not self.model or not self.index or self.index.ntotal == 0:
            return []

        try:
            query_vector = self.model.encode([query])
            if FAISS_AVAILABLE:
                faiss.normalize_L2(query_vector)
                distances, indices = self.index.search(query_vector, k)

                results = []
                for i in range(len(indices[0])):
                    idx = indices[0][i]
                    if idx != -1:
                        dist = distances[0][i]
                        doc = self.documents.get(idx, "Document not found")
                        # L2 distance normalized similarity
                        results.append((doc, float(1.0 - dist)))
                return results
        except Exception as e:
            logger.error(f"Error during RAG search: {e}")
            return []
        
        return []
