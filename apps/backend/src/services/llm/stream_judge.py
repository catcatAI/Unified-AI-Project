# =============================================================================
# ANGELA-MATRIX: [L3] [β] [B] [L2]
# =============================================================================
"""StreamJudgeWindow — rolling judgment window for streamed generation.

Phase 2 of STREAMING_WINDOW_DUALMODEL_PLAN. Transport streaming (Phase 1)
deliberately made NO routing judgments (per-token windows are too narrow and
templates misfire more). This container restores judgment quality on streams:

- Rolling text window (default 336 chars ≈ a short Chinese paragraph).
- Lightweight judgment (QueryClassifier, same as full-text path) every N
  tokens (default 8).
- K-consecutive-agreement lock (default K=2): no commitment before that;
  downstream (highlight/interrupt/tool-prefetch) may act only after lock.
- Consistency check vs full-text classification (bench gate ≥95%).

When unsure it defaults to full-text behavior (wait, don't guess).
"""

from __future__ import annotations

import logging
from collections import deque
from typing import Any, Deque, Dict, List, Optional

logger = logging.getLogger(__name__)


class StreamJudgeWindow:
    """Rolling-window type judge over a token stream (stdlib only)."""

    def __init__(
        self,
        window_chars: int = 336,
        judge_every_tokens: int = 8,
        lock_k: int = 2,
    ) -> None:
        self.window_chars = max(32, int(window_chars))
        self.judge_every_tokens = max(1, int(judge_every_tokens))
        self.lock_k = max(1, int(lock_k))
        self._buffer: Deque[str] = deque()
        self._buffer_len = 0
        self._token_count = 0
        self._since_judge = 0
        self._recent: List[str] = []
        self.locked_type: Optional[str] = None
        self.judgments = 0

    def feed(self, token: str) -> Optional[Dict[str, Any]]:
        """Append a token; return a judgment event on lock/state change.

        Returns None most calls (no news). Event shapes:
        {"judge": "locked", "type": str} on first lock;
        {"judge": "changed", "from": str, "to": str} if a locked type flips
        (rare; downstream should treat the latest as truth).
        """
        if token:
            self._buffer.append(token)
            self._buffer_len += len(token)
            self._token_count += 1
            while self._buffer_len > self.window_chars and len(self._buffer) > 1:
                dropped = self._buffer.popleft()
                self._buffer_len -= len(dropped)
        self._since_judge += 1
        if self._since_judge < self.judge_every_tokens:
            return None
        self._since_judge = 0
        current = self._judge_locked_window()
        if current is None:
            return None
        self.judgments += 1
        self._recent.append(current)
        if len(self._recent) > self.lock_k:
            self._recent.pop(0)
        if (
            self.locked_type is None
            and len(self._recent) >= self.lock_k
            and all(t == self._recent[0] for t in self._recent)
        ):
            self.locked_type = self._recent[0]
            return {"judge": "locked", "type": self.locked_type}
        if (
            self.locked_type is not None
            and self._recent
            and self._recent[-1] != self.locked_type
            and all(t == self._recent[-1] for t in self._recent[-self.lock_k :])
            and len(self._recent) >= self.lock_k
        ):
            old, self.locked_type = self.locked_type, self._recent[-1]
            return {"judge": "changed", "from": old, "to": self.locked_type}
        return None

    def _judge_locked_window(self) -> Optional[str]:
        text = "".join(self._buffer).strip()
        if len(text) < 8:
            return None
        try:
            from ai.core.query_classifier import QueryClassifier

            result = QueryClassifier().classify(text)
            primary = getattr(result.primary_type, "value", result.primary_type)
            return str(primary or "")
        except Exception as exc:
            logger.debug("stream judge failed: %s", exc)
            return None

    def finalize(self, full_text: str) -> Dict[str, Any]:
        """Compare stream-locked type vs full-text classification."""
        full_type: Optional[str] = None
        try:
            from ai.core.query_classifier import QueryClassifier

            result = QueryClassifier().classify(full_text or "")
            primary = getattr(result.primary_type, "value", result.primary_type)
            full_type = str(primary or "") or None
        except Exception as exc:
            logger.debug("stream finalize failed: %s", exc)
        return {
            "stream_locked": self.locked_type,
            "full": full_type,
            "consistent": self.locked_type is not None and self.locked_type == full_type,
            "judgments": self.judgments,
            "tokens": self._token_count,
        }
