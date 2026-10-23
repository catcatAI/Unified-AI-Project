# =============================================================================
# ANGELA-MATRIX: [L3] [β] [A] [L4]
# LAYER: knowledge
# =============================================================================
"""Extractive factual recall over an offline encyclopedia index.

The curated store (``ai.knowledge_base``) covers a few dozen subjects. This
module is the general layer behind it: a SQLite FTS5 index built from a public
Wikipedia dump (``scripts/build_knowledge_index.py``) and a small extractive
reader — retrieve candidate articles, then pick the sentence that answers the
question.

It is deliberately *extractive*: it never generates a sentence, so a wrong
answer is a retrieval or selection failure, not a hallucination. The module
abstains (returns ``None``) when no sentence carries enough of the question's
content words; an honest "I don't know" beats a confident guess.

Design notes
------------
- Pure stdlib (``sqlite3``), no network, no model weights.
- IDF is computed from the index itself (one ``count(*)`` per distinct word,
  cached in-process), so rare words decide the subject.
- The question's head ("how many", "what gas") constrains the shape of the
  answer sentence; this is question-type reasoning, not per-question rules.
- Units are converted only when the question names the unit ("... in km/s")
  and the sentence uses another one; the conversion table is generic.
"""

from __future__ import annotations

import logging
import math
import os
import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

DEFAULT_DB = Path("data/knowledge/wiki.sqlite")
MIN_OVERLAP = 2.0
MAX_CANDIDATES = 80

_STOPWORDS = frozenset(
    """
    a about above after again against all am an and any are as at be because
    been before being below between both but by can could did do does doing
    down during each few for from further had has have having he her here hers
    herself him himself his how i if in into is it its itself just me more most
    my myself no nor not now of off on once only or other our ours ourselves
    out over own same she should so some such than that the their theirs them
    themselves then there these they this those through to too under until up
    very was we were what when where which while who whom why will with would
    you your yours yourself yourselves tell give name called known kind type
    primary main usually approximately approx roughly
    say says said make makes made get gets got take takes give gives use uses
    used work works help helps keep keeps put puts see sees seem seems become
    becomes come comes go goes want wants like likes need needs
    """.split()
)

_SUFFIXES = ("ing", "ed", "es", "s", "ly")
_PLURAL_SIBILANT = ("ses", "xes", "zes", "ches", "shes")
_NUMBER_WORDS = {
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "hundred",
    "thousand",
    "million",
    "billion",
}
# Heads that name a *type* or *property* the answer must be. "What is the
# capital of Atlantis?" is not answered by an article that never says
# "capital"; the sentence has to be about the asked relation, not merely
# the asked subject.
_ANSWER_TYPE_HEADS = frozenset(
    """
    capital population height length width area weight mass author writer
    founder currency language president leader inventor director producer
    publisher diameter distance temperature speed age depth birthday
    birthplace location planet star element gas organ force animal insect
    bird metal colour color continent ocean country city river mountain
    number symbol formula
    """.split()
)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_UNIT_ALIASES = {
    "km/s": ("km/s", "kilometres per second", "kilometers per second"),
    "m/s": ("m/s", "metres per second", "meters per second"),
}

# unit -> (metres, seconds) multipliers relative to the base (m/s)
_SPEED_UNITS: Dict[str, float] = {
    "m/s": 1.0,
    "metres per second": 1.0,
    "meters per second": 1.0,
    "km/s": 1000.0,
    "kilometres per second": 1000.0,
    "kilometers per second": 1000.0,
    "km/h": 1000.0 / 3600.0,
    "mph": 1609.344 / 3600.0,
    "miles per hour": 1609.344 / 3600.0,
}

_NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _stem(word: str) -> str:
    """A deliberately small stemmer (plurals first, then common suffixes).

    Retrieval only needs "continents" to meet "Continent" and "gases" to meet
    "gas"; a real stemmer is a dependency. Plurals are handled before the
    generic suffix list because "force"+"s" must stay "force" (stripping "es"
    from "forces" would give "forc", which never meets "force").
    """
    word = word.lower()
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith(_PLURAL_SIBILANT):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    for suffix in ("ing", "ed", "ly"):
        if len(word) > 5 and word.endswith(suffix):
            return word[: -len(suffix)]
    return word


def _words(text: str) -> List[str]:
    return [w for w in re.split(r"[^0-9A-Za-z\u4e00-\u9fff]+", text.lower()) if w]


