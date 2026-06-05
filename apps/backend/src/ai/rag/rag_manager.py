#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

logger = logging.getLogger(__name__)

SentenceTransformer = None
SENTENCE_TRANSFORMERS_AVAILABLE = False
FAISS_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    faiss = None


class RAGManager:
    def __init__(self, model_name: str = None):
        self.model = None
        self.embedding_dim = 0
        self.index = None
        self.documents: dict[int, str] = {}
        self.next_doc_id = 0

        if model_name and SENTENCE_TRANSFORMERS_AVAILABLE:
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension() or 0
        elif model_name:
            logger.warning("sentence-transformers not available, RAGManager running without model")

        if self.embedding_dim > 0 and FAISS_AVAILABLE:
            self.index = faiss.IndexFlatL2(self.embedding_dim)

    def add_document(self, text: str) -> None:
        if not self.model:
            return
        embedding = self.model.encode([text])
        if FAISS_AVAILABLE and self.index is not None:
            faiss.normalize_L2(embedding)
            self.index.add(embedding)
        self.documents[self.next_doc_id] = text
        self.next_doc_id += 1

    def search(self, query: str, k: int = 5) -> list:
        if not self.model or not self.index or self.index.ntotal == 0:
            return []
        query_embedding = self.model.encode([query])
        if FAISS_AVAILABLE:
            faiss.normalize_L2(query_embedding)
        distances, indices = self.index.search(query_embedding, k)
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx in self.documents:
                score = 1.0 - distances[0][i]
                score = round(max(0.0, min(1.0, score)), 2)
                results.append((self.documents[idx], score))
        return results
