"""
ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
有查證知識庫 — 存放「事實主張」及其查證狀態與來源。
純 stdlib，無網路依賴；可單元測試。
"""

import json
import logging
import hashlib
import os
import re
import threading
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VerificationStatus(str, Enum):
    """A claim's verification state."""
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    CONTRADICTED = "contradicted"
    DISPUTED = "disputed"


@dataclass
class SourceRef:
    """A single verification source (URL + snippet)."""
    url: str
    title: str = ""
    snippet: str = ""


@dataclass
class GroundedClaim:
    """A single factual claim with its verification lifecycle."""
    claim_key: str
    claim_text: str
    sources: List[SourceRef] = field(default_factory=list)
    status: VerificationStatus = VerificationStatus.UNVERIFIED
    confidence: float = 0.0
    domain: Optional[str] = None
    first_seen: str = ""
    last_verified: str = ""
    verify_count: int = 0
    contradict_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        d["sources"] = [asdict(s) for s in self.sources]
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GroundedClaim":
        sources = [SourceRef(**s) for s in d.get("sources", [])]
        try:
            status = VerificationStatus(d.get("status", "unverified"))
        except ValueError:
            status = VerificationStatus.UNVERIFIED
        return cls(
            claim_key=d.get("claim_key", ""),
            claim_text=d.get("claim_text", ""),
            sources=sources,
            status=status,
            confidence=float(d.get("confidence", 0.0)),
            domain=d.get("domain"),
            first_seen=d.get("first_seen", ""),
            last_verified=d.get("last_verified", ""),
            verify_count=int(d.get("verify_count", 0)),
            contradict_count=int(d.get("contradict_count", 0)),
        )


_TOKEN_RE = re.compile(r"[a-z0-9一-鿿]+", re.UNICODE)


def normalize_claim(text: str) -> str:
    """Normalize claim text for stable dedupe key (lowercase, drop punctuation)."""
    lowered = text.lower().strip()
    # keep alphanumerics, CJK and whitespace; replace everything else
    cleaned = re.sub(r"[^\w\s一-鿿]", " ", lowered, flags=re.UNICODE)
    collapsed = re.sub(r"\s+", " ", cleaned)
    return collapsed.strip()


def claim_key(text: str) -> str:
    """Stable hash key for a claim (after normalization)."""
    return hashlib.sha1(normalize_claim(text).encode("utf-8")).hexdigest()


def tokens_of(text: str) -> set:
    """Extract lowercased word tokens (alnum + CJK) for similarity."""
    return set(_TOKEN_RE.findall(text.lower()))


class GroundedKnowledgeStore:
    """
    In-memory store of grounded claims with JSON persistence.

    Verification is performed elsewhere (KnowledgeVerifier); this store only
    records the outcome (status + sources + confidence) and serves lookups.
    """

    def __init__(self):
        self._claims: Dict[str, GroundedClaim] = {}
        # Guards concurrent mutation/iteration: background verification tasks
        # (record_verification) can run while the answer path reads (find_related).
        self._lock = threading.RLock()

    # ---- write path -------------------------------------------------------
    def add_or_update(self, claim_text: str, domain: Optional[str] = None) -> GroundedClaim:
        """Insert a new claim (UNVERIFIED) or return the existing one."""
        with self._lock:
            key = claim_key(claim_text)
            existing = self._claims.get(key)
            if existing is not None:
                if domain and not existing.domain:
                    existing.domain = domain
                return existing
            claim = GroundedClaim(
                claim_key=key,
                claim_text=claim_text.strip(),
                status=VerificationStatus.UNVERIFIED,
                domain=domain,
            )
            self._claims[key] = claim
            return claim

    def record_verification(
        self,
        claim_key: str,
        status: VerificationStatus,
        sources: Optional[List[SourceRef]] = None,
        confidence: float = 0.0,
    ) -> Optional[GroundedClaim]:
        """Apply a verification outcome to a claim."""
        with self._lock:
            claim = self._claims.get(claim_key)
            if claim is None:
                return None
            claim.status = status
            claim.confidence = max(0.0, min(1.0, float(confidence)))
            new_sources = sources or []
            seen = {(s.url, s.title) for s in claim.sources}
            for s in new_sources:
                if (s.url, s.title) not in seen:
                    claim.sources.append(s)
                    seen.add((s.url, s.title))
            if status == VerificationStatus.VERIFIED:
                claim.verify_count += 1
                claim.last_verified = _now_iso()
            elif status == VerificationStatus.CONTRADICTED:
                claim.contradict_count += 1
                claim.last_verified = _now_iso()
            return claim

    # ---- read path (cheap, local) ----------------------------------------
    def find_related(self, query: str, limit: int = 5) -> List[GroundedClaim]:
        """Return claims whose tokens overlap the query, best-first."""
        q_tokens = tokens_of(query)
        if not q_tokens:
            return []
        with self._lock:
            claims = list(self._claims.values())
        scored = []
        for claim in claims:
            c_tokens = tokens_of(claim.claim_text)
            overlap = len(q_tokens & c_tokens)
            if overlap > 0:
                scored.append((overlap, claim))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:limit]]

    def verified_for(self, query: str, limit: int = 3) -> List[GroundedClaim]:
        """Return VERIFIED claims relevant to the query, highest confidence first."""
        related = self.find_related(query, limit=limit * 4 + 10)
        verified = [c for c in related if c.status == VerificationStatus.VERIFIED]
        verified.sort(key=lambda c: c.confidence, reverse=True)
        return verified[:limit]

    def get(self, key: str) -> Optional[GroundedClaim]:
        with self._lock:
            return self._claims.get(key)

    def all(self) -> List[GroundedClaim]:
        with self._lock:
            return list(self._claims.values())

    def count(self) -> int:
        with self._lock:
            return len(self._claims)

    def stats(self) -> Dict[str, int]:
        s = {"total": 0, "verified": 0, "contradicted": 0, "unverified": 0, "disputed": 0}
        with self._lock:
            for c in self._claims.values():
                s["total"] += 1
                s[c.status.value] += 1
        return s

    # ---- persistence ------------------------------------------------------
    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with self._lock:
            state = [c.to_dict() for c in self._claims.values()]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        logger.info("GroundedKnowledgeStore: saved %d claims to %s", len(state), path)

    def load(self, path: str) -> int:
        if not os.path.exists(path):
            return 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                state = json.load(f)
            with self._lock:
                for d in state:
                    claim = GroundedClaim.from_dict(d)
                    self._claims[claim.claim_key] = claim
            logger.info("GroundedKnowledgeStore: loaded %d claims from %s", len(state), path)
            return len(state)
        except Exception as e:
            logger.warning("GroundedKnowledgeStore: failed to load %s: %s", path, e)
            return 0


def _now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "VerificationStatus",
    "SourceRef",
    "GroundedClaim",
    "GroundedKnowledgeStore",
    "normalize_claim",
    "claim_key",
    "tokens_of",
]
