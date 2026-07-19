"""Geometric Visual Vocabulary — shared representation for generation + recognition.

The vocabulary stores:
- Visual words: cluster centers in primitive parameter space
- Concept distributions: per-class statistics over visual words
- Primitive type analysis: which types are common for each concept

This is the foundation for both generation (top-down) and recognition (bottom-up).
"""

import json
import logging
import math
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class VisualWord:
    """A single visual word — a pattern in primitive parameter space."""

    word_id: int
    center: np.ndarray  # (263,) cluster center
    count: int  # how many images map to this word
    primitive_signature: dict = field(default_factory=dict)  # which primitives dominate

    def to_dict(self) -> dict:
        return {
            "word_id": self.word_id,
            "center": self.center.tolist(),
            "count": self.count,
            "primitive_signature": self.primitive_signature,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "VisualWord":
        return cls(
            word_id=d["word_id"],
            center=np.array(d["center"], dtype=np.float32),
            count=d["count"],
            primitive_signature=d.get("primitive_signature", {}),
        )


@dataclass
class ConceptDistribution:
    """Distribution of visual words for a concept (e.g., "cat")."""

    concept_name: str
    label: int
    visual_word_ids: List[int]  # which words appear
    word_frequencies: np.ndarray  # frequency of each word
    param_means: np.ndarray  # (263,) mean parameters for this concept
    param_stds: np.ndarray  # (263,) std of parameters
    n_images: int

    def to_dict(self) -> dict:
        return {
            "concept_name": self.concept_name,
            "label": self.label,
            "visual_word_ids": self.visual_word_ids,
            "word_frequencies": self.word_frequencies.tolist(),
            "param_means": self.param_means.tolist(),
            "param_stds": self.param_stds.tolist(),
            "n_images": self.n_images,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ConceptDistribution":
        return cls(
            concept_name=d["concept_name"],
            label=d["label"],
            visual_word_ids=d["visual_word_ids"],
            word_frequencies=np.array(d["word_frequencies"], dtype=np.float32),
            param_means=np.array(d["param_means"], dtype=np.float32),
            param_stds=np.array(d["param_stds"], dtype=np.float32),
            n_images=d["n_images"],
        )


class GeometricVocabulary:
    """Shared geometric vocabulary for generation and recognition.

    Architecture:
        - Visual words: k-means cluster centers in 263-dim parameter space
        - Concept distributions: per-class statistics (mean, std, word frequencies)
        - Recognition features: which words are present + their parameters

    Dual-use:
        - Generation: concept → visual words → initialize parameters → optimize
        - Recognition: image → extract parameters → match visual words → classify
    """

    CLASSES = [
        "airplane",
        "automobile",
        "bird",
        "cat",
        "deer",
        "dog",
        "frog",
        "horse",
        "ship",
        "truck",
    ]

    def __init__(self, n_visual_words: int = 20, param_dim: int = 263):
        self._n_visual_words = n_visual_words
        self._param_dim = param_dim
        self._visual_words: List[VisualWord] = []
        self._concept_distributions: Dict[str, ConceptDistribution] = {}
        self._all_params: Optional[np.ndarray] = None  # (N, 263)
        self._all_labels: Optional[np.ndarray] = None  # (N,)

    def build_from_optimized(
        self, params: np.ndarray, labels: np.ndarray, class_names: Optional[List[str]] = None
    ):
        """Build vocabulary from optimized primitive vectors.

        Args:
            params: (N, 263) optimized primitive parameter vectors
            labels: (N,) integer class labels
            class_names: optional list of class names (default: CIFAR-10)
        """
        if class_names is None:
            class_names = self.CLASSES

        self._all_params = params.astype(np.float32)
        self._all_labels = labels.astype(int)

        logger.info("Building vocabulary from %d images...", len(params))

        # Step 1: K-means to find visual words
        logger.info("  Step 1: Clustering → visual words...")
        self._cluster_to_visual_words(params)

        # Step 2: Build concept distributions
        logger.info("  Step 2: Building concept distributions...")
        for label_int in range(len(class_names)):
            name = class_names[label_int]
            mask = labels == label_int
            if mask.sum() < 2:
                continue
            concept_params = params[mask]
            self._build_concept_distribution(name, label_int, concept_params)

        logger.info(
            "  Vocabulary built: %d visual words, %d concepts",
            len(self._visual_words),
            len(self._concept_distributions),
        )

    def _cluster_to_visual_words(self, params: np.ndarray):
        """K-means clustering to find visual words."""
        n = len(params)
        k = min(self._n_visual_words, n)

        # Simple k-means (no sklearn dependency)
        rng = np.random.default_rng(42)
        indices = rng.choice(n, size=k, replace=False)
        centers = params[indices].copy()

        for iteration in range(20):
            # Assign each point to nearest center
            dists = np.sqrt(((params[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2))
            assignments = np.argmin(dists, axis=1)

            # Update centers
            new_centers = np.zeros_like(centers)
            for c in range(k):
                mask = assignments == c
                if mask.sum() > 0:
                    new_centers[c] = params[mask].mean(axis=0)
                else:
                    new_centers[c] = centers[c]

            # Check convergence
            shift = np.sqrt(((new_centers - centers) ** 2).sum(axis=1)).max()
            centers = new_centers
            if shift < 1e-4:
                break

        # Build visual word objects
        dists = np.sqrt(((params[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2))
        assignments = np.argmin(dists, axis=1)

        self._visual_words = []
        for c in range(k):
            mask = assignments == c
            count = int(mask.sum())
            # Analyze which primitive types dominate this word
            sig = self._analyze_primitive_signature(centers[c])
            self._visual_words.append(
                VisualWord(
                    word_id=c,
                    center=centers[c],
                    count=count,
                    primitive_signature=sig,
                )
            )

    def _analyze_primitive_signature(self, center: np.ndarray) -> dict:
        """Analyze which primitive types contribute most to a visual word."""
        from .primitive_types import N_ARCS, N_CIRCLES, N_LINES, N_PLANES, N_POINTS

        sig = {}
        off = 5  # skip header

        # Points: [off:off + N_POINTS*5]
        pts = center[off : off + N_POINTS * 5].reshape(N_POINTS, 5)
        active_pts = np.sum((pts[:, 0] > 0.01) | (pts[:, 1] > 0.01))
        sig["n_points"] = int(active_pts)
        sig["point_colors"] = (
            pts[pts[:, 0] > 0.01, 2:5].mean(axis=0).tolist() if active_pts > 0 else [0, 0, 0]
        )

        off += N_POINTS * 5

        # Lines: [off:off + N_LINES*8]
        lns = center[off : off + N_LINES * 8].reshape(N_LINES, 8)
        active_lines = np.sum((lns[:, 0] > 0.01) | (lns[:, 2] > 0.01))
        sig["n_lines"] = int(active_lines)

        off += N_LINES * 8

        # Planes: [off:off + N_PLANES*9]
        pls = center[off : off + N_PLANES * 9].reshape(N_PLANES, 9)
        active_planes = np.sum((pls[:, 2] > 0.01) | (pls[:, 3] > 0.01))
        sig["n_planes"] = int(active_planes)
        sig["plane_colors"] = (
            pls[pls[:, 2] > 0.01, 4:7].mean(axis=0).tolist() if active_planes > 0 else [0, 0, 0]
        )

        off += N_PLANES * 9

        # Circles: [off:off + N_CIRCLES*7]
        crs = center[off : off + N_CIRCLES * 7].reshape(N_CIRCLES, 7)
        active_circles = np.sum(crs[:, 2] > 0.005)
        sig["n_circles"] = int(active_circles)
        sig["circle_colors"] = (
            crs[crs[:, 2] > 0.005, 3:6].mean(axis=0).tolist() if active_circles > 0 else [0, 0, 0]
        )

        off += N_CIRCLES * 7

        # Arcs: [off:off + N_ARCS*10]
        arcs = center[off : off + N_ARCS * 10].reshape(N_ARCS, 10)
        active_arcs = np.sum(arcs[:, 2] > 0.005)
        sig["n_arcs"] = int(active_arcs)

        return sig

    def _build_concept_distribution(self, name: str, label: int, concept_params: np.ndarray):
        """Build distribution for a single concept."""
        # Find which visual words this concept uses
        dists = np.sqrt(
            (
                (
                    concept_params[:, None, :]
                    - np.array([vw.center for vw in self._visual_words])[None, :, :]
                )
                ** 2
            ).sum(axis=2)
        )
        assignments = np.argmin(dists, axis=1)

        # Word frequencies
        word_freq = np.zeros(len(self._visual_words), dtype=np.float32)
        for c in range(len(self._visual_words)):
            word_freq[c] = (assignments == c).sum() / len(concept_params)

        # Parameter statistics
        param_means = concept_params.mean(axis=0)
        param_stds = concept_params.std(axis=0) + 1e-6

        # Find which words are actually used (frequency > 0.05)
        used_ids = [i for i, f in enumerate(word_freq) if f > 0.05]

        self._concept_distributions[name] = ConceptDistribution(
            concept_name=name,
            label=label,
            visual_word_ids=used_ids,
            word_frequencies=word_freq,
            param_means=param_means,
            param_stds=param_stds,
            n_images=len(concept_params),
        )

    def get_concept(self, name: str) -> Optional[ConceptDistribution]:
        """Get concept distribution by name."""
        return self._concept_distributions.get(name)

    def get_concept_by_label(self, label: int) -> Optional[ConceptDistribution]:
        """Get concept distribution by label."""
        for c in self._concept_distributions.values():
            if c.label == label:
                return c
        return None

    def get_visual_words(self) -> List[VisualWord]:
        """Get all visual words."""
        return self._visual_words

    def get_visual_word(self, word_id: int) -> Optional[VisualWord]:
        """Get a specific visual word."""
        for vw in self._visual_words:
            if vw.word_id == word_id:
                return vw
        return None

    def find_nearest_word(self, params: np.ndarray, top_k: int = 1):
        """Find the nearest visual word to a parameter vector.

        Args:
            params: (263,) parameter vector
            top_k: number of nearest words to return

        Returns:
            If top_k=1: (word_id, distance)
            If top_k>1: (list of word_ids, list of distances)
        """
        if not self._visual_words:
            if top_k == 1:
                return -1, float("inf")
            return [], []

        centers = np.array([vw.center for vw in self._visual_words])
        dists = np.sqrt(((centers - params) ** 2).sum(axis=1))
        sorted_indices = np.argsort(dists)

        if top_k == 1:
            return int(sorted_indices[0]), float(dists[sorted_indices[0]])

        top_ids = [int(sorted_indices[i]) for i in range(min(top_k, len(sorted_indices)))]
        top_dists = [float(dists[i]) for i in sorted_indices[:top_k]]
        return top_ids, top_dists

    def initialize_from_concept(
        self, concept_name: str, rng: Optional[np.random.Generator] = None
    ) -> np.ndarray:
        """Initialize a parameter vector from a concept distribution.

        Returns a (263,) vector sampled from the concept's distribution.
        """
        concept = self._concept_distributions.get(concept_name)
        if concept is None:
            # Return random init if concept not found
            if rng is None:
                rng = np.random.default_rng()
            vec = rng.uniform(0.2, 0.8, self._param_dim).astype(np.float32)
            vec[0:3] = 0.5
            return vec

        if rng is None:
            rng = np.random.default_rng()

        # Sample from concept distribution
        noise = rng.normal(0, 0.05, self._param_dim).astype(np.float32)
        vec = concept.param_means + concept.param_stds * noise
        vec = np.clip(vec, 0.0, 1.0).astype(np.float32)

        # Use a visual word as base, then add noise
        if concept.visual_word_ids:
            word_id = rng.choice(concept.visual_word_ids)
            vw = self.get_visual_word(word_id)
            if vw is not None:
                vec = vw.center.copy()
                noise = rng.normal(0, 0.03, self._param_dim).astype(np.float32)
                vec = np.clip(vec + noise, 0.0, 1.0)

        return vec

    def compute_recognition_features(self, params: np.ndarray) -> np.ndarray:
        """Compute recognition features from a parameter vector.

        Features: visual word assignment + parameter values for assigned word.
        """
        word_id, dist = self.find_nearest_word(params)

        features = []

        # Word assignment (one-hot)
        word_onehot = np.zeros(len(self._visual_words), dtype=np.float32)
        if word_id >= 0:
            word_onehot[word_id] = 1.0
        features.append(word_onehot)

        # Distance to nearest word
        features.append(np.array([dist / 10.0], dtype=np.float32))

        # Parameter values (downsampled)
        features.append(params[::5])  # every 5th dim

        return np.concatenate(features)

    def save(self, path: str):
        """Save vocabulary to JSON."""
        data = {
            "n_visual_words": self._n_visual_words,
            "param_dim": self._param_dim,
            "visual_words": [vw.to_dict() for vw in self._visual_words],
            "concept_distributions": {
                k: v.to_dict() for k, v in self._concept_distributions.items()
            },
        }
        if self._all_params is not None:
            data["all_params"] = self._all_params.tolist()
        if self._all_labels is not None:
            data["all_labels"] = self._all_labels.tolist()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)
        logger.info("Vocabulary saved to %s", path)

    @classmethod
    def load(cls, path: str) -> "GeometricVocabulary":
        """Load vocabulary from JSON."""
        with open(path) as f:
            data = json.load(f)

        vocab = cls(
            n_visual_words=data["n_visual_words"],
            param_dim=data["param_dim"],
        )
        vocab._visual_words = [VisualWord.from_dict(vw) for vw in data["visual_words"]]
        vocab._concept_distributions = {
            k: ConceptDistribution.from_dict(v) for k, v in data["concept_distributions"].items()
        }
        if "all_params" in data:
            vocab._all_params = np.array(data["all_params"], dtype=np.float32)
        if "all_labels" in data:
            vocab._all_labels = np.array(data["all_labels"], dtype=int)
        logger.info(
            "Vocabulary loaded: %d words, %d concepts",
            len(vocab._visual_words),
            len(vocab._concept_distributions),
        )
        return vocab
