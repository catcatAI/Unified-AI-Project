# =============================================================================
# ANGELA-MATRIX: [L3] [β] [B] [L2]
# =============================================================================
"""Visual verdict adjudication — the L5 no-fabrication gate (2026-10-11).

Models confabulate (SAO vs FGO-plus-Death-Note-names on the same image).
The mechanism, not a slogan: collect independent model votes, require a
supermajority, otherwise ABSTAIN with the dissent on record. A fluent wrong
answer is worse than silence — it impersonates seeing.
"""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# One model, one vote (probe-count is effort, not evidence: 4 CLIP probes
# from one model = 1 vote). Supermajority bars.
COUNT_BAR = 2.0 / 3.0
LABEL_BAR = 2.0 / 3.0


def _norm_label(label: str) -> str:
    return " ".join(str(label).strip().lower().split())


def adjudicate(votes: List[Any], bar: float = COUNT_BAR) -> Dict[str, Any]:
    """Majority vote with abstention. Returns answer or silence + dissent."""
    total = len(votes)
    if total == 0:
        return {"status": "abstained", "answer": None, "agreement": 0.0, "votes": []}
    counts: Counter = Counter(votes)
    winner, n = counts.most_common(1)[0]
    agreement = n / total
    if agreement >= bar:
        return {
            "status": "decided",
            "answer": winner,
            "agreement": round(agreement, 3),
            "dissent": sorted(set(votes) - {winner}, key=str),
            "votes": list(votes),
        }
    return {
        "status": "abstained",
        "answer": None,
        "agreement": round(agreement, 3),
        "dissent": sorted(set(votes), key=str),
        "votes": list(votes),
    }


def adjudicate_label(votes: List[str], bar: float = LABEL_BAR) -> Dict[str, Any]:
    """Identity votes: normalized exact-match, same abstention rule."""
    return adjudicate([_norm_label(v) for v in votes], bar=bar)
