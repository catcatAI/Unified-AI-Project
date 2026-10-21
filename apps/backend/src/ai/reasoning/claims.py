"""帶條件與例外的斷言推理——「最正確」那一級。

**為什麼需要這一層**：確定性引擎答得出「A 比 B 高」這種**關係**，答不出
「X 這句話對嗎？」這種**斷言**——而後者正是「最正確 vs 近似正確」的差別
所在。同一個斷言在不同的條件下會變，所以答案必須帶著條件與例外：

> 問：水的沸點是 100∘C，這句話對嗎？
> 事實正確：在大氣壓下的純水沸點確實是 100∘C。
> 例外：高山上不到 90∘C 就沸騰；加鹽的濃鹽水沸點高於 100∘C。
> 最正確：在大氣壓下的純水沸點是 100∘C；但高海拔不到 90∘C 就沸騰，加鹽則高於
> 100∘C——所以「固定 100∘C」不成立。

**這裡的斷言庫是知識，不是推理**：斷言庫沒有的斷言（例：標準集裡那 324 題的
主題）就答不出來——那時誠實棄權是正確行為。量測分兩塊：斷言庫覆蓋的題目
（`claim_holdout` 類）量的是**機制**，標準集裡那 324 題量的是**知識缺口**
（兩者不重疊，見 `apps/backend/configs/standard/reasoning/claims.yaml`）。
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

CLAIMS_ASSET = (
    Path(__file__).resolve().parents[3] / "configs" / "standard" / "reasoning" / "claims.yaml"
)


@dataclass(frozen=True)
class Claim:
    """One assertion with its condition and its exception."""

    id: str
    statement: str
    condition: str
    exception: str
    keywords: Tuple[str, ...]
    irrelevant: str = ""


_CLAIMS: Optional[List[Claim]] = None


def load_claims() -> List[Claim]:
    """The claim library (the knowledge asset)."""
    global _CLAIMS
    if _CLAIMS is not None:
        return _CLAIMS
    claims: List[Claim] = []
    try:
        import yaml

        data = yaml.safe_load(CLAIMS_ASSET.read_text(encoding="utf-8")) or {}
        for entry in data.get("claims") or []:
            claims.append(
                Claim(
                    id=str(entry.get("id") or ""),
                    statement=str(entry.get("statement") or ""),
                    condition=str(entry.get("condition") or ""),
                    exception=str(entry.get("exception") or ""),
                    keywords=tuple(str(k) for k in (entry.get("keywords") or [])),
                    irrelevant=str(entry.get("irrelevant") or ""),
                )
            )
    except Exception as exc:  # pragma: no cover - the asset is optional
        logger.debug("claim library unavailable: %s", exc)
    _CLAIMS = claims
    return claims


# The question shapes: "X 對嗎？" / "這項規定正確嗎？" / "X 這句話對嗎？"
_QUESTION_SHAPES = (
    r"對(?:的)?嗎",
    r"正確(?:的)?嗎",
    r"對不對",
    r"是否正確",
    r"同意嗎",
    r"這句話",
    r"is (that|this|it) (true|correct|right)",
    r"correct\?",
    r"true\?",
)
_QUESTION_RE = re.compile("|".join(_QUESTION_SHAPES), re.IGNORECASE)


def is_claim_question(text: str) -> bool:
    """True when the message asks whether an assertion holds."""
    return bool(_QUESTION_RE.search(text or ""))


def _longest_common_run(left: str, right: str) -> int:
    """The longest run of characters shared by two texts."""
    a, b = left or "", right or ""
    if not a or not b:
        return 0
    previous = [0] * (len(b) + 1)
    best = 0
    for i in range(1, len(a) + 1):
        current = [0] * (len(b) + 1)
        for j in range(1, len(b) + 1):
            if a[i - 1] == b[j - 1]:
                current[j] = previous[j - 1] + 1
                if current[j] > best:
                    best = current[j]
        previous = current
    return best


def _match_score(claim: Claim, text: str) -> Tuple[int, int]:
    """(how many keywords matched, the longest shared run with the statement).

    The shared run breaks the tie: "沸點" matches both the alcohol and the
    altitude claim, but the question's wording only overlaps the *statement*
    of the claim it is really about.
    """
    lowered = (text or "").lower()
    matched = [keyword for keyword in claim.keywords if keyword.lower() in lowered]
    shared = _longest_common_run(lowered, claim.statement.lower())
    return len(matched), shared


def find_claim(text: str) -> Optional[Claim]:
    """The claim the question is about (None when the library has no answer)."""
    if not is_claim_question(text):
        return None
    best: Optional[Claim] = None
    best_score: Tuple[int, int] = (0, 0)
    for claim in load_claims():
        score = _match_score(claim, text)
        if score > best_score:
            best, best_score = claim, score
    return best if best_score[0] > 0 else None


def answer_claim_question(text: str) -> Optional[str]:
    """The boundary-aware answer ("the most correct" shape).

    The answer states the fact **with its condition** and **names the
    exception** — that is what separates it from the merely approximate
    answer.
    """
    claim = find_claim(text)
    if claim is None:
        return None
    parts = [f"{claim.condition}，{claim.statement}。"]
    if claim.exception:
        parts.append(f"但{claim.exception}。")
    if claim.irrelevant:
        parts.append(f"（像「{claim.irrelevant}」那樣就完全不符合了。）")
    return "".join(parts)


def claim_index() -> Dict[str, Claim]:
    """The claim library keyed by id (for the tests and the diagnostics)."""
    return {claim.id: claim for claim in load_claims()}


__all__ = [
    "CLAIMS_ASSET",
    "Claim",
    "answer_claim_question",
    "claim_index",
    "find_claim",
    "is_claim_question",
    "load_claims",
]
