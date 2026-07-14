"""
ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
知識查證器 — 用專案自帶的網路搜尋（WebSearchTool）查證事實主張。
搜尋後端與評估器皆可注入（預設 WebSearchTool + heuristic_assess），可單測。
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from ai.memory.grounded_knowledge import (
    SourceRef,
    VerificationStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    status: VerificationStatus
    confidence: float
    sources: List[SourceRef] = field(default_factory=list)
    query: str = ""


# Negation cues (English + Chinese) used by the heuristic assessor.
_NEG_RE = re.compile(
    r"\b(not|no|never|false|incorrect|wrong|myth|debunked|fake|untrue|"
    r"錯誤|誤|假|不實|謠言| debunk|false)\b",
    re.IGNORECASE | re.UNICODE,
)

_STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "and",
    "or", "in", "on", "at", "by", "for", "with", "that", "this", "it", "its",
    "the", "as", "from", "into", "means", "refers", "equals",
    "是", "為", "指", "的", "了", "之", "與", "及", "和", "一個", "這", "那",
}

_KEY_TOKEN_RE = re.compile(r"[A-Z][a-zA-Z0-9]+|[\d][\d.,:%]*|\b[a-z]{4,}\b", re.UNICODE)
_QUOTE_RE = re.compile(r"[""「『]([^""」』]{2,40})[""」』]")


def _claim_key_tokens(claim_text: str) -> List[str]:
    """Pick meaningful tokens from a claim to drive the search query."""
    tokens: List[str] = []
    for m in _QUOTE_RE.finditer(claim_text):
        tokens.append(m.group(1))
    for m in re.finditer(r"[A-Z][a-zA-Z0-9]+", claim_text):
        tokens.append(m.group(0))
    for m in re.finditer(r"\b\d[\d.,:%]*\b", claim_text):
        tokens.append(m.group(0))
    low = [t.lower() for t in re.findall(r"[a-z]{4,}", claim_text.lower())]
    tokens.extend(t for t in low if t not in _STOPWORDS)
    # dedupe, preserve order, cap
    seen = set()
    out = []
    for t in tokens:
        if t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
        if len(out) >= 6:
            break
    return out


def build_query(claim_text: str) -> str:
    """Build a web-search query from a claim's key tokens."""
    tokens = _claim_key_tokens(claim_text)
    return " ".join(tokens) if tokens else claim_text[:60]


def _result_text(r: Dict[str, Any]) -> str:
    if not isinstance(r, dict):
        return ""
    if "error" in r:
        return ""
    return f"{r.get('title', '')} {r.get('snippet', '')} {r.get('url', '')}"


def _contains_negation_near(text: str, token: str, window: int = 50) -> bool:
    idx = text.lower().find(token.lower())
    if idx < 0:
        return False
    start = max(0, idx - window)
    end = min(len(text), idx + len(token) + window)
    return bool(_NEG_RE.search(text[start:end]))


def heuristic_assess(
    claim_text: str,
    results: List[Dict[str, Any]],
) -> Tuple[VerificationStatus, float]:
    """
    Transparent, source-backed heuristic assessment.

    Returns (status, confidence). Support = fraction of non-error sources whose
    text contains a claim key token without a nearby negation; contradict =
    fraction containing a key token with a nearby negation. This is NOT strict
    fact recognition — it is an explainable verification channel (see plan §6).
    """
    key_tokens = _claim_key_tokens(claim_text)
    if not key_tokens:
        return VerificationStatus.UNVERIFIED, 0.0

    valid = [r for r in results if isinstance(r, dict) and "error" not in r]
    if not valid:
        return VerificationStatus.UNVERIFIED, 0.0

    support = 0
    contradict = 0
    for r in valid:
        text = _result_text(r)
        if not text:
            continue
        has_token = any(t.lower() in text.lower() for t in key_tokens)
        if not has_token:
            continue
        if any(_contains_negation_near(text, t) for t in key_tokens):
            contradict += 1
        else:
            support += 1

    n = len(valid)
    support_ratio = support / n
    contradict_ratio = contradict / n

    if contradict_ratio >= 0.34:
        return VerificationStatus.CONTRADICTED, round(contradict_ratio, 3)
    if support_ratio >= 0.34:
        return VerificationStatus.VERIFIED, round(support_ratio, 3)
    return VerificationStatus.UNVERIFIED, 0.0


class KnowledgeVerifier:
    """
    Verifies a claim by searching the web and assessing the returned sources.

    The search backend (``search_tool``) must expose
    ``search(query, num_results) -> List[Dict]`` and is injectable so tests can
    use a fake. The assessor is also injectable (default ``heuristic_assess``).
    """

    def __init__(
        self,
        search_tool: Optional[Any] = None,
        assessor: Optional[
            Callable[[str, List[Dict[str, Any]]], Tuple[VerificationStatus, float]]
        ] = None,
        cache: Optional[Dict[str, VerificationResult]] = None,
    ):
        if search_tool is None:
            try:
                from core.tools.web_search_tool import WebSearchTool
                search_tool = WebSearchTool()
            except Exception as e:  # pragma: no cover - defensive
                logger.warning("KnowledgeVerifier: WebSearchTool unavailable: %s", e)
                search_tool = None
        self.search_tool = search_tool
        self.assessor = assessor or heuristic_assess
        self._cache: Dict[str, VerificationResult] = cache if cache is not None else {}

    @property
    def available(self) -> bool:
        return self.search_tool is not None

    async def verify(
        self,
        claim_text: str,
        num_results: int = 5,
        use_cache: bool = True,
    ) -> VerificationResult:
        """Verify a claim's text; returns status + confidence + sources."""
        from ai.memory.grounded_knowledge import claim_key

        key = claim_key(claim_text)
        if use_cache and key in self._cache:
            return self._cache[key]

        if self.search_tool is None:
            return VerificationResult(
                VerificationStatus.UNVERIFIED, 0.0, query=build_query(claim_text)
            )

        query = build_query(claim_text)
        try:
            results = await asyncio.to_thread(self.search_tool.search, query, num_results)
        except Exception as e:
            logger.debug("KnowledgeVerifier: search failed for '%s': %s", query, e)
            results = []

        status, confidence = self.assessor(claim_text, results)
        sources = [
            SourceRef(
                url=r.get("url", ""),
                title=r.get("title", ""),
                snippet=r.get("snippet", ""),
            )
            for r in results
            if isinstance(r, dict) and "error" not in r
        ]
        result = VerificationResult(
            status=status, confidence=confidence, sources=sources, query=query
        )
        if use_cache:
            self._cache[key] = result
        return result


__all__ = [
    "VerificationResult",
    "KnowledgeVerifier",
    "heuristic_assess",
    "build_query",
]
