"""
Unified Engine — the single AI engine replacing three_axis + ED3N + GARDEN
for text/dialogue inference.

Routing (first matching stage wins):
  1. deterministic math     — MathVerifier (Python ast); labelled "not AI"
  2. deterministic logic    — evaluate_logic truth tables; labelled "not AI"
  3. deterministic reasoning — symbolic/relational; labelled "not AI"
  4. statistical core       — FixedSizeCore generalisation + generation
     (REAL learned model: fixed memory, generalises to unseen inputs)

The statistical core is the only "learned" component. Stages 1-3 are honest
deterministic capabilities, kept separate and labelled, because they are real
but not learned. This mirrors the project's own honest-assessment discipline:
ED3N/GARDEN previously blurred this line by growing verbatim dictionaries and
labelling them "learning" — that is what this engine removes.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from ai.arithmetic.deterministic_router import try_logic as _det_try_logic
from ai.arithmetic.deterministic_router import try_math as _det_try_math
from ai.unified_engine.core_model import FixedSizeCore
from core.system.config.magic_numbers import (
    _probe_ram_total_gb,
    effective_capacity_bytes,
)

logger = logging.getLogger(__name__)


class UnifiedEngine:
    """Single engine: deterministic routing first, then the fixed-size
    statistical core. model_bytes is constant across training."""

    def __init__(self, memory_cap_mb: Optional[float] = None, max_seq: int = 512) -> None:
        self.core = FixedSizeCore(max_seq=max_seq)
        self._cap_bytes = self._resolve_cap(memory_cap_mb)
        self._last_confidence = 0.0
        self._last_route = ""
        self._frozen = False

    @staticmethod
    def _resolve_cap(memory_cap_mb: Optional[float]) -> int:
        if memory_cap_mb is not None:
            return int(memory_cap_mb * 1024 * 1024)
        try:
            ram = _probe_ram_total_gb()
            return int(effective_capacity_bytes("memory", total_gb=ram, numeric_mb=2048))
        except Exception:
            return 2048 * 1024 * 1024

    @property
    def model_bytes(self) -> int:
        return self.core.model_bytes

    @property
    def corpus_bytes(self) -> int:
        return self.core._bytes_seen

    @property
    def memory_cap_bytes(self) -> int:
        return self._cap_bytes

    def memory_usage_ratio(self) -> float:
        return self.core.estimate_memory_bytes() / max(1, self._cap_bytes)

    def compression_ratio(self) -> float:
        """corpus_bytes / model_bytes. >1 means the model is smaller than the
        data it learned from (the AI claim)."""
        mb = max(1, self.model_bytes)
        return self.core._bytes_seen / mb

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def learn_batch(self, samples: List[str]) -> Dict[str, Any]:
        stats = self.core.learn_batch(samples)
        stats["compression_ratio"] = round(self.compression_ratio(), 4)
        stats["memory_ratio"] = round(self.memory_usage_ratio(), 4)
        return stats

    # ------------------------------------------------------------------
    # Deterministic layers (real, but not learned)
    # ------------------------------------------------------------------
    def _try_math(self, text: str) -> Optional[str]:
        """Deterministic math via the single deterministic router."""
        return _det_try_math(text)

    def _try_logic(self, text: str) -> Optional[str]:
        """Deterministic boolean logic via the single deterministic router."""
        return _det_try_logic(text)

    # ------------------------------------------------------------------
    # Statistical inference (the learned model)
    # ------------------------------------------------------------------
    def _infer_from_core(self, text: str) -> Optional[Tuple[str, float, str]]:
        """Answer a query using the statistical core's generalisation.

        Two learned paths, both discriminative statistical inference:
          - boolean layer: log-odds over hashed n-grams for True/False
            questions (handles 'nor' -> False style correlations that naive
            voting dilutes)
          - answer-vote layer: atomic answer-string voting for open answers
        Unseen problems are answered because their n-grams overlap the
        training distribution.
        """
        q = text.rstrip("? ").rstrip("=").rstrip(" ")
        if not q:
            return None
        # Boolean questions first: the discriminative layer is stronger.
        score = self.core.boolean_score(q)
        if score is not None:
            bool_ans = "true" if score >= 0.0 else "false"
            conf = min(0.9, max(0.5, 0.5 + 0.2 * min(1.0, abs(score) / 2.0)))
            result = f"{q}={bool_ans}"
            return result, conf, "statistical-core"
        best = self.core.best_answer(q)
        if best is None:
            return None
        answer, share = best
        if not answer or len(answer) > 32:
            return None
        conf = min(0.90, max(0.3, 0.3 + share))
        result = f"{q}={answer}"
        return result, conf, "statistical-core"

    # ------------------------------------------------------------------
    # Public process
    # ------------------------------------------------------------------
    def process(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        # 1. Deterministic (real, not learned).
        r = self._try_math(text)
        if r is not None:
            self._last_route = "deterministic-math"
            self._last_confidence = 1.0
            return r
        r = self._try_logic(text)
        if r is not None:
            self._last_route = "deterministic-logic"
            self._last_confidence = 1.0
            return r
        # 2. Learned statistical core.
        r = self._infer_from_core(text)
        if r is not None:
            result, conf, route = r
            self._last_route = route
            self._last_confidence = conf
            return result
        self._last_route = "none"
        self._last_confidence = 0.0
        return text

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        state = {
            "format": "unified/1",
            "core": self.core.to_dict(),
            "cap_bytes": self._cap_bytes,
            "frozen": self._frozen,
        }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)

    def load(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as fh:
                state = json.load(fh)
            if state.get("format") != "unified/1":
                logger.warning("unified: incompatible format %r", state.get("format"))
                return False
            self.core = FixedSizeCore.from_dict(state["core"])
            self._cap_bytes = state.get("cap_bytes", self._cap_bytes)
            self._frozen = state.get("frozen", False)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("unified: failed to load %s: %s", path, exc)
            return False

    def freeze(self) -> None:
        self._frozen = True

    def unfreeze(self) -> None:
        self._frozen = False
