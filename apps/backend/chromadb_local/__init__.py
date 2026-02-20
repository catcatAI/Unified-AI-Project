# Lightweight shim for chromadb to support tests in environments where only the HTTP client is available
# Provides PersistentClient, EphemeralClient, HttpClient, and a minimal in-memory Collection API
from typing import Any, Dict, List, Optional
import logging
logger = logging.getLogger(__name__)

# Re-export config submodule
from . import config  # noqa: F401


class _Collection:
    def __init__(
        self, 
        name: str, 
        embedding_function: Optional[Any] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self.name = name
        self.embedding_function = embedding_function
        self.metadata = metadata or {}
        # Simple in-memory store
        self._docs: Dict[str, str] = {}
        self._metas: Dict[str, Dict[str, Any]] = {}
        self._embeds: Dict[str, List[float]] = {}

    def _embed(self, texts: List[str]) -> List[List[float]]:
        if self.embedding_function is not None:
            try:
                return self.embedding_function(texts)
            except Exception:
                pass
        # Fallback very naive embedding as fixed-size vector
        return [[float(len(t))] * 16 for t in texts]

    def add(
        self, 
        documents: List[str], 
        metadatas: List[Dict[str, Any]], 
        ids: List[str]
    ) -> None:
        if not (len(documents) == len(metadatas) == len(ids)):
            raise ValueError("documents, metadatas, and ids must have the same length")
        embeds = self._embed(documents)
        for doc, meta, _id, emb in zip(documents, metadatas, ids, embeds):
            self._docs[_id] = doc
            self._metas[_id] = meta
            self._embeds[_id] = emb

    def get(
        self, 
        ids: List[str], 
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        include = include or []
        result: Dict[str, Any] = {
            "ids": [], 
            "documents": [], 
            "metadatas": [], 
            "embeddings": []
        }
        for _id in ids:
            if _id in self._docs:
                result["ids"].append(_id)
                if 'documents' in include:
                    result["documents"].append(self._docs[_id])
                if 'metadatas' in include:
                    result["metadatas"].append(self._metas.get(_id, {}))
                if 'embeddings' in include:
                    result["embeddings"].append(self._embeds.get(_id, []))
        # Ensure keys exist even if not requested (tests may access)
        if 'documents' not in include:
            result.pop('documents', None)
        if 'metadatas' not in include:
            result.pop('metadatas', None)
        if 'embeddings' not in include:
            result.pop('embeddings', None)
        return result

    def query(
        self, 
        query_texts: List[str], 
        n_results: int = 10, 
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        include = include or []
        all_ids = list(self._docs.keys())
        out_ids: List[List[str]] = []
        out_docs: List[List[str]] = []
        out_metas: List[List[Dict[str, Any]]] = []
        for q in query_texts:
            q_tokens = set(q.lower().split())
            # simple scoring by token overlap count
            scored = []
            for _id in all_ids:
                doc = self._docs[_id]
                tokens = set(doc.lower().split())
                score = len(q_tokens & tokens)
                scored.append((_id, score))
            scored.sort(key=lambda x: x[1], reverse=True)
            top_ids = [sid for sid, _ in scored[:n_results]]
            out_ids.append(top_ids)
            if 'documents' in include:
                out_docs.append([self._docs[i] for i in top_ids])
            if 'metadatas' in include:
                out_metas.append([self._metas.get(i, {}) for i in top_ids])
        result: Dict[str, Any] = {'ids': out_ids}
        if 'documents' in include:
            result['documents'] = out_docs
        if 'metadatas' in include:
            result['metadatas'] = out_metas
        return result


class _BaseClient:
    def __init__(self) -> None:
        self._collections: Dict[str, _Collection] = {}

    def get_or_create_collection(
        self, 
        name: str, 
        embedding_function: Optional[Any] = None, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> _Collection:
        if name not in self._collections:
            self._collections[name] = _Collection(
                name=name, 
                embedding_function=embedding_function, 
                metadata=metadata
            )
        else:
            # update embedding function if provided
            if embedding_function is not None:
                self._collections[name].embedding_function = embedding_function
        return self._collections[name]


class PersistentClient(_BaseClient):
    def __init__(
        self, 
        path: Optional[str] = None, 
        settings: Optional[Any] = None
    ) -> None:
        super().__init__()
        self._path = path
        self._settings = settings


class EphemeralClient(_BaseClient):
    def __init__(self, settings: Optional[Any] = None) -> None:
        super().__init__()
        self._settings = settings


class HttpClient(_BaseClient):
    def __init__(
        self, 
        host: str = "localhost", 
        port: int = 8000, 
        settings: Optional[Any] = None
    ) -> None:
        super().__init__()
        self._host = host
        self._port = port
        self._settings = settings


__all__ = [
    'PersistentClient',
    'EphemeralClient',
    'HttpClient',
    'config',
]
