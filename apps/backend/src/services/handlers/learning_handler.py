"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
LearningHandler — processes learning/teach/remember intents from ChatService.
Captures knowledge, facts, and rules the user wants Angela to remember.
Persists to the process-wide VectorMemoryStore (see _store_fact for why the
previous AnchorLearningEngine target was a no-op).
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class LearningHandler:
    """Handles learning/teach/remember intents."""

    async def handle(self, text: str, intent: str) -> str:
        """Handle."""
        fact = self._extract_fact(text)
        if not fact:
            return "（學習）想讓我記住什麼呢？請告訴我一些你想讓我學習的事情。"
        stored = await self._store_fact(fact)
        return f"（學習）我記住了：{fact}\n" + (
            "（已儲存到長期記憶）" if stored else "（暫時記在心上）"
        )

    async def _store_fact(self, fact: str) -> bool:
        """Persist a user-taught fact to the process-wide vector memory.

        WHY this changed: the previous implementation handed the fact to
        ``AnchorLearningEngine``, which is a *state-vector* engine and exposes
        neither ``record_fact`` nor ``learn`` — so every write silently failed
        and the handler answered 「暫時記在心上」 forever. The real long-term
        memory owner is ``VectorMemoryStore`` (single-owner accessor), which is
        the same store ChatService writes conversation memory to.
        """
        import uuid as _uuid

        memory_id = f"fact_{_uuid.uuid4().hex[:12]}"
        content = f"User taught Angela: {fact}"
        metadata = {"type": "user_fact", "source": "learning_handler"}
        try:
            from ai.memory.vector_store import get_vector_store

            store = get_vector_store()
            if store is None:
                logger.warning("[LearningHandler] vector memory unavailable; fact not stored")
                return False
            await store.add_memory(memory_id, content, metadata)
            return True
        except Exception as e:
            logger.warning(f"[LearningHandler] store failed: {e}", exc_info=True)
            return False

    def _extract_fact(self, text: str) -> Optional[str]:
        """Extract fact."""
        prefixes = sorted(
            [
                "記住這個",
                "幫我記住",
                "帮我记住",
                "幫我記下",
                "帮我记下",
                "learn that",
                "remember that",
                "記住",
                "學習",
                "記錄",
                "教我",
                "調整",
                "理解",
                "please remember",
                "please learn",
                "remember",
                "learn",
                "teach",
            ],
            key=len,
            reverse=True,
        )
        for prefix in prefixes:
            pattern = re.compile(re.escape(prefix), re.IGNORECASE)
            text = pattern.sub("", text, count=1).strip()
        # Strip the politeness wrapper and separator left behind by the prefix
        # removal: 「請記住：我的貓叫小咪」 must yield 「我的貓叫小咪」, not
        # 「請：我的貓叫小咪」 — a stored fact keeps its junk forever.
        text = re.sub(r"^[\s請请幫帮麻煩麻烦給给]+", "", text)
        text = re.sub(r"^[\s:：,，。;；、]+", "", text)
        text = re.sub(r"^(關於|有關|就是|這個是|這是|那|那個)\s*", "", text).strip()
        text = re.sub(r"[，。！？；：,\.!?;:]+$", "", text).strip()
        return text if text and len(text) >= 2 else None
