"""Shared latent space — projects modality-specific vectors to a unified embedding space."""

import logging
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class SharedLatentSpace:
    """Projects feature vectors from any modality into a shared N-dim latent space.

    Each modality has its own linear projection:
        latent = W_m @ feature + b_m

    Similarity between modalities is computed as cosine similarity in latent space.
    """

    LATENT_DIM: int = 64

    def __init__(self, latent_dim: Optional[int] = None):
        self._latent_dim = latent_dim or self.LATENT_DIM
        self._projections: Dict[str, Dict[str, np.ndarray]] = {}
        self._embedding_cache: Dict[str, np.ndarray] = {}

    def register_modality(self, name: str, input_dim: int) -> None:
        """Register a modality with its expected input dimension."""
        rng = np.random.default_rng(hash(name) % (2 ** 31))
        self._projections[name] = {
            "W": rng.normal(0, 1 / np.sqrt(input_dim),
                           (self._latent_dim, input_dim)).astype(np.float32),
            "b": np.zeros(self._latent_dim, dtype=np.float32),
        }
        logger.info("Registered modality '%s' (input %d → latent %d)",
                    name, input_dim, self._latent_dim)

    def project(self, modality: str, features: np.ndarray) -> np.ndarray:
        """Project a modality-specific feature vector into latent space."""
        proj = self._projections.get(modality)
        if proj is None:
            logger.warning("Unknown modality '%s', returning zeros", modality)
            return np.zeros(self._latent_dim, dtype=np.float32)
        latent = proj["W"] @ features + proj["b"]
        norm = np.linalg.norm(latent)
        if norm > 0:
            latent = latent / norm
        self._embedding_cache[modality] = latent
        return latent

    def similarity(self, mod_a: str, mod_b: str) -> float:
        """Cosine similarity between two modalities in latent space."""
        emb_a = self._embedding_cache.get(mod_a)
        emb_b = self._embedding_cache.get(mod_b)
        if emb_a is None or emb_b is None:
            return 0.0
        dot = float(np.dot(emb_a, emb_b))
        return max(0.0, min(1.0, (dot + 1.0) / 2.0))

    def get_embedding(self, modality: str) -> Optional[np.ndarray]:
        """Return the current latent embedding for a modality, if set."""
        return self._embedding_cache.get(modality)

    def registered_modalities(self) -> List[str]:
        return list(self._projections.keys())

    def reset(self) -> None:
        self._embedding_cache.clear()
