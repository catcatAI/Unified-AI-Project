"""The intermediate layer between the neural model and the deterministic teacher.

The deterministic engine (``ai.symbolic_reasoner``) answers comparison chains
with a *fixed* vocabulary: it knows "taller", "bigger", "older", "colder", ...
Anything outside that list ("X exceeds Y", "A outranks B", "X is cooler than
Y") is invisible to it.

This module is the middle layer the user asked for:

1. **接觸 (contact)** — the relation phrase is found *semantically*: the
   shipped multilingual encoder projects the phrase onto the concept
   prototypes (dimension, direction), so "cooler" lands on the temperature
   concept even though the teacher never mentions it.
2. **對齊 (alignment)** — when the teacher does answer, the phrase is fed
   back and the *concept prototype* moves one step toward it. The prototype
   is aligned, never the question, so the layer keeps generalising.
3. **合成 (composition)** — the relations become a graph and the question's
   superlative picks the entity (the greatest = no incoming edge, the least
   = no outgoing edge), exactly the semantics the teacher uses.

Nothing here memorises questions: the alignment step only moves prototypes.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# The concept lattice
# --------------------------------------------------------------------------- #
# A concept is (dimension, direction). The dimension says *what* is compared
# (so "youngest" and "coldest" are not confused), the direction says which
# way the relation points.
GREATER = "greater"
LESSER = "lesser"
GREATEST = "greatest"
LEAST = "least"
# The dimension of a relation the structure states but the words do not
# ("A > B"): it fits any dimension.
ANY_DIMENSION = "*"

# (dimension, direction) -> the teacher's seed phrases. These are exactly the
# words the deterministic engine knows (``ai.symbolic_reasoner._GREATER`` /
# ``_LESSER`` / ``_EXTRA_GREATER`` / ``_EXTRA_LESSER``); the layer
# *generalises* from them. No word that is not in the teacher's vocabulary
# may enter this table, otherwise the generalisation claim is false.
CONCEPT_SEEDS: Dict[Tuple[str, str], List[str]] = {
    ("size", GREATER): [
        "taller",
        "bigger",
        "larger",
        "higher",
        "longer",
        "wider",
        "more",
        "高",
        "大",
        "多",
        "長",
    ],
    ("size", LESSER): ["shorter", "smaller", "lower", "less", "低", "小", "少"],
    ("age", GREATER): ["older"],
    ("age", LESSER): ["younger"],
    ("temperature", GREATER): ["hotter"],
    ("temperature", LESSER): ["colder"],
    ("speed", GREATER): ["faster", "快"],
    ("speed", LESSER): ["slower", "慢"],
    ("weight", GREATER): ["heavier", "重"],
    ("weight", LESSER): ["lighter", "輕"],
    ("strength", GREATER): ["stronger", "強"],
    ("strength", LESSER): ["weaker", "弱"],
    ("wealth", GREATER): ["richer"],
    ("wealth", LESSER): ["poorer"],
}


def _dimension_seed_map() -> Dict[str, List[str]]:
    """Every word of a dimension (the direction is ignored)."""
    seeds: Dict[str, List[str]] = {}
    for (dim, _direction), words in CONCEPT_SEEDS.items():
        seeds.setdefault(dim, []).extend(words)
    return seeds


DIMENSION_SEEDS = _dimension_seed_map()

# The superlative direction of the question ("top" / "lowest"). These are the
# aggregation words; the dimension is matched separately.
# How much weaker the question's dimension may be than the overall best
# before the best match wins instead.
_DIMENSION_MARGIN = 0.15
# How many aligned phrases a concept may accumulate.
_MAX_ALIGNED_SEEDS = 64

# The superlative words of the teacher: its own "comparator → superlative"
# table, grouped per dimension. The direction of a question is matched
# against the superlatives of the dimension the question names, so "the
# coolest" cannot be pulled to "the hottest" by the mere similarity of two
# temperature superlatives.
SUPERLATIVE_SEEDS: Dict[Tuple[str, str], List[str]] = {}


def _superlative_seed_map() -> Dict[Tuple[str, str], List[str]]:
    """(dimension, direction) -> the teacher's superlative words."""
    from ai.symbolic_reasoner import _superlative

    seeds: Dict[Tuple[str, str], List[str]] = {}
    for (dimension, relation), words in CONCEPT_SEEDS.items():
        for word in words:
            for direction, least in ((GREATEST, False), (LEAST, True)):
                phrase = _superlative(word, least=least).lower()
                bucket = seeds.setdefault((dimension, direction), [])
                if phrase not in bucket:
                    bucket.append(phrase)
                bare = phrase[4:] if phrase.startswith("the ") else phrase
                if bare and bare not in bucket:
                    bucket.append(bare)
    return seeds


SUPERLATIVE_SEEDS.update(_superlative_seed_map())

# The global direction seeds (the union): used when the question names no
# dimension ("which one is on top?").
DIRECTION_SEEDS: Dict[str, List[str]] = {GREATEST: [], LEAST: []}
for (_dimension, _direction), _words in SUPERLATIVE_SEEDS.items():
    for _word in _words:
        if _word not in DIRECTION_SEEDS[_direction]:
            DIRECTION_SEEDS[_direction].append(_word)
del _dimension, _direction, _words, _word

# The Chinese superlatives are *derived* from the teacher's Chinese
# comparators (最高 = 最 + 高): the concept is the teacher's, only the
# Chinese superlative marker is added.
_CN_SUPERLATIVE_PREFIX = "最"
for (_dimension, _relation), _words in CONCEPT_SEEDS.items():
    for _word in _words:
        if len(_word) == 1 and not _word.isascii():
            # The direction of the Chinese superlative follows the direction
            # of the comparator: 高 → 最高 (the greatest), 低 → 最低 (the least).
            _direction = GREATEST if _relation == GREATER else LEAST
            _derived = _CN_SUPERLATIVE_PREFIX + _word
            for _bucket in (
                SUPERLATIVE_SEEDS[(_dimension, _direction)],
                DIRECTION_SEEDS[_direction],
            ):
                if _derived not in _bucket:
                    _bucket.append(_derived)
del _dimension, _relation, _words, _word

# A dimension match above this score is trusted enough to reject a question
# whose dimension disagrees with the chain.
_CONFIDENT_AGGREGATION = 0.80
# When the two directions are this close, the question's dimension decides.
_DIRECTION_MARGIN = 0.05

