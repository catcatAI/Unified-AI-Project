"""Shared latent space — projects modality vectors to a unified embedding space + contrastive learning."""

import logging
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

logger = logging.getLogger(__name__)

Pair = Tuple[str, np.ndarray, str, np.ndarray]


class SharedLatentSpace:
    """Projects feature vectors from any modality into a shared N-dim latent space.

    Supports contrastive learning: train projection weights from co-occurrence pairs
    so that positive pairs (e.g. image + its caption) have high cosine similarity
    and negative pairs have low similarity.
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
        """Project a modality-specific feature vector into latent space. Returns raw (unnormalized) vector.

        Callers should L2-normalize for similarity comparisons if needed.
        """
        proj = self._projections.get(modality)
        if proj is None:
            logger.warning("Unknown modality '%s', returning zeros", modality)
            return np.zeros(self._latent_dim, dtype=np.float32)
        latent = proj["W"] @ features + proj["b"]
        self._embedding_cache[modality] = latent
        return latent

    @staticmethod
    def _l2_normalize(v: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(v)
        return v / norm if norm > 0 else v

    def similarity(self, mod_a: str, mod_b: str) -> float:
        """Cosine similarity between two modalities in latent space, mapped to [0,1]."""
        emb_a = self._embedding_cache.get(mod_a)
        emb_b = self._embedding_cache.get(mod_b)
        if emb_a is None or emb_b is None:
            return 0.0
        a_norm = self._l2_normalize(emb_a)
        b_norm = self._l2_normalize(emb_b)
        dot = float(np.dot(a_norm, b_norm))
        return max(0.0, min(1.0, (dot + 1.0) / 2.0))

    def get_embedding(self, modality: str) -> Optional[np.ndarray]:
        """Return the current latent embedding for a modality, if set."""
        return self._embedding_cache.get(modality)

    def registered_modalities(self) -> List[str]:
        return list(self._projections.keys())

    def reset(self) -> None:
        self._embedding_cache.clear()

    # ------------------------------------------------------------------
    # P43: Semantic modality support
    # ------------------------------------------------------------------

    def register_semantic_modality(self, base_name: str, input_dim: int) -> None:
        """Register a semantic variant of an existing modality.

        Creates a modality named ``{base_name}_semantic`` that can be used
        alongside the structural ``{base_name}`` modality.  Both remain
        addressable independently for similarity / attention queries.

        Example::

            ls.register_modality("vision", 256)          # structural
            ls.register_semantic_modality("vision", 512)  # semantic
        """
        self.register_modality(f"{base_name}_semantic", input_dim)

    def semantic_consistency(self, modality: str,
                             features_list: Sequence[np.ndarray]) -> float:
        """Measure how consistently a set of semantic features cluster in
        latent space.

        Projects every feature through the ``{modality}_semantic`` projection,
        then computes the average pairwise cosine similarity between the
        resulting latent vectors.  A high score means the features form a
        tight cluster (e.g. different views of the same object).

        The raw cosine similarity (range [-1, 1]) is mapped linearly to
        [0, 1] via ``(cos + 1) / 2``, so:

        * **1.0** = identical direction (perfectly clustered)
        * **0.5** ≈ orthogonal / random relationship
        * **0.0** = exactly opposite direction

        Returns
        -------
        float
            Score in [0, 1].  Returns 0 when fewer than 2 features are
            provided or the semantic modality is not registered.
        """
        semantic_name = f"{modality}_semantic"
        if semantic_name not in self._projections:
            logger.warning("Semantic modality '%s' not registered", semantic_name)
            return 0.0

        if len(features_list) < 2:
            return 0.0

        latents = [self._l2_normalize(self.project(semantic_name, f))
                   for f in features_list]

        total_sim = 0.0
        count = 0
        for i in range(len(latents)):
            for j in range(i + 1, len(latents)):
                total_sim += float(np.dot(latents[i], latents[j]))
                count += 1

        avg_sim = total_sim / max(count, 1)
        # Map from [-1, 1] to [0, 1]
        return max(0.0, (avg_sim + 1.0) / 2.0)

    def semantic_contrastive_train(self,
                                   pos_pairs: List[Tuple[np.ndarray, np.ndarray]],
                                   neg_pairs: List[Tuple[np.ndarray, np.ndarray]],
                                   modality: str = "vision_semantic",
                                   epochs: int = 10,
                                   lr: float = 0.01,
                                   margin: float = 0.5) -> Dict[str, Any]:
        """Train *semantic* projection weights with contrastive learning.

        Contrasts features projected through the ``{modality}`` projection
        matrix.  Each pair is ``(feat_a, feat_b)`` from the same modality.
        This is a convenience wrapper around :meth:`train`.

        Returns
        -------
        dict
            ``{"final_loss": …, "history": […]}``
        """
        if not pos_pairs and not neg_pairs:
            return {"final_loss": 0.0, "history": []}

        formatted_pos = [(modality, a, modality, b) for a, b in pos_pairs]
        formatted_neg = [(modality, a, modality, b) for a, b in neg_pairs]
        return self.train(formatted_pos, formatted_neg,
                          epochs=epochs, lr=lr, margin=margin)

    # ------------------------------------------------------------------
    # P16: Contrastive learning
    # ------------------------------------------------------------------

    def train(self, pos_pairs: List[Pair], neg_pairs: List[Pair],
              epochs: int = 10, lr: float = 0.01, margin: float = 0.5) -> Dict[str, float]:
        """Train projection weights using contrastive loss.

        Args:
            pos_pairs: List of (mod_a, feat_a, mod_b, feat_b) that should be similar.
            neg_pairs: List of (mod_a, feat_a, mod_b, feat_b) that should be dissimilar.
            epochs: Number of training epochs.
            lr: Learning rate for SGD.
            margin: Margin for contrastive loss.

        Returns:
            dict with final loss and epoch history.
        """
        if epochs == 0 or (not pos_pairs and not neg_pairs):
            return {"final_loss": 0.0, "history": []}
        history = []
        for epoch in range(epochs):
            loss = self._train_epoch(pos_pairs, neg_pairs, lr, margin)
            history.append(loss)
            if epoch % 5 == 0 or epoch == epochs - 1:
                logger.debug("Contrastive epoch %d/%d: loss=%.4f", epoch + 1, epochs, loss)
        return {"final_loss": float(history[-1]), "history": history}

    def _train_epoch(self, pos_pairs: List[Pair], neg_pairs: List[Pair],
                     lr: float, margin: float) -> float:
        """Single training epoch with contrastive loss."""
        total_loss = 0.0
        count = 0

        for mod_a, feat_a, mod_b, feat_b in pos_pairs:
            loss, grad_a, grad_b = self._contrastive_loss(
                mod_a, feat_a, mod_b, feat_b, margin, is_positive=True
            )
            self._apply_gradients(mod_a, feat_a, grad_a, lr)
            self._apply_gradients(mod_b, feat_b, grad_b, lr)
            total_loss += loss
            count += 1

        for mod_a, feat_a, mod_b, feat_b in neg_pairs:
            loss, grad_a, grad_b = self._contrastive_loss(
                mod_a, feat_a, mod_b, feat_b, margin, is_positive=False
            )
            self._apply_gradients(mod_a, feat_a, grad_a, lr)
            self._apply_gradients(mod_b, feat_b, grad_b, lr)
            total_loss += loss
            count += 1

        return total_loss / max(count, 1)

    def _contrastive_loss(self, mod_a: str, feat_a: np.ndarray,
                          mod_b: str, feat_b: np.ndarray,
                          margin: float, is_positive: bool) -> Tuple[float, np.ndarray, np.ndarray]:
        """Compute contrastive loss and gradients w.r.t. latent embeddings.

        Uses cosine distance: d = 1 - cos(a,b).
        pos: d  (pull positive pairs together)
        neg: max(0, margin - d)  (push negative pairs apart)
        """
        proj_a = self._projections.get(mod_a)
        proj_b = self._projections.get(mod_b)
        if proj_a is None or proj_b is None:
            return 0.0, np.zeros(self._latent_dim), np.zeros(self._latent_dim)

        latent_a = proj_a["W"] @ feat_a + proj_a["b"]
        latent_b = proj_b["W"] @ feat_b + proj_b["b"]

        a_norm = self._l2_normalize(latent_a)
        b_norm = self._l2_normalize(latent_b)
        cos_sim = float(np.dot(a_norm, b_norm))
        cos_dist = 1.0 - cos_sim

        if is_positive:
            loss = cos_dist
            grad_a = -(b_norm - cos_sim * a_norm) / max(np.linalg.norm(latent_a), 1e-8)
            grad_b = -(a_norm - cos_sim * b_norm) / max(np.linalg.norm(latent_b), 1e-8)
        else:
            loss = max(0.0, margin - cos_dist)
            if loss > 0:
                grad_a = (b_norm - cos_sim * a_norm) / max(np.linalg.norm(latent_a), 1e-8)
                grad_b = (a_norm - cos_sim * b_norm) / max(np.linalg.norm(latent_b), 1e-8)
            else:
                grad_a = np.zeros(self._latent_dim)
                grad_b = np.zeros(self._latent_dim)

        return loss, grad_a.astype(np.float32), grad_b.astype(np.float32)

        diff = latent_a - latent_b
        dist_sq = float(np.dot(diff, diff))

        if is_positive:
            loss = dist_sq
            grad_a = 2.0 * diff
            grad_b = -2.0 * diff
        else:
            loss = max(0.0, margin ** 2 - dist_sq)
            if loss > 0:
                grad_a = -2.0 * diff
                grad_b = 2.0 * diff
            else:
                grad_a = np.zeros(self._latent_dim)
                grad_b = np.zeros(self._latent_dim)

        return loss, grad_a, grad_b

    def _apply_gradients(self, modality: str, features: np.ndarray,
                         grad_latent: np.ndarray, lr: float) -> None:
        """Update W and b using gradient w.r.t. latent embedding, with clipping."""
        proj = self._projections.get(modality)
        if proj is None or np.all(grad_latent == 0):
            return
        grad_norm = np.linalg.norm(grad_latent)
        if grad_norm > 10.0:
            grad_latent = grad_latent / (grad_norm / 10.0)
        proj["W"] -= lr * np.outer(grad_latent, features)
        proj["b"] -= lr * grad_latent

    # ------------------------------------------------------------------
    # P16: Cross-modal attention
    # ------------------------------------------------------------------

    def cross_modal_attention(self, query_mod: str, target_mods: List[str]) -> Dict[str, float]:
        """Compute attention weights: how much each target modality attends to the query.

        Uses dot-product attention: score = exp(query @ target) / sum(exp(...)).
        Both embeddings must already be projected (via .project()).

        Returns:
            {modality: attention_weight} with weights summing to 1.
        """
        query_emb = self._embedding_cache.get(query_mod)
        if query_emb is None:
            return {m: 0.0 for m in target_mods}

        scores = {}
        for tm in target_mods:
            target_emb = self._embedding_cache.get(tm)
            if target_emb is not None:
                scores[tm] = float(np.dot(query_emb, target_emb))
            else:
                scores[tm] = 0.0

        scores_arr = np.array(list(scores.values()), dtype=np.float32)
        scores_arr = np.exp(scores_arr - scores_arr.max())
        total = scores_arr.sum()
        if total > 0:
            scores_arr = scores_arr / total

        return dict(zip(scores.keys(), scores_arr.tolist()))
