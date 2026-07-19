"""MultimodalRetriever — vector-based cross-modal retrieval for ED3N integration.

P21: Indexes 64-dim latent vectors from any modality and enables
cross-modal similarity search. Integrates with ED3N DictionaryLayer
via the modality_encoders hook.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class MultimodalRetriever:
    """Vector index for cross-modal retrieval using brute-force cosine similarity.

    Stores (key, latent_vector, modality, metadata) triples and searches
    by cosine similarity on the 64-dim latent space.

    Supports persistence via numpy + JSON (no external deps).
    """

    LATENT_DIM: int = 64

    def __init__(self):
        self._keys: List[str] = []
        self._vectors: List[np.ndarray] = []
        self._modalities: List[str] = []
        self._metadata: List[Dict[str, Any]] = []

    def add(
        self,
        key: str,
        latent: np.ndarray,
        modality: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Index a latent vector with a dictionary key."""
        if len(latent) != self.LATENT_DIM:
            logger.warning("Expected latent dim %d, got %d", self.LATENT_DIM, len(latent))
            return
        self._keys.append(key)
        self._vectors.append(latent.copy().astype(np.float32))
        self._modalities.append(modality)
        self._metadata.append(metadata or {})

    def add_from_bridge(
        self,
        key: str,
        latent_list: List[float],
        modality: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add from MultimodalBridge-style List[float] latent."""
        arr = np.array(latent_list, dtype=np.float32)
        self.add(key, arr, modality, metadata)

    def search(self, query_latent: np.ndarray, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search index by cosine similarity. Returns top-k results.

        Each result: {'key': str, 'score': float, 'modality': str, 'metadata': dict}
        """
        if len(self._vectors) == 0:
            return []
        if len(query_latent) != self.LATENT_DIM:
            logger.warning(
                "Query latent dim mismatch: %d != %d", len(query_latent), self.LATENT_DIM
            )
            return []

        q = query_latent.astype(np.float32)
        q_norm = q / max(np.linalg.norm(q), 1e-8)

        stack = np.stack(self._vectors, axis=0)
        norms = np.linalg.norm(stack, axis=1)
        stack_norm = stack / np.maximum(norms[:, None], 1e-8)
        scores = stack_norm @ q_norm

        top_indices = np.argsort(scores)[-top_k:][::-1]
        results = []
        for idx in top_indices:
            results.append(
                {
                    "key": self._keys[idx],
                    "score": float(scores[idx]),
                    "modality": self._modalities[idx],
                    "metadata": self._metadata[idx],
                }
            )
        return results

    def search_by_modality(
        self, query_latent: np.ndarray, target_modality: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search, filtering results to a specific target modality."""
        all_results = self.search(query_latent, top_k=len(self._vectors))
        filtered = [r for r in all_results if r["modality"] == target_modality]
        return filtered[:top_k]

    def search_by_list(self, query_list: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search from a List[float] query latent (e.g. from MultimodalBridge)."""
        q = np.array(query_list, dtype=np.float32)
        return self.search(q, top_k)

    def count(self) -> int:
        return len(self._keys)

    def get_key(self, idx: int) -> Optional[str]:
        return self._keys[idx] if 0 <= idx < len(self._keys) else None

    def get_vector(self, idx: int) -> Optional[np.ndarray]:
        return self._vectors[idx].copy() if 0 <= idx < len(self._vectors) else None

    def clear(self) -> None:
        self._keys.clear()
        self._vectors.clear()
        self._modalities.clear()
        self._metadata.clear()

    def save(self, filepath: str) -> None:
        """Save index to disk (npy + JSON)."""
        if not filepath.endswith(".npy"):
            filepath += ".npy"
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        if self._vectors:
            stack = np.stack(self._vectors, axis=0)
            np.save(filepath, stack)
        else:
            np.save(filepath, np.zeros((0, self.LATENT_DIM), dtype=np.float32))
        meta_path = filepath.replace(".npy", ".json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "keys": self._keys,
                    "modalities": self._modalities,
                    "metadata": self._metadata,
                },
                f,
                ensure_ascii=False,
            )

    def load(self, filepath: str) -> int:
        """Load index from disk (npy + JSON). Returns entry count."""
        if not filepath.endswith(".npy"):
            filepath += ".npy"
        meta_path = filepath.replace(".npy", ".json")
        if not os.path.exists(filepath) or not os.path.exists(meta_path):
            return 0
        vectors = np.load(filepath, allow_pickle=False)
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        self._keys = meta["keys"]
        self._modalities = meta.get("modalities", [""] * len(self._keys))
        self._metadata = meta.get("metadata", [{}] * len(self._keys))
        self._vectors = [vectors[i] for i in range(len(self._keys))]
        return len(self._keys)
