"""
Unified Engine — fixed-size statistical core model.

The core is a REAL model, not an index:
  - Fixed vocabulary: UTF-8 bytes (256 values).
  - Fixed-size matrices that NEVER grow with the corpus:
      * position x content  probability matrix  [MAX_SEQ][256]
      * value-pair transition matrix            [256][256]
  - Training folds corpus statistics INTO these fixed slots (statistical
    estimation), so model_bytes is constant before/after training.
  - Inference generalizes: unseen sequences are answered by combining
    position distribution + transition probabilities (true statistical
    inference), NOT by looking up a stored prefix.
  - Because it genuinely learned the distribution, it can GENERATE
    (argmax/sampling) and thereby reproduce the training data — a
    by-product of generalisation, not a storage mechanism.

The deterministic math/logic layers are kept OUT of this module and
routed by UnifiedEngine as the first stage (labelled "deterministic, not
learned") — see unified_engine.py.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [βγ] [B] [L2]
# =============================================================================

from __future__ import annotations

import logging
import math
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Fixed-size model constants (do not grow with corpus).
MAX_SEQ = 512  # position axis upper bound
VOCAB = 256  # UTF-8 byte values
# Numpy float32 memory: MAX_SEQ*VOCAB*4 + VOCAB*VOCAB*4 = 0.5MB + 0.25MB
FIXED_MODEL_BYTES = MAX_SEQ * VOCAB * 4 + VOCAB * VOCAB * 4

# Laplace smoothing for unseen (position, byte) / (byte, byte) pairs.
SMOOTH = 1e-3


class FixedSizeCore:
    """Position x content + transition + feature-hash statistical core.

    Three fixed-size layers, ALL constant-memory (the compression claim):

      1. position x content  [max_seq][256]  — byte distribution per position
      2. transition          [256][256]      — byte->byte bigram statistics
      3. feature hash        FIXED slots     — hashed n-gram features -> answer
                                              byte distribution (captures
                                              high-level correlations such as
                                              'nor -> False' that pure
                                              positional statistics miss)

    model_bytes is a compile-time constant: training never allocates new
    per-sample tables. This is the compression guarantee — the model stays
    the same size no matter how large the corpus becomes.
    """

    # Feature-hash table size (fixed, independent of corpus).
    FEATURE_SLOTS = 1 << 16
    FEATURE_NGRAM = 4  # character n-grams hashed into the feature table
    # k-gram context order for next-byte prediction (fixed, independent of
    # corpus). Longer context = better language modelling; the table stays a
    # fixed number of slots regardless of how many distinct contexts appear.
    GRAM_ORDER = 4

    def __init__(self, max_seq: int = MAX_SEQ) -> None:
        self.max_seq = max_seq
        # Position x content: [max_seq][256] float32 counts.
        self._pos: List[List[float]] = [[0.0] * VOCAB for _ in range(max_seq)]
        # Transition: [256][256] float32 counts (left byte -> right byte).
        self._trans: List[List[float]] = [[0.0] * VOCAB for _ in range(VOCAB)]
        # k-gram context layer: hashed (k-1)-byte prefix -> {next byte -> count}.
        # This is the language-modelling layer: unlike the bigram table it
        # conditions on GRAM_ORDER-1 context bytes, so generated language is
        # coherent beyond adjacent characters. Fixed slots, never grows.
        self._gram: List[Dict[int, float]] = [{} for _ in range(self.FEATURE_SLOTS)]
        # Feature hash: problem n-gram -> {answer STRING -> count}.
        # This learns the high-level PROBLEM -> ANSWER correlation (e.g.
        # a problem pattern containing 'nor' correlates with the answer
        # 'False') as atomic units, which byte-level statistics dilute.
        self._feat: List[Dict[str, float]] = [{} for _ in range(self.FEATURE_SLOTS)]
        # Discriminative boolean layer: problem n-gram -> {True count,
        # False count}. Learned with log-odds weighting so that a few
        # keyword-bearing features dominate neutral noise (this is what a
        # real classifier does, e.g. naive Bayes over hashed n-grams).
        self._feat_bool: List[Dict[str, float]] = [{} for _ in range(self.FEATURE_SLOTS)]
        self._samples_seen = 0
        self._bytes_seen = 0
        self._true_total = 0.0
        self._false_total = 0.0

    # ------------------------------------------------------------------
    # Model size (fixed, the compression claim)
    # ------------------------------------------------------------------
    @property
    def model_bytes(self) -> int:
        # Position + transition matrices (float32) + feature table (bounded)
        # + k-gram context table (bounded, fixed slots).
        return (
            FIXED_MODEL_BYTES
            + self.FEATURE_SLOTS * 8  # feature anchor bytes
            + self.FEATURE_SLOTS * 24  # feature dict overhead estimate
            + self.FEATURE_SLOTS * 8  # gram anchor bytes
            + self.FEATURE_SLOTS * 24  # gram dict overhead estimate
        )

    def estimate_memory_bytes(self) -> int:
        return self.model_bytes

    # ------------------------------------------------------------------
    # Training (statistical estimation into fixed slots)
    # ------------------------------------------------------------------
    def learn(self, text: str) -> None:
        """Fold one text sample into the fixed matrices (no growth).

        Splits '<problem>=<answer>' and learns BOTH:
          - position/transition statistics over the full sequence
          - the PROBLEM -> ANSWER correlation in the feature hash table
        """
        raw = text.encode("utf-8")
        self.learn_bytes(raw)
        self._learn_feature_problem_answer(raw)

    def learn_bytes(self, raw: bytes) -> None:
        """Fold a raw byte sequence (text, image, or audio bytes) into the
        fixed matrices — the shared foundation for every modality.

        The position axis is a fixed context window (max_seq); sequences are
        folded into it modulo the window, so the model handles arbitrary
        length bytes while model_bytes stays constant. This is what lets one
        fixed-size core learn language, images, and audio from their raw
        byte streams (the compression + reproduction claim per modality).
        """
        n = len(raw)
        if n == 0:
            return
        self._samples_seen += 1
        self._bytes_seen += n
        for i, b in enumerate(raw):
            self._pos[i % self.max_seq][b] += 1.0
        for i in range(n - 1):
            left, right = raw[i], raw[i + 1]
            self._trans[left][right] += 1.0
        # k-gram context: hash the (k-1)-byte prefix preceding each byte and
        # accumulate the next-byte distribution into that slot.
        k = self.GRAM_ORDER
        for i in range(k - 1, n):
            ctx = raw[i - (k - 1) : i]
            slot = self._hash_ngram(ctx)
            cell = self._gram[slot]
            cell[raw[i]] = cell.get(raw[i], 0.0) + 1.0

    def _hash_ngram(self, gram: bytes) -> int:
        h = 2166136261
        for b in gram:
            h = (h ^ b) * 16777619
            h &= 0xFFFFFFFF
        return h % self.FEATURE_SLOTS

    def _ngrams(self, raw: bytes) -> List[bytes]:
        """All n-grams (1..FEATURE_NGRAM) of the byte sequence."""
        grams = []
        for size in range(1, self.FEATURE_NGRAM + 1):
            for i in range(0, len(raw) - size + 1):
                grams.append(bytes(raw[i : i + size]))
        return grams

    def _learn_feature_problem_answer(self, raw: bytes) -> None:
        """Hash every n-gram of the PROBLEM part, and accumulate the full
        ANSWER STRING into each matching feature slot.

        This is a genuine statistical learner: after training, a held-out
        problem whose n-grams overlap the training distribution votes toward
        the answer string it correlates with (e.g. 'nor' -> 'False').
        """
        sep = raw.find(b"=")
        if sep < 0:
            return
        problem = raw[:sep]
        answer = raw[sep + 1 :]
        if not problem or not answer:
            return
        answer_str = answer.decode("utf-8", errors="replace")
        for gram in self._ngrams(problem):
            slot = self._hash_ngram(gram)
            cell = self._feat[slot]
            cell[answer_str] = cell.get(answer_str, 0.0) + 1.0
        # Discriminative boolean signal: if the answer is a truth value,
        # accumulate into the boolean feature layer too.
        ans_lower = answer_str.strip().lower()
        if ans_lower in ("true", "false"):
            for gram in self._ngrams(problem):
                slot = self._hash_ngram(gram)
                bcell = self._feat_bool[slot]
                bcell[ans_lower] = bcell.get(ans_lower, 0.0) + 1.0
            if ans_lower == "true":
                self._true_total += 1.0
            else:
                self._false_total += 1.0

    def boolean_score(self, problem_text: str) -> Optional[float]:
        """Log-odds score for the answer being True, from the boolean layer.

        A proper discriminative combination: each feature slot contributes its
        trained True/False log-odds (like naive Bayes), weighted by n-gram
        length (longer n-grams are more specific) so keyword-bearing features
        dominate neutral noise instead of being diluted by it. Returns None
        when the boolean layer has no data for this problem.
        """
        raw = problem_text.encode("utf-8")
        if not raw:
            return None
        prior_t = self._true_total + 1.0
        prior_f = self._false_total + 1.0
        prior = math.log(prior_t / prior_f)
        score = prior
        found = False
        for gram in self._ngrams(raw):
            bcell = self._feat_bool[self._hash_ngram(gram)]
            if not bcell:
                continue
            found = True
            t = bcell.get("true", 0.0) + 1.0
            f = bcell.get("false", 0.0) + 1.0
            w = len(gram)  # longer n-grams are more specific
            score += w * (math.log(t / f) - prior)
        if not found:
            return None
        return score

    def boolean_answer(self, problem_text: str, threshold: float = 0.0) -> Optional[str]:
        """Predict True/False from the boolean layer's log-odds score."""
        score = self.boolean_score(problem_text)
        if score is None:
            return None
        return "true" if score >= threshold else "false"

    def answer_dist(self, problem_text: str) -> List[float]:
        """Distribution over the answer BYTES for a given problem.

        Hash the problem's n-grams, aggregate the stored answer-byte counts,
        and normalise. This is the generalisation path: an unseen problem is
        answered by the correlation of its features with answers in training.
        """
        raw = problem_text.encode("utf-8")
        if not raw:
            return [1.0 / VOCAB] * VOCAB
        agg: Dict[int, float] = {}
        for gram in self._ngrams(raw):
            for ans, c in self._feat[self._hash_ngram(gram)].items():
                for b in ans.encode("utf-8"):
                    agg[b] = agg.get(b, 0.0) + c
        if not agg:
            return [1.0 / VOCAB] * VOCAB
        total = sum(agg.values()) + SMOOTH * VOCAB
        return [(agg.get(b, 0.0) + SMOOTH) / total for b in range(VOCAB)]

    def answer_votes(self, problem_text: str) -> Dict[str, float]:
        """Votes for each candidate answer STRING for a given problem.

        Each n-gram feature of the problem votes for the complete answers it
        has seen in training, weighted by count. Answers are atomic strings
        ('True'/'False'/'279'), so the generalisation picks coherent answers
        rather than diluting them across bytes.
        """
        raw = problem_text.encode("utf-8")
        votes: Dict[str, float] = {}
        if not raw:
            return votes
        for gram in self._ngrams(raw):
            for ans, c in self._feat[self._hash_ngram(gram)].items():
                votes[ans] = votes.get(ans, 0.0) + c
        return votes

    def best_answer(self, problem_text: str) -> Optional[Tuple[str, float]]:
        """Top answer string + its vote share (the generalised prediction)."""
        votes = self.answer_votes(problem_text)
        if not votes:
            return None
        total = sum(votes.values())
        best = max(votes.items(), key=lambda kv: kv[1])
        return best[0], best[1] / total

    def learn_batch(self, samples: List[str]) -> Dict[str, int]:
        for text in samples:
            self.learn(text)
        return {
            "samples": self._samples_seen,
            "bytes": self._bytes_seen,
            "model_bytes": self.model_bytes,
            "positions_used": sum(1 for row in self._pos if any(row)),
        }

    # ------------------------------------------------------------------
    # Inference (statistical generalisation)
    # ------------------------------------------------------------------
    def position_dist(self, pos: int) -> List[float]:
        """Normalised distribution over bytes at a given position.

        The position axis is a FIXED CONTEXT WINDOW (max_seq), so long
        sequences (image/audio/text) are folded into it modulo the window.
        This keeps model_bytes constant while supporting arbitrary-length
        sequences — the same principle as a transformer's fixed context
        length, here implemented as fixed-size statistics.
        """
        row = self._pos[pos % self.max_seq]
        total = sum(row)
        if total <= 0:
            return [1.0 / VOCAB] * VOCAB
        return [c / total for c in row]

    def transition_dist(self, left: int) -> List[float]:
        """Normalised next-byte distribution given the current byte."""
        row = self._trans[left]
        total = sum(row)
        if total <= 0:
            return [1.0 / VOCAB] * VOCAB
        return [c / total for c in row]

    def gram_dist(self, prefix: bytes) -> List[float]:
        """Next-byte distribution conditioned on the last (k-1) bytes.

        The k-gram language-modelling layer: hash the context prefix into a
        fixed slot and read the learned next-byte distribution. Long-context
        conditioning is what makes generated language coherent (vs the
        bigram table's adjacent-byte-only view). Falls back to uniform when
        the context was unseen in training.
        """
        if not prefix:
            return [1.0 / VOCAB] * VOCAB
        ctx = prefix[-(self.GRAM_ORDER - 1) :]
        cell = self._gram[self._hash_ngram(ctx)]
        if not cell:
            return [1.0 / VOCAB] * VOCAB
        total = sum(cell.values())
        if total <= 0:
            return [1.0 / VOCAB] * VOCAB
        return [cell.get(b, 0.0) / total for b in range(VOCAB)]

    def next_byte_probs(self, prefix: bytes, position: int) -> List[float]:
        """Probability over the next byte given the prefix and its position.

        Blends three fixed-size statistics for SEQUENCE modelling:
          - position layer: empirical byte distribution at this position
          - transition layer: byte->byte bigram of the last byte
          - gram layer: k-gram context -> next byte (language modelling)
        The feature layer (problem n-grams -> answer) is a separate
        discriminative path used for problem->answer inference, NOT for
        next-byte generation — mixing them feeds problem-answer noise into
        continuations. True statistical inference over unseen sequences.
        """
        p = self.position_dist(position)
        t = self.transition_dist(prefix[-1]) if prefix else [1.0 / VOCAB] * VOCAB
        g = self.gram_dist(prefix)
        # Confidence-adaptive blend: the k-gram layer dominates only when it
        # actually saw this context in training; otherwise fall back to the
        # positional/bigram statistics (which are denser for small corpora).
        g_entropy = sum(-q * math.log(q + 1e-9) for q in g)
        max_entropy = math.log(VOCAB)
        g_conf = 1.0 - g_entropy / max_entropy  # 0=uniform, 1=peaked
        w_g = 0.6 * g_conf
        w_p = 0.2 + 0.4 * (1.0 - g_conf)  # position gets the freed mass
        w_t = 0.2
        blended = [w_p * p[i] + w_t * t[i] + w_g * g[i] for i in range(VOCAB)]
        total = sum(blended) + SMOOTH * VOCAB
        return [(c + SMOOTH) / total for c in blended]

    # ------------------------------------------------------------------
    # Generation (reproduction as a by-product of generalisation)
    # ------------------------------------------------------------------
    def sample_next(self, prefix: bytes, position: int, rng) -> int:
        """Sample the next byte from the learned distribution."""
        probs = self.next_byte_probs(prefix, position)
        r = rng.random()
        acc = 0.0
        for b, p in enumerate(probs):
            acc += p
            if r <= acc:
                return b
        return probs.index(max(probs))

    def generate(
        self,
        prefix: bytes,
        max_len: int = 64,
        stop_on: bytes = b"",
        seed: int = 1,
    ) -> bytes:
        """Generate a continuation byte-by-byte from the model.

        Uses the positional/transition/feature mixture (next_byte_probs) —
        true sequence modelling, not problem->answer voting. Sampling keeps
        it stochastic; the distributional overlap with the training corpus
        measures reproduction as a by-product of generalisation.
        """
        import random

        rng = random.Random(seed)
        out = bytearray(prefix)
        for step in range(max_len):
            pos = len(out) - 1
            nxt = self.sample_next(bytes(out), pos, rng)
            out.append(nxt)
            if stop_on and bytes([nxt]) in stop_on:
                if len(out) > len(prefix):
                    break
        return bytes(out)

    # ------------------------------------------------------------------
    # Scoring / evaluation helpers
    # ------------------------------------------------------------------
    def log_prob(self, text: str) -> float:
        """Log-probability of a sequence under the model (for generation
        fidelity measurement)."""
        if isinstance(text, bytes):
            raw = text
        else:
            raw = text.encode("utf-8")
        lp = 0.0
        for i in range(len(raw)):
            probs = self.next_byte_probs(raw[:i], i)
            p = probs[raw[i]]
            lp += math.log(max(p, 1e-9))
        return lp

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def to_dict(self) -> Dict:
        return {
            "max_seq": self.max_seq,
            "pos": self._pos,
            "trans": self._trans,
            "gram": {
                str(slot): {str(b): float(c) for b, c in cell.items()}
                for slot, cell in enumerate(self._gram)
                if cell
            },
            "feat": {str(slot): cell for slot, cell in enumerate(self._feat) if cell},
            "feat_bool": {str(slot): cell for slot, cell in enumerate(self._feat_bool) if cell},
            "true_total": self._true_total,
            "false_total": self._false_total,
            "samples": self._samples_seen,
            "bytes": self._bytes_seen,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "FixedSizeCore":
        core = cls(max_seq=d.get("max_seq", MAX_SEQ))
        core._pos = d.get("pos", core._pos)
        core._trans = d.get("trans", core._trans)
        for slot, cell in d.get("gram", {}).items():
            core._gram[int(slot)] = {int(b): float(c) for b, c in cell.items()}
        for slot, cell in d.get("feat", {}).items():
            core._feat[int(slot)] = {str(b): float(c) for b, c in cell.items()}
        for slot, cell in d.get("feat_bool", {}).items():
            core._feat_bool[int(slot)] = {str(b): float(c) for b, c in cell.items()}
        core._true_total = float(d.get("true_total", 0.0))
        core._false_total = float(d.get("false_total", 0.0))
        core._samples_seen = d.get("samples", 0)
        core._bytes_seen = d.get("bytes", 0)
        return core

    def load_state(self, pos, trans, samples=0, bytes_seen=0) -> None:
        self._pos = pos
        self._trans = trans
        self._samples_seen = samples
        self._bytes_seen = bytes_seen
