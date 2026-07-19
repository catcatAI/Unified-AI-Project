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

    def __init__(self, semantic_encoder=None, dictionary=None, key_mapper=None):
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

            if (
                self._dictionary is not None
                and dict_key
                and dict_key not in self._dictionary.entries
            ):
                zh = spec.get("zh", concept_name)
                en = spec.get("en", concept_name)
                self._dictionary.entries[dict_key] = type(
                    "Entry",
                    (),
                    {
                        "surface_forms": {"zh": zh, "en": en},
                        "contexts": [],
                        "relations": {},
                        "confidence": 1.0,
                    },
                )()

            count += 1

        self._built = True
        logger.info("ConceptLibrary: indexed %d concepts (%d labels)", count, len(all_labels))
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
            concept_scores[name] = scores[label_idx : label_idx + n_labels].tolist()
            label_idx += n_labels

        results = []
        for name, info in self._concepts.items():
            scs = concept_scores[name]
            best_score = max(scs) if scs else 0.0
            results.append(
                {
                    "concept_name": name,
                    "dict_key": info["dict_key"],
                    "confidence": round(float(best_score), 4),
                    "action": info["action"],
                    "labels": info["labels"],
                }
            )

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
            concept_scores[name] = scores[label_idx : label_idx + n_labels].tolist()
            label_idx += n_labels

        results = []
        for name, info in self._concepts.items():
            scs = concept_scores[name]
            best_score = max(scs) if scs else 0.0
            results.append(
                {
                    "concept_name": name,
                    "dict_key": info["dict_key"],
                    "confidence": round(float(best_score), 4),
                    "action": info["action"],
                }
            )

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
        """Built-in concept definitions with CLIP-friendly labels."""
        return [
            # --- Animals ---
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
                    "a photo of a kitten",
                    "a drawing of a cat",
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
                    "a photo of a puppy",
                    "a drawing of a dog",
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
            {
                "name": "fish",
                "dict_key": "concept_fish",
                "zh": "鱼",
                "en": "fish",
                "labels": [
                    "a photo of a fish",
                    "a photo of a goldfish",
                    "a drawing of a fish",
                ],
                "action": "在游水",
            },
            {
                "name": "horse",
                "dict_key": "concept_horse",
                "zh": "马",
                "en": "horse",
                "labels": [
                    "a photo of a horse",
                    "a photo of a brown horse",
                    "a drawing of a horse",
                ],
                "action": "在跑",
            },
            {
                "name": "rabbit",
                "dict_key": "concept_rabbit",
                "zh": "兔子",
                "en": "rabbit",
                "labels": [
                    "a photo of a rabbit",
                    "a photo of a white rabbit",
                    "a drawing of a rabbit",
                ],
                "action": "在跳",
            },
            {
                "name": "elephant",
                "dict_key": "concept_elephant",
                "zh": "大象",
                "en": "elephant",
                "labels": [
                    "a photo of an elephant",
                    "a photo of a large elephant",
                    "a drawing of an elephant",
                ],
                "action": "在走",
            },
            {
                "name": "bear",
                "dict_key": "concept_bear",
                "zh": "熊",
                "en": "bear",
                "labels": [
                    "a photo of a bear",
                    "a photo of a brown bear",
                    "a drawing of a bear",
                ],
                "action": "在站",
            },
            # --- Food ---
            {
                "name": "apple",
                "dict_key": "concept_apple",
                "zh": "苹果",
                "en": "apple",
                "labels": [
                    "a photo of an apple",
                    "a photo of a red apple",
                    "a drawing of an apple",
                ],
                "action": "",
            },
            {
                "name": "banana",
                "dict_key": "concept_banana",
                "zh": "香蕉",
                "en": "banana",
                "labels": [
                    "a photo of a banana",
                    "a photo of yellow bananas",
                    "a drawing of a banana",
                ],
                "action": "",
            },
            {
                "name": "rice",
                "dict_key": "concept_rice",
                "zh": "米饭",
                "en": "rice",
                "labels": [
                    "a photo of a bowl of rice",
                    "a photo of cooked rice",
                    "a drawing of rice",
                ],
                "action": "",
            },
            # --- Objects ---
            {
                "name": "car",
                "dict_key": "concept_car",
                "zh": "汽车",
                "en": "car",
                "labels": [
                    "a photo of a car",
                    "a photo of a red car",
                    "a drawing of a car",
                ],
                "action": "在開",
            },
            {
                "name": "house",
                "dict_key": "concept_house",
                "zh": "房子",
                "en": "house",
                "labels": [
                    "a photo of a house",
                    "a photo of a small house",
                    "a drawing of a house",
                ],
                "action": "",
            },
            {
                "name": "tree",
                "dict_key": "concept_tree",
                "zh": "树",
                "en": "tree",
                "labels": [
                    "a photo of a tree",
                    "a photo of a green tree",
                    "a drawing of a tree",
                ],
                "action": "",
            },
            {
                "name": "flower",
                "dict_key": "concept_flower",
                "zh": "花",
                "en": "flower",
                "labels": [
                    "a photo of a flower",
                    "a photo of a red flower",
                    "a drawing of a flower",
                ],
                "action": "",
            },
            {
                "name": "book",
                "dict_key": "concept_book",
                "zh": "书",
                "en": "book",
                "labels": [
                    "a photo of a book",
                    "a photo of an open book",
                    "a drawing of a book",
                ],
                "action": "",
            },
            {
                "name": "chair",
                "dict_key": "concept_chair",
                "zh": "椅子",
                "en": "chair",
                "labels": [
                    "a photo of a chair",
                    "a photo of a wooden chair",
                    "a drawing of a chair",
                ],
                "action": "",
            },
            # --- Outdoor scenes ---
            {
                "name": "mountain",
                "dict_key": "concept_mountain",
                "zh": "山",
                "en": "mountain",
                "labels": [
                    "a photo of a mountain",
                    "a photo of snow-capped mountains",
                    "a drawing of a mountain",
                ],
                "action": "",
            },
            {
                "name": "ocean",
                "dict_key": "concept_ocean",
                "zh": "海",
                "en": "ocean",
                "labels": [
                    "a photo of the ocean",
                    "a photo of ocean waves",
                    "a drawing of the sea",
                ],
                "action": "",
            },
            {
                "name": "person",
                "dict_key": "concept_person",
                "zh": "人",
                "en": "person",
                "labels": [
                    "a photo of a person",
                    "a photo of a man",
                    "a photo of a woman",
                    "a drawing of a person",
                ],
                "action": "",
            },
        ]
