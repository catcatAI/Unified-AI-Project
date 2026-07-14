"""
ANGELA-MATRIX: [L3-L4] [βγδ] [B] [L2]
有查證學習管理器 — 協調「萃取主張 → 查證 → 記錄 → 接地注入」。
單例工廠 get_grounded_learning_manager() 與 §X #263 apply_domain_cognition 同一模式，
避免多實例分歧。
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from ai.memory.grounded_knowledge import (
    GroundedClaim,
    GroundedKnowledgeStore,
    SourceRef,
    VerificationStatus,
)
from ai.memory.claim_extractor import extract_claims
from ai.meta.knowledge_verifier import KnowledgeVerifier, VerificationResult

logger = logging.getLogger(__name__)

DEFAULT_DATA_PATH = os.path.join("data", "grounded_knowledge.json")

# tokens used to format the grounded-context block injected into prompts
_GROUND_HEADER = "[已查證知識]"


class GroundedLearningManager:
    """
    Coordinates grounded learning:

    - ``queue_claims`` extracts candidate claims from a dialogue turn and
      schedules background verification (fire-and-forget; never blocks the
      answer path).
    - ``get_grounded_context`` returns a cheap, local snippet of VERIFIED
      claims relevant to a query, for optional prompt grounding.
    """

    def __init__(
        self,
        store: Optional[GroundedKnowledgeStore] = None,
        verifier: Optional[KnowledgeVerifier] = None,
        data_path: str = DEFAULT_DATA_PATH,
        max_concurrent: int = 10,
    ):
        self.store = store or GroundedKnowledgeStore()
        self.verifier = verifier or KnowledgeVerifier()
        self.data_path = data_path
        self.max_concurrent = max_concurrent
        self._in_flight: Dict[str, asyncio.Task] = {}

    # ---- extraction + enqueue (sync, no network) -------------------------
    def enqueue_claims(self, *texts: str) -> List[GroundedClaim]:
        """Extract candidate claims from texts and add them as UNVERIFIED."""
        added: List[GroundedClaim] = []
        for text in texts:
            for claim_text in extract_claims(text or ""):
                claim = self.store.add_or_update(claim_text)
                if claim.status == VerificationStatus.UNVERIFIED:
                    added.append(claim)
        return added

    # ---- verification ----------------------------------------------------
    async def verify_claim(self, claim: GroundedClaim) -> VerificationResult:
        """Verify one claim and record the outcome in the store."""
        result = await self.verifier.verify(claim.claim_text)
        self.store.record_verification(
            claim.claim_key, result.status, result.sources, result.confidence
        )
        return result

    async def run_pending_verifications(self) -> int:
        """Verify every currently-UNVERIFIED claim (synchronous helper / tests)."""
        pending = [c for c in self.store.all() if c.status == VerificationStatus.UNVERIFIED]
        done = 0
        for claim in pending:
            try:
                await self.verify_claim(claim)
                done += 1
            except Exception as e:  # pragma: no cover - defensive
                logger.debug("verify_claim failed for '%s': %s", claim.claim_text[:40], e)
        if done:
            self.save()
        return done

    async def queue_claims(self, user_message: str, response_text: str) -> List[GroundedClaim]:
        """
        Extract claims and schedule background verification.

        Fire-and-forget from the chat path: callers should ``asyncio.create_task``
        this so it does not block the answer. Verification errors are swallowed
        internally and never affect the main response.
        """
        added = self.enqueue_claims(user_message, response_text)
        for claim in added:
            if len(self._in_flight) >= self.max_concurrent:
                break
            if claim.claim_key in self._in_flight:
                continue
            task = asyncio.create_task(self._verify_one(claim))
            self._in_flight[claim.claim_key] = task
            task.add_done_callback(
                lambda t, k=claim.claim_key: self._in_flight.pop(k, None)
            )
        return added

    async def _verify_one(self, claim: GroundedClaim) -> None:
        try:
            await self.verify_claim(claim)
        except Exception as e:  # pragma: no cover - defensive
            logger.debug("background verify failed for '%s': %s", claim.claim_text[:40], e)

    # ---- read path (cheap, local) ----------------------------------------
    def get_grounded_context(self, query: str, limit: int = 3) -> str:
        """Return a short VERIFIED-knowledge block for prompt grounding, else ''."""
        verified = self.store.verified_for(query, limit=limit)
        if not verified:
            return ""
        lines = [_GROUND_HEADER]
        for c in verified:
            src = c.sources[0].url if c.sources else ""
            line = f"- {c.claim_text}"
            if src:
                line += f" (來源: {src})"
            lines.append(line)
        return "\n".join(lines)

    def learn_verified_from_search(
        self, query: str, results: List[Dict[str, Any]]
    ) -> Optional[GroundedClaim]:
        """Record a web-search result as VERIFIED knowledge (proactive grounding).

        Called when the system searches the web to answer an uncertain query, so the
        fact is remembered (verified, with sources) and can ground future answers
        without re-searching.
        """
        sources = [
            SourceRef(url=r.get("url", ""), title=r.get("title", ""), snippet=r.get("snippet", ""))
            for r in results
            if isinstance(r, dict) and "error" not in r and r.get("url")
        ]
        if not sources:
            # no usable sources -> do not record anything
            return None
        claim = self.store.add_or_update(query)
        self.store.record_verification(
            claim.claim_key, VerificationStatus.VERIFIED, sources, confidence=0.7
        )
        self.save()
        return claim

    # ---- stats / persistence --------------------------------------------
    def get_stats(self) -> Dict[str, object]:
        return {
            "store": self.store.stats(),
            "verifier_available": self.verifier.available,
            "in_flight": len(self._in_flight),
        }

    def save(self) -> None:
        try:
            self.store.save(self.data_path)
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("GroundedLearningManager.save failed: %s", e)

    def load(self) -> int:
        try:
            return self.store.load(self.data_path)
        except Exception as e:  # pragma: no cover - defensive
            logger.warning("GroundedLearningManager.load failed: %s", e)
            return 0


_manager: Optional[GroundedLearningManager] = None
_loaded_at_startup: bool = False


def get_grounded_learning_manager() -> GroundedLearningManager:
    """Shared singleton (mirrors the apply_domain_cognition single-entry pattern)."""
    global _manager, _loaded_at_startup
    if _manager is None:
        _manager = GroundedLearningManager()
        # best-effort load of previously verified knowledge (once per process)
        if not _loaded_at_startup:
            _loaded_at_startup = True
            try:
                _manager.load()
            except Exception as e:  # pragma: no cover - defensive
                logger.debug("GroundedLearningManager startup load skipped: %s", e)
    return _manager


__all__ = [
    "GroundedLearningManager",
    "get_grounded_learning_manager",
    "DEFAULT_DATA_PATH",
]
