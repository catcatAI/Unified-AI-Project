# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================
"""
GARDEN TensorSNNCore — PyTorch-accelerated Leaky Integrate-and-Fire spiking neural network.

Implements:
  - Dense relation weight matrix stored as torch.FloatTensor
  - LIF membrane potential integration across multiple timesteps
  - Sparse batch reordering (only active neurons propagate per step)
  - Hormonal modulation (threshold adjustment via cortisol/serotonin scalars)
  - save/load of the full weight matrix

Design:
  The network maintains a square weight matrix W of shape [V, V] where V is the
  number of unique concept keys registered. Each cell W[i,j] represents the
  connection strength from concept i to concept j across all relation types.
  Multiple relation types are layered as additive contributions to the same matrix.

  During forward():
    1. Input concept keys are mapped to indices
    2. Initial activation vector a = [1.0 for input keys, 0.0 for rest]
    3. LIF integration loop:
         potential[t] = potential[t-1] * (1 - leak) + a[t-1] @ W * modulation
         spikes[t]    = (potential[t] > threshold).float()
         a[t]         = spikes[t]
    4. Output: dict mapping concept keys -> cumulative activation score
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy torch import (compatible with Python 3.14 where torch may be absent)
# ---------------------------------------------------------------------------

_torch = None

def _lazy_torch():
    global _torch
    if _torch is None:
        import torch
        import torch.nn.functional as F
        _torch = (torch, F)
    return _torch

# ---------------------------------------------------------------------------
# LIF parameters (defaults)
# ---------------------------------------------------------------------------

DEFAULT_LEAK       = 0.2    # membrane potential leakage per timestep
DEFAULT_THRESHOLD  = 0.35   # spike threshold
DEFAULT_TIMESTEPS  = 6      # number of LIF integration steps
DEFAULT_DECAY      = 0.6    # propagation decay per hop


# ---------------------------------------------------------------------------
# Hormonal modulator (adjusts threshold)
# ---------------------------------------------------------------------------

class HormonalModulator:
    """
    Translates Angela's biological hormone levels into a threshold multiplier for the SNN.
    Cortisol (stress) lowers threshold → more reactive.
    Serotonin (stability) raises threshold → more calm.
    """

    def __init__(self):
        self.hormones: Dict[str, float] = {
            "cortisol":     0.5,
            "serotonin":    0.5,
            "dopamine":     0.5,
            "adrenaline":   0.3,
            "oxytocin":     0.5,
            "noradrenaline": 0.3,
        }

    def set_hormone(self, name: str, value: float) -> None:
        self.hormones[name] = max(0.0, min(1.0, value))

    def get_threshold_multiplier(self) -> float:
        cortisol   = self.hormones.get("cortisol", 0.5)
        serotonin  = self.hormones.get("serotonin", 0.5)
        adrenaline = self.hormones.get("adrenaline", 0.3)
        # Stress hormones lower threshold (more reactive)
        stress = cortisol * 0.4 + adrenaline * 0.2
        # Stability hormones raise threshold
        stability = serotonin * 0.3
        return max(0.4, min(1.6, 1.0 - stress + stability))

    def get_profile_summary(self) -> Dict[str, float]:
        return dict(self.hormones)


# ---------------------------------------------------------------------------
# TensorSNNCore
# ---------------------------------------------------------------------------

class TensorSNNCore:
    """
    PyTorch-based spiking neural network core for GARDEN.

    The weight matrix W is a learnable float32 tensor of shape [V, V].
    All relation types share the same W; add_relation() additively writes into W.
    The forward() method runs multi-step LIF integration and returns activation scores.
    """

    def __init__(
        self,
        leak: float = DEFAULT_LEAK,
        threshold: float = DEFAULT_THRESHOLD,
        timesteps: int = DEFAULT_TIMESTEPS,
        decay: float = DEFAULT_DECAY,
        device: str = "cpu",
    ):
        self.leak = leak
        self.base_threshold = threshold
        self.timesteps = timesteps
        self.decay = decay
        self.device = device

        self.modulator = HormonalModulator()

        # Concept key registry
        self._key_to_idx: Dict[str, int] = {}
        self._idx_to_key: List[str] = []

        # Weight matrix (grows dynamically as new keys are registered)
        self._W: Optional[torch.Tensor] = None   # [V, V] float32

        # Training history
        self.total_steps = 0
        self.total_hebbian_updates = 0

    # ------------------------------------------------------------------
    # Key registry
    # ------------------------------------------------------------------

    def _register_key(self, key: str) -> int:
        if key not in self._key_to_idx:
            idx = len(self._idx_to_key)
            self._key_to_idx[key] = idx
            self._idx_to_key.append(key)
            self._grow_matrix(idx + 1)
        return self._key_to_idx[key]

    def _pre_allocate(self, keys: List[str]) -> None:
        torch, _ = _lazy_torch()
        for key in keys:
            if key not in self._key_to_idx:
                idx = len(self._idx_to_key)
                self._key_to_idx[key] = idx
                self._idx_to_key.append(key)
        V = len(self._idx_to_key)
        self._W = torch.zeros(V, V, dtype=torch.float32)

    def _grow_matrix(self, new_size: int) -> None:
        torch, _ = _lazy_torch()
        if self._W is not None and new_size <= self._W.shape[0]:
            return
        if self._W is None:
            self._W = torch.zeros(new_size, new_size, dtype=torch.float32)
            return
        old_size = self._W.shape[0]
        if new_size <= old_size:
            return
        new_W = torch.zeros(new_size, new_size, dtype=torch.float32)
        new_W[:old_size, :old_size] = self._W
        self._W = new_W

    @property
    def vocab_size(self) -> int:
        return len(self._idx_to_key)

    # ------------------------------------------------------------------
    # Relation management
    # ------------------------------------------------------------------

    def add_relation(
        self, key1: str, key2: str, weight: float = 1.0, bidirectional: bool = True
    ) -> None:
        """Register a directed (or bidirectional) relation between two concept keys."""
        i = self._register_key(key1)
        j = self._register_key(key2)
        self._W[i, j] = min(1.0, self._W[i, j] + weight)
        if bidirectional:
            self._W[j, i] = min(1.0, self._W[j, i] + weight)

    def add_relations_from_entry(self, key: str, relations: Dict[str, List[str]]) -> None:
        """Bulk-load relations from a ConceptEntry.relations dict."""
        weight_map = {
            "synonym": 0.9,
            "antonym": 0.5,
            "mapping": 0.7,
            "analogy": 0.6,
        }
        for rel_type, targets in relations.items():
            w = weight_map.get(rel_type, 0.5)
            for target in targets:
                self.add_relation(key, target, weight=w, bidirectional=True)

    # ------------------------------------------------------------------
    # Forward pass (LIF multi-step)
    # ------------------------------------------------------------------

    def forward(
        self,
        input_keys: List[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, float]:
        """
        Run LIF integration for self.timesteps steps.
        Returns dict of concept_key -> cumulative activation.
        """
        if not input_keys or self._W is None or self.vocab_size == 0:
            return {}

        torch, _ = _lazy_torch()
        V = self.vocab_size
        W = self._W  # [V, V]

        # Build initial activation vector
        a = torch.zeros(V, dtype=torch.float32)
        for key in input_keys:
            idx = self._key_to_idx.get(key)
            if idx is not None:
                a[idx] = 1.0

        if a.sum() == 0.0:
            return {}

        # Hormonal modulation: adjust threshold
        thr_mult = self.modulator.get_threshold_multiplier()
        threshold = max(0.05, self.base_threshold * thr_mult)

        potential  = torch.zeros(V, dtype=torch.float32)
        cumulative = torch.zeros(V, dtype=torch.float32)

        for t in range(self.timesteps):
            # LIF: integrate
            potential = potential * (1.0 - self.leak) + (a @ W)
            # Spike
            spikes = (potential >= threshold).float()
            # Decay for next step
            a = spikes * (self.decay ** t)
            # Accumulate
            cumulative += spikes

        self.total_steps += 1

        # Map back to keys
        result: Dict[str, float] = {}
        nonzero = cumulative.nonzero(as_tuple=False).squeeze(-1)
        for idx in nonzero.tolist():
            key = self._idx_to_key[idx]
            result[key] = float(cumulative[idx]) / self.timesteps
        return result

    # ------------------------------------------------------------------
    # Hebbian training step
    # ------------------------------------------------------------------

    def hebbian_update(
        self,
        input_keys: List[str],
        target_keys: List[str],
        lr: float = 0.05,
        target_strength: float = 0.8,
    ) -> float:
        """
        Hebbian weight update: strengthen connections between co-active input and target keys.
        Returns total weight delta applied.
        """
        if not input_keys or not target_keys:
            return 0.0

        delta_total = 0.0
        for src in input_keys:
            i = self._register_key(src)
            for tgt in target_keys:
                j = self._register_key(tgt)
                old_w = float(self._W[i, j])
                # Oja's rule variant: Δw = lr * (target - w)
                delta = lr * (target_strength - old_w)
                new_w = max(0.0, min(1.0, old_w + delta))
                self._W[i, j] = new_w
                self._W[j, i] = new_w  # symmetric
                delta_total += abs(delta)

        self.total_hebbian_updates += 1
        return delta_total

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str) -> None:
        """Save weight matrix and key registry to a .pt checkpoint."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        state = {
            "W": self._W,
            "key_to_idx": self._key_to_idx,
            "idx_to_key": self._idx_to_key,
            "leak": self.leak,
            "base_threshold": self.base_threshold,
            "timesteps": self.timesteps,
            "decay": self.decay,
            "total_steps": self.total_steps,
            "total_hebbian_updates": self.total_hebbian_updates,
        }
        torch, _ = _lazy_torch()
        torch.save(state, path)
        logger.info("GARDEN SNN: saved checkpoint to %s (V=%d)", path, self.vocab_size)

    def load(self, path: str) -> None:
        """Load weight matrix and key registry from a .pt checkpoint."""
        torch, _ = _lazy_torch()
        state = torch.load(path, map_location="cpu", weights_only=True)
        self._W                    = state["W"]
        self._key_to_idx           = state["key_to_idx"]
        self._idx_to_key           = state["idx_to_key"]
        self.leak                  = state.get("leak", DEFAULT_LEAK)
        self.base_threshold        = state.get("base_threshold", DEFAULT_THRESHOLD)
        self.timesteps             = state.get("timesteps", DEFAULT_TIMESTEPS)
        self.decay                 = state.get("decay", DEFAULT_DECAY)
        self.total_steps           = state.get("total_steps", 0)
        self.total_hebbian_updates = state.get("total_hebbian_updates", 0)
        logger.info("GARDEN SNN: loaded checkpoint from %s (V=%d)", path, self.vocab_size)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        density = 0.0
        if self._W is not None and self._W.numel() > 0:
            density = float((self._W > 0).float().mean())
        return {
            "vocab_size": self.vocab_size,
            "weight_matrix_shape": list(self._W.shape) if self._W is not None else [],
            "matrix_density": round(density, 4),
            "matrix_memory_bytes": (self._W.numel() * 4) if self._W is not None else 0,
            "leak": self.leak,
            "threshold": self.base_threshold,
            "timesteps": self.timesteps,
            "total_steps": self.total_steps,
            "total_hebbian_updates": self.total_hebbian_updates,
            "hormones": self.modulator.get_profile_summary(),
        }