def _content_words(text: str) -> List[str]:
    return [w for w in _words(text) if w not in _STOPWORDS and len(w) > 1]


def _clean_number(text: str) -> Optional[float]:
    try:
        return float(text.replace(",", "").rstrip("."))
    except ValueError:
        return None


class WikiFacts:
    """Extractive reader over a Wikipedia FTS5 index."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        configured = os.environ.get("ANGELA_WIKI_DB")
        path = Path(configured) if configured else (db_path or DEFAULT_DB)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[5] / path
        self._path = path
        self._connection: Optional[sqlite3.Connection] = None
        self._df: Dict[str, int] = {}
        self._total: Optional[int] = None

    # -- index access ------------------------------------------------------ #
    def available(self) -> bool:
        return self._path.is_file()

    def _db(self) -> Optional[sqlite3.Connection]:
        if self._connection is not None:
            return self._connection
        if not self.available():
            return None
        try:
            self._connection = sqlite3.connect(
                f"file:{self._path}?mode=ro", uri=True, check_same_thread=False
            )
            self._connection.row_factory = sqlite3.Row
        except sqlite3.Error as exc:  # pragma: no cover - unreadable index
            logger.warning("wiki index unreadable: %s", exc)
            return None
        return self._connection

    def _corpus_size(self) -> int:
        if self._total is None:
            connection = self._db()
            self._total = 0
            if connection is not None:
                try:
                    self._total = connection.execute("SELECT count(*) FROM pages").fetchone()[0]
                except sqlite3.Error:  # pragma: no cover
                    self._total = 0
        return self._total

    def _idf(self, word: str) -> float:
        if word in self._df:
            count = self._df[word]
        else:
            connection = self._db()
            count = 0
            if connection is not None:
                try:
                    # The quoted term keeps FTS5 syntax out of the query.
                    count = connection.execute(
                        "SELECT count(*) FROM pages WHERE pages MATCH ?", (f'"{word}"',)
                    ).fetchone()[0]
                except sqlite3.Error:  # pragma: no cover
                    count = 0
            self._df[word] = count
        total = self._corpus_size() or 1
        return math.log((total + 1.0) / (count + 1.0)) + 1.0

    def _candidates(self, words: Sequence[str]) -> List[sqlite3.Row]:
        connection = self._db()
        if connection is None:
            return []
        terms = sorted(set(words), key=lambda w: -self._idf(w))[:8]
        if not terms:
            return []
        query = " OR ".join(f'"{term}"' for term in terms)
        try:
            return connection.execute(
                "SELECT title, body, rank FROM pages WHERE pages MATCH ? "
                "ORDER BY rank LIMIT ?",
                (query, MAX_CANDIDATES),
            ).fetchall()
        except sqlite3.Error as exc:  # pragma: no cover
            logger.debug("wiki query failed: %s", exc)
            return []

    # -- unit handling ----------------------------------------------------- #
    @staticmethod
    def _requested_units(question: str) -> List[str]:
        requested: List[str] = []
        lowered = question.lower()
        for unit, aliases in _UNIT_ALIASES.items():
            if any(alias in lowered for alias in aliases):
                requested.append(unit)
        return requested

    @staticmethod
    def _convert_sentence(sentence: str, unit: str) -> Optional[str]:
        """Rewrite a speed in the requested unit ("299,792,458 m/s" -> km/s)."""
        if unit not in _SPEED_UNITS:
            return None
        for source, factor in sorted(_SPEED_UNITS.items(), key=lambda kv: -len(kv[0])):
            if source == unit:
                continue
            pattern = re.compile(
                r"(\d[\d,]*(?:\.\d+)?)\s*" + re.escape(source) + r"\b", re.IGNORECASE
            )
            match = pattern.search(sentence)
            if not match:
                continue
            value = _clean_number(match.group(1))
            if value is None:
                continue
            converted = value * factor / _SPEED_UNITS[unit]
            if converted >= 1000:
                text = f"{round(converted):,}"
            else:
                text = f"{converted:g}"
            return f"{text} {unit}"
        return None

    # -- public API -------------------------------------------------------- #
    def _phrases(self, question: str) -> List[str]:
        """Question bigrams, in text order ("the Red Planet" -> "red planet")."""
        words = _words(question)
        return [f"{first} {second}" for first, second in zip(words, words[1:])]

    @staticmethod
    def _head(question: str) -> Optional[str]:
        """The noun the question asks about ("how many LEGS", "what GAS")."""
        words = _words(question)
        for index, word in enumerate(words):
            if word in ("many", "much", "what", "which"):
                for following in words[index + 1 : index + 4]:
                    if following not in _STOPWORDS and len(following) > 1:
                        return following
        return None

    @staticmethod
    def _entity(question: str) -> bool:
        """The question asks for an entity ("what/which <thing> ...")."""
        return bool(re.match(r"\s*(what|which|who|name)\b", question.lower()))

    def _sentences(self, body: str) -> List[str]:
        return [part.strip() for part in _SENTENCE_SPLIT.split(body) if part.strip()]

    def _entity_answer(
        self,
        question: str,
        question_stems: set,
        phrases: List[str],
        type_stem: Optional[str],
        title: str,
        sentences: List[str],
    ) -> Optional[Tuple[float, str]]:
        """The article's subject, when the article opens by defining it."""
        if not type_stem:
            return None
        title_words = _words(title)
        if not title_words:
            return None
        opening = {_stem(w) for w in _words(" ".join(sentences[:4]))}
        # The lead must name the subject in its first few words ("Spiders (...)
        # are ..."), plural-tolerant, otherwise the article is about something
        # else that merely mentions the title.
        if not {_stem(w) for w in _words(" ".join(sentences[:1]))} & {
            _stem(w) for w in title_words
        }:
            return None
        overlap = question_stems & opening
        if len(overlap) < 2:
            return None
        # The defining sentence must say what the subject *is*: "<Title> is a
        # <head>" ("Carbon dioxide ... is a gas"). A title that only appears
        # somewhere in the first sentence is not a definition ("Leaf" is not
        # the answer to "what gas do plants absorb").
        if not self._defines(sentences[:3], type_stem):
            return None
        lead = " ".join(sentences[:2]).lower()
        score = sum(self._idf(stem) for stem in overlap) + 1.5
        score += sum(1.5 for phrase in phrases if phrase in lead)
        score += 1.5
        if len(title_words) <= 2:
            score += 2.0  # "Sun" over "Department of Energy and Climate Change"
        if {_stem(w) for w in title_words} <= question_stems:
            score += 1.0
        return (score, title)

    def answer(self, question: str) -> Optional[str]:
        """The sentence (or entity) that answers *question*, or ``None``."""
        if not question or not self.available():
            return None
        words = _content_words(question)
        question_stems = {_stem(w) for w in words}
        if not question_stems:
            return None
        phrases = self._phrases(question)
        head = self._head(question)
        head_stem = _stem(head) if head else None
        # Only a *type* head ("what organ", "which gas") licenses the
        # definition-shaped entity answer; a head that is the agent ("what do
        # BEES collect") must not.
        type_stem = head_stem if head_stem in _ANSWER_TYPE_HEADS else None
        wants_number = bool(
            re.match(r"\s*(how many|how much|how old|how long|how far)", question.lower())
        )
        units = self._requested_units(question)
        approximate = bool(
            re.search(
                r"\b(approximately|approx\.?|roughly|about|around)\b", question.lower()
            )
        )
        rows = self._candidates(words)
        if not rows:
            return None

        best: Optional[Tuple[float, str]] = None
        for row in rows:
            title = row["title"]
            title_stems = {_stem(w) for w in _words(title)}
            sentences = self._sentences(row["body"])
            if not sentences:
                continue
            subject = bool(title_stems) and title_stems <= question_stems
            for index in range(len(sentences)):
                window = sentences[index]
                if index + 1 < len(sentences):
                    window = f"{window} {sentences[index + 1]}"
                window_stems = {_stem(w) for w in _words(window)}
                overlap = question_stems & window_stems
                # One rare word is not evidence: a question carries a
                # subject *and* a relation, and the answer sentence must
                # connect at least two of them ("capital" + "Atlantis",
                # not a world city that merely says "capital").
                if len(overlap) < 2:
                    continue
                if type_stem and type_stem not in window_stems:
                    continue
                score = sum(self._idf(stem) for stem in overlap)
                score += sum(1.0 for phrase in phrases if phrase in window.lower())
                score -= 0.002 * max(0, len(window) - 160)
                if index == 0:
                    score += 1.2
                elif index == 1:
                    score += 0.6
                score += 0.6 * sum(
                    self._idf(stem) for stem in (question_stems & title_stems)
                )
                if subject:
                    score += 2.0
                if head_stem and head_stem in window_stems:
                    score += 1.0
                if wants_number:
                    # The number must be *about* the head noun ("eight legs"),
                    # not just any number in the same sentence.
                    if head_stem and self._number_before(window, head_stem):
                        score += 6.0
                    elif not _NUMBER.search(window) and not any(
                        word in _NUMBER_WORDS for word in _words(window)
                    ):
                        score -= 1.5
                if units and not _NUMBER.search(window):
                    score -= 2.0
                if best is None or score > best[0]:
                    best = (score, window)

            if self._entity(question) and not wants_number and not units:
                entity = self._entity_answer(
                    question, question_stems, phrases, type_stem, title, sentences
                )
                if entity is not None and (best is None or entity[0] > best[0]):
                    best = entity

        if best is None or best[0] < MIN_OVERLAP:
            return None
        answer = best[1]
        for unit in units:
            converted = self._convert_sentence(answer, unit)
            if converted:
                answer = converted
                break
        if approximate and units:
            answer = self._round_answer(answer, 2)
        return answer[:400]

    @staticmethod
    def _defines(sentences: List[str], head_stem: str) -> bool:
        """Does "<subject> is a <head>" appear near a copula?"""
        for sentence in sentences:
            words = _words(sentence)
            for index, word in enumerate(words):
                if word not in ("is", "are", "was", "were"):
                    continue
                predicate = words[index + 1 : index + 6]
                for offset, word in enumerate(predicate):
                    if _stem(word) != head_stem:
                        continue
                    # "Its main functions are photosynthesis AND gas
                    # exchange" lists two things; the head is not the
                    # predicate that defines the subject.
                    if any(connector in predicate[:offset] for connector in ("and", "or")):
                        break
                    return True
        return False

    @staticmethod
    def _number_before(sentence: str, head_stem: str) -> bool:
        words = _words(sentence)
        for index, word in enumerate(words):
            if word in _NUMBER_WORDS or _NUMBER.fullmatch(word):
                for following in words[index + 1 : index + 3]:
                    if _stem(following) == head_stem:
                        return True
        return False

    @staticmethod
    def _round_answer(answer: str, digits: int) -> str:
        """Round a leading number to *digits* significant figures."""
        match = _NUMBER.search(answer)
        if not match:
            return answer
        value = _clean_number(match.group(0))
        if value is None or value == 0:
            return answer
        exponent = math.floor(math.log10(abs(value)))
        rounded = round(value, -(exponent - digits + 1))
        formatted = f"{rounded:,}" if rounded >= 1000 else f"{rounded:g}"
        return answer[: match.start()] + formatted + answer[match.end() :]


