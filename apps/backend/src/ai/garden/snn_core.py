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

from core.system.config.magic_numbers import timeout_value

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dual backend: torch (when available) → numpy (fallback)
# Cross-platform compatible: works on Win/Linux/macOS, CPU/GPU.
# ---------------------------------------------------------------------------

_xp: Any = None  # array module reference (torch or numpy)
_is_torch: bool = False  # True if using torch


def _check_torch_subprocess() -> bool:
    """Check if torch can be imported, with a strict timeout.

    On Windows/Python 3.14, torch import hangs indefinitely in-process,
    so we probe in a short-lived subprocess that can be killed cleanly.
    On Linux (non-3.14) an in-process import is fast and reliable — the
    subprocess probe spuriously fails under heavy parallel load (e.g. a
    full pytest run), which would silently downgrade SNN to the numpy
    backend and make torch-format checkpoints unloadable.
    """
    import platform
    import sys

    py_ver = sys.version_info
    if sys.platform.startswith("linux") and not (py_ver.major == 3 and py_ver.minor >= 14):
        try:
            import torch  # noqa: F401

            return True
        except ImportError:
            return False

    import subprocess

    try:
        result = subprocess.run(
            [sys.executable, "-c", "import torch; print('ok')"],
            capture_output=True,
            timeout=timeout_value("garden.torch_check", 10),
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        logger.debug("torch availability subprocess check failed", exc_info=True)
        return False


def _get_backend():
    """Return (module, is_torch) — prefers torch, falls back to numpy."""
    global _xp, _is_torch
    if _xp is None:
        from core.system.config.magic_numbers import compute_log_fallback

        if _check_torch_subprocess():
            try:
                import torch

                _xp = torch
                _is_torch = True
                logger.debug("SNN using torch backend")
            except ImportError:
                if compute_log_fallback():
                    logger.info("torch not installed; SNN using numpy backend")
                _xp = np
                _is_torch = False
        else:
            if compute_log_fallback():
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
    if hasattr(arr, "float"):
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
    if hasattr(arr, "numel"):
        return arr.numel()
    return arr.size


def _as_array(lst):
    """Convert a Python list of ints to a backend index array (torch or numpy)."""
    xp, _ = _get_backend()
    if _is_torch:
        return xp.tensor(lst, dtype=xp.long)
    return np.asarray(lst, dtype=np.int64)


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
    """Load SNN checkpoint — handles both numpy and torch formats.

    Auto-detects format: if .npy file exists, load as numpy regardless of
    current backend (training may have used torch, inference may use numpy).
    """
    npy_path = path if path.endswith(".npy") else path + ".npy"
    json_path = path.rsplit(".", 1)[0] + ".json"

    # Prefer numpy format if .npy exists (cross-backend compatible)
    if os.path.exists(npy_path):
        W = np.load(npy_path)
        meta = {}
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        meta["W"] = W
        return meta

    # Fall back to torch format
    xp, is_torch = _get_backend()
    if is_torch:
        return xp.load(path, map_location="cpu", weights_only=True)

    # Neither format found
    raise FileNotFoundError(f"No checkpoint found at {path} (tried {npy_path} and torch format)")


# ---------------------------------------------------------------------------
# LIF parameters (defaults)
# ---------------------------------------------------------------------------

DEFAULT_LEAK = 0.2  # membrane potential leakage per timestep
DEFAULT_THRESHOLD = 0.30  # spike threshold (balanced: fires on strong connections only)
DEFAULT_TIMESTEPS = 6  # number of LIF integration steps
DEFAULT_DECAY = 0.6  # propagation decay per hop


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
            "cortisol": 0.5,
            "serotonin": 0.5,
            "dopamine": 0.5,
            "adrenaline": 0.3,
            "oxytocin": 0.5,
            "noradrenaline": 0.3,
        }

    def set_hormone(self, name: str, value: float) -> None:
        self.hormones[name] = max(0.0, min(1.0, value))

    def get_threshold_multiplier(self) -> float:
        cortisol = self.hormones.get("cortisol", 0.5)
        serotonin = self.hormones.get("serotonin", 0.5)
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
        max_vocab: int = 0,
        connection_budget: int = 0,
    ):
        self.leak = leak
        self.base_threshold = threshold
        self.timesteps = timesteps
        self.decay = decay
        self.device = device

        from core.system.config.magic_numbers import compute_int, limit_value, model_sizing_config

        # Use compute config (profile-aware) unless explicit values passed.
        # Falls back to dynamic model sizing config (conservative/extended).
        sizing = model_sizing_config()
        self.max_vocab = max_vocab if max_vocab > 0 else compute_int("garden_snn", "max_vocab", sizing["max_vocab"])
        self.connection_budget = (
            connection_budget
            if connection_budget > 0
            else compute_int("garden_snn", "connection_budget", sizing["connection_budget"])
        )
        logger.info(
            "SNN sizing: max_vocab=%d, connection_budget=%d (%.1fMB matrix)",
            self.max_vocab,
            self.connection_budget,
            self.max_vocab * self.max_vocab * 4 / 1024 / 1024,
        )

        self.modulator = HormonalModulator()

        # Concept key registry
        self._key_to_idx: Dict[str, int] = {}
        self._idx_to_key: List[str] = []

        # Weight matrix (grows dynamically as new keys are registered)
        self._W: Optional[Any] = None  # [V, V] float32 (torch.Tensor or np.ndarray)

        # LRU bookkeeping for eviction under the memory budget.
        self._last_used: Dict[int, int] = {}
        self._clock: int = 0

        # Training history
        self.total_steps = 0
        self.total_hebbian_updates = 0
        self._total_active = 0  # total active neurons across all forward() calls
        self.total_evictions = 0

    # ------------------------------------------------------------------
    # Key registry
    # ------------------------------------------------------------------

    def _register_key(self, key: str) -> int:
        if key in self._key_to_idx:
            self._touch(self._key_to_idx[key])
            return self._key_to_idx[key]
        # If at (or would exceed) the memory budget, evict a BATCH of the
        # least-recently-used neurons in a single matrix compaction, then
        # register the new key. Training still ingests the current sample — we
        # never truncate the input dataset; we only shed the least-useful
        # neurons from an already-trained matrix to keep V**2 memory bounded.
        if self.max_vocab > 0 and len(self._idx_to_key) >= self.max_vocab:
            self._evict_batch()
        idx = len(self._idx_to_key)
        self._key_to_idx[key] = idx
        self._idx_to_key.append(key)
        self._grow_matrix(idx + 1)
        self._touch(idx)
        return idx

    def _touch(self, idx: int) -> None:
        self._last_used[idx] = self._clock
        self._clock += 1

    def _evict_batch(self) -> None:
        """Evict a batch of the least-recently-used neurons in one compaction.

        Evicts down to ~90% of ``max_vocab`` so the next many registrations are
        cheap (amortized O(V**2) total instead of O(V**3) from per-key eviction).
        """
        if len(self._idx_to_key) <= 1:
            return
        target = max(1, int(self.max_vocab * 0.9))
        if len(self._idx_to_key) <= target:
            return
        # LRU indices: smallest _last_used first.
        order = sorted(range(len(self._idx_to_key)), key=lambda i: self._last_used.get(i, 0))
        evict_n = len(self._idx_to_key) - target
        evicted = set(order[:evict_n])
        keep = [i for i in range(len(self._idx_to_key)) if i not in evicted]
        self._compact(keep)
        self.total_evictions += evict_n

    def _compact(self, keep_indices: List[int]) -> None:
        """Rebuild the index maps and weight matrix keeping only ``keep_indices``.

        This is the inverse of truncation: instead of dropping input data, we
        drop the *least useful neurons* from an already-trained matrix so the
        memory footprint stays under budget while still having trained on all
        samples.

        The new matrix is allocated at ``max_vocab`` capacity (when a budget is
        set) rather than exactly ``len(keep)``, so subsequent registrations fill
        existing rows instead of re-growing + copying the whole matrix each time.

        The sub-matrix copy is done with vectorized advanced indexing (a single
        backend op), NOT a Python double loop, so compaction stays O(V**2) in C
        rather than O(V**2) in the interpreter.
        """
        if self._W is None:
            self._reindex(keep_indices)
            return
        old_W = self._W
        new_size = len(keep_indices)
        cap = self.max_vocab if self.max_vocab > 0 else new_size
        alloc = max(new_size, cap, int(old_W.shape[0]))
        idx_arr = _as_array(keep_indices)
        # Vectorized sub-matrix extraction: W[keep, keep]. Use the backend's
        # native index_select (torch) / ix_ (numpy) — a SINGLE op — because
        # double advanced indexing (W[idx][:, idx]) materializes a huge
        # intermediate and hangs on the torch backend.
        if _is_torch:
            sub = old_W.index_select(0, idx_arr).index_select(1, idx_arr)
        else:
            sub = old_W[np.ix_(idx_arr, idx_arr)]
        # Allocate at the budget capacity (when set) so subsequent registrations
        # fill existing rows instead of re-copying the whole matrix each time.
        # The live region is new_size x new_size; forward() slices to it.
        new_W = _zeros((alloc, alloc))
        new_W[:new_size, :new_size] = sub
        self._W = new_W
        self._reindex(keep_indices)

    def _reindex(self, keep_indices: List[int]) -> None:
        new_key_to_idx: Dict[str, int] = {}
        new_idx_to_key: List[str] = []
        new_last_used: Dict[int, int] = {}
        for new_i, old_i in enumerate(keep_indices):
            key = self._idx_to_key[old_i]
            new_key_to_idx[key] = new_i
            new_idx_to_key.append(key)
            if old_i in self._last_used:
                new_last_used[new_i] = self._last_used[old_i]
        self._key_to_idx = new_key_to_idx
        self._idx_to_key = new_idx_to_key
        self._last_used = new_last_used

    def _pre_allocate(self, keys: List[str]) -> None:
        for key in keys:
            if key not in self._key_to_idx:
                idx = len(self._idx_to_key)
                self._key_to_idx[key] = idx
                self._idx_to_key.append(key)
        V = len(self._idx_to_key)
        self._grow_matrix(V)

    def _grow_matrix(self, new_size: int) -> None:
        if self._W is not None and new_size <= self._W.shape[0]:
            return
        if self._W is None:
            self._W = _zeros((new_size, new_size))
            return
        old_size = self._W.shape[0]
        if new_size <= old_size:
            return
        # Amortized growth: over-allocate (doubling) so the total copy cost over
        # V registrations is O(V**2) instead of O(V**3). The live region is the
        # first ``vocab_size`` rows/cols; forward() slices to that region.
        target = max(new_size, int(old_size * 2))
        new_W = _zeros((target, target))
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
        self._touch(i)
        self._touch(j)
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
        input_keys: Dict[str, float],
        context: Optional[Dict[str, Any]] = None,
        top_k_ratio: float = 0.05,
    ) -> Dict[str, float]:
        """Run LIF integration with top-k competition.

        input_keys is a dict of key → confidence (from VectorDictionary.encode()).
        Each key activates its neuron at the given confidence level instead of
        a hard binary 1.0.  Low-confidence matches contribute less to the SNN
        dynamics, letting learned weights override weak signals.

        Returns dict of concept_key -> cumulative activation.
        """
        if not input_keys or self._W is None or self.vocab_size == 0:
            return {}

        V = self.vocab_size
        W = self._W[:V, :V]

        a = _zeros(V)
        for key, conf in input_keys.items():
            idx = self._key_to_idx.get(key)
            if idx is not None:
                a[idx] = max(0.0, min(1.0, conf))
                self._touch(idx)

        # NeuralBridge injection: the context slot was declared but never read.
        # StateMatrix axis values (mapped to concept keys, all in [0,1]) are
        # merged into the initial activations — a minimal-translation direct
        # numeric link (no vector projection). Skip keys outside the vocab.
        neural_state = (context or {}).get("neural_state")
        if neural_state:
            for key, conf in neural_state.items():
                idx = self._key_to_idx.get(key)
                if idx is not None and a[idx] == 0:
                    a[idx] = max(0.0, min(1.0, conf))
                    self._touch(idx)

        if a.sum() == 0.0:
            return {}

        thr_mult = self.modulator.get_threshold_multiplier()
        threshold = max(0.01, self.base_threshold * thr_mult)

        potential = _zeros(V)
        cumulative = _zeros(V)
        total_active = 0
        max_active = max(1, int(V * top_k_ratio))

        for t in range(self.timesteps):
            active_idx = _nonzero_indices(a)
            n_active = len(active_idx)
            if n_active > 0:
                _use_torch = hasattr(W[active_idx], "sum") and hasattr(
                    W[active_idx].sum, "dim"
                )
                if _use_torch:
                    incoming = W[active_idx].sum(dim=0)
                else:
                    incoming = W[active_idx].sum(axis=0)
                potential = potential * (1.0 - self.leak) + incoming
            else:
                potential = potential * (1.0 - self.leak)

            # Top-k competition
            if _numel(potential) > max_active:
                sorted_idx = np.argpartition(potential, -max_active)[-max_active:]
            else:
                sorted_idx = _nonzero_indices(potential)
            spike_mask = _float(potential >= threshold)
            topk_mask = _zeros(V)
            if hasattr(sorted_idx, "tolist"):
                topk_mask[sorted_idx.tolist()] = 1.0
            else:
                topk_mask[sorted_idx] = 1.0
            spikes = spike_mask * topk_mask

            # Reset potential for spiking neurons (refractory period).
            # Without this, strongly-coupled pairs enter runaway oscillation
            # and prevent 2+ hop propagation.
            spike_idx = _nonzero_indices(spikes)
            if len(spike_idx) > 0:
                potential[spike_idx] = 0.0

            a = spikes * (self.decay ** t)
            cumulative += spikes
            total_active += n_active

        self.total_steps += 1
        self._total_active += total_active

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
        input_keys: Dict[str, float],
        target_keys: Dict[str, float],
        lr: float = 0.05,
        target_strength: float = 0.35,
        weight_decay: float = 0.002,
    ) -> float:
        """Hebbian weight update with Oja's rule + targeted row decay.

        input_keys and target_keys are Dict[str, float] from VectorDictionary.encode().
        The confidence score gates the learning rate: low-confidence matches
        contribute less to weight changes, reducing noise from fuzzy matches.

        Oja's rule drives connections toward target_strength.
        After updating, applies decay ONLY to rows that were modified
        (O(nnz_per_row) instead of O(V^2)).

        Vectorized over the (|input| × |output|) block: the weight patch is
        read once, updated in bulk, and written back — instead of a Python
        double loop that crosses the torch/numpy scalar boundary once per
        element (the dominant cost in batch training at V≈8k).

        Returns total weight delta applied.
        """
        if not input_keys or not target_keys:
            return 0.0

        # Register any unseen keys first (preserves legacy auto-registration),
        # then map to row/col indices, vectorized.
        for k in input_keys:
            self._register_key(k)
        for k in target_keys:
            self._register_key(k)
        src_items = [(k, c) for k, c in input_keys.items() if k in self._key_to_idx]
        tgt_items = [(k, c) for k, c in target_keys.items() if k in self._key_to_idx]
        if not src_items or not tgt_items:
            return 0.0
        src_idx = [self._key_to_idx[k] for k, _ in src_items]
        tgt_idx = [self._key_to_idx[k] for k, _ in tgt_items]
        src_conf = [c for _, c in src_items]
        tgt_conf = [c for _, c in tgt_items]

        # Build the (len(src) × len(tgt)) confidence-gate matrix.
        # gate[i, j] = conf_i * conf_j
        xp = _zeros  # backend-agnostic helper; use numpy/torch arrays below
        import numpy as np

        is_torch = self._W.__class__.__module__.startswith("torch")
        if is_torch:
            xp, _ = _get_backend()
            src_t = xp.as_tensor(src_idx, dtype=xp.int64)
            tgt_t = xp.as_tensor(tgt_idx, dtype=xp.int64)
            src_a = self._W.new_tensor(src_conf, dtype=self._W.dtype)
            tgt_a = self._W.new_tensor(tgt_conf, dtype=self._W.dtype)
            gate = src_a.unsqueeze(1) * tgt_a.unsqueeze(0)  # [S, T]
            # index_select rows then columns: guaranteed [S, T].
            old_patch = self._W.index_select(0, src_t).index_select(1, tgt_t)
            delta_patch = lr * gate * (target_strength - old_patch)
            new_patch = old_patch + delta_patch
            new_patch = new_patch.clamp(min=0.0, max=1.0)
            # Cartesian-pair write-back: broadcast src rows × tgt cols.
            rr, cc = xp.meshgrid(src_t, tgt_t, indexing="ij")
            self._W[rr, cc] = new_patch
            self._W[cc, rr] = new_patch
            delta_total = float(delta_patch.abs().sum())
            touched_rows = set(src_idx) | set(tgt_idx)
        else:
            gate = (
                np.asarray(src_conf, dtype=np.float32)[:, None]
                * np.asarray(tgt_conf, dtype=np.float32)[None, :]
            )
            old_patch = self._W[np.ix_(src_idx, tgt_idx)]
            delta_patch = lr * gate * (target_strength - old_patch)
            new_patch = np.clip(old_patch + delta_patch, 0.0, 1.0)
            self._W[np.ix_(src_idx, tgt_idx)] = new_patch
            self._W[np.ix_(tgt_idx, src_idx)] = new_patch
            delta_total = float(np.abs(delta_patch).sum())
            touched_rows = set(src_idx) | set(tgt_idx)

        for i in src_idx:
            self._touch(i)
        for j in tgt_idx:
            self._touch(j)

        # Targeted decay: only decay rows that were touched (O(nnz_per_row))
        if weight_decay > 0:
            for row in touched_rows:
                row_data = self._W[row, :]
                mask = row_data > 0.0
                row_data[mask] = row_data[mask] * (1.0 - weight_decay)
                # Prune near-zero in this row only
                prune = row_data < 0.01
                row_data[prune] = 0.0

        self.total_hebbian_updates += 1
        return delta_total

    def apply_decay(self, weight_decay: float = 0.002) -> None:
        """Apply weight decay + pruning to ALL non-zero weights. O(nnz).

        Call periodically (e.g., every 1000 samples) for global forgetting.
        """
        if weight_decay <= 0 or self._W is None:
            return
        V = self.vocab_size
        live = self._W[:V, :V]
        mask = live > 0.0
        live[mask] = live[mask] * (1.0 - weight_decay)
        prune_mask = live < 0.01
        live[prune_mask] = 0.0

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
        self._W = state["W"]
        self._key_to_idx = state["key_to_idx"]
        self._idx_to_key = state["idx_to_key"]
        self.leak = float(state.get("leak", DEFAULT_LEAK))
        self.base_threshold = float(state.get("base_threshold", DEFAULT_THRESHOLD))
        self.timesteps = int(state.get("timesteps", DEFAULT_TIMESTEPS))
        self.decay = float(state.get("decay", DEFAULT_DECAY))
        self.total_steps = int(state.get("total_steps", 0))
        self.total_hebbian_updates = int(state.get("total_hebbian_updates", 0))
        logger.info("GARDEN SNN: loaded checkpoint from %s (V=%d)", path, self.vocab_size)

    def reset_for_retrain(self) -> None:
        """Reset weight matrix to sparse random initialization for retraining.

        Use when the SNN has become saturated and produces identical outputs.
        Preserves key registry but reinitializes weights.
        """
        if self._W is None:
            return
        V = self.vocab_size
        xp, is_torch = _get_backend()
        if is_torch:
            self._W = xp.rand(V, V, dtype=xp.float32) * 0.3
            self._W = (self._W + self._W.T) / 2.0
            mask = xp.rand(V, V) > 0.05
            self._W[mask] = 0.0
        else:
            self._W = np.random.rand(V, V).astype(np.float32) * 0.3
            self._W = (self._W + self._W.T) / 2.0
            mask = np.random.rand(V, V) > 0.05
            self._W[mask] = 0.0
        self.total_steps = 0
        self.total_hebbian_updates = 0
        self._total_active = 0
        nnz = int(np.count_nonzero(self._W)) if not is_torch else int((self._W != 0).sum())
        logger.info(
            "GARDEN SNN: reset weights for retrain (V=%d, nnz=%d, density=%.2f%%)",
            V, nnz, nnz / (V * V) * 100,
        )

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        density = 0.0
        mean_weight = 0.0
        if self._W is not None and _numel(self._W) > 0:
            live = self._W[: self.vocab_size, : self.vocab_size]
            density = float(_float(live > 0).mean())
            nnz = int(_float(live > 0).sum())
            if nnz > 0:
                mean_weight = float(_float(live[live > 0]).mean())
        total_possible = self.vocab_size * self.timesteps * max(1, self.total_steps)
        sparsity_ratio = (
            round(1.0 - (self._total_active / max(1, total_possible)), 4)
            if total_possible > 0
            else 0.0
        )
        live_W = self.vocab_size
        if self._W is None:
            live_shape: List[int] = []
        else:
            live_shape = [live_W, live_W]
        return {
            "vocab_size": self.vocab_size,
            "max_vocab": self.max_vocab,
            "weight_matrix_shape": live_shape,
            "matrix_density": round(density, 4),
            "mean_weight": round(mean_weight, 4),
            "matrix_memory_bytes": (live_W * live_W * 4),
            "leak": self.leak,
            "threshold": self.base_threshold,
            "timesteps": self.timesteps,
            "total_steps": self.total_steps,
            "total_hebbian_updates": self.total_hebbian_updates,
            "total_evictions": self.total_evictions,
            "hormones": self.modulator.get_profile_summary(),
            "sparsity_ratio": sparsity_ratio,
            "computation_saved": self._total_active,
            "computation_possible": total_possible,
        }