# The dimension-agnostic superlatives: "which one is on top?" does not name a
# dimension at all, so the answer is the top of whatever the chain is about.
AGGREGATION_ANY_SEEDS: List[str] = [
    "the greatest",
    "the top",
    "top",
    "the winner",
    "winner",
    "the first",
    "first",
]


# --------------------------------------------------------------------------- #
# The encoder
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=8192)
def _encode_cached(text: str) -> np.ndarray:
    """The sentence embedding (the shipped multilingual ONNX encoder)."""
    from ai.unified_engine.semantic_qa import _features

    return np.asarray(_features(text), dtype=np.float32)


def _encode(text: str) -> np.ndarray:
    return _encode_cached(text)


def _unit(vec: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vec))
    if norm <= 0.0:
        return vec
    return vec / norm


_QUESTION = re.compile(
    r"[?？]\s*$"
    r"|\b(yes or no|yes/no)\b|是嗎|對嗎"
    r"|^\s*(what|who|whom|which|whose|when|where|why|how|is|are|was|were|do|does|did|"
    r"can|could|should|would|will)\b"
    r"|^(誰|哪|什麼|甚麼|怎麼|為什麼|為何|是不是|有沒有|幾點|哪個)",
    re.IGNORECASE,
)


def _looks_like_question(text: str) -> bool:
    """True when the message asks something.

    The bridge answers *questions* ("who is the tallest?"). Without this
    guard any statement could be read as a comparison ("寫Unity腳本" became
    "寫 is the tallest").
    """
    return bool(_QUESTION.search((text or "").strip()))


def _phrase_windows(phrase: str) -> List[str]:
    """The tail windows of a phrase ("who is the coolest" -> "coolest").

    Only the *tail* is used: the superlative is the last word, and the whole
    phrase carries the question's filler ("is the ..."), which lands the
    match on the wrong concept ("is the heaviest" matched the size
    dimension because "is the" resembles "taller").
    """
    words = (phrase or "").split()
    if not words:
        return []
    windows = [words[-1]]
    if len(words) > 1:
        windows.append(" ".join(words[-2:]))
    return windows


def _similarity(vec: np.ndarray, proto: np.ndarray) -> float:
    if vec.size == 0 or proto.size == 0 or vec.size != proto.size:
        return 0.0
    return float(vec @ proto)


