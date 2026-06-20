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

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dual backend: torch (when available) → numpy (fallback)
# Cross-platform compatible: works on Win/Linux/macOS, CPU/GPU.
# ---------------------------------------------------------------------------

_xp: Any = None          # array module reference (torch or numpy)
_is_torch: bool = False  # True if using torch


def _check_torch_subprocess() -> bool:
    """Check if torch can be imported by spawning a subprocess with a strict timeout.
    
    On Windows/Python 3.14, torch import hangs indefinitely in-process,
    so we probe in a short-lived subprocess that can be killed cleanly.
    """
    import subprocess
    import sys
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import torch; print('ok')"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False


def _get_backend():
    """Return (module, is_torch) — prefers torch, falls back to numpy."""
    global _xp, _is_torch
    if _xp is None:
        if _check_torch_subprocess():
            try:
                import torch
                _xp = torch
                _is_torch = True
                logger.debug("SNN using torch backend")
            except ImportError:
                logger.info("torch not installed; SNN using numpy backend")
                _xp = np
                _is_torch = False
        else:
            logger.info("torch unavailable (subprocess check failed); SNN using numpy backend")
            _xp = np
            _is_torch = False
    return _xp, _is_torch


# -- Backend helper functions (abstract torch/numpy API differences) ----------

def _zeros(shape):
    xp, is_torch = _get_backend()
    if is_torch:
        return xp.zeros(shape, dtype=xp.float32)
    return xp.zeros(shape, dtype=np.float32)


def _float(arr):
    """Convert boolean/integer array to float32."""
    if hasattr(arr, 'float'):
        return arr.float()
    return arr.astype(np.float32)


def _nonzero_indices(arr):
    """Return 1-D indices of nonzero elements.

    Uses ``_get_backend()`` to distinguish torch (which supports
    ``as_tuple``) from numpy (which does not in newer versions).
    """
    xp, is_torch = _get_backend()
    if is_torch:
        return arr.nonzero(as_tuple=False).squeeze(-1)
    return np.nonzero(arr)[0]


def _numel(arr):
    if hasattr(arr, 'numel'):
        return arr.numel()
    return arr.size


def _save_checkpoint(path: str, state: dict) -> None:
    """Save SNN checkpoint — handles both numpy and torch tensors."""
    xp, is_torch = _get_backend()
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    if is_torch:
        xp.save(state, path)
    else:
        W = state.pop("W")
        np.save(path, W)
        json_path = path.rsplit(".", 1)[0] + ".json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)


def _load_checkpoint(path: str) -> dict:
    """Load SNN checkpoint — handles both numpy and torch formats."""
    xp, is_torch = _get_backend()
    if is_torch:
        return xp.load(path, map_location="cpu", weights_only=True)
    npy_path = path if path.endswith(".npy") else path + ".npy"
    W = np.load(npy_path)
    json_path = path.rsplit(".", 1)[0] + ".json"
    with open(json_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    meta["W"] = W
    return meta

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
        self._W: Optional[Any] = None   # [V, V] float32 (torch.Tensor or np.ndarray)

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
        for key in keys:
            if key not in self._key_to_idx:
                idx = len(self._idx_to_key)
                self._key_to_idx[key] = idx
                self._idx_to_key.append(key)
        V = len(self._idx_to_key)
        self._W = _zeros((V, V))

    def _grow_matrix(self, new_size: int) -> None:
        if self._W is not None and new_size <= self._W.shape[0]:
            return
        if self._W is None:
            self._W = _zeros((new_size, new_size))
            return
        old_size = self._W.shape[0]
        if new_size <= old_size:
            return
        new_W = _zeros((new_size, new_size))
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

        V = self.vocab_size
        W = self._W  # [V, V]

        # Build initial activation vector
        a = _zeros(V)
        for key in input_keys:
            idx = self._key_to_idx.get(key)
            if idx is not None:
                a[idx] = 1.0

        if a.sum() == 0.0:
            return {}

        # Hormonal modulation: adjust threshold
        thr_mult = self.modulator.get_threshold_multiplier()
        threshold = max(0.05, self.base_threshold * thr_mult)

        potential  = _zeros(V)
        cumulative = _zeros(V)

        for t in range(self.timesteps):
            # LIF: integrate
            potential = potential * (1.0 - self.leak) + (a @ W)
            # Spike
            spikes = _float(potential >= threshold)
            # Decay for next step
            a = spikes * (self.decay ** t)
            # Accumulate
            cumulative += spikes

        self.total_steps += 1

        # Map back to keys
        result: Dict[str, float] = {}
        for idx in _nonzero_indices(cumulative).tolist():
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
        """Save weight matrix and key registry to a checkpoint."""
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
        _save_checkpoint(path, state)
        logger.info("GARDEN SNN: saved checkpoint to %s (V=%d)", path, self.vocab_size)

    def load(self, path: str) -> None:
        """Load weight matrix and key registry from a checkpoint."""
        state = _load_checkpoint(path)
        self._W                    = state["W"]
        self._key_to_idx           = state["key_to_idx"]
        self._idx_to_key           = state["idx_to_key"]
        self.leak                  = float(state.get("leak", DEFAULT_LEAK))
        self.base_threshold        = float(state.get("base_threshold", DEFAULT_THRESHOLD))
        self.timesteps             = int(state.get("timesteps", DEFAULT_TIMESTEPS))
        self.decay                 = float(state.get("decay", DEFAULT_DECAY))
        self.total_steps           = int(state.get("total_steps", 0))
        self.total_hebbian_updates = int(state.get("total_hebbian_updates", 0))
        logger.info("GARDEN SNN: loaded checkpoint from %s (V=%d)", path, self.vocab_size)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        density = 0.0
        if self._W is not None and _numel(self._W) > 0:
            density = float(_float(self._W > 0).mean())
        return {
            "vocab_size": self.vocab_size,
            "weight_matrix_shape": list(self._W.shape) if self._W is not None else [],
            "matrix_density": round(density, 4),
            "matrix_memory_bytes": (_numel(self._W) * 4) if self._W is not None else 0,
            "leak": self.leak,
            "threshold": self.base_threshold,
            "timesteps": self.timesteps,
            "total_steps": self.total_steps,
            "total_hebbian_updates": self.total_hebbian_updates,
            "hormones": self.modulator.get_profile_summary(),
        }
