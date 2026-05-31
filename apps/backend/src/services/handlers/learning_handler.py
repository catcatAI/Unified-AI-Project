"""
ANGELA-MATRIX: [L3-L4] [β] [B] [L2]
LearningHandler — processes learning/teach/remember intents from ChatService.
Captures knowledge, facts, and rules the user wants Angela to remember.
Optionally persists via AnchorLearningEngine if available.
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class LearningHandler:
    """Handles learning/teach/remember intents."""

    def __init__(self):
        self._anchor = None

    @property
    def _anchor_engine(self):
        if self._anchor is None:
            try:
                from core.engine.anchor_learning import AnchorLearningEngine
                self._anchor = AnchorLearningEngine()
            except Exception as e:
                logger.warning(f"[LearningHandler] AnchorLearningEngine unavailable: {e}")
        return self._anchor

    async def handle(self, text: str, intent: str) -> str:
        fact = self._extract_fact(text)
        if not fact:
            return "（學習）想讓我記住什麼呢？請告訴我一些你想讓我學習的事情。"
        stored = await self._store_fact(fact)
        return (
            f"（學習）我記住了：{fact}\n"
            + ("（已儲存到長期記憶）" if stored else "（暫時記在心上）")
        )

    async def _store_fact(self, fact: str) -> bool:
        engine = self._anchor_engine
        if not engine:
            return False
        try:
            if hasattr(engine, "record_fact"):
                engine.record_fact(fact)
                return True
            elif hasattr(engine, "learn"):
                await engine.learn(fact)
                return True
        except Exception as e:
            logger.warning(f"[LearningHandler] store failed: {e}")
        return False

    def _extract_fact(self, text: str) -> Optional[str]:
        prefixes = sorted(
            ["記住這個", "記住", "學習", "記錄", "教我", "調整", "理解",
             "please remember", "please learn", "remember", "learn", "teach"],
            key=len, reverse=True,
        )
        for prefix in prefixes:
            pattern = re.compile(re.escape(prefix), re.IGNORECASE)
            text = pattern.sub("", text, count=1).strip()
        text = re.sub(r"^(關於|有關|就是|這個是|這是|那|那個)\s*", "", text).strip()
        text = re.sub(r"[，。！？；：,\.!?;:]$", "", text).strip()
        return text if text and len(text) >= 2 else None