# --------------------------------------------------------------------------- #
# The matcher
# --------------------------------------------------------------------------- #
class RelationMatcher:
    """Matches a phrase to a relation/aggregation concept, neurally.

    A concept is scored by two numbers: the best of its *seed words* (the
    teacher's own vocabulary — this is what generalises to unseen
    paraphrases) and its *centroid* (the prototype the feedback step moves).
    The best of the two wins, so a concept that the teacher could not place
    can still be pulled closer by the alignment.
    """

    def __init__(self, alignment_rate: float = 0.15) -> None:
        self._alignment_rate = alignment_rate
        # kind ("relation" / "dimension" / "direction") -> key -> prototype
        self._prototypes: Dict[str, Dict[str, np.ndarray]] = {}
        # kind -> key -> the seed vectors
        self._seeds: Dict[str, Dict[str, List[np.ndarray]]] = {}
        # kind -> key -> the seed words
        self._seed_map: Dict[str, Dict[str, List[str]]] = {}
        # kind -> key -> the phrases the feedback has taught (persisted)
        self._aligned: Dict[str, Dict[str, List[str]]] = {}
        self.seed()

    # -- seeding ---------------------------------------------------------- #
    def seed(self) -> None:
        """(Re)build the prototypes from the teacher's vocabulary."""
        self._prototypes = {}
        self._seeds = {}
        self._seed_map = {}
        self._register(self._concept_map(), "relation")
        self._register(self._dimension_map(), "dimension")
        self._register(self._direction_map(), "direction")
        any_vecs = [_unit(_encode(w)) for w in AGGREGATION_ANY_SEEDS]
        self._any_prototype = _unit(np.mean(any_vecs, axis=0)) if any_vecs else None

    @staticmethod
    def _concept_map() -> Dict[str, List[str]]:
        return {
            f"{dim}|{direction}": list(words) for (dim, direction), words in CONCEPT_SEEDS.items()
        }

    @staticmethod
    def _dimension_map() -> Dict[str, List[str]]:
        return {dim: list(words) for dim, words in DIMENSION_SEEDS.items()}

    @staticmethod
    def _direction_map() -> Dict[str, List[str]]:
        mapping = {direction: list(words) for direction, words in DIRECTION_SEEDS.items()}
        # The per-dimension superlatives ("the coldest" belongs to the
        # temperature dimension, not to every dimension).
        for (dimension, direction), words in SUPERLATIVE_SEEDS.items():
            mapping[f"{dimension}|{direction}"] = list(words)
        return mapping

    def _register(self, mapping: Dict[str, List[str]], kind: str) -> None:
        for key, words in mapping.items():
            vectors = [_unit(_encode(w)) for w in words if w]
            vectors = [v for v in vectors if v.size]
            if not vectors:
                continue
            self._seeds.setdefault(kind, {})[key] = vectors
            self._seed_map.setdefault(kind, {})[key] = list(words)
            self._prototypes.setdefault(kind, {})[key] = _unit(np.mean(vectors, axis=0))

    # -- matching --------------------------------------------------------- #
    def _score(self, vec: np.ndarray, kind: str, key: str) -> float:
        """The similarity of *vec* to a concept.

        The **best seed word** discriminates; the centroid (the mean of the
        seeds) is a hub that many unrelated words sit near — "outweighs"
        matched the size centroid instead of the weight seeds. The centroid
        therefore only breaks the ties.
        """
        best = 0.0
        for seed in self._seeds.get(kind, {}).get(key, ()):
            sim = _similarity(vec, seed)
            if sim > best:
                best = sim
        proto = self._prototypes.get(kind, {}).get(key)
        if proto is not None:
            best += 0.02 * _similarity(vec, proto)
        return best

    def _best(self, vec: np.ndarray, kind: str, threshold: float) -> Optional[Tuple[str, float]]:
        best: Optional[Tuple[str, float]] = None
        for key in self._seeds.get(kind, {}):
            sim = self._score(vec, kind, key)
            if best is None or sim > best[1]:
                best = (key, sim)
        if best is None or best[1] < threshold:
            return None
        return best

    def _best_over_windows(
        self,
        phrase: str,
        kind: str,
        threshold: float,
        keys: Optional[Sequence[str]] = None,
    ) -> Optional[Tuple[str, float]]:
        """The best (key, score) over the phrase and its tail windows."""
        if not phrase or not phrase.strip():
            return None
        table = self._seeds.get(kind, {})
        candidates = [k for k in (keys if keys is not None else table) if k in table]
        if not candidates:
            return None
        best: Optional[Tuple[str, float]] = None
        for window in _phrase_windows(phrase):
            vec = _unit(_encode(window))
            if vec.size == 0:
                continue
            for key in candidates:
                sim = self._score(vec, kind, key)
                if best is None or sim > best[1]:
                    best = (key, sim)
        if best is None or best[1] < threshold:
            return None
        return best

    def classify_all(
        self, phrase: str, kind: str = "relation"
    ) -> List[Tuple[Tuple[str, str], float]]:
        """Every concept with its score (the caller may re-rank by dimension)."""
        if not phrase or not phrase.strip():
            return []
        vec = _unit(_encode(phrase))
        if vec.size == 0:
            return []
        scored: List[Tuple[Any, float]] = []
        for key in self._seeds.get(kind, {}):
            sim = self._score(vec, kind, key)
            if kind == "relation":
                dimension, direction = key.split("|", 1)
                scored.append(((dimension, direction), sim))
            else:
                scored.append((key, sim))
        scored.sort(key=lambda item: -item[1])
        return scored

    def classify(
        self, phrase: str, kind: str = "relation", threshold: float = 0.45
    ) -> Optional[Tuple[Tuple[str, str], float]]:
        """The best concept for *phrase* (None when nothing is close enough).

        ``kind="relation"`` returns the (dimension, direction) concept.
        """
        if not phrase or not phrase.strip():
            return None
        vec = _unit(_encode(phrase))
        if vec.size == 0:
            return None
        best = self._best(vec, "relation", threshold)
        if best is None:
            return None
        dimension, direction = best[0].split("|", 1)
        return ((dimension, direction), best[1])

    def is_superlative_word(self, word: str, threshold: float = 0.97) -> bool:
        """True when the word is one of the teacher's superlatives.

        "the tallest person" contains no comparison: "tallest" is the
        question's superlative, so it is neither a relation word nor an
        entity. The threshold is high on purpose: "hotter" is close to
        "the hottest" but is a comparative, not a superlative.
        """
        if not word or len(word) < 3:
            return False
        direction = self.classify_direction(word, threshold=0.0)
        return direction is not None and direction[1] >= threshold

    def is_relation_phrase(self, phrase: str, score: float) -> bool:
        """True when the phrase can be a comparison word.

        The encoder puts *every* short word near the concept centroids
        ("many", "km", "how" all match the size concept at ~0.7), so a fuzzy
        match on a short word is noise, not a comparison. A short phrase is
        only accepted when it is one of the teacher's own words (an exact
        seed match), or when it is a Chinese glyph.
        """
        text = (phrase or "").strip()
        if not text:
            return False
        if len(text) == 1 and not text.isascii():
            return True  # a Chinese comparator glyph
        if score >= 0.95:
            return True  # an exact teacher word
        if len(text) >= 5:
            return True
        # A four-letter word is only a comparison when it is not a function
        # word ("aged" is, "many" is not).
        return len(text) == 4 and text.lower() not in _STOPWORDS

    def classify_dimension(
        self, phrase: str, threshold: float = 0.40
    ) -> Optional[Tuple[str, float]]:
        """The dimension a superlative names ("the coldest" → temperature)."""
        return self._best_over_windows(phrase, "dimension", threshold)

    def classify_direction(
        self,
        phrase: str,
        threshold: float = 0.40,
        dimension: Optional[str] = None,
    ) -> Optional[Tuple[str, float]]:
        """The superlative direction of a question phrase (greatest / least).

        When the question names a dimension, the direction is matched
        against *that* dimension's superlatives ("the coolest" against the
        temperature superlatives, so "the hottest" cannot win). Otherwise
        the global superlatives are used. Several windows of the phrase are
        tried ("who is the coolest" → "coolest").
        """
        scores = self._direction_scores(phrase)
        if not scores:
            return None
        ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        best_direction, best_score = ordered[0]
        if len(ordered) > 1 and (best_score - ordered[1][1]) < _DIRECTION_MARGIN and dimension:
            # The two directions are close (two temperature superlatives are
            # near each other): the dimension of the question decides.
            scoped = self._best_over_windows(
                phrase,
                "direction",
                threshold,
                keys=(f"{dimension}|{GREATEST}", f"{dimension}|{LEAST}"),
            )
            if scoped is not None:
                return scoped
        if best_score < threshold:
            return None
        return (best_direction, best_score)

    def _direction_scores(self, phrase: str) -> Dict[str, float]:
        """The best score of each direction (greatest / least)."""
        table = self._seeds.get("direction", {})
        scores: Dict[str, float] = {}
        for window in _phrase_windows(phrase):
            vec = _unit(_encode(window))
            if vec.size == 0:
                continue
            for direction in (GREATEST, LEAST):
                score = self._score(vec, "direction", direction)
                if score > scores.get(direction, 0.0):
                    scores[direction] = score
        return scores

    def classify_aggregation(
        self, phrase: str, threshold: float = 0.65
    ) -> Optional[Tuple[Optional[str], str, float]]:
        """The aggregation for *phrase*: (dimension or None, direction, sim).

        ``None`` for the dimension means "any dimension" (the question asks
        for the top of the chain without naming a dimension).

        The threshold is deliberately high: a question must *ask* for a
        superlative (the teacher's own superlative words score ≈1.0). At 0.40
        any sentence matched something ("寫Unity Editor腳本只輸出代碼" was
        read as a comparison).
        """
        if not phrase or not phrase.strip():
            return None
        dir_match = self.classify_direction(phrase)
        # The dimension comes from the *specific* superlative ("the heaviest"
        # belongs to the weight dimension): the per-dimension direction seeds
        # are more precise than the dimension prototypes, where "heaviest" sits
        # nearer to "taller" than to "heavier".
        dimension: Optional[str] = None
        dim_sim = 0.0
        if dir_match is not None:
            for key, score in self.classify_all(phrase, kind="direction"):
                if not isinstance(key, str) or "|" not in key:
                    continue
                dim_name, dim_direction = key.split("|", 1)
                if dim_direction == dir_match[0] and score > dim_sim:
                    dimension = dim_name
                    dim_sim = score
        if dimension is None:
            dim_match = self.classify_dimension(phrase)
            dimension = dim_match[0] if dim_match else None
            dim_sim = dim_match[1] if dim_match else 0.0
        if dimension is None and dir_match is None:
            return None
        any_sim = 0.0
        if self._any_prototype is not None:
            for window in _phrase_windows(phrase):
                any_sim = max(any_sim, _similarity(_unit(_encode(window)), self._any_prototype))
        if any_sim > dim_sim:
            # The question names no dimension ("which one is on top?").
            dimension = None
            dim_sim = any_sim
        if dir_match is not None:
            direction = dir_match[0]
            score = max(dir_match[1], dim_sim)
        else:
            # The teacher defaults to the greatest when the question is not a
            # "least" question.
            direction = GREATEST
            score = dim_sim
        if score < threshold:
            return None
        return (dimension, direction, score)

    # -- alignment (the feedback step) ------------------------------------ #
    def aligned_phrases(self) -> Dict[str, Dict[str, List[str]]]:
        """The phrases the feedback has taught, per concept (for persistence)."""
        return {
            kind: {key: list(words) for key, words in table.items()}
            for kind, table in self._aligned.items()
        }

    def load_aligned_phrases(self, table: Dict[str, Dict[str, List[str]]]) -> int:
        """Replay saved feedback (the learned state survives a restart)."""
        count = 0
        for kind, concepts in (table or {}).items():
            for key, phrases in concepts.items():
                if kind == "relation" and "|" in key:
                    dimension, direction = key.split("|", 1)
                    for phrase in phrases:
                        self.align(phrase, (dimension, direction), kind="relation")
                        count += 1
                elif kind == "direction":
                    for phrase in phrases:
                        self.align_direction(phrase, key)
                        count += 1
        return count

    def align(self, phrase: str, concept: Tuple[str, str], kind: str = "relation") -> float:
        """Move the concept's prototype toward *phrase* (one feedback step).

        This is the "根據反饋的資訊來與神經網路對齊" step: the teacher
        says the phrase belongs to a concept, and the prototype for that
        concept is nudged toward the phrase. It aligns *concepts*, never
        questions, so the layer generalises instead of memorising.
        """
        if not phrase:
            return 0.0
        table = "relation" if kind == "relation" else "dimension"
        key = f"{concept[0]}|{concept[1]}" if table == "relation" else str(concept)
        vec = _unit(_encode(phrase))
        if vec.size == 0:
            return 0.0
        proto = self._prototypes.get(table, {}).get(key)
        if proto is None:
            if table == "relation" and concept[0] == ANY_DIMENSION:
                # A generic relation word ("exceeds") has no dimension of its
                # own: the question supplies it. The concept is created by its
                # first teaching example instead of refusing to learn it.
                self._seeds.setdefault(table, {})[key] = []
                self._seed_map.setdefault(table, {})[key] = []
                self._prototypes.setdefault(table, {})[key] = vec
                proto = vec
            else:
                return 0.0
        before = _similarity(vec, proto)
        updated = _unit(proto * (1.0 - self._alignment_rate) + vec * self._alignment_rate)
        self._prototypes[table][key] = updated
        # The aligned phrase joins the concept's own seeds — the concept now
        # *contains* the word it was taught (the score is the best seed, so
        # without this the alignment would barely move anything).
        seeds = self._seeds.get(table, {}).get(key)
        if seeds is not None and len(seeds) < _MAX_ALIGNED_SEEDS:
            seeds.append(vec)
            self._aligned.setdefault(table, {}).setdefault(key, []).append(phrase)
        return _similarity(vec, updated) - before

    def align_direction(self, phrase: str, direction: str) -> float:
        """Move the direction prototype toward *phrase* (the aggregation side)."""
        proto = self._prototypes.get("direction", {}).get(direction)
        if proto is None or not phrase:
            return 0.0
        vec = _unit(_encode(phrase))
        if vec.size == 0:
            return 0.0
        before = _similarity(vec, proto)
        updated = _unit(proto * (1.0 - self._alignment_rate) + vec * self._alignment_rate)
        self._prototypes["direction"][direction] = updated
        self._aligned.setdefault("direction", {}).setdefault(direction, []).append(phrase)
        return _similarity(vec, updated) - before

    def stats(self) -> Dict[str, int]:
        return {
            "relation_concepts": len(self._seeds.get("relation", {})),
            "dimension_concepts": len(self._seeds.get("dimension", {})),
            "direction_concepts": len(self._seeds.get("direction", {})),
        }


