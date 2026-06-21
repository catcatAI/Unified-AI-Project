"""
SemanticKeyMapper — bridges semantic latent vectors to ED3N concept keys (P44).

The core insight for P44 is that ED3N's CoreNetwork and GARDEN's SNN only
accept **text keys** (concept names). The semantic latents from P42-P43
live in SharedLatentSpace but have no path into ED3N's forward/process
pipeline.

SemanticKeyMapper solves this by maintaining an index of
``(key → structural_latent, semantic_latent)`` pairs and providing
``map_latent_to_keys(latent, modality, top_k)`` — a cosine-similarity
search that finds the closest concept keys to a given latent vector.

This enables the full lower-bound chain::

    image → DualEncoderRouter → semantic_latent
        → SemanticKeyMapper → closest concept keys
            → ED3NEngine.process(keys) → "I see a chicken!"
"""

import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class SemanticKeyMapper:
    """Maps semantic latent vectors to ED3N concept keys via cosine similarity.

    Maintains a growing index of registered concept keys paired with their
    structural and semantic latent projections.  When a new latent is
    presented, the mapper finds the *k* most similar registered keys.

    This is the final bridge between the DualEncoderRouter's semantic
    latents and ED3N's text-key-based CoreNetwork / SNN.
    """

    def __init__(self, max_entries: int = 10000):
        self._max_entries = max_entries
        # Index structures: parallel lists
        self._keys: List[str] = []
        self._structural_latents: List[np.ndarray] = []  # 64-dim each
        self._semantic_latents: List[np.ndarray] = []    # 64-dim each
        self._combined_latents: List[np.ndarray] = []    # 64-dim each

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------

    def index_key(self, key: str,
                  structural_latent: Optional[np.ndarray] = None,
                  semantic_latent: Optional[np.ndarray] = None,
                  combined_latent: Optional[np.ndarray] = None) -> None:
        """Register a concept key with its latent projections.

        At least one of *structural_latent* or *semantic_latent* must be
        provided.  If *combined_latent* is not given, it defaults to the
        semantic (or structural) latent.
        """
        if structural_latent is None and semantic_latent is None:
            logger.warning("SemanticKeyMapper.index_key: no latents provided for '%s'", key)
            return

        if len(self._keys) >= self._max_entries:
            logger.warning("SemanticKeyMapper at max capacity (%d), dropping oldest", self._max_entries)
            self._keys.pop(0)
            self._structural_latents.pop(0)
            self._semantic_latents.pop(0)
            self._combined_latents.pop(0)

        flat_struct = structural_latent.flatten().astype(np.float32) if structural_latent is not None else np.zeros(64, dtype=np.float32)
        flat_sem = semantic_latent.flatten().astype(np.float32) if semantic_latent is not None else np.zeros(64, dtype=np.float32)
        if combined_latent is None:
            combined = flat_sem if semantic_latent is not None else flat_struct
        else:
            combined = combined_latent.flatten().astype(np.float32)

        # Avoid duplicates
        if key in self._keys:
            idx = self._keys.index(key)
            self._structural_latents[idx] = flat_struct
            self._semantic_latents[idx] = flat_sem
            self._combined_latents[idx] = combined
        else:
            self._keys.append(key)
            self._structural_latents.append(flat_struct)
            self._semantic_latents.append(flat_sem)
            self._combined_latents.append(combined)

    def index_from_router_result(self, key: str,
                                 router_result: Dict[str, Any]) -> None:
        """Register a key using the result dict from DualEncoderRouter.

        Extracts ``structural_latent``, ``semantic_latent``, and ``latent``
        from the router result.
        """
        self.index_key(
            key=key,
            structural_latent=router_result.get("structural_latent"),
            semantic_latent=router_result.get("semantic_latent"),
            combined_latent=router_result.get("latent"),
        )

    def index_batch(self, keys_and_latents: List[Tuple[str, Optional[np.ndarray],
                                                         Optional[np.ndarray],
                                                         Optional[np.ndarray]]]) -> int:
        """Bulk-index multiple entries.

        Each tuple is ``(key, structural_latent, semantic_latent, combined_latent)``.
        Returns the number of entries indexed.
        """
        count = 0
        for key, s_lat, sem_lat, c_lat in keys_and_latents:
            self.index_key(key, s_lat, sem_lat, c_lat)
            count += 1
        return count

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def map_latent_to_keys(self,
                           query_latent: np.ndarray,
                           top_k: int = 5,
                           mode: str = "auto") -> List[Dict[str, Any]]:
        """Find the *top_k* closest registered keys to *query_latent*.

        Args:
            query_latent: 64-dim SharedLatentSpace vector.
            top_k: Number of results to return.
            mode: Which latent pool to compare against:
                  - "auto" (default): uses ``_combined_latents`` if
                    any entry has one, otherwise falls back to
                    ``_semantic_latents`` then ``_structural_latents``.
                  - "combined": always use ``_combined_latents``.
                  - "semantic": use ``_semantic_latents``.
                  - "structural": use ``_structural_latents``.

        Returns:
            List of ``{key, score}`` dicts, sorted by descending cosine
            similarity.  Empty list when the index is empty.
        """
        if not self._keys:
            return []

        query = query_latent.flatten().astype(np.float32)
        q_norm = np.linalg.norm(query)
        if q_norm > 0:
            query = query / q_norm

        # Determine which pool to query
        if mode == "auto":
            if any(c is not None for c in self._combined_latents):
                pool = self._combined_latents
            elif any(c is not None for c in self._semantic_latents):
                pool = self._semantic_latents
            else:
                pool = self._structural_latents
        elif mode == "combined":
            pool = self._combined_latents
        elif mode == "semantic":
            pool = self._semantic_latents
        elif mode == "structural":
            pool = self._structural_latents
        else:
            pool = self._combined_latents

        pool_np = np.array(pool, dtype=np.float32)  # [V, 64]
        norms = np.linalg.norm(pool_np, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        pool_np = pool_np / norms

        scores = pool_np @ query  # [V] cosine similarities

        top_indices = np.argsort(scores)[-top_k:][::-1]
        results = []
        for idx in top_indices:
            results.append({
                "key": self._keys[idx],
                "score": round(float(scores[idx]), 4),
            })
        return results

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def count(self) -> int:
        return len(self._keys)

    @property
    def keys(self) -> List[str]:
        return list(self._keys)

    def clear(self) -> None:
        self._keys.clear()
        self._structural_latents.clear()
        self._semantic_latents.clear()
        self._combined_latents.clear()
