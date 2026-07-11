"""Concept Mapper — maps CLIP text embeddings to geometric vocabulary.

Phase 7: Maps text → concept → primitive type distribution.

This is where CLIP semantic similarity belongs:
- "cat" → CLIP encode → find closest concept → get primitive distribution
- NOT: CLIP → evaluate rendered output

Now integrated with concept space mapping for shared representation.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

from .geometric_vocabulary import ConceptDistribution, GeometricVocabulary
from .primitive_types import TOTAL_DIM


class ConceptMapper:
    """Maps CLIP text embeddings to geometric vocabulary concepts.

    Architecture:
        CLIP text encode → Concept Space → find closest concept → return primitive distribution

    Uses concept space for shared representation:
    - Same concept (cat) → same region in concept space
    - Concept space captures "what geometric primitives compose a cat"
    """

    def __init__(self, vocabulary: GeometricVocabulary):
        self._vocabulary = vocabulary
        self._concept_clip_embeddings: Dict[str, np.ndarray] = {}
        self._clip_dim = 512
        self._concept_space = None  # Optional ConceptSpaceMapper

    def set_concept_space(self, concept_space):
        """Set the concept space mapping for shared representation."""
        self._concept_space = concept_space

    def register_concept_embedding(self, concept_name: str, clip_embedding: np.ndarray):
        """Register a CLIP embedding for a concept.

        This is typically done by encoding the concept name with CLIP:
            "cat" → CLIP encode → 512-dim vector
        """
        self._concept_clip_embeddings[concept_name] = clip_embedding.astype(np.float32)

    def register_concepts_from_clip(self, clip_encoder, class_names: Optional[List[str]] = None):
        """Register CLIP embeddings for all concepts using a CLIP encoder.

        Args:
            clip_encoder: SemanticVisualEncoder instance with encode_text() method
            class_names: list of class names to encode (default: CIFAR-10 classes)
        """
        if class_names is None:
            from .geometric_vocabulary import GeometricVocabulary
            class_names = GeometricVocabulary.CLASSES

        # Encode all class names at once
        text_vecs = clip_encoder.encode_text(class_names)
        if text_vecs is not None:
            for i, name in enumerate(class_names):
                self._concept_clip_embeddings[name] = text_vecs[i]
            logger.info("Registered %d concept embeddings from CLIP", len(class_names))
        else:
            logger.warning("CLIP text encoding unavailable, using random embeddings")
            rng = np.random.default_rng(42)
            for name in class_names:
                self._concept_clip_embeddings[name] = rng.random(512).astype(np.float32)

    def map_text_to_concept(self, clip_embedding: np.ndarray,
                             top_k: int = 3) -> List[Tuple[str, float]]:
        """Map CLIP text embedding to closest concept(s).

        If concept space is available, use it for mapping.
        Otherwise, fall back to direct CLIP embedding comparison.

        Args:
            clip_embedding: (512,) CLIP text embedding
            top_k: number of top concepts to return

        Returns:
            List of (concept_name, similarity) sorted by similarity
        """
        if not self._concept_clip_embeddings:
            return []

        concepts = list(self._concept_clip_embeddings.keys())
        embeddings = np.array([self._concept_clip_embeddings[c] for c in concepts])

        # Use concept space if available
        if self._concept_space is not None and self._concept_space._is_trained:
            # Map text embeddings to concept space
            concept_space_vecs = self._concept_space.encode(embeddings)
            text_concept_vec = self._concept_space.encode(clip_embedding.reshape(1, -1))

            # Compare in concept space
            sims = concept_space_vecs @ text_concept_vec.T
            sims = sims.flatten()
        else:
            # Fall back to direct CLIP embedding comparison
            clip_norm = clip_embedding / (np.linalg.norm(clip_embedding) + 1e-8)
            emb_norms = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)
            sims = emb_norms @ clip_norm

        # Top-k
        top_indices = np.argsort(sims)[::-1][:top_k]
        return [(concepts[i], float(sims[i])) for i in top_indices]

    def map_text_to_primitives(self, clip_embedding: np.ndarray) -> Dict:
        """Map CLIP text embedding to primitive type distribution.

        Returns:
            {
                "concept": str,
                "similarity": float,
                "param_means": (263,) array,
                "param_stds": (263,) array,
                "visual_word_ids": list of int,
                "initialization": (263,) array for optimization,
            }
        """
        matches = self.map_text_to_concept(clip_embedding, top_k=1)
        if not matches:
            return self._default_mapping()

        concept_name, sim = matches[0]
        concept = self._vocabulary.get_concept(concept_name)
        if concept is None:
            return self._default_mapping()

        # Initialize parameters from concept distribution
        init_vec = self._vocabulary.initialize_from_concept(concept_name)

        return {
            "concept": concept_name,
            "similarity": sim,
            "param_means": concept.param_means,
            "param_stds": concept.param_stds,
            "visual_word_ids": concept.visual_word_ids,
            "initialization": init_vec,
        }

    def _default_mapping(self) -> Dict:
        """Default mapping when no concept matches."""
        rng = np.random.default_rng()
        return {
            "concept": "unknown",
            "similarity": 0.0,
            "param_means": np.full(TOTAL_DIM, 0.5, dtype=np.float32),
            "param_stds": np.ones(TOTAL_DIM, dtype=np.float32),
            "visual_word_ids": [],
            "initialization": rng.uniform(0.2, 0.8, TOTAL_DIM).astype(np.float32),
        }

    def save(self, path: str):
        """Save concept mapper state."""
        data = {
            "clip_dim": self._clip_dim,
            "concept_embeddings": {
                k: v.tolist() for k, v in self._concept_clip_embeddings.items()
            },
        }
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)

    @classmethod
    def load(cls, vocabulary: GeometricVocabulary, path: str) -> "ConceptMapper":
        """Load concept mapper state."""
        with open(path) as f:
            data = json.load(f)

        mapper = cls(vocabulary)
        mapper._clip_dim = data["clip_dim"]
        for k, v in data["concept_embeddings"].items():
            mapper._concept_clip_embeddings[k] = np.array(v, dtype=np.float32)

        return mapper