# --------------------------------------------------------------------------- #
# The span extraction (neural-first: the matcher finds the relation phrase)
# --------------------------------------------------------------------------- #
# The structural patterns that do NOT need a comparison vocabulary:
#   - the Chinese "A 比 B <adj>" shape (the direction is given by the shape)
#   - the symbolic "A > B" shape (the direction is given by the symbol)
_CN_COMPARISON = re.compile(r"([\w一-鿿]{1,10})\s*比\s*([\w一-鿿]{1,10})\s*([\w一-鿿]{1,3})")
_SYMBOLIC_RELATION = re.compile(
    r"\b([A-Za-z][A-Za-z0-9_]{0,15})\s*>\s*([A-Za-z][A-Za-z0-9_]{0,15})\b"
)
# The symbolic tokens: an entity or a comparison symbol. A chain ("X > Y > Z")
# is a sequence of them, so the pairs are read from the sequence.
_SYMBOLIC_TOKENS = re.compile(r"([A-Za-z][A-Za-z0-9_]{0,15})|([<>]=?|=)")
# The clause separators: the relations live inside one clause.
_CLAUSE_SPLIT = re.compile(r"[,;.!?，。；！？]")

# The words that belong to the shape, not to the relation.
_PHRASE_FILLERS = (
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "than",
    "to",
    "not",
    "as",
    "the",
    "a",
    "an",
    "of",
    "in",
    "at",
    "on",
    "by",
    "with",
    "from",
)
# The words that belong to the question, not to the entity.
_QUESTION_WORDS = (
    "who",
    "whom",
    "which",
    "what",
    "whose",
    "anyone",
    "anybody",
    "everyone",
    "everybody",
    "how",
    "many",
    "much",
    "when",
    "where",
    "why",
    "tell",
    "explain",
    "please",
    "give",
    "calculate",
    "compute",
    "convert",
    "is",
    "are",
    "was",
    "were",
    "does",
    "do",
    "did",
    "the",
    "a",
    "an",
    "one",
)
# The comparative markers: they sit between the entity and the comparative
# ("A is more valuable than B"), so they never belong to an entity.
_COMPARATIVE_MARKERS = ("more", "less", "most", "least", "much", "far", "way")
# The English function words: they can never be a comparison word, and the
# encoder puts every one of them near the concept centroids ("many" matches
# the size concept at 0.77). This is a *structural* list, not a comparison
# vocabulary.
_STOPWORDS = frozenset("""
    how many much when where why what which who whom whose there here this
    that these those it its they them their he she his her you your we our
    i me my one two three four five six seven eight nine ten
    very more most less least some any all both each every other another
    same such own just only also too can could will would shall should may
    might must do does did done have has had get got give given
    """.split())
