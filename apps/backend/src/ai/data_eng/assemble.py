# =============================================================================
# ANGELA-MATRIX: [L3] [αβ] [B] [L2]
# =============================================================================
"""
data_eng.assemble — single anchored-decode reassembly policy.

Consolidates the two independent "anchored_decode" implementations:
  * ``GARDEN Engineering._anchored_decode`` (garden_engine.py)
  * the anchor-first + network-keys philosophy in ED3N output_anchor.py

Both follow the same anchor-first, then dedup SNN keys, then the decoder
reassembly.  This module provides the *selection* policy (pure, stateless) so
the two engine decoders share one slot-budget + combine rule.  The engines
remain responsible for invoking their own dictionary.decode.
"""

from __future__ import annotations

from typing import Dict, List, Optional

__all__ = [
    "decode_slot_budget",
    "select_anchored_keys",
]

# Minimum SNN activation to enter the response (1 spike in ~6 timesteps).
_DECODE_GATE = 0.15


def decode_slot_budget(n_input: int) -> tuple[int, int]:
    """Return (anchor_slots, snn_slots) for an input of *n_input* keys.

    Single source of truth for both anchored-decodes:
      short (<=3)  : keep all input (<=3) + up to 4 SNN keys
      normal (4-15): 3 anchors + 3 SNN keys
      long (>15)   : 3 anchors + 6 SNN keys
    """
    if n_input <= 3:
        return min(3, n_input), 4
    if n_input <= 15:
        return 3, 3
    return 3, 6


def select_anchored_keys(
    network_output: Dict[str, float],
    input_keys: Dict[str, float],
    decode_gate: Optional[float] = None,
) -> List[str]:
    """Combine top input anchors with thresholded, deduped SNN keys.

    Anchors first (highest confidence input), then any SNN-only candidates
    scoring at/above *decode_gate*, deduplicated against the anchors, up to the
    SNN slot budget.  Returns the ordered key list for the decoder.
    """
    anchor_slots, snn_slots = decode_slot_budget(len(input_keys))

    # SNN candidates separate from input self-activation, thresholded.
    gate = _DECODE_GATE if decode_gate is None else decode_gate
    snn_only = {k: v for k, v in network_output.items() if k not in input_keys}
    snn_candidates = [k for k, v in snn_only.items() if v >= gate]
    snn_sorted = sorted(snn_candidates, key=lambda k: snn_only[k], reverse=True)

    # Anchors = top input keys by confidence.
    anchor_keys = sorted(
        input_keys.keys(), key=lambda k: input_keys[k], reverse=True
    )[:anchor_slots]

    seen: set = set(anchor_keys)
    combined: List[str] = list(anchor_keys)
    for k in snn_sorted:
        if k not in seen:
            if len(combined) - len(anchor_keys) >= snn_slots:
                break
            seen.add(k)
            combined.append(k)
    return combined