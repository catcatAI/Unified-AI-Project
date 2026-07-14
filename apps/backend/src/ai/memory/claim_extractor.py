"""
ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
事實主張萃取 — 從對話/回答文字中抽出「像事實」的句子，供後續查證。
純函數、無網路依賴、可單元測試。
"""

import logging
import re
from typing import List

logger = logging.getLogger(__name__)

_COPULA = [
    r"\bis\b", r"\bare\b", r"\bwas\b", r"\bwere\b", r"\bbe\b",
    r"\bmeans\b", r"\bmeans that\b", r"\bequals?\b", r"\brefers to\b",
    r"\bdiscovered\b", r"\binvented\b", r"\bfounded\b", r"\bestablished\b",
    r"\bcreated\b", r"\bdeveloped\b", r"\bborn\b", r"\bdied\b",
    r"是指", r"是", r"為", r"等於", r"成立於", r"發明", r"發現", r"創立",
    r"成立", r"位於", r"位於於", r"屬於", r"來自",
]
_COPULA_RE = re.compile("|".join(_COPULA), re.IGNORECASE | re.UNICODE)

_NEG_PREFIX = re.compile(
    r"^\s*(please|pls|請|幫我|請幫我|can you|could you|would you|let's|let us)\b",
    re.IGNORECASE,
)

_QUESTION_RE = re.compile(r"[?？]$")

# anchors: capitalized token, digit, quoted term, or a domain keyword
_ANCHOR_TOKEN_RE = re.compile(r"[A-Z][a-zA-Z0-9]+|[\d][\d.,:%]*")
_QUOTE_RE = re.compile(r"[""「『]([^""」』]{2,40})[""」』]")
_DOMAIN_WORDS = {
    "physics", "chemistry", "biology", "math", "mathematics", "history",
    "science", "technology", "physics", "element", "molecule", "atom",
    "water", "oxygen", "carbon", "gold", "silver", "energy", "force",
    "光速", "原子", "分子", "元素", "化學", "物理", "生物", "數學", "歷史",
    "科學", "科技", "能量", "力", "溫度", "質量", "速度",
}
_DOMAIN_RE = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in _DOMAIN_WORDS) + r")\b", re.IGNORECASE
)

_SENT_SPLIT_RE = re.compile(r"(?<=[。！？.!?\n])\s*")


def _has_anchor(sentence: str) -> bool:
    if _ANCHOR_TOKEN_RE.search(sentence):
        return True
    if _QUOTE_RE.search(sentence):
        return True
    if _DOMAIN_RE.search(sentence):
        return True
    return False


def _looks_factual(sentence: str) -> bool:
    if not _COPULA_RE.search(sentence):
        return False
    if not _has_anchor(sentence):
        return False
    return True


def extract_claims(text: str, max_claims: int = 8) -> List[str]:
    """
    Extract candidate factual claims (sentences) from free text.

    Heuristic: a sentence is a candidate claim if it contains a copula /
    relation verb AND at least one anchor (capitalized token, digit, quoted
    term, or domain keyword). Questions, imperatives, and pure chit-chat are
    excluded.
    """
    if not text:
        return []
    sentences = [s.strip() for s in _SENT_SPLIT_RE.split(text) if s.strip()]
    claims: List[str] = []
    seen = set()
    for s in sentences:
        if len(s) < 8 or len(s) > 400:
            continue
        if _QUESTION_RE.search(s):
            continue
        if _NEG_PREFIX.match(s):
            continue
        if not _looks_factual(s):
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        claims.append(s)
        if len(claims) >= max_claims:
            break
    return claims


__all__ = ["extract_claims"]
