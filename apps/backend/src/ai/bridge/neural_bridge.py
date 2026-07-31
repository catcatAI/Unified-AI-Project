# =============================================================================
# ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
# =============================================================================
"""
NeuralBridge — 最少轉譯直接連結 StateMatrix ↔ GARDEN/ED3N SNN.

Core insight from the neural-representation research:
  - StateMatrix4D stores axis values as ``{key: float∈[0,1]}`` (a symbolic
    numeric table, NOT a vector space).
  - GARDEN/ED3N SNN forward() outputs ``{concept_key: activation∈[0,1]}``.
  Both are "key → [0,1] value" dictionaries. Because both sides already share
  the [0,1] numeric domain, the ONLY required translation is a symbolic
  key-name mapping between StateMatrix axis keys and neural concept keys —
  no vector projection, no re-embedding, no numeric scaling.

Connection points:
  Forward  (StateMatrix → SNN): axis values mapped to concept keys are
      injected as SNN input activations via the ``neural_state`` context slot
      (GARDEN TensorSNNCore.forward() declares ``context`` but never reads it —
      this bridge activates that designed-but-unused injection point).
  Writeback (SNN → StateMatrix): SNN output activations mapped back to axis
      keys update the corresponding dimension values, closing the loop.

The bridge is gated by the compute-config switch ``neural_bridge``:
  - off (default): the neural connection is inert; existing text pipeline runs
    unchanged.
  - on: the chat pipeline may route through the neural connection, bypassing
    the LLM text-based transfer when the switch is enabled.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from core.system.config.magic_numbers import compute_bool

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Switch
# ---------------------------------------------------------------------------

_BRIDGE_FEATURE = "neural_bridge"


def neural_bridge_enabled() -> bool:
    """Return True when the neural bridge switch is enabled (compute config)."""
    try:
        return compute_bool(_BRIDGE_FEATURE, False)
    except Exception as e:  # config must never crash the bridge
        logger.warning("neural_bridge switch check failed: %s", e, exc_info=True)
        return False


# ---------------------------------------------------------------------------
# Static symbolic mapping: StateMatrix (axis, key) ↔ neural concept key
# ---------------------------------------------------------------------------
# These are the minimal-translation bridges. Only entries with a real neural
# concept key are listed — unmapped state keys stay in the symbolic table and
# do not enter the neural network (no forced projection of unrelated state).

_STATE_TO_GARDEN: Dict[Tuple[str, str], str] = {
    ("alpha", "energy"): "sci_energy",
    ("gamma", "happiness"): "emo_happy",
    ("gamma", "sadness"): "emo_sadness",
    ("gamma", "anger"): "emo_anger",
    ("gamma", "fear"): "emo_fear",
    ("gamma", "surprise"): "emo_surprise",
    ("gamma", "disgust"): "emo_disgust",
    ("delta", "attention"): "c2",
    ("beta", "focus"): "c1",
}

_GARDEN_TO_STATE: Dict[str, Tuple[str, str]] = {
    v: k for k, v in _STATE_TO_GARDEN.items()
}


def state_to_neural_inputs(state_matrix: Any) -> Dict[str, float]:
    """Map StateMatrix axis values to neural concept-key activations.

    Args:
        state_matrix: StateMatrix4D (or any object exposing ``<axis>.values``
            dicts for alpha/beta/gamma/delta).

    Returns:
        Dict of neural concept key → value in [0,1]. Only keys that exist in
        the static mapping are exported; values are clamped to [0,1] on the
        way through (matching the neural domain exactly).
    """
    result: Dict[str, float] = {}
    if state_matrix is None:
        return result
    for (axis, key), neural_key in _STATE_TO_GARDEN.items():
        dim = getattr(state_matrix, axis, None)
        if dim is None:
            continue
        values = getattr(dim, "values", None)
        if not isinstance(values, dict):
            continue
        val = values.get(key)
        if val is None:
            continue
        result[neural_key] = max(0.0, min(1.0, float(val)))
    return result


def neural_outputs_to_state_updates(
    neural_output: Optional[Dict[str, float]],
) -> Dict[str, Dict[str, float]]:
    """Map SNN output activations back to StateMatrix axis-key updates.

    Args:
        neural_output: Dict of concept key → activation in [0,1] from an SNN
            forward() call.

    Returns:
        Dict of axis name → {key: value} updates, ready to apply via the
        dimension ``update(**kwargs)`` API. Values clamped to [0,1].
    """
    updates: Dict[str, Dict[str, float]] = {}
    if not neural_output:
        return updates
    for concept_key, activation in neural_output.items():
        axis_key = _GARDEN_TO_STATE.get(concept_key)
        if axis_key is None:
            continue
        axis, key = axis_key
        updates.setdefault(axis, {})[key] = max(0.0, min(1.0, float(activation)))
    return updates


def apply_state_updates(state_matrix: Any, updates: Dict[str, Dict[str, float]]) -> int:
    """Apply axis-key updates to the StateMatrix via its dimension API.

    Uses ``<axis>.update(**{key: value})`` — the same public API used by
    ``update_gamma`` etc. — so the values stay clamped and the timestamp
    refresh behaviour is preserved. Returns the number of keys applied.
    """
    if state_matrix is None:
        return 0
    applied = 0
    for axis, values in updates.items():
        dim = getattr(state_matrix, axis, None)
        if dim is None or not hasattr(dim, "update"):
            continue
        try:
            dim.update(**values)
            applied += len(values)
        except Exception as e:
            logger.warning(
                "NeuralBridge writeback to axis '%s' failed: %s", axis, e, exc_info=True
            )
    return applied


def build_neural_context(
    context: Optional[Dict[str, Any]], state_matrix: Any
) -> Dict[str, Any]:
    """Return a context copy augmented with the ``neural_state`` injection slot.

    The GARDEN SNN forward() reads ``context.get("neural_state")`` (a dict of
    concept key → [0,1]) and merges it into its input activations. This is the
    StateMatrix → SNN direction of the bridge.
    """
    ctx = dict(context) if context else {}
    neural_inputs = state_to_neural_inputs(state_matrix)
    if neural_inputs:
        ctx["neural_state"] = neural_inputs
    return ctx
