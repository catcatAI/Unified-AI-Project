# =============================================================================
# ANGELA-MATRIX: [L2-L3] [βγδ] [C] [L2]
# =============================================================================

"""
Three-Axis System engine.

Architecture (per docs/03-technical-architecture/THREE_AXIS_SYSTEM.md):

  UTF-8 axis : characters mapped to their fixed UTF-8 byte values (0..255).
  Position   : each position holds the content-value distribution observed
               during training (sparse position x content matrix).
  Content    : value-pair association learned from training data. For dialogue,
               resolution is precedence-ordered:
                 1. anchor-aligned  (learned EM anchor split + whitespace-fold +
                                     suffix lookup; grants sliding alignment)
                 2. exact-completion (full known prefix seen verbatim -> next)
                 3. prefix-recall     (bounded left-context -> next)
                 4. position-exact    (a position observed with a single value)
                 5. position-majority (most frequent value at the position)
                 6. bigram transition (most frequent right-value given left)
                 7. global majority value
               The anchor path is the primary dialogue route (see
               AnchorLearner); exact-completion generation remains the fallback
               for verbatim continuation, continuing only while the whole
               prefix has a corpus continuation and stopping at the end of a
               memorised answer.

Memory is constrained by the project capacity config (2 GiB default via
``effective_capacity_bytes("memory", ...)``); the engine enforces the cap and
degrades gracefully (drops oldest low-support value-pairs) rather than OOM.

Honest note: this engine performs corpus *recall*, not generalisation. The
learned anchor alignment adds *formal* freedom (whitespace / leading-word /
length-offset variants align to the same key) but not *semantic* generalisation
(an unseen operand combination is still not computed). See the linearity-trap
analysis (verify_linearity_trap.py) in the system document.
"""

# =============================================================================
# ANGELA-MATRIX: [L2-L3] [βγδ] [C] [L2]
# =============================================================================

import json
import logging
import os
import threading
from collections import Counter, OrderedDict
from typing import Any, Dict, List, Optional, Tuple

from core.system.config.magic_numbers import _probe_ram_total_gb, effective_capacity_bytes

from .anchor_learner import AnchorLearner

logger = logging.getLogger(__name__)


def _estimate_entry_bytes() -> int:
    """Rough bytes-per-entry for the value-pair / bigram tables."""
    return 4 + 4 + 8  # key overhead (2 ints) + value (count)


