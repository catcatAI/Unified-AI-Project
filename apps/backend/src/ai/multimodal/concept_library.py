"""
Concept Library — pre-indexed visual concepts for CLIP-based classification.

Builds a library of animal/object concepts by encoding CLIP text embeddings
and mapping them to ED3N dictionary keys. Enables zero-shot image classification
against a curated set of concepts.
"""

import logging
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ConceptLibrary:
    """Pre-indexed library of visual concepts for CLIP-based classification.

    Stores CLIP text embeddings for common objects, enabling:
    1. Zero-shot classification via text embedding similarity
    2. SemanticKeyMapper raw mode integration
    3. ED3N dictionary key mapping

    Built at startup or on first use.
    """

    def __init__(self,
                 semantic_encoder=None,
                 dictionary=None,
                 key_mapper=None):
        self._encoder = semantic_encoder
        self._dictionary = dictionary
        self._mapper = key_mapper
        self._concepts: Dict[str, Dict[str, Any]] = {}
        self._all_labels: List[str] = []
        self._all_label_vecs: Optional[np.ndarray] = None
        self._built = False

    def build(self, concept_specs: Optional[List[Dict]] = None) -> int:
        """Build the concept library.

        Args:
            concept_specs: Optional custom concept list.
                          If None, uses built-in animal concepts.

        Returns: Number of concepts indexed.
        """
        if concept_specs is None:
            concept_specs = self._default_concepts()

        if self._encoder is None or not self._encoder.is_available:
            logger.warning("ConceptLibrary: CLIP unavailable, cannot build")
            return 0

        all_labels = []
        for spec in concept_specs:
            for label in spec.get("labels", []):
                all_labels.append(label)

        if not all_labels:
            return 0

        text_vecs = self._encoder.encode_text(all_labels)
        if text_vecs is None:
            return 0

        self._all_labels = all_labels
        self._all_label_vecs = text_vecs

        count = 0
        label_idx = 0
        for spec in concept_specs:
            concept_name = spec["name"]
            dict_key = spec.get("dict_key", "")
            labels = spec.get("labels", [])
            primary_vec = text_vecs[label_idx]
            label_idx += len(labels)

            self._concepts[concept_name] = {
                "dict_key": dict_key,
                "labels": labels,
                "text_embedding": primary_vec,
                "action": spec.get("action", ""),
            }

            if self._mapper is not None:
                self._mapper.index_key(
                    key=dict_key or concept_name,
                    raw_semantic=primary_vec,
                )

            if self._dictionary is not None and dict_key and dict_key not in self._dictionary.entries:
                zh = spec.get("zh", concept_name)
                en = spec.get("en", concept_name)
                self._dictionary.entries[dict_key] = type('Entry', (), {
                    'surface_forms': {'zh': zh, 'en': en},
                    'contexts': [],
                    'relations': {},
                    'confidence': 1.0,
                })()

            count += 1

        self._built = True
        logger.info("ConceptLibrary: indexed %d concepts (%d labels)",
                     count, len(all_labels))
        return count

    def classify(self, image_data: bytes, top_k: int = 3) -> List[Dict[str, Any]]:
        """Classify an image against all indexed concepts.

        Returns top_k results with concept_name, dict_key, confidence, action.
        """
        if not self._built or self._encoder is None:
            return []

        img_vec = self._encoder.encode(image_data)
        if img_vec is None:
            return []

        scores = self._all_label_vecs @ img_vec

        concept_scores: Dict[str, List[float]] = {}
        label_idx = 0
        for name, info in self._concepts.items():
            n_labels = len(info["labels"])
            concept_scores[name] = scores[label_idx:label_idx + n_labels].tolist()
            label_idx += n_labels

        results = []
        for name, info in self._concepts.items():
            scs = concept_scores[name]
            best_score = max(scs) if scs else 0.0
            results.append({
                "concept_name": name,
                "dict_key": info["dict_key"],
                "confidence": round(float(best_score), 4),
                "action": info["action"],
                "labels": info["labels"],
            })

        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results[:top_k]

    def classify_raw(self, img_vec: np.ndarray, top_k: int = 3) -> List[Dict[str, Any]]:
        """Classify a pre-encoded image vector against all indexed concepts."""
        if not self._built or self._all_label_vecs is None:
            return []

        scores = self._all_label_vecs @ img_vec

        concept_scores: Dict[str, List[float]] = {}
        label_idx = 0
        for name, info in self._concepts.items():
            n_labels = len(info["labels"])
            concept_scores[name] = scores[label_idx:label_idx + n_labels].tolist()
            label_idx += n_labels

        results = []
        for name, info in self._concepts.items():
            scs = concept_scores[name]
            best_score = max(scs) if scs else 0.0
            results.append({
                "concept_name": name,
                "dict_key": info["dict_key"],
                "confidence": round(float(best_score), 4),
                "action": info["action"],
            })

        results.sort(key=lambda x: x["confidence"], reverse=True)
        return results[:top_k]

    @property
    def concept_count(self) -> int:
        return len(self._concepts)

    @property
    def is_built(self) -> bool:
        return self._built

    @staticmethod
    def _default_concepts() -> List[Dict]:
        """Built-in animal concept definitions with CLIP-friendly labels."""
        return [
            {
                "name": "chicken",
                "dict_key": "concept_chicken",
                "zh": "鸡",
                "en": "chicken",
                "labels": [
                    "a photo of a chicken",
                    "a photo of a small yellow chicken",
                    "a photo of a chick",
                    "a drawing of a chicken",
                    "an illustration of a chicken",
                ],
                "action": "在吃米",
            },
            {
                "name": "cat",
                "dict_key": "concept_cat",
                "zh": "猫",
                "en": "cat",
                "labels": [
                    "a photo of a cat",
                    "a photo of a yellow cat",
                    "a photo of a kitten",
                    "a drawing of a cat",
                    "an illustration of a cat",
                ],
                "action": "在坐著",
            },
            {
                "name": "dog",
                "dict_key": "concept_dog",
                "zh": "狗",
                "en": "dog",
                "labels": [
                    "a photo of a dog",
                    "a photo of a yellow dog",
                    "a photo of a puppy",
                    "a drawing of a dog",
                    "an illustration of a dog",
                ],
                "action": "在跑",
            },
            {
                "name": "bird",
                "dict_key": "concept_bird",
                "zh": "鸟",
                "en": "bird",
                "labels": [
                    "a photo of a bird",
                    "a photo of a small bird",
                    "a drawing of a bird",
                ],
                "action": "在飛",
            },
        ]