_NEGATIONS = ("not", "n't", "never", "no")
# The Chinese question words that can precede the subject ("若甲比乙高").
_CN_QUESTION_WORDS = ("若", "誰", "哪", "何", "請", "那", "在")


def _tokens(text: str) -> List[str]:
    """Words of *text* (letters/digits/CJK), punctuation dropped."""
    return re.findall(r"[A-Za-z0-9]+|[一-鿿]", text or "")


def _trim(tokens: Sequence[str], start: int, end: int) -> Tuple[int, int, str]:
    """Drop the shape words from the window (start, end]."""
    window = list(tokens[start:end])
    lo, hi = 0, len(window)
    while lo < hi and window[lo].lower() in _PHRASE_FILLERS:
        lo += 1
    while hi > lo and window[hi - 1].lower() in _PHRASE_FILLERS:
        hi -= 1
    if lo >= hi:
        return start, end, ""
    return start + lo, start + hi, " ".join(window[lo:hi])


def _is_entity_token(word: str) -> bool:
    """A single upper-case letter is an entity ("A", "X", "Q"), not a word."""
    return len(word) == 1 and word.isupper()


def _is_shape_word(word: str) -> bool:
    """True for the words that belong to the shape, not to the entity."""
    lowered = word.lower()
    return (
        lowered in _QUESTION_WORDS or lowered in _PHRASE_FILLERS or lowered in _COMPARATIVE_MARKERS
    )


def _is_relation_window(tokens: Sequence[str], lo: int, hi: int) -> bool:
    """True when the window can be a relation word.

    A relation word is a content word: it is not a question word, not a
    shape word and not a single letter (the entities of a comparison are
    often single letters: "A", "X", "Q").
    """
    for word in tokens[lo:hi]:
        if _is_entity_token(word):
            return False
        if len(word) < 3:
            return False
        if _is_shape_word(word):
            return False
        if not word.isascii():
            # The Chinese shape is handled by its own pattern.
            return False
    return True


_ARTICLES = ("the", "a", "an")
# The prepositions: the object of a comparison stands right next to the
# relation word ("A outranks B"), a preposition means the phrase is part of
# a noun phrase ("the smartest student in the class").
# ("to" is not here: "superior to X" is a comparison, not a noun phrase.)
# "by" is not here: "A is exceeded by B" is a passive comparison, the
# preposition belongs to the relation, not to a noun phrase.
_PREPOSITIONS = ("in", "at", "on", "with", "from", "of", "for", "into")


def _trim_entity(words: List[str]) -> str:
    """The entity name of *words* (the shape words at both ends dropped)."""
    while words and _is_shape_word(words[0]) and not _is_entity_token(words[0]):
        words.pop(0)
    while words and _is_shape_word(words[-1]) and not _is_entity_token(words[-1]):
        words.pop()
    if len(words) > 1 and words[0].lower() in _ARTICLES:
        words.pop(0)
    if not words:
        return ""
    return words[-1] if len(words) == 1 else " ".join(words[-2:])


def _entity_before(tokens: Sequence[str], start: int) -> str:
    """The entity words right before position *start* (the article dropped)."""
    return _trim_entity([w for w in tokens[:start]])


def _entity_after(tokens: Sequence[str], end: int) -> str:
    """The entity words right after position *end*."""
    words = list(tokens[end:])
    while words and _is_shape_word(words[0]) and not _is_entity_token(words[0]):
        words.pop(0)
    if len(words) > 1 and words[0].lower() in _ARTICLES:
        words.pop(0)
    if not words:
        return ""
    name = words[:2]
    while len(name) > 1 and _is_shape_word(name[-1]) and not _is_entity_token(name[-1]):
        name.pop()
    return " ".join(name)


def extract_relation_spans(text: str) -> List[Tuple[str, str, str]]:
    """(subject, phrase, object) spans of the *structural* shapes.

    The Chinese "A 比 B 高" and the symbolic "A > B" carry the direction in
    their shape, so they need no comparison vocabulary. The English shape is
    found by the *matcher* (see NeuralBridge.find_relations), because the
    relation word can be any verb: "X exceeds Y", "A outranks B", "X is
    taller than Y".
    """
    spans: List[Tuple[str, str, str]] = []
    for m in _CN_COMPARISON.finditer(text):
        subject = m.group(1)
        for word in _CN_QUESTION_WORDS:
            if subject.startswith(word) and len(subject) > len(word):
                subject = subject[len(word) :]
                break
        spans.append((subject, m.group(3), m.group(2)))
    spans.extend(_symbolic_pairs(text))
    return spans


def _symbolic_pairs(text: str) -> List[Tuple[str, str, str]]:
    """The "A > B" pairs, chains included ("X > Y > Z" → (X,Y) and (Y,Z)).

    The symbol itself states the direction: A > B means A is greater, so
    every pair is normalised to the "greater" direction.
    """
    pairs: List[Tuple[str, str, str]] = []
    last_entity: Optional[str] = None
    symbol: Optional[str] = None
    for token in _SYMBOLIC_TOKENS.finditer(text or ""):
        entity, marker = token.group(1), token.group(2)
        if entity is not None:
            if symbol is not None and last_entity is not None:
                if symbol.startswith(">"):
                    pairs.append((last_entity, "greater", entity))
                else:
                    # "A < B" means B is the greater one.
                    pairs.append((entity, "greater", last_entity))
            last_entity = entity
            symbol = None
            continue
        if marker is not None:
            symbol = marker
    return pairs


