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
import threading
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

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


def _np_as_float32(arr) -> "np.ndarray":
    return np.asarray(arr, dtype=np.float32)


class UnifiedEngine:
    """Single engine: deterministic routing first, then the fixed-size
    statistical core. model_bytes is constant across training."""

    def __init__(
        self,
        memory_cap_mb: Optional[float] = None,
        max_seq: int = 512,
        slots: Optional[int] = None,
        use_feat: Optional[bool] = None,
        use_delta: Optional[bool] = None,
    ) -> None:
        # slots/use_feat/use_delta: config-driven via compute.unified, explicit
        # args win over config. Keeps 65k default (259MB) unless hardware
        # profile or ANGELA_EXTENDED_MODEL opts into 128k.
        if slots is None:
            try:
                from core.system.config.magic_numbers import compute_int

                slots = compute_int("unified", "slots", 65536)
            except Exception:
                slots = 65536
        if use_feat is None:
            try:
                from core.system.config.magic_numbers import compute_bool as _cb

                # unified.use_feat is not a mode flag; read via _get directly
                from core.system.config.magic_numbers import _get

                v = _get("unified.use_feat", None)
                use_feat = bool(v) if v is not None else True
            except Exception:
                use_feat = True
        if use_delta is None:
            try:
                from core.system.config.magic_numbers import _get as _g2

                v2 = _g2("unified.use_delta", None)
                use_delta = bool(v2) if v2 is not None else True
            except Exception:
                use_delta = True
        # Clamp slots by RAM on extended (128k) to avoid OOM on 8GB boxes:
        # effective cap is the same cascade that guards GARDEN (usable-2GB).
        if slots is not None and slots > 65536:
            try:
                from core.system.config.magic_numbers import _probe_ram_total_gb, effective_capacity_bytes

                ram = _probe_ram_total_gb()
                if ram and ram > 0:
                    # unified tables: 4 gram tables + delta + feat ≈ 5*slots*256*4
                    # ~= slots*5120 bytes. Clamp so unified alone fits in cap.
                    cap = effective_capacity_bytes("memory", total_gb=max(0, ram - 2.0), numeric_mb=8192)
                    max_slots = int(cap / 5120)
                    # round down to power of two
                    max_pow2 = 1 << (max_slots.bit_length() - 1) if max_slots > 0 else 65536
                    if slots > max_pow2:
                        logger.info("Unified slots %d clamped to %d by RAM cap", slots, max_pow2)
                        slots = max(32768, max_pow2)
            except Exception:
                pass
        self.core = FixedSizeCore(max_seq=max_seq, slots=slots, use_feat=use_feat, use_delta=use_delta)
        self._cap_bytes = self._resolve_cap(memory_cap_mb)
        self._last_confidence = 0.0
        self._last_route = ""
        self._frozen = False
        self._process_lock = threading.Lock()
        self.semantic_qa: Optional[SemanticQA] = None
        # Multi-turn context: last few user questions + our answers, for
        # pronoun resolution ("it", "他") and topic continuation.
        self._turns: List[Tuple[str, str]] = []
        self._load_default_qa_knowledge()

    def _load_default_qa_knowledge(self) -> None:
        """Auto-load the shipped QA knowledge file when present, else tiny built-in."""
        try:
            from core.data_config import get_checkpoints_dir

            path = os.path.join(
                str(get_checkpoints_dir()), "unified", "qa_knowledge.json"
            )
            if os.path.exists(path):
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
                    return
        except Exception as exc:  # noqa: BLE001 - optional boot feature
            logger.debug("semantic QA auto-load skipped: %s", exc)
        # Fallback: tiny built-in facts so offline factual queries work
        # even without a shipped checkpoint (prevents "早安～..." gibberish).
        try:
            self.semantic_qa = SemanticQA()
            fallback_pairs = [
                ("capital of France", "Paris"),
                ("capital of Japan", "Tokyo"),
                ("capital of China", "Beijing"),
                ("sky is what color", "blue"),
                ("天空是什么颜色", "蓝色"),
                ("法国的首都是哪里", "巴黎"),
                ("日本的首都是哪里", "东京"),
                ("what is the capital of France", "Paris"),
                ("what is the capital of Japan", "Tokyo"),
                ("opposite of hot", "cold"),
                ("cat says", "meow"),
                ("dog says", "woof"),
            ]
            self.semantic_qa.learn(fallback_pairs, epochs=10)
            logger.info("semantic QA fallback loaded %d facts", len(fallback_pairs))
        except Exception as exc:
            logger.debug("semantic QA fallback failed: %s", exc)
            self.semantic_qa = None

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
        # Serialize concurrent calls: _last_route/_last_confidence are instance
        # state read immediately after this call by the provider. Without the
        # lock, concurrent requests would race and read each other's metadata.
        with self._process_lock:
            return self._process_inner(text, context)

    def _process_inner(self, text: str, context: Optional[Dict[str, Any]] = None) -> str:
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
                    # For factual QA the answer is a city name ("Paris") that
                    # never contains the query word ("capital"/"France"), so
                    # high-similarity hits bypass the guard (sim is 0.98 for
                    # capital queries via ONNX). Guard only fires when sim <0.85.
                    import re as _re

                    ans, sim = hit
                    if sim < 0.85:
                        stop = {"what", "is", "the", "of", "are", "there", "a", "an",
                                "to", "in", "on", "how", "does", "do", "many", "much"}
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
        """Persist engine state.

        Format ``unified/2`` = npz: the four (65536, 256) float32 gram tables
        are stored as raw ndarrays instead of JSON lists. Measured on a
        2-example engine: JSON was 325 MB, 64 s to write and ~2.3 GB of
        Python objects to parse back (list-of-lists ≈ 36 B/float vs 4 B in
        binary) — enough to OOM-kill the process on load. npz keeps the
        matrices at their native 256 MB total with zero parse inflation.
        Legacy ``unified/1`` JSON files remain readable via load().
        """
        os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        meta = {
            "format": "unified/2",
            "cap_bytes": self._cap_bytes,
            "frozen": self._frozen,
            "semantic_qa": self.semantic_qa.to_dict() if self.semantic_qa else None,
        }
        core_arrays = {
            "core_pos": self.core._pos,
            "core_trans": self.core._trans,
            "core_gram": self.core._gram,
            "core_gram3": self.core._gram3,
            "core_gram5": self.core._gram5,
            "core_uni": self.core._uni,
            "core_feat": self.core._feat,
            "core_feat_bool": self.core._feat_bool,
        }
        scalars = np.array(
            [
                self.core.max_seq,
                self.core._true_total,
                self.core._false_total,
                self.core._samples_seen,
                self.core._bytes_seen,
            ],
            dtype=np.float64,
        )
        try:
            with open(path, "wb") as fh:
                np.savez(
                    fh,
                    # <U… string array (NOT object dtype) so load() can use
                    # allow_pickle=False.
                    meta=np.array(json.dumps(meta)),
                    scalars=scalars,
                    **core_arrays,
                )
        except Exception as e:
            logger.error("unified: npz save failed (%s); falling back to json", e)
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
        # unified/2 (npz) — sniff the zip magic before json parsing.
        with open(path, "rb") as fh:
            magic = fh.read(2)
        if magic == b"PK":
            return self._load_npz(path)
        return self._load_json(path)

    def _load_npz(self, path: str) -> bool:
        try:
            with np.load(path, allow_pickle=False) as data:
                meta = json.loads(str(data["meta"]))
                if meta.get("format") != "unified/2":
                    logger.warning("unified: incompatible format %r", meta.get("format"))
                    return False
                sc = data["scalars"]
                self.core._true_total = float(sc[1])
                self.core._false_total = float(sc[2])
                self.core._samples_seen = int(sc[3])
                self.core._bytes_seen = int(sc[4])
                self.core._pos = _np_as_float32(data["core_pos"])
                self.core._trans = _np_as_float32(data["core_trans"])
                self.core._gram = _np_as_float32(data["core_gram"])
                self.core._gram3 = _np_as_float32(data["core_gram3"])
                self.core._gram5 = _np_as_float32(data["core_gram5"])
                self.core._uni = _np_as_float32(data["core_uni"])
                self.core._feat = _np_as_float32(data["core_feat"])
                self.core._feat_bool = _np_as_float32(data["core_feat_bool"])
            self._cap_bytes = meta.get("cap_bytes", self._cap_bytes)
            self._frozen = meta.get("frozen", False)
            sq = meta.get("semantic_qa")
            if sq:
                if self.semantic_qa is None:
                    self.semantic_qa = SemanticQA()
                self.semantic_qa.load_dict(sq)
            logger.info("unified: loaded npz state from %s", path)
            return True
        except Exception as e:
            logger.warning("unified: npz load failed: %s", e, exc_info=True)
            return False

    def _load_json(self, path: str) -> bool:
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
