# =============================================================================
# ANGELA-MATRIX: [L3] [αβ] [B] [L2]
# =============================================================================
"""
data_eng.grow — single source of truth for vocabulary-growth gating.

Consolidates the five scattered cap authorities:
  * GARDEN ``VectorDictionary.max_entries`` (10000)
  * ED3N ``DictionaryLayer.max_entries`` (500000)
  * SNN ``max_vocab`` / ``connection_budget`` with 90% eviction
  * ``semantic_key_mapper`` cap
  * ``magic_numbers.model_sizing_config()``

The canonical cap comes from ``magic_numbers.model_sizing_config()`` so config
drives growth; the SNN/dictionary layers pass their own current
``max_entries`` to the pure predicates below, which decide YES/NO for growth
without mutating global state (the layer still owns its own eviction).
"""

from __future__ import annotations

from typing import Iterable, List, Optional

__all__ = [
    "batch_cap_ok",
    "growth_cap_ok",
    "growth_gate_batch",
    "resolved_max_entries",
]


def resolved_max_entries(config_max: Optional[int], default: int = 10000) -> int:
    """Return an effective max-entries value, preferring config.

    Mirrors the per-layer fallback pattern (garden default 10000, ED3N default
    500000) but accepts an explicit ``config_max`` so a single config source
    can override.  When not given, falls back to *default*.
    """
    if config_max is not None and config_max > 0:
        return int(config_max)
    return int(default)


def growth_cap_ok(entry_count: int, max_entries: int) -> bool:
    """True if we may still grow to *entry_count*+1.

    Precision-loss guard (returns False = stop adding, never crashes).
    Equivalent to ``len(entries) < max_entries``.
    """
    return entry_count < max_entries


def batch_cap_ok(
    entry_count: int,
    num_pending: int,
    max_entries: int,
) -> bool:
    """True if adding *num_pending* new entries stays at/below *max_entries*."""
    return entry_count + max(num_pending, 0) <= max_entries


def growth_gate_batch(
    entry_count: int,
    texts: Iterable[str],
    max_entries: int,
) -> List[str]:
    """Yield the sub-list of *texts* that still fits under the cap.

    Stops early once adding the next item would exceed *max_entries*.  The
    caller is responsible for actual add_entry; this only decides admission.
    Mirrors the early-``break`` in ``grow_batch``'s cap gate.
    """
    accepted: List[str] = []
    count = entry_count
    for text in texts:
        if count >= max_entries:
            break
        accepted.append(text)
        count += 1
    return accepted