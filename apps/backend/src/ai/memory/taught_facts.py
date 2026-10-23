# =============================================================================
# ANGELA-MATRIX: [L2] [β] [A] [L5]
# LAYER: memory
# =============================================================================
"""Facts the user taught in conversation, and the relation names they used.

WHY this exists
---------------
The curated store and the encyclopedia answer *public* knowledge; neither can
learn "Zorblax's capital is Quuxville" from a sentence the user just said.
Recall that only quotes the user back ("你剛才說過…") is not learning either:
the fact has to answer an *ordinary* question, in a *new* wording, afterwards.

This module is the smallest honest learner for that:

- **extract** a (subject, relation, object) triple from a user *statement*
  ("X 的首都是 Y" / "the capital of X is Y" / "X's capital is Y");
- **correct**: "X 的首都不是 A，是 B" replaces the old object (the newest
  statement about the same subject+relation wins);
- **aliases**: "首府和首都指的是同一件事" teaches a relation synonym that then
  applies to *every* subject, including ones taught earlier or later;
- **abstain**: a question is never learned as a fact, and a lookup answers only
  when the question names both a taught subject and its relation.

No per-question strings, no benchmark knowledge: the only training signal is
the conversation. Storage is a small JSON file in the data dir (the probe points
the data dir at a sandbox).
"""

from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set, Tuple

logger = logging.getLogger(__name__)

MAX_FACTS = 5000
MAX_ALIAS_CLASSES = 500

_CJK = "\u4e00-\u9fff"
_ZH_SUBJECT = rf"[A-Za-z0-9{_CJK}][A-Za-z0-9{_CJK}·]{{0,29}}"
_ZH_RELATION = rf"[{_CJK}A-Za-z]{{1,12}}"
_OBJECT = r"[^，。！？；：,.;:!?]{1,60}"

_ZH_CORRECTION = re.compile(
    rf"(?P<subject>{_ZH_SUBJECT})\s*的\s*(?P<relation>{_ZH_RELATION})\s*"
    rf"(?:不是|不再是|並不是)\s*(?P<old>{_OBJECT})\s*[，,]\s*(?:而)?(?:是|為)\s*"
    rf"(?P<object>{_OBJECT})"
)
_ZH_FACT = re.compile(
    rf"(?P<subject>{_ZH_SUBJECT})\s*的\s*(?P<relation>{_ZH_RELATION})\s*"
    rf"(?:是|為)\s*(?P<object>{_OBJECT})"
)
_EN_FACT_OF = re.compile(
    r"the (?P<relation>[A-Za-z][A-Za-z ]{0,20}?) of "
    r"(?P<subject>[A-Z][\w\-]*(?: [A-Z][\w\-]*){0,2}) is (?P<object>[^.,;!?]{1,40})"
)
_EN_FACT_POSS = re.compile(
    r"(?P<subject>[A-Z][\w\-]*(?: [A-Z][\w\-]*){0,2})(?:'s|’s) "
    r"(?P<relation>[A-Za-z][A-Za-z ]{0,20}?) is (?P<object>[^.,;!?]{1,40})"
)

_ALIAS_CUE = re.compile(r"同一|同義|同義詞|一樣|相等|同位|共指")
_ALIAS_ZH = re.compile(
    rf"(?:「(?P<a1>[^」]{{1,20}})」|(?P<a2>[A-Za-z{_CJK}]{{1,20}}?))"
    rf"\s*(?:和|與|跟|、)\s*"
    rf"(?:「(?P<b1>[^」]{{1,20}})」|(?P<b2>[A-Za-z{_CJK}]{{1,20}}?))"
    r"\s*(?=是|指|代表|同|相等|，|,|。|$)"
)