def extract_aggregation_span(text: str) -> Optional[str]:
    """The question's aggregation phrase (the superlative it asks for)."""
    body = (text or "").strip()
    for mark in ("?", "？"):
        if body.endswith(mark):
            body = body[: -len(mark)].strip()
            break
    if not body:
        return None
    if re.search(r"[一-鿿]", body):
        # Chinese: the superlative is the tail of the question ("誰最高" → "最高").
        return body[-3:].lower()
    words = _tokens(body)
    if not words:
        return None
    # The superlative is the tail of the question ("who coldest" → "coldest").
    return " ".join(words[-3:] if len(words) >= 3 else words).lower()


# --------------------------------------------------------------------------- #
# The bridge
# --------------------------------------------------------------------------- #
class NeuralBridge:
    """Answers comparison-chain questions by semantic matching + composition."""

    def __init__(self, matcher: Optional[RelationMatcher] = None) -> None:
        self.matcher = matcher or RelationMatcher()

    # -- the relations ----------------------------------------------------- #
    def find_relations(
        self, text: str, dimension: Optional[str] = None
    ) -> List[Tuple[str, Tuple[str, str], str]]:
        """The (subject, concept, object) relations of *text*.

        The concept is (dimension, direction). The English relation word is
        found by the matcher, not by a vocabulary: that is the generalisation
        the teacher cannot do.

        ``dimension`` is the dimension the *question* asks about ("who is the
        heaviest?" → weight). The encoder alone cannot place "outweighs"
        (it sits near "less" and "heavier" alike), but the question already
        says which dimension the chain is about — so the relation is read in
        that dimension.
        """
        relations: List[Tuple[str, Tuple[str, str], str]] = []
        seen: Set[Tuple[str, str, str]] = set()

        # 1. The structural shapes (the direction is in the shape).
        for subject, phrase, obj in extract_relation_spans(text):
            if phrase == "greater":  # the symbolic "A > B" form
                concept = (ANY_DIMENSION, GREATER)
            else:
                match = self._classify_relation(phrase, dimension)
                if match is None:
                    continue
                concept = match[0]
            key = (subject, concept[1], obj)
            if key in seen:
                continue
            seen.add(key)
            relations.append((subject, concept, obj))

        # 2. The English shape: the matcher finds the relation word.
        for subject, phrase, obj, negated in self._english_relations(text, dimension):
            match = self._classify_relation(phrase, dimension)
            if match is None:
                continue
            concept_dimension, direction = match[0]
            if negated:
                # "A is not as short as B" — the negation flips the relation.
                direction = LESSER if direction == GREATER else GREATER
            key = (subject, direction, obj)
            if key in seen:
                continue
            seen.add(key)
            relations.append((subject, (concept_dimension, direction), obj))
        return relations

    def _classify_relation(
        self, phrase: str, dimension: Optional[str]
    ) -> Optional[Tuple[Tuple[str, str], float]]:
        """The relation concept, read in the dimension the question asks about.

        The question's dimension is a *hint*, not a command: it only wins when
        it is not much weaker than the overall best (otherwise "the box is
        bigger than the bag ... who coldest?" would read "bigger" as a
        temperature and answer nonsense).
        """
        scored = self.matcher.classify_all(phrase, kind="relation")
        if not scored:
            return None
        concept, score = scored[0]
        if concept[0] == ANY_DIMENSION:
            # The word carries the direction, the question carries the
            # dimension ("X exceeds Y ... who is the oldest?").
            return ((dimension or ANY_DIMENSION, concept[1]), score)
        if dimension:
            for candidate, candidate_score in scored:
                if candidate[0] == dimension:
                    if candidate_score >= score - _DIMENSION_MARGIN:
                        return candidate, candidate_score
                    break
        return concept, score

    def _english_relations(
        self, text: str, dimension: Optional[str] = None
    ) -> List[Tuple[str, str, str, bool]]:
        """The English relation spans (subject, phrase, object, negated)."""
        spans: List[Tuple[str, str, str, bool]] = []
        for clause in _CLAUSE_SPLIT.split(text or ""):
            tokens = _tokens(clause)
            if len(tokens) < 3:
                continue
            best = (
                self._than_anchored(tokens, dimension)
                or self._as_anchored(tokens, dimension)
                or self._window_scan(tokens, dimension)
            )
            if best is None:
                continue
            _score, lo, hi, phrase = best
            subject = _entity_before(tokens, lo)
            obj = _entity_after(tokens, hi)
            if not subject or not obj:
                continue
            negated = any(w.lower() in _NEGATIONS for w in tokens[:lo])
            spans.append((subject, phrase, obj, negated))
        return spans

    def _has_superlative_entity(self, *entities: str) -> bool:
        """True when an entity is the question's superlative ("the tallest")."""
        return any(
            self.matcher.is_superlative_word(word) for entity in entities for word in entity.split()
        )

    def _than_anchored(
        self, tokens: List[str], dimension: Optional[str] = None
    ) -> Optional[Tuple[float, int, int, str]]:
        """The relation of the "X <comparative> than Y" shape.

        The comparative marker ("than") anchors the phrase: the words right
        before it are the comparative ("more valuable", "taller"), and the
        words right after it are the object. Without this anchor the scan
        would stop at a bare marker word ("more") and lose the dimension.
        """
        than_indexes = [i for i, token in enumerate(tokens) if token.lower() == "than"]
        if not than_indexes:
            return None
        index = than_indexes[-1]
        best: Optional[Tuple[float, int, int, str]] = None
        for length in (1, 2, 3):
            start = index - length
            if start < 0:
                continue
            lo, hi, phrase = _trim(tokens, start, index)
            if not phrase:
                continue
            if not _is_relation_window(tokens, lo, hi):
                continue
            match = self._classify_relation(phrase, dimension)
            if match is None:
                continue
            if not self.matcher.is_relation_phrase(phrase, match[1]):
                continue
            if self.matcher.is_superlative_word(phrase):
                # The question's own superlative is not a comparison.
                continue
            if best is None or match[1] > best[0]:
                best = (match[1], lo, hi, phrase)
        if best is None:
            return None
        _score, lo, hi, phrase = best
        # The object follows the marker.
        obj_index = index + 1
        subject = _entity_before(tokens, lo)
        obj = _entity_after(tokens, obj_index)
        if not subject or not obj:
            return None
        if self._has_superlative_entity(subject, obj):
            return None
        return best

    def _as_anchored(
        self, tokens: List[str], dimension: Optional[str] = None
    ) -> Optional[Tuple[float, int, int, str]]:
        """The relation of the "not as <adjective> as" shape.

        This shape has no "than", so the adjective sits between two "as"
        markers. The adjective is the *base* form ("old", not "older"), so it
        is read in the dimension the question names; the negation (handled by
        the caller) flips the direction. Without a negation or a comparative
        marker the shape is an equality, not a comparison.
        """
        markers = [i for i, token in enumerate(tokens) if token.lower() == "as"]
        if len(markers) < 2:
            return None
        best: Optional[Tuple[float, int, int, str]] = None
        for first, second in zip(markers, markers[1:]):
            lo, hi, phrase = _trim(tokens, first + 1, second)
            if not phrase or hi <= lo:
                continue
            negated = any(w.lower() in _NEGATIONS for w in tokens[:first])
            comparative = any(w.lower() in _COMPARATIVE_MARKERS for w in tokens[lo:hi])
            if not negated and not comparative:
                # "A is as tall as B" states equality, not a chain link.
                continue
            match = self._classify_relation(phrase, dimension)
            if match is None:
                continue
            concept, score = match
            if dimension and concept[0] != dimension:
                # The base adjective has no direction of its own; it is only
                # readable in the dimension the question asks about.
                continue
            if not phrase.isascii() and len(phrase) == 1:
                continue
            if best is None or score > best[0]:
                subject = _entity_before(tokens, first)
                obj = _entity_after(tokens, second + 1)
                if not subject or not obj:
                    continue
                if self._has_superlative_entity(subject, obj):
                    continue
                best = (score, lo, hi, phrase)
        return best

    def _window_scan(
        self, tokens: List[str], dimension: Optional[str] = None
    ) -> Optional[Tuple[float, int, int, str]]:
        """The relation of a shape without a comparative marker.

        "A outranks B", "A beats B": the relation word is found by the
        matcher, the entities are the words around it.
        """
        best: Optional[Tuple[float, int, int, str]] = None
        for start in range(len(tokens)):
            for length in (1, 2, 3):
                end = start + length
                if end > len(tokens):
                    continue
                lo, hi, phrase = _trim(tokens, start, end)
                if not phrase:
                    continue
                if not _is_relation_window(tokens, lo, hi):
                    continue
                match = self._classify_relation(phrase, dimension)
                if match is None:
                    continue
                if not self.matcher.is_relation_phrase(phrase, match[1]):
                    continue
                if self.matcher.is_superlative_word(phrase):
                    # The question's own superlative is not a comparison.
                    continue
                if hi < len(tokens) and tokens[hi].lower() == "by":
                    # Passive voice: "A is exceeded by B". The bare verb
                    # ("exceeded") sits between its active and passive
                    # meanings; the "by" disambiguates it and belongs to the
                    # relation, so the phrase keeps it.
                    passive = f"{phrase} by"
                    passive_match = self._classify_relation(passive, dimension)
                    if passive_match is not None and passive_match[1] > match[1]:
                        match = passive_match
                        phrase = passive
                        hi += 1
                if best is None or match[1] > best[0]:
                    # A relation word always has an entity on both sides:
                    # the subject before it and the object after it.
                    subject = _entity_before(tokens, lo)
                    obj = _entity_after(tokens, hi)
                    if not subject or not obj:
                        continue
                    if self._has_superlative_entity(subject, obj):
                        # "the tallest person" is not a comparison.
                        continue
                    if hi < len(tokens) and tokens[hi].lower() in _PREPOSITIONS:
                        # "the smartest student in the class": the phrase
                        # belongs to a noun phrase, not to a comparison.
                        continue
                    best = (match[1], lo, hi, phrase)
        return best

    # -- composition ------------------------------------------------------ #
    def _compose(
        self,
        relations: List[Tuple[str, Tuple[str, str], str]],
        dimension: Optional[str],
        direction: str,
    ) -> Optional[str]:
        """The entity that is the greatest/least in the chain's dimension.

        The semantics are the teacher's: the greatest entity is the one
        nothing is greater than (no incoming edge) and it dominates every
        other entity; the least is the one that is greater than nothing (no
        outgoing edge) and is dominated by every other entity.
        """
        if not relations:
            return None
        # Every relation becomes a "greater" edge: X -> Y means X is greater
        # than Y. A "lesser" relation (A less than B) is the edge B -> A.
        greater: Dict[str, Set[str]] = {}
        for subject, concept, obj in relations:
            dim, rel = concept
            if dimension and dim not in (dimension, ANY_DIMENSION):
                # A different dimension: the edge cannot answer this question.
                continue
            if rel == GREATER:
                greater.setdefault(subject, set()).add(obj)
            else:
                greater.setdefault(obj, set()).add(subject)
        nodes: Set[str] = set(greater)
        for ups in greater.values():
            nodes.update(ups)
        if not nodes:
            return None
        if direction == GREATEST:
            # Nothing is greater than the top.
            greater_than = {n for ups in greater.values() for n in ups}
            candidates = [n for n in nodes if n not in greater_than]
            candidates = [n for n in candidates if self._dominates_all(n, greater, nodes)]
        else:
            # The bottom is greater than nobody.
            candidates = [n for n in nodes if not greater.get(n)]
            candidates = [n for n in candidates if self._dominated_by_all(n, greater, nodes)]
        if not candidates:
            return None
        if len(candidates) > 1:
            # Ambiguous (a tie): prefer the node that appears last in the text.
            for subject, _c, _o in reversed(relations):
                if subject in candidates:
                    return subject
            return sorted(candidates)[0]
        return candidates[0]

    @staticmethod
    def _reachable(node: str, graph: Dict[str, Set[str]]) -> Set[str]:
        seen: Set[str] = set()
        stack = list(graph.get(node, ()))
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            stack.extend(graph.get(current, ()))
        return seen

    def _dominates_all(self, node: str, greater: Dict[str, Set[str]], nodes: Set[str]) -> bool:
        """True when *node* transitively reaches every other node."""
        return self._reachable(node, greater) >= (nodes - {node})

    def _dominated_by_all(self, node: str, greater: Dict[str, Set[str]], nodes: Set[str]) -> bool:
        """True when every other node reaches *node*."""
        for other in nodes - {node}:
            if node not in self._reachable(other, greater):
                return False
        return True

    def _answer_yes_no(
        self, relations: List[Tuple[str, Tuple[str, str], str]], question: str
    ) -> Optional[str]:
        """Reachability: is the first subject greater than the last object?"""
        if len(relations) < 2:
            return None
        subject = relations[0][0]
        obj = relations[-1][2]
        edges: Dict[str, Set[str]] = {}
        for s, concept, o in relations:
            _dim, rel = concept
            if rel == GREATER:
                edges.setdefault(s, set()).add(o)
            else:
                edges.setdefault(o, set()).add(s)
        # BFS from the subject.
        seen = {subject}
        stack = [subject]
        while stack:
            node = stack.pop()
            for nxt in edges.get(node, set()):
                if nxt not in seen:
                    seen.add(nxt)
                    stack.append(nxt)
        return "yes" if obj in seen else "no"

    # -- the public entry point ------------------------------------------- #
    def answer(self, question: str) -> Optional[str]:
        """The answer (the entity), or None when the layer cannot make sense of it."""
        solved = self._solve(question)
        return solved[0] if solved else None

    def answer_sentence(self, question: str) -> Optional[str]:
        """The answer as a sentence ("C is the shortest"), like the teacher."""
        solved = self._solve(question)
        if solved is None:
            return None
        entity, direction, dimension = solved
        wording = self._wording(dimension, direction)
        return f"{entity} is {wording}"

    @staticmethod
    def _wording(dimension: Optional[str], direction: str) -> str:
        """The superlative wording of a direction ("the tallest")."""
        if dimension:
            words = SUPERLATIVE_SEEDS.get((dimension, direction))
            if words:
                return words[0]
        return (
            SUPERLATIVE_SEEDS.get((ANY_DIMENSION, direction), ["the greatest"])[0]
            if (
                ANY_DIMENSION,
                direction,
            )
            in SUPERLATIVE_SEEDS
            else ("the greatest" if direction == GREATEST else "the least")
        )

    def _solve(self, question: str) -> Optional[Tuple[str, str, Optional[str]]]:
        """The (entity, direction, dimension) of the question, or None."""
        if not question or not question.strip():
            return None
        # 1. 接觸 — which entity does the question ask for? (The question's
        # dimension also constrains how the relation words are read.)
        agg_phrase = extract_aggregation_span(question)
        if agg_phrase is None:
            return None
        agg = self.matcher.classify_aggregation(agg_phrase)
        if agg is None:
            return None
        dimension, direction, agg_score = agg

        if not _looks_like_question(question):
            # A statement is not a comparison question.
            return None

        relations = self.find_relations(question, dimension=dimension)
        if not relations:
            return None

        # A yes/no question is answered by reachability in the chain.
        if re.search(r"\b(yes or no|yes/no)\b|是嗎|對嗎", question, re.IGNORECASE):
            answer = self._answer_yes_no(relations, question)
            return (answer, direction, dimension) if answer else None

        # 2. 對齊 — the chain's dimension must agree with the question's.
        chain_dimensions = {dim for _s, (dim, _d), _o in relations if dim != ANY_DIMENSION}
        if (
            dimension
            and chain_dimensions
            and dimension not in chain_dimensions
            and agg_score >= _CONFIDENT_AGGREGATION
        ):
            # The question clearly asks for another dimension than the chain
            # is about ("the coldest" over a chain of sizes): the layer does
            # not answer a question it cannot ground.
            return None
        chain_dimension = next(iter(chain_dimensions)) if len(chain_dimensions) == 1 else dimension

        # 3. 合成.
        entity = self._compose(relations, chain_dimension, direction)
        if entity is None:
            return None
        return (entity, direction, chain_dimension)

    # -- the feedback step ------------------------------------------------- #
    def align_phrase(self, phrase: str, concept) -> Dict[str, float]:
        """Align one phrase with a concept (the teacher's verdict, applied).

        The concept's prototype moves one step toward the phrase. A relation
        concept is a (dimension, direction) pair; a direction concept is the
        string "greatest" / "least" (the aggregation side). Nothing about
        the question is stored, so the layer keeps generalising.
        """
        if not phrase:
            return {"aligned": 0.0, "delta": 0.0}
        if isinstance(concept, str):
            delta = self.matcher.align_direction(phrase, concept)
        else:
            delta = self.matcher.align(phrase, concept, kind="relation")
        return {"aligned": 1.0 if delta else 0.0, "delta": delta}

    def align_from_feedback(
        self,
        question: str,
        expected: Optional[str],
        teacher_concept: Optional[Tuple[str, str]] = None,
    ) -> Dict[str, float]:
        """Align the prototypes from the teacher's verdict.

        The teacher tells us which *concept* the comparison phrase should
        have matched; the prototype for that concept moves one step toward
        the phrase. Nothing about the question itself is stored, so the layer
        keeps generalising.
        """
        stats = {"aligned": 0.0, "delta": 0.0}
        if not expected:
            return stats
        for _subject, phrase, _obj in extract_relation_spans(question):
            if not phrase or phrase == "greater":
                continue
            concept: Optional[Tuple[str, str]] = teacher_concept
            if concept is None:
                match = self.matcher.classify(phrase, kind="relation")
                if match is None:
                    continue
                concept = match[0]
            delta = self.matcher.align(phrase, concept, kind="relation")
            if delta:
                stats["aligned"] += 1.0
                stats["delta"] += delta
        return stats


_BRIDGE: Optional[NeuralBridge] = None


def get_neural_bridge() -> NeuralBridge:
    """The process-wide bridge, taught from the committed curriculum.

    ``NeuralBridge()`` stays raw on purpose: the probes need the *untaught*
    layer to measure what teaching adds. The production singleton is the
    taught one, so the measured number and the shipped behaviour are the
    same thing.
    """
    global _BRIDGE
    if _BRIDGE is None:
        bridge = NeuralBridge()
        try:
            from ai.reasoning.paraphrase_curriculum import apply_curriculum

            apply_curriculum(bridge)
        except Exception:  # a missing/invalid curriculum must not break answering
            logger.warning("paraphrase curriculum not applied", exc_info=True)
        _BRIDGE = bridge
    return _BRIDGE


__all__ = [
    "AGGREGATION_ANY_SEEDS",
    "ANY_DIMENSION",
    "CONCEPT_SEEDS",
    "DIMENSION_SEEDS",
    "DIRECTION_SEEDS",
    "GREATER",
    "GREATEST",
    "LESSER",
    "LEAST",
    "NeuralBridge",
    "RelationMatcher",
    "extract_aggregation_span",
    "extract_relation_spans",
    "get_neural_bridge",
]
