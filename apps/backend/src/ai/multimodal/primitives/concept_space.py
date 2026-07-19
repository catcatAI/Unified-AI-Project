"""Concept Space — learned mapping from CLIP features to shared concept space.

The key insight: different images of the same class should map to the same
region in concept space. This captures the "wholeness" of a concept —
what geometric primitives compose a cat, not just the specific cat's parameters.

Architecture:
    CLIP image features (512-dim) → FC → Concept Space (64-dim)

Training:
    Same class images → similar concept space vectors
    Different class images → different concept space vectors

This is the missing piece that enables dual-use vocabulary:
- Generation: text → CLIP → concept space → primitive distribution → optimize → render
- Recognition: image → CLIP → concept space → classify
"""

import json
import logging
import os

logger = logging.getLogger(__name__)
import time
from typing import Dict, List, Optional, Tuple

import numpy as np


class ConceptSpaceMapper:
    """Maps CLIP features to a shared concept space.

    The concept space is trained so that:
    - All images of the same class map to similar vectors
    - Different classes map to different regions
    - The space captures the semantic structure of concepts

    This enables:
    - Recognition: CLIP image → concept space → nearest class center
    - Generation: CLIP text → concept space → primitive distribution → optimize
    """

    def __init__(self, clip_dim: int = 512, concept_dim: int = 64, hidden_dim: int = 128):
        self._clip_dim = clip_dim
        self._concept_dim = concept_dim
        self._hidden_dim = hidden_dim

        # Simple 2-layer FC network
        rng = np.random.default_rng(42)
        scale1 = np.sqrt(2.0 / clip_dim)
        scale2 = np.sqrt(2.0 / hidden_dim)
        scale3 = np.sqrt(2.0 / hidden_dim)

        self._W1 = rng.normal(0, scale1, (hidden_dim, clip_dim)).astype(np.float32)
        self._b1 = np.zeros(hidden_dim, dtype=np.float32)
        self._W2 = rng.normal(0, scale2, (hidden_dim, hidden_dim)).astype(np.float32)
        self._b2 = np.zeros(hidden_dim, dtype=np.float32)
        self._W3 = rng.normal(0, scale3, (concept_dim, hidden_dim)).astype(np.float32)
        self._b3 = np.zeros(concept_dim, dtype=np.float32)

        # Class centers in concept space (learned during training)
        self._class_centers: Optional[np.ndarray] = None
        self._class_names: List[str] = []
        self._is_trained = False

    def _relu(self, x: np.ndarray) -> np.ndarray:
        return np.maximum(0, x)

    def _forward(self, clip_features: np.ndarray) -> np.ndarray:
        """Forward pass: CLIP features → concept space."""
        h1 = self._relu(clip_features @ self._W1.T + self._b1)
        h2 = self._relu(h1 @ self._W2.T + self._b2)
        out = h2 @ self._W3.T + self._b3

        # L2 normalize
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return out / norms

    def encode(self, clip_features: np.ndarray) -> np.ndarray:
        """Map CLIP features to concept space.

        Args:
            clip_features: (N, 512) CLIP image features

        Returns:
            (N, 64) concept space vectors (L2-normalized)
        """
        if clip_features.ndim == 1:
            clip_features = clip_features.reshape(1, -1)
        return self._forward(clip_features)

    def train(
        self,
        clip_features: np.ndarray,
        labels: np.ndarray,
        class_names: List[str],
        n_epochs: int = 200,
        lr: float = 0.001,
        batch_size: int = 32,
        verbose: bool = True,
    ):
        """Train the concept space mapping.

        Uses supervised contrastive loss:
        - Pull same-class vectors together
        - Push different-class vectors apart

        Args:
            clip_features: (N, 512) CLIP image features
            labels: (N,) integer class labels
            class_names: list of class names
            n_epochs: number of training epochs
            lr: learning rate
            batch_size: mini-batch size
            verbose: print progress
        """
        self._class_names = class_names
        n_classes = len(class_names)
        n_samples = len(clip_features)

        if verbose:
            logger.info("Training concept space: %d images, %d classes", n_samples, n_classes)
            logger.info(
                "  Architecture: %d → %d → %d → %d",
                self._clip_dim,
                self._hidden_dim,
                self._hidden_dim,
                self._concept_dim,
            )

        t_start = time.time()

        for epoch in range(n_epochs):
            # Shuffle data
            perm = np.random.permutation(n_samples)
            clip_shuffled = clip_features[perm]
            label_shuffled = labels[perm]

            total_loss = 0.0
            n_batches = 0

            for i in range(0, n_samples, batch_size):
                batch_clip = clip_shuffled[i : i + batch_size]
                batch_labels = label_shuffled[i : i + batch_size]
                bs = len(batch_clip)

                if bs < 2:
                    continue

                # Forward pass
                concept_vecs = self._forward(batch_clip)  # (bs, concept_dim)

                # Compute loss: supervised contrastive
                loss = self._contrastive_loss(concept_vecs, batch_labels)

                # Backward pass (finite differences for simplicity)
                grad = self._compute_gradient(batch_clip, batch_labels)

                # Update weights
                self._W1 -= lr * grad["W1"]
                self._b1 -= lr * grad["b1"]
                self._W2 -= lr * grad["W2"]
                self._b2 -= lr * grad["b2"]
                self._W3 -= lr * grad["W3"]
                self._b3 -= lr * grad["b3"]

                total_loss += loss
                n_batches += 1

            if verbose and (epoch + 1) % 50 == 0:
                avg_loss = total_loss / max(n_batches, 1)
                elapsed = time.time() - t_start
                logger.info(
                    "  Epoch %d/%d: loss=%.4f (%.1fs)", epoch + 1, n_epochs, avg_loss, elapsed
                )

        # Compute class centers
        concept_vecs = self._forward(clip_features)
        self._class_centers = np.zeros((n_classes, self._concept_dim), dtype=np.float32)
        for c in range(n_classes):
            mask = labels == c
            if mask.sum() > 0:
                self._class_centers[c] = concept_vecs[mask].mean(axis=0)
                # Normalize center
                norm = np.linalg.norm(self._class_centers[c])
                if norm > 0:
                    self._class_centers[c] /= norm

        self._is_trained = True
        if verbose:
            elapsed = time.time() - t_start
            logger.info("Training complete (%.1fs)", elapsed)

    def _contrastive_loss(self, concept_vecs: np.ndarray, labels: np.ndarray) -> float:
        """Supervised contrastive loss.

        For each anchor, pull positive (same class) together,
        push negative (different class) apart.
        """
        bs = len(concept_vecs)
        if bs < 2:
            return 0.0

        # Similarity matrix
        sims = concept_vecs @ concept_vecs.T  # (bs, bs)

        # Label mask
        labels_row = labels.reshape(-1, 1)
        pos_mask = (labels_row == labels_row.T).astype(float)
        np.fill_diagonal(pos_mask, 0)  # exclude self

        # Negative mask
        neg_mask = 1.0 - pos_mask
        np.fill_diagonal(neg_mask, 0)

        # Contrastive loss (InfoNCE-like)
        pos_sims = (sims * pos_mask).sum(axis=1)
        n_pos = pos_mask.sum(axis=1)
        n_pos[n_pos == 0] = 1

        # Log-sum-exp for denominator
        exp_sims = np.exp(sims - sims.max(axis=1, keepdims=True))
        denom = exp_sims.sum(axis=1) - np.exp(0)  # exclude self

        loss = -pos_sims.mean() / n_pos.mean() + np.log(denom.mean() + 1e-8)
        return float(loss)

    def _compute_gradient(
        self, clip_batch: np.ndarray, labels: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """Compute gradients via finite differences."""
        eps = 0.001
        grad = {}

        # For each parameter, compute finite difference
        for name, param in [
            ("W1", self._W1),
            ("b1", self._b1),
            ("W2", self._W2),
            ("b2", self._b2),
            ("W3", self._W3),
            ("b3", self._b3),
        ]:
            grad[name] = np.zeros_like(param)
            # Random subspace (too many params for full finite diff)
            n_probe = min(20, param.size)
            flat = param.ravel()
            probe_idx = np.random.choice(param.size, n_probe, replace=False)

            for idx in probe_idx:
                # Forward with +eps
                flat[idx] += eps
                vecs_plus = self._forward(clip_batch)
                loss_plus = self._contrastive_loss(vecs_plus, labels)

                # Forward with -eps
                flat[idx] -= 2 * eps
                vecs_minus = self._forward(clip_batch)
                loss_minus = self._contrastive_loss(vecs_minus, labels)

                # Restore
                flat[idx] += eps

                # Gradient
                grad[name].ravel()[idx] = (loss_plus - loss_minus) / (2 * eps)

        return grad

    def predict(self, clip_features: np.ndarray) -> Tuple[int, float]:
        """Predict class from CLIP features.

        Returns:
            (predicted_class_index, confidence)
        """
        if not self._is_trained or self._class_centers is None:
            return -1, 0.0

        concept_vec = self.encode(clip_features)
        sims = concept_vec @ self._class_centers.T  # (1, n_classes)
        pred_idx = int(np.argmax(sims))
        confidence = float(sims[0, pred_idx])

        return pred_idx, confidence

    def predict_batch(self, clip_features: np.ndarray) -> List[Tuple[int, float]]:
        """Predict classes for a batch."""
        return [self.predict(clip_features[i : i + 1]) for i in range(len(clip_features))]

    def get_concept_vector(self, clip_features: np.ndarray) -> np.ndarray:
        """Get concept space vector for use in generation pipeline."""
        return self.encode(clip_features)

    def save(self, path: str):
        """Save concept space mapper."""
        data = {
            "clip_dim": self._clip_dim,
            "concept_dim": self._concept_dim,
            "hidden_dim": self._hidden_dim,
            "W1": self._W1.tolist(),
            "b1": self._b1.tolist(),
            "W2": self._W2.tolist(),
            "b2": self._b2.tolist(),
            "W3": self._W3.tolist(),
            "b3": self._b3.tolist(),
            "class_names": self._class_names,
            "is_trained": self._is_trained,
        }
        if self._class_centers is not None:
            data["class_centers"] = self._class_centers.tolist()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)
        logger.info("Concept space saved to %s", path)

    @classmethod
    def load(cls, path: str) -> "ConceptSpaceMapper":
        """Load concept space mapper."""
        with open(path) as f:
            data = json.load(f)

        mapper = cls(
            clip_dim=data["clip_dim"],
            concept_dim=data["concept_dim"],
            hidden_dim=data["hidden_dim"],
        )
        mapper._W1 = np.array(data["W1"], dtype=np.float32)
        mapper._b1 = np.array(data["b1"], dtype=np.float32)
        mapper._W2 = np.array(data["W2"], dtype=np.float32)
        mapper._b2 = np.array(data["b2"], dtype=np.float32)
        mapper._W3 = np.array(data["W3"], dtype=np.float32)
        mapper._b3 = np.array(data["b3"], dtype=np.float32)
        mapper._class_names = data["class_names"]
        mapper._is_trained = data["is_trained"]
        if "class_centers" in data:
            mapper._class_centers = np.array(data["class_centers"], dtype=np.float32)

        logger.info(
            "Concept space loaded: %s → %s → %s",
            mapper._clip_dim,
            mapper._hidden_dim,
            mapper._concept_dim,
        )
        return mapper