_WH_WORDS = frozenset(
    "什麼 什麼 誰 哪裡 哪 哪個 哪座 多少 幾 何 怎麼 為什麼 如何 "
    "what which who whom where when why how".split()
)
_QUESTION_START = re.compile(
    r"^\s*(?:什麼|誰|哪裡|哪|多少|幾|怎麼|為什麼|如何|"
    r"what|which|who|whom|where|when|why|how|is|are|does|do|did|can)\b",
    re.IGNORECASE,
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _clean(text: str) -> str:
    return (text or "").strip().strip("「」『』\"'()（）").strip()


def _bigrams(text: str) -> Set[str]:
    compact = re.sub(r"[\s\W_]+", "", _norm(text), flags=re.UNICODE)
    if len(compact) < 2:
        return {compact} if compact else set()
    return {compact[index : index + 2] for index in range(len(compact) - 1)}


def _overlap(left: Set[str], right: Set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left)


def _is_question(text: str) -> bool:
    stripped = (text or "").strip()
    if stripped.endswith(("?", "？")):
        return True
    return bool(_QUESTION_START.match(stripped))


@dataclass
class Fact:
    subject: str
    relation: str
    object: str
    source: str = ""
    revision: int = 1
    updated_at: float = 0.0


class TaughtFacts:
    """A tiny store of user-taught triples, with correction and aliases."""

    def __init__(self, path: Optional[Path] = None) -> None:
        self._lock = threading.Lock()
        self._facts: Dict[Tuple[str, str], Fact] = {}
        self._aliases: List[Set[str]] = []
        self._path = path or _default_path()
        self._load()

    # -- persistence ------------------------------------------------------- #
    def _load(self) -> None:
        if not self._path.is_file():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - corrupt file
            logger.warning("taught-facts file unreadable: %s", exc)
            return
        for raw in data.get("facts", []):
            try:
                fact = Fact(**raw)
            except TypeError:
                continue
            self._facts[(_norm(fact.subject), _norm(fact.relation))] = fact
        self._aliases = [
            {_norm(alias) for alias in group if _norm(alias)}
            for group in data.get("aliases", [])
            if group
        ]

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "facts": [asdict(fact) for fact in self._facts.values()],
                "aliases": [sorted(group) for group in self._aliases],
            }
            self._path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
            )
        except Exception as exc:  # pragma: no cover - read-only fs
            logger.warning("taught-facts file not written: %s", exc)

    # -- teaching ---------------------------------------------------------- #
    def learn_from_turn(self, text: str) -> None:
        """Learn from a user *statement* (a question teaches nothing)."""
        if not text or not text.strip():
            return
        if _is_question(text):
            return
        if self._teach_aliases(text):
            return
        learned = self._extract_facts(text)
        if not learned:
            return
        with self._lock:
            for fact in learned:
                self._upsert(fact)
            self._save()

    def _teach_aliases(self, text: str) -> bool:
        if not _ALIAS_CUE.search(text):
            return False
        pairs: List[Tuple[str, str]] = []
        for match in _ALIAS_ZH.finditer(text):
            first = _clean(match.group("a1") or match.group("a2") or "")
            second = _clean(match.group("b1") or match.group("b2") or "")
            if first and second and first != second:
                pairs.append((first, second))
        if not pairs:
            return False
        with self._lock:
            for first, second in pairs:
                self._merge_alias(_norm(first), _norm(second))
            self._save()
        return True

    def _merge_alias(self, left: str, right: str) -> None:
        merged = {left, right}
        remaining: List[Set[str]] = []
        for group in self._aliases:
            if group & merged:
                merged |= group
            else:
                remaining.append(group)
        remaining.append(merged)
        self._aliases = remaining[-MAX_ALIAS_CLASSES:]

    def _extract_facts(self, text: str) -> List[Fact]:
        facts: List[Fact] = []
        for match in _ZH_CORRECTION.finditer(text):
            facts.append(
                Fact(
                    subject=_clean(match.group("subject")),
                    relation=_clean(match.group("relation")),
                    object=_clean(match.group("object")),
                    source=text.strip()[:200],
                    updated_at=time.time(),
                )
            )
        corrected_spans = [(m.start(), m.end()) for m in _ZH_CORRECTION.finditer(text)]
        for match in _ZH_FACT.finditer(text):
            if any(start <= match.start() < end for start, end in corrected_spans):
                continue
            obj = _clean(match.group("object"))
            if _norm(obj) in {_norm(word) for word in _WH_WORDS}:
                continue
            facts.append(
                Fact(
                    subject=_clean(match.group("subject")),
                    relation=_clean(match.group("relation")),
                    object=obj,
                    source=text.strip()[:200],
                    updated_at=time.time(),
                )
            )
        for pattern in (_EN_FACT_OF, _EN_FACT_POSS):
            for match in pattern.finditer(text):
                obj = _clean(match.group("object"))
                if _norm(obj) in {_norm(word) for word in _WH_WORDS}:
                    continue
                facts.append(
                    Fact(
                        subject=_clean(match.group("subject")),
                        relation=_clean(match.group("relation")),
                        object=obj,
                        source=text.strip()[:200],
                        updated_at=time.time(),
                    )
                )
        return facts

    def _upsert(self, fact: Fact) -> None:
        key = (_norm(fact.subject), _norm(fact.relation))
        previous = self._facts.get(key)
        if previous is not None:
            fact.revision = previous.revision + 1
        if len(self._facts) >= MAX_FACTS and key not in self._facts:
            oldest = min(self._facts, key=lambda k: self._facts[k].updated_at)
            self._facts.pop(oldest, None)
        self._facts[key] = fact

    # -- answering --------------------------------------------------------- #
    def _alias_class(self, relation: str) -> Set[str]:
        wanted = _norm(relation)
        for group in self._aliases:
            if wanted in group:
                return set(group)
        return {wanted}

    def _relation_matches(self, relation: str, question: str) -> bool:
        normalized = _norm(relation)
        if normalized and normalized in question:
            return True
        for alias in self._alias_class(relation):
            if alias and alias in question:
                return True
            if _overlap(_bigrams(alias), _bigrams(question)) >= 0.5:
                return True
        return False

    def lookup(self, question: str) -> Optional[str]:
        """Answer from taught facts when the question names subject + relation."""
        if not question:
            return None
        normalized = _norm(question)
        with self._lock:
            facts = list(self._facts.values())
        matches: List[Fact] = []
        for fact in facts:
            if _norm(fact.subject) not in normalized:
                continue
            if not self._relation_matches(fact.relation, normalized):
                continue
            matches.append(fact)
        if not matches:
            return None
        # Answer in the order the question names the subjects.
        matches.sort(key=lambda fact: normalized.find(_norm(fact.subject)))
        # Composition: several taught subjects in one question ("A 和 B 的…").
        seen: Set[str] = set()
        unique: List[Fact] = []
        for fact in matches:
            if _norm(fact.subject) in seen:
                continue
            seen.add(_norm(fact.subject))
            unique.append(fact)
        english = not re.search(r"[\u4e00-\u9fff]", question)
        if len(unique) == 1:
            fact = unique[0]
            if english:
                return f"The {fact.relation} of {fact.subject} is {fact.object}."
            return f"{fact.subject}的{fact.relation}是 {fact.object}。"
        if english:
            parts = [
                f"{fact.subject}: {fact.object}" for fact in unique[:4]
            ]
            return "; ".join(parts) + "."
        parts = [f"{fact.subject}的{fact.relation}是 {fact.object}" for fact in unique[:4]]
        return "；".join(parts) + "。"

    # -- introspection ----------------------------------------------------- #
    def facts(self) -> List[Fact]:
        with self._lock:
            return list(self._facts.values())

    def aliases(self) -> List[Set[str]]:
        with self._lock:
            return [set(group) for group in self._aliases]


def _default_path() -> Path:
    override = os.environ.get("ANGELA_TAUGHT_FACTS")
    if override:
        return Path(override)
    try:
        from core.system.path_config import DATA_DIR

        return Path(DATA_DIR) / "taught_facts.json"
    except Exception:  # pragma: no cover - path module unavailable
        return Path(os.getcwd()) / "data" / "taught_facts.json"


_INSTANCE: Optional[TaughtFacts] = None


def get_taught_facts() -> TaughtFacts:
    """The process-wide store (loads once; the data dir may be sandboxed)."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = TaughtFacts()
    return _INSTANCE


def reset_taught_facts() -> None:
    """Drop the singleton (tests, and a probe that switches data dirs)."""
    global _INSTANCE
    _INSTANCE = None


__all__ = ["Fact", "TaughtFacts", "get_taught_facts", "reset_taught_facts"]
