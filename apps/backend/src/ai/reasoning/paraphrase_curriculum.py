"""The paraphrase curriculum: the sentences the middle layer is taught from.

The curriculum is *training data*, not a test set. Each entry names one
relation phrase and the concept it belongs to (a dimension and a direction,
or ``"*"`` when only the direction is lexical and the question supplies the
dimension). The alignment step moves the concept prototype toward the phrase;
nothing about a sentence is stored, so the layer generalises instead of
memorising.

The eval sentences live in ``benchmarks/data/paraphrase_v1.json`` and never
appear here; ``scripts/probe_paraphrase.py`` checks that.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

CURRICULUM_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "standard"
    / "reasoning"
    / "paraphrase_curriculum.yaml"
)
_DIRECTIONS = ("greater", "lesser")


def load_curriculum(path: Path = CURRICULUM_PATH) -> List[Dict[str, str]]:
    """The curriculum entries, validated (a malformed entry is an error)."""
    if not path.is_file():
        return []
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    entries = payload.get("entries") or []
    validated: List[Dict[str, str]] = []
    for entry in entries:
        phrase = str((entry or {}).get("phrase") or "").strip()
        dimension = str((entry or {}).get("dimension") or "").strip()
        direction = str((entry or {}).get("direction") or "").strip()
        if not phrase or not dimension or direction not in _DIRECTIONS:
            raise ValueError(f"malformed curriculum entry: {entry!r}")
        validated.append({"phrase": phrase, "dimension": dimension, "direction": direction})
    return validated


def apply_curriculum(bridge: Any, path: Path = CURRICULUM_PATH) -> int:
    """Teach *bridge* every curriculum entry (returns the aligned count)."""
    aligned = 0
    for entry in load_curriculum(path):
        concept: Tuple[str, str] = (entry["dimension"], entry["direction"])
        stats = bridge.align_phrase(entry["phrase"], concept)
        # The first example of a generic concept has zero delta (the
        # prototype starts at the phrase itself); it is still taught.
        aligned += 1
    return aligned


__all__ = ["CURRICULUM_PATH", "apply_curriculum", "load_curriculum"]