class ThreeAxisEngine:
    """Three-axis engine: UTF-8 axis x position axis x content axis.

    Public interface mirrors GARDEN/ED3N engines:

      process(text, context=None) -> str   (synchronous, sets _last_confidence)
      learn_batch(samples)                 (train from a list of strings)
      save(path) / load(path)              (JSON checkpoint)

    Memory safety: the value-pair / bigram tables are bounded (value-pair keys
    only, <= 65,536), the position x content matrix is sparse, and training
    honours the project RAM capacity cap (2 GiB default) via
    ``effective_capacity_bytes``.
    """

    # =========================================================================
    # ANGELA-MATRIX: [L2-L3] [βγδ] [C] [L2]
    # =========================================================================

    MAX_VALUE_PAIRS = 256 * 256
    # Exact-completion table bound (distinct full prefixes in the corpus).
    # Decoupled from MAX_VALUE_PAIRS: this table tracks corpus prefixes, not the
    # 256x256 value-pair space; 1M entries ~= 50 MB, far inside the 2 GiB cap.
    MAX_EXACT_COMPLETIONS = 1000000
    DEFAULT_MAX_SEQ = 512
    UNKNOWN = "?"
    # Prefix recall context depth: how many left-context chars are used to
    # disambiguate an unknown slot. A short window (6) keeps memory bounded;
    # the full-context exact recall path (exact_completions) handles the case
    # where the whole query prefix was seen verbatim in training.
    PREFIX_DEPTH = 6
    CONF_EXACT = 0.95
    CONF_POSITION = 0.60
    CONF_BIGRAM = 0.55
    CONF_GLOBAL = 0.50
    CONF_NONE = 0.0

    def __init__(
        self,
        memory_cap_mb: Optional[float] = None,
        max_seq_len: int = DEFAULT_MAX_SEQ,
        value_pair_cap: int = MAX_VALUE_PAIRS,
        exact_completions_cap: int = MAX_EXACT_COMPLETIONS,
    ) -> None:
        self.max_seq_len = max_seq_len
        self.value_pair_cap = value_pair_cap
        self.exact_completions_cap = exact_completions_cap
        self.memory_cap_mb = memory_cap_mb
        self._lock = threading.RLock()
        # Position x content: position -> utf8 value -> count (sparse matrix).
        self._position_content: Dict[int, Dict[int, int]] = {}
        # Bigram transition: (left_utf8, right_utf8) -> count.
        self._transitions: Dict[Tuple[int, int], int] = OrderedDict()
        # Prefix recall: (left-context up to PREFIX_DEPTH chars) -> next utf8 value
        # -> count. This is the bounded neighbour-context disambiguation shown
        # in the chain-matrix verification experiment.
        self._prefix_recall: Dict[Tuple[int, ...], Dict[int, int]] = OrderedDict()
        # Exact completions: full known context (bounded count) -> next value.
        # Resolves queries whose entire prefix was seen verbatim in training,
        # removing the short-window ambiguity of _prefix_recall.
        self._exact_completions: Dict[Tuple[int, ...], Dict[int, int]] = OrderedDict()
        # Anchor alignment (learned, EM): normalized problem -> answer counts.
        # Built after AnchorLearner converges; grants sliding alignment so
        # whitespace/leading-word variants align to the same key.
        self._anchor_problems: Dict[str, Dict[str, int]] = OrderedDict()
        # Suffix index: normalized problem suffix -> aggregated answer counts,
        # used for prefix-insensitive lookup when the full key is absent.
        self._anchor_suffixes: Dict[str, Dict[str, int]] = OrderedDict()
        self._anchor_learner = AnchorLearner()
        self._corpus_chars = 0
        self._last_confidence = 0.0
        self._last_route = ""
        self._frozen = False
        # Maintained memory estimate (cheap, no per-call recompute).
        self._est_bytes = 1024
        self._resolve_memory_cap()

    # ------------------------------------------------------------------
    # Memory cap
    # ------------------------------------------------------------------
    def _resolve_memory_cap(self) -> None:
        """Resolve the effective memory cap from project capacity config."""
        if self.memory_cap_mb is not None:
            self._cap_bytes = int(self.memory_cap_mb * 1024 * 1024)
            return
        try:
            ram_total = _probe_ram_total_gb()
            self._cap_bytes = int(
                effective_capacity_bytes("memory", total_gb=ram_total, numeric_mb=2048)
            )
        except Exception:  # pragma: no cover - defensive fallback
            self._cap_bytes = 2048 * 1024 * 1024
        if self._cap_bytes <= 0:
            self._cap_bytes = 2048 * 1024 * 1024

    @property
    def memory_cap_bytes(self) -> int:
        return self._cap_bytes

    def estimate_memory_bytes(self) -> int:
        """Estimate resident memory of the engine's data structures."""
        return self._est_bytes

    def memory_usage_ratio(self) -> float:
        """Fraction (0..1+) of the memory cap currently in use."""
        return self.estimate_memory_bytes() / max(1, self._cap_bytes)

    def _enforce_memory_cap(self) -> None:
        """Graceful degradation under the RAM cap.

        If the bigram table exceeds the cap, drop the oldest entries (LRU).
        This mirrors the project's "precision" loss model (evict LRU, never
        cross-cut).
        """
        if self._est_bytes <= self._cap_bytes:
            return
        while self._transitions and self._est_bytes > self._cap_bytes:
            self._transitions.popitem(last=False)  # oldest entry
            self._est_bytes -= _estimate_entry_bytes()
        logger.debug(
            "three_axis: pruned transition table to %d entries (cap %d bytes)",
            len(self._transitions),
            self._cap_bytes,
        )

    def _trim_transitions(self) -> None:
        """Drop lowest-support bigram entries when over the value-pair cap."""
        if len(self._transitions) <= self.value_pair_cap:
            return
        ordered = sorted(self._transitions.items(), key=lambda kv: kv[1], reverse=True)
        dropped = len(self._transitions) - self.value_pair_cap
        self._transitions = OrderedDict(ordered[: self.value_pair_cap])
        self._est_bytes = max(1024, self._est_bytes - dropped * _estimate_entry_bytes())

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def learn(self, text: str) -> None:
        """Learn one text sample (UTF-8 values at positions, bigram stats)."""
        with self._lock:
            if self._frozen:
                return
            vals = [ord(c) for c in text]
            self._corpus_chars += len(vals)
            for pos, v in enumerate(vals[: self.max_seq_len]):
                cells = self._position_content.get(pos)
                if cells is None:
                    cells = {}
                    self._position_content[pos] = cells
                    self._est_bytes += 40  # new position row overhead
                if v not in cells:
                    self._est_bytes += 24  # new value cell
                cells[v] = cells.get(v, 0) + 1
            for i in range(len(vals) - 1):
                key = (vals[i], vals[i + 1])
                if key not in self._transitions:
                    self._est_bytes += _estimate_entry_bytes()
                self._transitions[key] = self._transitions.get(key, 0) + 1
            # Prefix recall: bounded left-context -> next value occurrence.
            for i in range(1, len(vals)):
                start = max(0, i - self.PREFIX_DEPTH)
                prefix = tuple(vals[start:i])
                nxt = vals[i]
                cell = self._prefix_recall.get(prefix)
                if cell is None:
                    cell = {}
                    self._prefix_recall[prefix] = cell
                    self._est_bytes += 8 + 24
                if nxt not in cell:
                    self._est_bytes += 24
                cell[nxt] = cell.get(nxt, 0) + 1
            # Exact completions: full known context -> next value.
            for i in range(1, len(vals)):
                prefix = tuple(vals[:i])
                nxt = vals[i]
                cell = self._exact_completions.get(prefix)
                if cell is None:
                    cell = {}
                    self._exact_completions[prefix] = cell
                    self._est_bytes += 8 + len(prefix) * 4 + 24
                if nxt not in cell:
                    self._est_bytes += 24
                cell[nxt] = cell.get(nxt, 0) + 1
            self._trim_exact_completions()
            self._trim_prefix_recall()
            self._trim_transitions()
            self._enforce_memory_cap()

    def _trim_exact_completions(self) -> None:
        """Bound the exact-completion table (LRU eviction of oldest prefixes)."""
        if len(self._exact_completions) <= self.exact_completions_cap:
            return
        while len(self._exact_completions) > self.exact_completions_cap:
            k, v = self._exact_completions.popitem(last=False)
            self._est_bytes -= 8 + len(k) * 4 + 24 * len(v)

    def _trim_prefix_recall(self) -> None:
        """Bound the prefix-recall table (LRU: drop oldest-inserted prefixes)."""
        if len(self._prefix_recall) <= self.value_pair_cap * 2:
            return
        while len(self._prefix_recall) > self.value_pair_cap * 2:
            k, v = self._prefix_recall.popitem(last=False)
            self._est_bytes -= 8 + 24 * len(v)

    def learn_batch(self, samples: List[str]) -> Dict[str, Any]:
        """Train from a list of text samples. Returns training stats."""
        with self._lock:
            for text in samples:
                self.learn(text)
            self._learn_anchors(samples)
            return {
                "samples": len(samples),
                "corpus_chars": self._corpus_chars,
                "positions": len(self._position_content),
                "transitions": len(self._transitions),
                "prefix_recall": len(self._prefix_recall),
                "exact_completions": len(self._exact_completions),
                "anchor_problems": len(self._anchor_problems),
                "anchor_suffixes": len(self._anchor_suffixes),
                "memory_bytes": self.estimate_memory_bytes(),
                "memory_cap_bytes": self._cap_bytes,
                "memory_ratio": round(self.memory_usage_ratio(), 3),
            }

    # ------------------------------------------------------------------
    # Anchor alignment (learned, EM)
    # ------------------------------------------------------------------
    def _learn_anchors(self, samples: List[str]) -> None:
        """EM-learn the alignment anchor set, then build problem/answer tables.

        The AnchorLearner converges on the delimiter set from data (on real
        arithmetic data: ``{=, -, .}``). Using the converged anchors, every
        sample is split into ``problem | delimiter | answer``; problems are
        whitespace-collapsed and indexed by full key plus suffixes, giving the
        position axis a *sliding alignment* freedom: queries differing by
        whitespace or leading words align to the same answer.
        """
        self._anchor_learner.learn(samples)
        anchors = self._anchor_learner.anchors
        problem_counts: Dict[str, Dict[str, int]] = {}
        suffix_counts: Dict[str, Dict[str, int]] = {}
        for text in samples:
            parts = self._anchor_learner.align(text)
            if parts is None:
                continue
            problem, delimiter, answer = parts
            key = AnchorLearner.normalize(problem)
            if not key:
                continue
            cell = problem_counts.get(key)
            if cell is None:
                cell = {}
                problem_counts[key] = cell
            cell[answer] = cell.get(answer, 0) + 1
            for L in range(len(key), 0, -1):
                suf = key[len(key) - L :]
                scell = suffix_counts.get(suf)
                if scell is None:
                    scell = {}
                    suffix_counts[suf] = scell
                scell[answer] = scell.get(answer, 0) + 1
        self._anchor_problems = OrderedDict(problem_counts)
        self._anchor_suffixes = OrderedDict(suffix_counts)
        # Rough memory accounting for the new tables.
        for key, cell in problem_counts.items():
            self._est_bytes += len(key) * 4 + 24 * len(cell)
        for suf in suffix_counts:
            self._est_bytes += len(suf) * 4

    def _lookup_anchor(self, query: str) -> Optional[str]:
        """Look up an answer via learned anchor alignment.

        Strategy: strip trailing ``?``/whitespace, whitespace-collapse the
        problem, try the full key; if absent, walk the suffix index from the
        longest suffix and require an *unambiguous* answer (single distinct
        answer across all problems sharing that suffix) — otherwise keep
        shortening. Returns the answer string or None.
        """
        q = query.rstrip("? ").rstrip("=").rstrip(" ")
        key = AnchorLearner.normalize(q)
        if not key:
            return None
        cell = self._anchor_problems.get(key)
        if cell and len(cell) == 1:
            return next(iter(cell))
        for L in range(len(key), 0, -1):
            suf = key[len(key) - L :]
            scell = self._anchor_suffixes.get(suf)
            if scell and len(scell) == 1:
                return next(iter(scell))
        return None

    # ------------------------------------------------------------------
    # Dialogue / inference
    # ------------------------------------------------------------------
    def process(self, text: str, context: Optional[str] = None) -> str:
        """Answer a query by resolving every ``?`` unknown position.

        When the query ends with ``?`` (result position), the engine recursively
        generates the answer character-by-character using prefix recall, feeding
        each predicted char back into the context (StepDecoder-style). This is
        the three-axis equivalent of iterative decoding: the position axis is
        traversed left-to-right, each step's value fixed by the content axis
        association.
        """
        with self._lock:
            if not text:
                self._last_confidence = self.CONF_NONE
                self._last_route = "none"
                return ""
            if text.endswith(self.UNKNOWN):
                prompt = text[:-1]
                answer = self._lookup_anchor(prompt)
                if answer is not None:
                    self._last_confidence = self.CONF_EXACT
                    self._last_route = "anchor-aligned"
                    return f"{prompt.rstrip('=? ')}={answer}"
                return self.generate(prompt)
            targets = [i for i, c in enumerate(text) if c == self.UNKNOWN]
            if not targets:
                self._last_confidence = 1.0
                self._last_route = "no-unknown"
                return text

            out = list(text)
            best_conf = self.CONF_NONE
            best_route = "none"
            for t in targets:
                pred, conf, route = self._resolve_position(text, t)
                if pred is not None:
                    out[t] = chr(pred)
                if conf > best_conf:
                    best_conf, best_route = conf, route
            self._last_confidence = best_conf
            self._last_route = best_route
            return "".join(out)

    def generate(self, prompt: str, max_new: int = 32) -> str:
        """Generate continuation from a prompt via recursive exact-completion.

        Each step predicts the next char by looking up the *full* known context
        in the exact-completion table (the verbatim-prefix recall path) and
        appends it. Generation continues only while the whole prefix was seen
        continued in training (route == ``exact-completion``). When the full
        context is no longer followed by anything in the corpus — i.e. the end
        of a memorised answer — generation stops.

        The short-window prefix-recall path is deliberately NOT used for
        continuation: it is ambiguous (a truncated context such as ``92=101``
        collides with ``827 + 192=1019``) and produced trailing garbage. It
        remains available for single-step ``resolve`` fallback.
        """
        with self._lock:
            out = prompt
            last_conf = self.CONF_NONE
            last_route = "none"
            for _ in range(max_new):
                pred, conf, route = self._resolve_position(out, len(out))
                last_conf, last_route = conf, route
                if pred is None or route != "exact-completion":
                    break
                out += chr(pred)
            self._last_confidence = last_conf
            self._last_route = last_route
            return out

    def _resolve_position(
        self, text: str, t: int
    ) -> Tuple[Optional[int], float, str]:
        """Resolve a single unknown position via precedence-ordered rules."""
        # 1. exact-completion: full known context seen verbatim -> next value.
        full_prefix = tuple(ord(c) for c in text[:t])
        if full_prefix:
            cell = self._exact_completions.get(full_prefix)
            if cell:
                best = max(cell.items(), key=lambda kv: kv[1])
                return (best[0], self.CONF_EXACT, "exact-completion")

        # 2. prefix-recall: bounded left-context seen in training -> next value.
        if t > 0:
            start = max(0, t - self.PREFIX_DEPTH)
            prefix = tuple(ord(c) for c in text[start:t])
            cell = self._prefix_recall.get(prefix)
            if cell:
                best = max(cell.items(), key=lambda kv: kv[1])
                return (best[0], self.CONF_EXACT, "prefix-recall")

        cells = self._position_content.get(t)

        # 2. position-exact: only one value ever observed at this position.
        if cells and len(cells) == 1:
            return (next(iter(cells)), self.CONF_POSITION, "position-exact")

        # 3. position-majority: most frequent value at this position.
        if cells:
            best = max(cells.items(), key=lambda kv: kv[1])
            return (best[0], self.CONF_POSITION, "position-majority")

        # 4. bigram transition: predict from the left neighbour value.
        if t > 0:
            left = ord(text[t - 1])
            candidates = {
                right: cnt
                for (l, right), cnt in self._transitions.items()
                if l == left
            }
            if candidates:
                best_right = max(candidates.items(), key=lambda kv: kv[1])[0]
                return (best_right, self.CONF_BIGRAM, "bigram-transition")

        # 5. global majority content value.
        global_mode = self._global_mode()
        if global_mode is not None:
            return (global_mode, self.CONF_GLOBAL, "global-majority")
        return (None, self.CONF_NONE, "none")

    def _global_mode(self) -> Optional[int]:
        counts: Dict[int, int] = {}
        for cells in self._position_content.values():
            for v, c in cells.items():
                counts[v] = counts.get(v, 0) + c
        if not counts:
            return None
        return max(counts.items(), key=lambda kv: kv[1])[0]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save(self, path: str) -> None:
        """Save the engine state to a JSON checkpoint."""
        with self._lock:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
            state = {
                "format": "three_axis/1",
                "max_seq_len": self.max_seq_len,
                "value_pair_cap": self.value_pair_cap,
                "corpus_chars": self._corpus_chars,
                "position_content": {str(p): cells for p, cells in self._position_content.items()},
                "transitions": {
                    f"{k[0]},{k[1]}": v for k, v in self._transitions.items()
                },
                "prefix_recall": {
                    ",".join(str(x) for x in k): v for k, v in self._prefix_recall.items()
                },
                "exact_completions": {
                    ",".join(str(x) for x in k): v for k, v in self._exact_completions.items()
                },
                "anchor_problems": {
                    k: v for k, v in self._anchor_problems.items()
                },
                "anchor_suffixes": {
                    k: v for k, v in self._anchor_suffixes.items()
                },
                "anchor_set": sorted(self._anchor_learner.anchors),
                "anchor_rounds": self._anchor_learner.rounds,
                "anchor_converged": self._anchor_learner.converged,
            }
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(state, fh)

    def load(self, path: str) -> bool:
        """Load a checkpoint. Returns False (and resets to empty) on failure."""
        if not os.path.exists(path):
            logger.warning("three_axis: checkpoint %s not found", path)
            return False
        try:
            with open(path, "r", encoding="utf-8") as fh:
                state = json.load(fh)
            self._position_content = {
                int(p): {int(k): int(v) for k, v in cells.items()}
                for p, cells in state.get("position_content", {}).items()
            }
            self._transitions = OrderedDict(
                (tuple(int(x) for x in k.split(",")), v)
                for k, v in state.get("transitions", {}).items()
            )
            self._prefix_recall = OrderedDict(
                (
                    tuple(int(x) for x in k.split(",")),
                    {int(vk): int(vv) for vk, vv in v.items()},
                )
                for k, v in state.get("prefix_recall", {}).items()
            )
            self._exact_completions = OrderedDict(
                (
                    tuple(int(x) for x in k.split(",")),
                    {int(vk): int(vv) for vk, vv in v.items()},
                )
                for k, v in state.get("exact_completions", {}).items()
            )
            self._anchor_problems = OrderedDict(
                (k, dict(v)) for k, v in state.get("anchor_problems", {}).items()
            )
            self._anchor_suffixes = OrderedDict(
                (k, dict(v)) for k, v in state.get("anchor_suffixes", {}).items()
            )
            anchor_set = state.get("anchor_set")
            if anchor_set:
                self._anchor_learner.anchors = set(anchor_set)
                self._anchor_learner.rounds = state.get("anchor_rounds", 0)
                self._anchor_learner.converged = state.get("anchor_converged", False)
            self._corpus_chars = state.get("corpus_chars", 0)
            self.max_seq_len = state.get("max_seq_len", self.max_seq_len)
            self.value_pair_cap = state.get("value_pair_cap", self.value_pair_cap)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("three_axis: failed to load %s: %s", path, exc)
            self._position_content = {}
            self._transitions = OrderedDict()
            self._prefix_recall = OrderedDict()
            self._exact_completions = OrderedDict()
            self._anchor_problems = OrderedDict()
            self._anchor_suffixes = OrderedDict()
            self._corpus_chars = 0
            return False

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @property
    def last_confidence(self) -> float:
        return self._last_confidence

    @property
    def corpus_chars(self) -> int:
        return self._corpus_chars

    def freeze(self) -> None:
        """Freeze training (dialogue mode)."""
        self._frozen = True

    def unfreeze(self) -> None:
        self._frozen = False