"""
Resonance Engine — 語義共振統一引擎
====================================

所有軸的相似度計算通過這裡：
- 計算向量與軸的共振度
- 找最佳軸 / 複合軸
- 計算跨軸不確定性（entropy）

使用方式:
    from core.allocation.resonance import ResonanceEngine

    engine = ResonanceEngine(axes=[alpha, beta, gamma, delta, epsilon])
    resonance = engine.compute_resonance(vector, target=alpha)
    best_axis = engine.find_best_axis(vector)

Author: Angela AI v6.2
Version: 6.2.1
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

_DEFAULT_DIMS = 32


def _keyword_to_dims(word: str, dims: int) -> List[int]:
    """Map a word to a set of dimension indices using hash."""
    h = hashlib.md5(word.encode("utf-8")).digest()
    n_activations = max(1, (h[0] % 5) + 1)
    indices: List[int] = []
    for i in range(n_activations):
        idx = (h[i] | (h[(i + 1) % len(h)] << 8)) % dims
        if idx not in indices:
            indices.append(idx)
    return indices


def _text_to_vector(text: str, dims: int = _DEFAULT_DIMS) -> List[float]:
    """Convert text to a normalized vector of given dimensionality."""
    vec = [0.0] * dims
    words = re.findall(r"[a-zA-Z]+", text.lower())
    for word in words:
        for idx in _keyword_to_dims(word, dims):
            vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _cosine_sim(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def _entropy(similarities: Dict[str, float]) -> float:
    vals = [max(v, 1e-10) for v in similarities.values()]
    total = sum(vals)
    if total == 0:
        return 0.0
    probs = [v / total for v in vals]
    return -sum(p * math.log(p) for p in probs) / math.log(len(probs) or 1)


_AXIS_KEYWORDS: Dict[str, List[str]] = {
    "alpha": ["energy", "arousal", "comfort", "tension", "rest", "vitality", "strength"],
    "beta": [
        "focus", "curiosity", "clarity", "confusion",
        "learning", "creativity", "understanding"
    ],
    "gamma": ["happiness", "calm", "fear", "sadness", "emotion", "feeling", "mood"],
    "delta": ["attention", "bond", "presence", "engagement", "social", "connection", "trust"],
    "epsilon": ["logic", "precision", "complexity", "certainty", "math", "reason", "analysis"],
    "theta": ["novelty", "ambiguity", "meta", "reflection", "awareness", "oversight", "strategy"],
}

_AXIS_NAMES = ["alpha", "beta", "gamma", "delta", "epsilon", "theta"]


def _build_initial_vectors(dims: int = _DEFAULT_DIMS) -> Dict[str, List[float]]:
    vectors: Dict[str, List[float]] = {}
    for axis, keywords in _AXIS_KEYWORDS.items():
        vec = [0.0] * dims
        for kw in keywords:
            for idx in _keyword_to_dims(kw, dims):
                vec[idx] += 0.3
        texts = keywords + [f"{axis}_core"]
        for t in texts:
            for idx in _keyword_to_dims(t, dims):
                vec[idx] += 0.2
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        vectors[axis] = [v / norm for v in vec]
    return vectors


@dataclass
class ResonanceProfile:
    best_axis: str = ""
    max_resonance: float = 0.0
    similarities: Dict[str, float] = field(default_factory=dict)
    entropy: float = 0.0
    active_count: int = 0
    num_high_sim: int = 0


@dataclass
class ResonanceResult:
    axis: str = ""
    similarity: float = 0.0


class ResonanceEngine:
    """語義共振引擎 — 計算向量與各軸的共振度。"""

    def __init__(self, axes: Optional[List[Any]] = None):
        self._semantic_vectors: Dict[str, List[float]] = _build_initial_vectors()
        self._dims = _DEFAULT_DIMS
        self._sparsity_log: Dict[str, List[int]] = {}
        if axes:
            axis_names = [getattr(a, "name", f"axis_{i}") for i, a in enumerate(axes)]
            for name in axis_names:
                if name and name not in self._semantic_vectors:
                    self._semantic_vectors[name] = [0.0] * self._dims

    def _text_to_vector(self, text: str, dims: Optional[int] = None) -> List[float]:
        return _text_to_vector(text, dims or self._dims)

    def compute_resonance(self, vector: List[float], axis: str) -> float:
        anchor = self._semantic_vectors.get(axis)
        if anchor is None or len(anchor) != len(vector):
            return 0.0
        return _cosine_sim(vector, anchor)

    def compute_profile(self, vector: List[float]) -> ResonanceProfile:
        sims: Dict[str, float] = {}
        for name in self._semantic_vectors:
            sim = self.compute_resonance(vector, name)
            sims[name] = sim
        best_axis = max(sims, key=sims.get) if sims else ""
        max_res = sims.get(best_axis, 0.0)
        active = sum(1 for v in sims.values() if v > 0.15)
        ent = _entropy(sims)
        return ResonanceProfile(
            best_axis=best_axis,
            max_resonance=max_res,
            similarities=sims,
            entropy=ent,
            active_count=active,
        )

    def find_best_axis(self, vector: List[float]) -> Tuple[str, float]:
        profile = self.compute_profile(vector)
        return profile.best_axis, profile.max_resonance

    def _sparsity_shift(self, axis_name: str, delta: int) -> None:
        """Track sparsity changes per axis (called by AnchorLearningEngine).

        Records the delta (change in nonzero component count) for diagnostics
        and potential sparsity-aware resonance adjustments.

        Args:
            axis_name: Name of the axis whose sparsity changed.
            delta: Change in nonzero component count (positive = denser, negative = sparser).
        """
        if axis_name not in self._sparsity_log:
            self._sparsity_log[axis_name] = []
        self._sparsity_log[axis_name].append(delta)
        if len(self._sparsity_log[axis_name]) > 100:
            self._sparsity_log[axis_name] = self._sparsity_log[axis_name][-100:]

    def get_sparsity_log(self, axis_name: Optional[str] = None) -> Dict[str, List[int]]:
        """Return sparsity shift log, optionally filtered by axis name."""
        if axis_name:
            return {axis_name: self._sparsity_log.get(axis_name, [])}
        return dict(self._sparsity_log)

    def find_composite_axes(
        self, vector: List[float], threshold: float = 0.3
    ) -> List[Tuple[str, float]]:
        sims = {
            name: self.compute_resonance(vector, name)
            for name in self._semantic_vectors
        }
        result = [(n, s) for n, s in sorted(sims.items(), key=lambda x: -x[1]) if s > threshold]
        return result


__all__ = ["ResonanceEngine", "ResonanceProfile", "ResonanceResult"]