_INSTANCE: Optional[WikiFacts] = None

_QUESTION_SHAPE = re.compile(
    r"^\s*(what|which|who|whom|whose|where|when|why|how|is|are|was|were|does|do|did|can)\b",
    re.IGNORECASE,
)


def looks_factual(text: str) -> bool:
    """A question that asks about the world (not about the conversation).

    The general layer is a fallback behind the curated store; it must not
    answer "how are you" with an encyclopedia article. Shape and length are
    cheap, honest filters; the retrieval score does the rest.
    """
    stripped = (text or "").strip()
    if len(stripped) < 12 or len(_content_words(stripped)) < 2:
        return False
    if not stripped.endswith("?") and not _QUESTION_SHAPE.match(stripped):
        return False
    return True


def get_wiki_facts() -> WikiFacts:
    """The process-wide reader (the connection and idf cache are reused)."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = WikiFacts()
    return _INSTANCE


def route_general_knowledge(text: str) -> Optional[str]:
    """Answer a factual question from the offline encyclopedia, or ``None``.

    This is the layer *behind* the curated store: the curated store answers
    what it knows exactly, and this general layer handles the long tail. It
    abstains on non-questions and on low-confidence retrievals.
    """
    if os.environ.get("ANGELA_WIKI_FACTS", "1").lower() in ("0", "false", "off"):
        return None
    if not looks_factual(text):
        return None
    try:
        return get_wiki_facts().answer(text)
    except Exception as exc:  # pragma: no cover - index/IO problems
        logger.warning("general knowledge lookup failed: %s", exc)
        return None


__all__ = ["WikiFacts", "get_wiki_facts", "looks_factual", "route_general_knowledge"]
