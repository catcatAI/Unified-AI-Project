"""
Unified Engine — the single AI engine replacing three_axis + ED3N + GARDEN
for text/dialogue inference.

Routing (first matching stage wins):
  0. reflex / presets      — canned greetings (single source, not learned)
  1. deterministic math     — MathVerifier (Python ast); labelled "not AI"
  2. deterministic logic    — evaluate_logic truth tables; labelled "not AI"
  3. statistical core       — FixedSizeCore generalisation + generation
     (REAL learned model: fixed memory, generalises to unseen inputs)

The statistical core is the only "learned" component. Stages 0-2 are honest
deterministic/canned capabilities, kept separate and labelled, because they
are real but not learned.
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
from ai.core.unicode_utils import normalize_text
from ai.data_eng.presets import REFLEX_PRESETS
from ai.unified_engine.core_model import FixedSizeCore
from ai.unified_engine.semantic_qa import SemanticQA
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
        self.semantic_qa: Optional[SemanticQA] = None
        # Multi-turn context: last few user questions + our answers, for
        # pronoun resolution ("it", "他") and topic continuation.
        self._turns: List[Tuple[str, str]] = []
        self._load_default_qa_knowledge()

    def _load_default_qa_knowledge(self) -> None:
        """Auto-load the shipped QA knowledge file when present (ZX or repo)."""
        try:
            from core.data_config import get_checkpoints_dir

            path = os.path.join(
                str(get_checkpoints_dir()), "unified", "qa_knowledge.json"
            )
            if not os.path.exists(path):
                return
            import json as _json

            with open(path, encoding="utf-8") as fh:
                d = _json.load(fh)
            self.semantic_qa = SemanticQA()
            if not self.semantic_qa.load_dict(d):
                self.semantic_qa = None
                logger.info("semantic QA knowledge file invalid, skipped")
            else:
                logger.info(
                    "semantic QA loaded %d facts", len(self.semantic_qa._questions)
                )
        except Exception as exc:  # noqa: BLE001 - optional boot feature
            logger.debug("semantic QA auto-load skipped: %s", exc)

    def learn_semantic_qa(self, qa_pairs, epochs: int = 60) -> Dict[str, float]:
        """Teach the semantic QA layer (SLS gradient-trained retrieval)."""
        if self.semantic_qa is None:
            self.semantic_qa = SemanticQA()
        return self.semantic_qa.learn(qa_pairs, epochs=epochs)

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
    # Reflex / presets (greetings, canned replies) — single source
    # ------------------------------------------------------------------
    def _try_reflex(self, text: str) -> Optional[str]:
        """Fast exact-pattern greeting/reflex lookup from the single presets.

        Uses word-boundary matching so "help" does not fire inside "helpful".
        """
        normalized = normalize_text(text).lower().strip().rstrip("?!=.。！？")
        normalized = normalized.strip()
        if not normalized:
            return None
        # Direct hit
        if normalized in REFLEX_PRESETS:
            return REFLEX_PRESETS[normalized]
        # Word-boundary scan for multi-word presets like "good morning"
        for pattern, response in REFLEX_PRESETS.items():
            if len(pattern) < 2:
                continue
            # Quick substring check first
            if pattern not in normalized:
                continue
            # Word-boundary check
            start = 0
            while True:
                idx = normalized.find(pattern, start)
                if idx == -1:
                    break
                before = idx == 0 or not normalized[idx - 1].isalnum()
                after = idx + len(pattern) >= len(normalized) or not normalized[idx + len(pattern)].isalnum()
                if before and after:
                    return response
                start = idx + 1
        return None

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
        # Boolean layer ONLY for proposition-shaped queries: must contain a
        # boolean connective or truth-value token. Open questions ("why is
        # the sky blue?") previously got fabricated "=true/false" answers.
        import re as _re

        proposition_re = _re.compile(
            r"\b(true|false|and|or|not|nor|nand|xor|xnor)\b"
            r"|真|假|且|或|並非|是否成立|是否"
            r"|既不是|也不是|互斥|都不成立|不都成立|不能同時成立|不能同时成立",
            _re.IGNORECASE,
        )
        score = (
            self.core.boolean_score(q)
            if self.core.use_feat and proposition_re.search(q)
            else None
        )
        if score is not None:
            bool_ans = "true" if score >= 0.0 else "false"
            conf = min(0.9, max(0.5, 0.5 + 0.2 * min(1.0, abs(score) / 2.0)))
            result = f"{q}={bool_ans}"
            return result, conf, "statistical-core"
        # Answer voting only for genuine questions. Statements ("please
        # explain X") previously got fabricated "=e" answers.
        is_question = text.rstrip().endswith(("?", "？")) or q.startswith(
            ("what ", "who ", "when ", "where ", "why ", "how ",
             "what'", "什麼", "什么", "誰", "谁", "為何", "为何", "如何")
        )
        if not is_question:
            return None
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
    # Multi-turn helpers
    # ------------------------------------------------------------------
    def _resolve_coreference(self, text: str) -> str:
        """Minimal pronoun/topic resolution: replace 'it/他/她/它/這個' with
        the topic entity from the previous turn when the raw question would
        otherwise retrieve nothing."""
        low = text.lower().strip()
        has_pronoun = any(w in low for w in (" it ", " it?", "it ", "他", "她", "它", "這個", "那个"))
        if not has_pronoun or not self._turns:
            return text
        prev_q = self._turns[-1][0]
        # extract content words from previous question as the topic
        import re as _re

        words = [w for w in _re.findall(r"[A-Za-z\u4e00-\u9fff]+", prev_q)
                 if len(w) > 2 and w.lower() not in
                 ("what", "which", "who", "where", "when", "the", "is", "of",
                  "capital", "city")]
        if not words:
            return text
        topic = words[-1]
        replaced = _re.sub(r"\b(it|this)\b", topic, low)
        for zh in ("他", "她", "它", "這個", "那个"):
            replaced = replaced.replace(zh, topic)
        return replaced

    def _wrap_answer(self, question: str, answer: str) -> str:
        """Wrap a (possibly bare) answer into a natural sentence."""
        """Natural sentence wrapping: if the stored answer is already a full
        sentence, keep it; if bare (e.g. 'Paris'), embed a light frame."""
        a = answer.strip()
        if len(a) > 0 and (a[0].isupper() or "\u4e00" <= a[0] <= "\u9fff") and (
            a.endswith((".", "!", "?", "。", "！"))
        ):
            return a
        q = question.strip().rstrip("？?").strip()
        lowq = q.lower()
        if lowq.startswith(("what is", "what's", "which city is")):
            return f"{q}: {a}."
        if lowq.startswith(("who ",)):
            return f"{q} — {a}."
        if lowq.startswith(("how many", "how much", "how fast", "how long")):
            return f"{q} — {a}."
        return f"{q}: {a}." if len(q) < 60 else f"{a}."

    def _remember_turn(self, question: str, answer: str) -> None:
        self._turns.append((question, answer))
        if len(self._turns) > 6:
            self._turns.pop(0)

    # ------------------------------------------------------------------
    # Public process
    # ------------------------------------------------------------------
    def process(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
        # 0. Reflex / presets (greetings, canned replies) — single source.
        r = self._try_reflex(text)
        if r is not None:
            self._last_route = "reflex"
            self._last_confidence = 1.0
            return r
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
        # 2. Learned semantic QA (SLS gradient layer) — factual open questions.
        # Skip proposition-style queries ("X nor Y=?"): those belong to the
        # statistical boolean layer, not factual retrieval.
        if self.semantic_qa is not None and "=" not in text and not text.rstrip().endswith("?="):
            resolved = self._resolve_coreference(text)
            # Pronoun-resolved queries must actually contain the resolved
            # topic word, otherwise retrieval fires on unrelated garbage.
            if resolved != text:
                hit = self.semantic_qa.answer(resolved)
                if hit is not None:
                    import re as _re

                    topic_words = [w.lower() for w in _re.findall(r"[A-Za-z]+", resolved)]
                    ans_low = hit[0].lower()
                    if not any(tw in ans_low or tw in resolved.lower() for tw in topic_words[:3]):
                        hit = None
            else:
                hit = self.semantic_qa.answer(resolved)
                if hit is not None:
                    # content-word overlap guard: at least one non-stopword
                    # from the query must appear in the answer, otherwise the
                    # match is topical noise (e.g. "light speed" -> continents).
                    import re as _re

                    stop = {"what", "is", "the", "of", "are", "there", "a", "an",
                            "to", "in", "on", "how", "does", "do", "many", "much"}
                    # Latin words (>=3 chars) AND CJK runs (>=2 chars) both count
                    # as content words — CJK-only queries previously skipped the
                    # guard entirely and matched cross-language noise.
                    qws = [w.lower() for w in _re.findall(r"[A-Za-z]{3,}", resolved)
                           if w.lower() not in stop]
                    qws += [c for c in _re.findall(r"[\u4e00-\u9fff]{2,}", resolved)]
                    if qws and not any(
                        w in hit[0].lower()
                        or any(c in hit[0] for c in w if "\u4e00" <= c <= "\u9fff")
                        for w in qws
                    ):
                        hit = None
            if hit is not None:
                ans, sim = hit
                self._last_route = "semantic-qa"
                self._last_confidence = min(0.95, max(0.5, sim))
                wrapped = self._wrap_answer(resolved, ans)
                self._remember_turn(text, wrapped)
                return wrapped
        # 3. Learned statistical core.
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
            "semantic_qa": self.semantic_qa.to_dict() if self.semantic_qa else None,
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
            sq = state.get("semantic_qa")
            if sq:
                if self.semantic_qa is None:
                    self.semantic_qa = SemanticQA()
                self.semantic_qa.load_dict(sq)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("unified: failed to load %s: %s", path, exc)
            return False

    def freeze(self) -> None:
        self._frozen = True

    def unfreeze(self) -> None:
        self._frozen = False
