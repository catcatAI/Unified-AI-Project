# =============================================================================
# ANGELA-MATRIX: [L3] [βδ] [B] [L1]
# =============================================================================

from __future__ import annotations

import copy
import logging
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .dictionary_layer import DictionaryEntry, DictionaryLayer

logger = logging.getLogger(__name__)


class RelationType(Enum):
    SYNONYM = "="
    ANTI_SYNONYM = "\u2260"
    MAPPING = "\u2192"
    ANTI_MAPPING = "\u219b"
    ANALOGY = "\u223c"
    ANTI_ANALOGY = "\u2241"
    UNRELATED = "?"

    def __str__(self) -> str:
        return self.value


class RelationClassifier:
    def __init__(self, dictionary: Optional["DictionaryLayer"] = None):
        self.dictionary = dictionary

    def classify(
        self,
        key1: str,
        key2: str,
        dictionary: Optional["DictionaryLayer"] = None,
    ) -> RelationType:
        result, _ = self.classify_pair(key1, key2, dictionary=dictionary)
        return result

    def classify_pair(
        self,
        key1: str,
        key2: str,
        context: Optional[Dict[str, Any]] = None,
        dictionary: Optional["DictionaryLayer"] = None,
    ) -> Tuple[RelationType, float]:
        if not key1 or not key2:
            return RelationType.UNRELATED
        d = dictionary or self.dictionary

        if d is None:
            return self._heuristic_classify(key1, key2, None)

        if key1 == key2:
            return RelationType.SYNONYM, 1.0

        entry1 = d.entries.get(key1)
        entry2 = d.entries.get(key2)

        if entry1 is None or entry2 is None:
            return self._heuristic_classify(key1, key2, d)

        if self._check_explicit_relation(entry1, entry2, "synonym"):
            return RelationType.SYNONYM, 0.95
        if self._check_explicit_relation(entry1, entry2, "mapping"):
            return RelationType.MAPPING, 0.90
        if self._check_explicit_relation(entry1, entry2, "analogy"):
            return RelationType.ANALOGY, 0.90
        if self._check_explicit_relation(entry1, entry2, "anti_synonym"):
            return RelationType.ANTI_SYNONYM, 0.95
        if self._check_explicit_relation(entry1, entry2, "anti_mapping"):
            return RelationType.ANTI_MAPPING, 0.95
        if self._check_explicit_relation(entry1, entry2, "anti_analogy"):
            return RelationType.ANTI_ANALOGY, 0.95

        return self._heuristic_classify(key1, key2, d, entry1, entry2)

    def get_synonym_group(
        self, entry: "DictionaryEntry", dictionary: "DictionaryLayer"
    ) -> List[str]:
        syns = list(entry.relations.get("synonym", []))
        result: List[str] = []
        seen: set = {entry.key}
        for s in syns:
            if s not in seen:
                seen.add(s)
                result.append(s)
                sub = dictionary.entries.get(s)
                if sub:
                    for ss in sub.relations.get("synonym", []):
                        if ss not in seen:
                            seen.add(ss)
                            result.append(ss)
        return result

    def get_mapping_group(
        self, entry: "DictionaryEntry", dictionary: "DictionaryLayer"
    ) -> List[str]:
        return list(entry.relations.get("mapping", []))

    def get_analogy_group(
        self,
        entry: "DictionaryEntry",
        dictionary: "DictionaryLayer",
        all_entries: Optional[Dict[str, "DictionaryEntry"]] = None,
    ) -> List[str]:
        candidates = all_entries or dictionary.entries
        results: List[str] = []
        for other_key, other_entry in candidates.items():
            if other_key == entry.key:
                continue
            shared_contexts = set(c.get("context_id") for c in entry.contexts) & set(
                c.get("context_id") for c in other_entry.contexts
            )
            if len(shared_contexts) >= 1:
                results.append(other_key)
        return results

    def _check_explicit_relation(
        self,
        entry1: "DictionaryEntry",
        entry2: "DictionaryEntry",
        relation_key: str,
    ) -> bool:
        targets = entry1.relations.get(relation_key, [])
        return entry2.key in targets

    def _heuristic_classify(
        self,
        key1: str,
        key2: str,
        dictionary: Optional["DictionaryLayer"],
        entry1: Optional["DictionaryEntry"] = None,
        entry2: Optional["DictionaryEntry"] = None,
    ) -> Tuple[RelationType, float]:
        if entry1 is not None and entry2 is not None:
            common_zh = set(entry1.surface_forms.values()) & set(entry2.surface_forms.values())
            if common_zh:
                return RelationType.SYNONYM, 0.80

            shared_contexts = set(c.get("context_id") for c in entry1.contexts) & set(
                c.get("context_id") for c in entry2.contexts
            )
            if shared_contexts:
                return RelationType.MAPPING, 0.65

            surface_sim = self._jaccard_similarity(
                " ".join(entry1.surface_forms.values()),
                " ".join(entry2.surface_forms.values()),
            )
            if surface_sim > 0.4:
                return RelationType.ANALOGY, round(surface_sim * 0.7, 2)

        return RelationType.ANTI_MAPPING, 0.50

    def _jaccard_similarity(self, a: str, b: str) -> float:
        set_a = set(a.lower().split())
        set_b = set(b.lower().split())
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union)

    def _levenshtein_distance(self, a: str, b: str) -> int:
        if len(a) < len(b):
            a, b = b, a
        if not b:
            return len(a)
        prev = list(range(len(b) + 1))
        for i, ca in enumerate(a):
            curr = [i + 1]
            for j, cb in enumerate(b):
                cost = 0 if ca == cb else 1
                curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
            prev = curr
        return prev[-1]
