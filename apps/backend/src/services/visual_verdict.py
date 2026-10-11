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

# Competence scope (2026-10-11, blind-001 lessons). Small local VLMs are
# not asked what they cannot do — this stops confabulation at the source
# instead of filtering it afterwards:
# - identity (which work / who): abstain by design, teach path only.
#   Proven twice: SAO + FGO-franchise-soup on the same image.
# - count: track-level only. Region votes (whole-image/crop CLIP probes)
#   double-count straddlers (001: 2+2 halves -> "four") — distribution
#   reference, never count votes.
ASK_SCOPE = {
    "count": ("vlm",),  # continuity-bearing counters only
    "describe": ("vlm", "clip"),
    "gender": ("vlm", "clip"),
    "identity": (),  # nobody local: abstain, teach path fills it
}


def repetition_score(answer: str) -> float:
    """Sentence-level copy-paste fraction (confabulation shape).

    Strips list markers first ("2. X" vs "3. X" are the same sentence said
    twice — the real SmolVLM shape), then counts exact + near dupes
    (word-Jaccard >= 0.75).
    """
    import re as _re

    raw = [s.strip().lower() for s in _re.split(r"[.!?\n]+", answer or "")]
    sents = [_re.sub(r"^[\d\s\-\*\.、\)\]]+", "", s).strip() for s in raw]
    sents = [s for s in sents if len(s) > 8]
    if len(sents) < 2:
        return 0.0

    def _jacc(a: str, b: str) -> float:
        wa, wb = set(a.split()), set(b.split())
        union = wa | wb
        return len(wa & wb) / max(len(union), 1)

    dupes = 0
    for i in range(len(sents)):
        for j in range(i):
            if sents[i] == sents[j] or _jacc(sents[i], sents[j]) >= 0.75:
                dupes += 1
                break
    return dupes / len(sents)


def is_degenerate(answer: str, question: str) -> bool:
    """Collapsed answers carry no signal and must not become votes.

    Observed shapes: single-word reply to a list task ("Girl."), single
    noun for a describe task ("Hair."), sentence-level copy-paste
    (SmolVLM's duplicated blondes).
    """
    text = (answer or "").strip()
    if not text:
        return True
    words = text.split()
    q = (question or "").lower()
    wants_list = any(k in q for k in ("list", "each", "left to right", "逐", "每"))
    if wants_list and len(words) <= 3:
        return True
    if ("describ" in q or "wearing" in q or "穿" in q or "描述" in q) and len(words) <= 3:
        return True
    if repetition_score(text) >= 0.3:
        return True
    return False


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
