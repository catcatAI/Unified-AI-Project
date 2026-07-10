# =============================================================================
# ANGELA-MATRIX: [L3] [αδ] [B] [L2]
# =============================================================================

import copy
import datetime
import json
import logging
import re
import threading
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from ai.core.unicode_utils import is_cjk, normalize_text, to_romaji
from core.system.config.magic_numbers import (
    behavior_threshold,
    cache_value,
    confidence_value,
    learning_rate,
    limit_value,
    threshold_value,
)

logger = logging.getLogger(__name__)


class DictionaryEntry:
    __slots__ = ("key", "surface_forms", "contexts", "relations", "confidence")

    def __init__(
        self,
        key: str,
        surface_forms: Dict[str, str],
        contexts: Optional[List[Dict[str, Any]]] = None,
        relations: Optional[Dict[str, List[str]]] = None,
        confidence: float = 1.0,
    ):
        self.key = key
        self.surface_forms = surface_forms
        self.contexts = contexts or []
        self.relations = relations or {}
        self.confidence = min(max(confidence, 0.0), 1.0)

    def __repr__(self) -> str:
        return (
            f"DictionaryEntry(key={self.key!r}, "
            f"surface={list(self.surface_forms.keys())}, "
            f"confidence={self.confidence:.2f})"
        )


class DictionaryLayer:
    def __init__(self, growth_threshold: float = 0.5, max_entries: int = 500000):
        self.entries: Dict[str, DictionaryEntry] = {}
        self.modality_encoders: Dict[str, Any] = {"text": None, "image": None, "audio": None}
        self.growth_threshold = growth_threshold
        self.max_entries = max_entries
        self._next_key_id: int = 1
        self._keyword_index: Dict[str, List[str]] = {}
        self._bigram_index: Dict[str, List[str]] = {}
        self._rebuilt_index: bool = False
        self._dirty: bool = True
        self._lock = threading.RLock()
        self._growth_history: List[Dict[str, Any]] = []
        self._index_version: int = 0
        self._encode_cache: OrderedDict = OrderedDict()
        self._encode_cache_max: int = cache_value("ai.dictionary_layer.encode_cache_max", 256)

    def _assign_key(self, prefix: str = "c") -> str:
        key = f"{prefix}{self._next_key_id}"
        self._next_key_id += 1
        return key

    def lookup(
        self, keys: List[str], anchors: Optional[List[DictionaryEntry]] = None
    ) -> Dict[str, Any]:
        if not keys:
            return {}
        result: Dict[str, Any] = {}
        anchor_keys = {e.key for e in (anchors or [])}
        for key in keys:
            entry = self.entries.get(key)
            if entry is None:
                result[key] = None
                continue
            if anchors and key not in anchor_keys:
                confidence_boost = behavior_threshold("ai.dictionary_layer.confidence_boost", 0.1)
                boosted = copy.copy(entry)
                boosted.confidence = min(boosted.confidence + confidence_boost, 1.0)
                result[key] = boosted
            else:
                result[key] = entry
        return result

    # Cap on encode results to prevent bigram explosion
    MAX_ENCODE_KEYS: int = limit_value("ai.dictionary_layer.max_encode_keys", 5)
    MIN_ENCODE_SCORE: float = threshold_value("ai.dictionary_layer.min_encode_score", 0.25)

    def encode(self, text: str, modality: str = "text") -> List[str]:
        raw: List[str]
        with self._lock:
            raw = self._encode_locked(text, modality)
        if len(raw) <= self.MAX_ENCODE_KEYS:
            return raw
        soft = self.encode_soft(text)
        scored = [(k, soft.get(k, 0.0)) for k in raw]
        scored.sort(key=lambda x: x[1], reverse=True)
        filtered = [k for k, s in scored if s >= self.MIN_ENCODE_SCORE]
        if not filtered:
            return raw[:self.MAX_ENCODE_KEYS]
        return filtered[:self.MAX_ENCODE_KEYS]

    def encode_soft(self, text: str) -> Dict[str, float]:
        if not text or not isinstance(text, str):
            return {}
        max_text_len = limit_value("ai.dictionary_layer.max_text_len", 10000)
        if len(text) > max_text_len:
            text = text[:max_text_len]
        text = normalize_text(text)
        self._rebuild_index()
        text_lower = text.lower().strip()
        scores: Dict[str, float] = {}
        max_len = max(len(text_lower), 1)

        # Collect candidate keys from keyword/bigram index
        candidates: set = set()
        for kw, keys in self._keyword_index.items():
            if kw in text_lower:
                candidates.update(keys)
        for bigram, keys in self._bigram_index.items():
            if bigram in text_lower:
                candidates.update(keys)
        if not candidates:
            return {}

        for key in candidates:
            entry = self.entries.get(key)
            if entry is None:
                continue
            best = 0.0
            for sf in entry.surface_forms.values():
                sf_lower = normalize_text(sf).lower().strip()
                if not sf_lower:
                    continue
                if sf_lower == text_lower:
                    best = 1.0
                    break
                if sf_lower in text_lower:
                    # Penalize single CJK character false positives from CC-CEDICT
                    if len(sf_lower) == 1 and not sf_lower.isascii() and len(text_lower) > 1:
                        best = max(best, 0.05)
                    else:
                        ratio = len(sf_lower) / max_len
                        best = max(best, ratio * behavior_threshold("ai.dictionary_layer.encode_exact_weight", 0.85))
                if text_lower in sf_lower:
                    ratio = len(text_lower) / max(len(sf_lower), 1)
                    best = max(best, ratio * behavior_threshold("ai.dictionary_layer.encode_substr_weight", 0.6))
            if best > 0:
                scores[key] = round(best * entry.confidence, 4)
        return scores

    def disambiguate(self, keys: List[str], context: Dict[str, Any]) -> List[str]:
        """Word sense disambiguation: reorder keys by contextual relevance.

        Scores each key by surface-form overlap with context text.
        Unmatched keys are deprioritised (moved to end).
        """
        if not keys or not context:
            return keys
        context_text = " ".join(
            str(v) for v in context.values()
            if isinstance(v, (str, list)) and v
        )
        if not context_text:
            return keys
        context_lower = normalize_text(context_text).lower()
        scored: List[Tuple[str, int]] = []
        for key in keys:
            entry = self.entries.get(key)
            if entry is None:
                scored.append((key, 0))
                continue
            overlap = 0
            for sf in entry.surface_forms.values():
                sf_lower = normalize_text(sf).lower()
                if sf_lower and sf_lower in context_lower:
                    overlap += len(sf_lower)
            scored.append((key, overlap))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [k for k, _ in scored]

    def _encode_locked(self, text: str, modality: str = "text") -> List[str]:
        if not text or not isinstance(text, str):
            return []
        max_text_len = limit_value("ai.dictionary_layer.max_text_len", 10000)
        if len(text) > max_text_len:
            text = text[:max_text_len]
        text = normalize_text(text)
        if modality != "text":
            logger.warning("Only 'text' modality is supported; falling back to text encoding.")
        self._rebuild_index()
        cache_key = (text.lower().strip(), self._index_version)
        cached = self._encode_cache.get(cache_key)
        if cached is not None:
            self._encode_cache.move_to_end(cache_key)
            return cached
        text_lower = text.lower().strip()
        matched_keys: List[str] = []

        for kw, keys in self._keyword_index.items():
            if kw in text_lower:
                matched_keys.extend(keys)

        for bigram, keys in self._bigram_index.items():
            if bigram in text_lower:
                matched_keys.extend(keys)

        seen: set = set()
        unique_keys: List[str] = []
        for k in matched_keys:
            if k not in seen:
                seen.add(k)
                unique_keys.append(k)

        expanded_keys: List[str] = []
        for k in list(unique_keys):
            syns = self.get_synonyms(k)
            for s in syns:
                if s not in seen and s in self.entries:
                    seen.add(s)
                    expanded_keys.append(s)
        unique_keys.extend(expanded_keys)

        if len(self._encode_cache) > self._encode_cache_max:
            self._encode_cache.popitem(last=False)
        self._encode_cache[cache_key] = unique_keys
        return unique_keys

    def decode(self, keys: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        if not keys:
            return ""
        if context and context.get("disambiguate"):
            keys = self.disambiguate(keys, context)
        parts: List[str] = []
        for key in keys:
            entry = self.entries.get(key)
            if entry is None:
                continue
            zh = entry.surface_forms.get("zh")
            en = entry.surface_forms.get("en")
            surface = zh or en or key
            parts.append(surface)
        return " ".join(parts)

    def add_entry(
        self,
        key: str,
        surface_forms: Dict[str, str],
        contexts: Optional[List[Dict[str, Any]]] = None,
        relations: Optional[Dict[str, List[str]]] = None,
        confidence: float = 1.0,
    ) -> DictionaryEntry:
        if not key or not isinstance(key, str):
            raise ValueError(f"Invalid key: {key}")
        if key in self.entries:
            logger.warning("Overwriting existing entry with key=%s", key)
        entry = DictionaryEntry(
            key=key,
            surface_forms=surface_forms,
            contexts=contexts,
            relations=relations,
            confidence=confidence,
        )
        self.entries[key] = entry
        self._dirty = True
        return entry

    def bulk_add_entries(
        self,
        entries_data: List[Dict[str, Any]],
    ) -> int:
        """Add many entries at once, rebuilding the index only once."""
        count = 0
        for data in entries_data:
            key = data.get("key", "")
            if not key or key in self.entries:
                continue
            self.entries[key] = DictionaryEntry(
                key=key,
                surface_forms=data.get("surface_forms", {}),
                contexts=data.get("contexts"),
                relations=data.get("relations", {}),
                confidence=data.get("confidence", 1.0),
            )
            count += 1
        self._dirty = True
        return count

    def grow(
        self, text: str, surface_form: str, confidence: float = 0.5
    ) -> str:
        if not text or not isinstance(text, str):
            logger.warning("Cannot grow entry from empty text")
            return ""
        if confidence < self.growth_threshold:
            logger.debug(
                "Confidence %.2f below growth threshold %.2f; skipping growth",
                confidence,
                self.growth_threshold,
            )
            return ""
        key = self._assign_key(prefix="l")
        entry = DictionaryEntry(
            key=key,
            surface_forms={"zh": surface_form, "en": text},
            confidence=confidence,
        )
        self.entries[key] = entry
        self._dirty = True
        self._growth_history.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "key": key,
            "surface_form": surface_form,
            "source_text": text,
            "confidence": confidence,
        })
        if len(self._growth_history) > limit_value("ai.dictionary_layer.growth_history_max", 5000):
            self._growth_history.pop(0)
        logger.info("Grew new entry: %s -> %s (%s)", key, surface_form, text)
        return key

    def get_synonyms(self, key: str) -> List[str]:
        entry = self.entries.get(key)
        if entry is None:
            return []
        syns = entry.relations.get("synonym", [])
        transitive: List[str] = []
        for s in syns:
            if s in self.entries:
                transitive.extend(
                    self.entries[s].relations.get("synonym", [])
                )
        merged: List[str] = []
        seen: set = set()
        for k in syns + transitive:
            if k not in seen and k != key:
                seen.add(k)
                merged.append(k)
        return merged

    def get_related(
        self, key: str, relation_type: Optional[str] = None
    ) -> List[str]:
        entry = self.entries.get(key)
        if entry is None:
            return []
        if relation_type:
            return entry.relations.get(relation_type, [])
        all_related: List[str] = []
        seen: set = set()
        for rels in entry.relations.values():
            for k in rels:
                if k not in seen:
                    seen.add(k)
                    all_related.append(k)
        return all_related

    def load_preset_responses(self) -> None:
        presets = self._build_presets()
        loaded = 0
        for preset in presets:
            if preset["key"] not in self.entries:
                self.add_entry(**preset)
                loaded += 1
        self._rebuild_index()
        logger.info("Loaded %d preset entries (%d new, %d skipped).",
                     len(presets), loaded, len(presets) - loaded)

    def load_preset_responses_from_dir(self, config_dir: Optional[str] = None) -> int:
        """Load dictionary entries + reflex from config JSON files."""
        import json
        import os
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), "config")
        loaded = 0
        patterns_loaded = 0

        # Load dictionary presets from JSON files
        for fname in os.listdir(config_dir):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(config_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Load reflex patterns if present
            if "reflex_patterns" in data:
                # These are loaded into the engine's reflex layer separately
                patterns_loaded += len(data["reflex_patterns"])
            # Load dictionary entries if present
            for entry_data in data.get("dictionary_entries", []):
                if entry_data["key"] not in self.entries:
                    self.add_entry(**entry_data)
                    loaded += 1
        self._rebuild_index()
        logger.info("Loaded %d entries and %d reflex patterns from %s", loaded, patterns_loaded, config_dir)
        return loaded

    def get_stats(self) -> Dict[str, Any]:
        total_relations = sum(len(e.relations) for e in self.entries.values())
        avg_confidence = (
            sum(e.confidence for e in self.entries.values()) / len(self.entries)
            if self.entries else 0.0
        )
        type_dist: Dict[str, int] = {}
        for e in self.entries.values():
            for lang in e.surface_forms:
                type_dist[lang] = type_dist.get(lang, 0) + 1
        return {
            "entry_count": len(self.entries),
            "relation_count": total_relations,
            "avg_confidence": round(avg_confidence, 4),
            "language_distribution": type_dist,
            "growth_history_count": len(self._growth_history),
        }

    def prune(self, min_confidence: float = threshold_value("ai.dictionary_layer.prune_min_confidence", 0.1), max_age_days: int = limit_value("ai.dictionary_layer.prune_max_age_days", 365)) -> int:
        pruned = 0
        now = datetime.datetime.now()
        keys_to_delete = []
        for key, entry in self.entries.items():
            if entry.confidence < min_confidence:
                keys_to_delete.append(key)
                continue
            if entry.contexts:
                timestamps = [c.get("timestamp", "") for c in entry.contexts if "timestamp" in c]
                if timestamps:
                    last_used = max(timestamps)
                    try:
                        age = (now - datetime.datetime.fromisoformat(last_used)).days
                        if age > max_age_days:
                            keys_to_delete.append(key)
                            continue
                    except ValueError:
                        logger.debug("Prune: invalid timestamp format for key %s", key, exc_info=True)
        for key in keys_to_delete:
            del self.entries[key]
            pruned += 1
        if keys_to_delete:
            self._rebuild_index()
            logger.info("Pruned %d low-confidence/stale entries (min_conf=%.2f, max_age=%dd)",
                        pruned, min_confidence, max_age_days)
        return pruned

    def detect_new_concepts(self, text: str, known_keys: List[str]) -> List[Dict[str, Any]]:
        text = normalize_text(text)
        known_surfaces: set = set()
        for k in known_keys:
            entry = self.entries.get(k)
            if entry:
                for s in entry.surface_forms.values():
                    known_surfaces.add(normalize_text(s).lower().strip())
        for e in self.entries.values():
            for s in e.surface_forms.values():
                known_surfaces.add(normalize_text(s).lower().strip())
        text_lower = text.lower().strip()
        candidates: List[Dict[str, Any]] = []
        tokens = re.findall(r"[\w\u4e00-\u9fff]{2,}", text_lower)
        seen: set = set()
        for token in tokens:
            if token in known_surfaces or token in seen:
                continue
            seen.add(token)
            is_chinese = bool(re.match(r"[\u4e00-\u9fff]", token))
            if is_chinese and len(token) >= 2:
                confidence = confidence_value("ai.dictionary_layer.concept_base_conf", 0.4) + min(len(token) * learning_rate("ai.dictionary_layer.concept_len_factor", 0.05), confidence_value("ai.dictionary_layer.concept_max_bonus", 0.3))
            elif not is_chinese and len(token) >= 4:
                confidence = confidence_value("ai.dictionary_layer.concept_base_conf", 0.4) + min(len(token) * learning_rate("ai.dictionary_layer.concept_len_factor_en", 0.03), confidence_value("ai.dictionary_layer.concept_max_bonus", 0.3))
            else:
                confidence = confidence_value("ai.dictionary_layer.concept_min_conf", 0.2)
            candidates.append({
                "text": token,
                "surface_form": token if is_chinese else f"en:{token}",
                "confidence": round(confidence, 2),
                "source_position": text_lower.find(token),
            })
        return candidates

    def learn_from_conversation(
        self, utterances: List[str], min_confidence: float = threshold_value("ai.dictionary_layer.learn_min_confidence", 0.4)
    ) -> List[str]:
        new_keys: List[str] = []
        all_text = " ".join(utterances)
        known_keys = list(self.entries.keys())
        candidates = self.detect_new_concepts(all_text, known_keys)
        threshold = max(self.growth_threshold, min_confidence)
        batch_new: List[str] = []
        for c in candidates:
            if c["confidence"] >= threshold:
                key = self.grow(c["text"], c["surface_form"], c["confidence"])
                if key:
                    new_keys.append(key)
                    batch_new.append(key)
        for i, k1 in enumerate(batch_new):
            for k2 in batch_new[i + 1:]:
                self.entries[k1].relations.setdefault("mapping", []).append(k2)
                self.entries[k2].relations.setdefault("mapping", []).append(k1)
        if batch_new:
            self._dirty = True
        return new_keys

    def merge_entries(self, source_key: str, target_key: str) -> bool:
        if source_key not in self.entries or target_key not in self.entries:
            logger.warning("Cannot merge: one or both keys not found (%s, %s)", source_key, target_key)
            return False
        if source_key == target_key:
            logger.warning("Cannot merge entry with itself")
            return False
        source = self.entries[source_key]
        target = self.entries[target_key]
        for lang, form in source.surface_forms.items():
            if lang not in target.surface_forms:
                target.surface_forms[lang] = form
        for rel_type, targets in source.relations.items():
            existing = target.relations.setdefault(rel_type, [])
            for t in targets:
                if t not in existing and t != target_key:
                    existing.append(t)
        target.confidence = max(target.confidence, source.confidence)
        for e in self.entries.values():
            for rels in e.relations.values():
                if source_key in rels:
                    rels[rels.index(source_key)] = target_key
        del self.entries[source_key]
        self._dirty = True
        logger.info("Merged %s -> %s", source_key, target_key)
        return True

    def export_to_json(self, filepath: str) -> None:
        data = {
            "version": "1.0",
            "exported_at": datetime.datetime.now().isoformat(),
            "entries": [
                {
                    "key": e.key,
                    "surface_forms": e.surface_forms,
                    "contexts": e.contexts,
                    "relations": e.relations,
                    "confidence": e.confidence,
                }
                for e in self.entries.values()
            ],
            "growth_history": self._growth_history,
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def import_from_json(self, filepath: str) -> int:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        count = 0
        for entry_data in data.get("entries", []):
            if entry_data["key"] not in self.entries:
                self.add_entry(
                    key=entry_data["key"],
                    surface_forms=entry_data["surface_forms"],
                    contexts=entry_data.get("contexts"),
                    relations=entry_data.get("relations"),
                    confidence=entry_data.get("confidence", 1.0),
                )
                count += 1
        self._rebuild_index()
        logger.info("Imported %d entries from %s", count, filepath)
        return count

    def _rebuild_index(self) -> None:
        if not self._dirty and self._rebuilt_index:
            return
        with self._lock:
            self._keyword_index.clear()
            self._bigram_index.clear()
            large_dict = len(self.entries) > 1000
            for key, entry in self.entries.items():
                for lang, surface in entry.surface_forms.items():
                    surface_lower = normalize_text(surface).lower()

                    if surface_lower.isascii():
                        tokens = surface_lower.split()
                    else:
                        tokens = re.findall(r"[\w]+", surface_lower)
                    for token in tokens:
                        self._keyword_index.setdefault(token, []).append(key)

                    # Skip bigram index for large dictionaries (>1000 entries)
                    # to avoid O(n * m) performance cost.
                    # Bigram index is only used as a fallback in encode_soft()
                    # when keyword search finds no candidates.
                    if not large_dict and len(surface_lower) >= 4:
                        for i in range(len(surface_lower) - 1):
                            bigram = surface_lower[i : i + 2]
                            if re.match(r"[\w]", bigram[0]) and re.match(r"[\w]", bigram[1]):
                                self._bigram_index.setdefault(bigram, []).append(key)
            self._rebuilt_index = True
            self._dirty = False
            self._index_version += 1
            self._encode_cache.clear()

    def _build_greeting_presets(self) -> List[Dict[str, Any]]:
        return [
            # ========== Greetings ==========
            {
                "key": "g1",
                "surface_forms": {"zh": "你好", "en": "hello"},
                "contexts": [{"context_id": "greeting", "formality": "neutral"}],
                "relations": {"synonym": ["g2", "g3"], "mapping": ["e1", "p1"]},
                "confidence": 1.0,
            },
            {
                "key": "g2",
                "surface_forms": {"zh": "早上好", "en": "good morning"},
                "contexts": [{"context_id": "greeting", "formality": "formal", "time": "morning"}],
                "relations": {"synonym": ["g1"], "mapping": ["g5"]},
                "confidence": 1.0,
            },
            {
                "key": "g3",
                "surface_forms": {"zh": "晚上好", "en": "good evening"},
                "contexts": [{"context_id": "greeting", "formality": "formal", "time": "evening"}],
                "relations": {"synonym": ["g1"], "mapping": ["g5"]},
                "confidence": 1.0,
            },
            {
                "key": "g4",
                "surface_forms": {"zh": "欢迎", "en": "welcome"},
                "contexts": [{"context_id": "greeting", "formality": "formal"}],
                "relations": {"synonym": ["g1"], "mapping": ["p1"]},
                "confidence": 1.0,
            },
            {
                "key": "g5",
                "surface_forms": {"zh": "嗨", "en": "hi"},
                "contexts": [{"context_id": "greeting", "formality": "casual"}],
                "relations": {"synonym": ["g1", "g6"]},
                "confidence": 1.0,
            },
            {
                "key": "g6",
                "surface_forms": {"zh": "哈喽", "en": "hey"},
                "contexts": [{"context_id": "greeting", "formality": "casual"}],
                "relations": {"synonym": ["g1", "g5"]},
                "confidence": 1.0,
            },
        ]

    def _build_farewell_presets(self) -> List[Dict[str, Any]]:
        return [
            # ========== Farewells ==========
            {
                "key": "f1",
                "surface_forms": {"zh": "再见", "en": "goodbye"},
                "contexts": [{"context_id": "farewell", "formality": "neutral"}],
                "relations": {"synonym": ["f2"], "mapping": ["p1"]},
                "confidence": 1.0,
            },
            {
                "key": "f2",
                "surface_forms": {"zh": "明天见", "en": "see you tomorrow"},
                "contexts": [{"context_id": "farewell", "formality": "casual"}],
                "relations": {"synonym": ["f1"], "mapping": ["g2"]},
                "confidence": 1.0,
            },
        ]

    def _build_politeness_presets(self) -> List[Dict[str, Any]]:
        return [
            # ========== Politeness ==========
            {
                "key": "p1",
                "surface_forms": {"zh": "谢谢", "en": "thank you"},
                "contexts": [{"context_id": "politeness", "formality": "neutral"}],
                "relations": {"synonym": ["p4"], "mapping": ["e1", "r1"]},
                "confidence": 1.0,
            },
            {
                "key": "p2",
                "surface_forms": {"zh": "对不起", "en": "sorry"},
                "contexts": [{"context_id": "politeness", "formality": "neutral", "sentiment": "apology"}],
                "relations": {"synonym": ["r2"], "mapping": ["r1"]},
                "confidence": 1.0,
            },
            {
                "key": "p3",
                "surface_forms": {"zh": "没关系", "en": "no problem"},
                "contexts": [{"context_id": "politeness", "formality": "neutral", "sentiment": "forgiveness"}],
                "relations": {"synonym": ["r3"], "mapping": ["p2"]},
                "confidence": 1.0,
            },
            {
                "key": "p4",
                "surface_forms": {"zh": "请", "en": "please"},
                "contexts": [{"context_id": "politeness", "formality": "formal"}],
                "relations": {"synonym": [], "mapping": ["g1", "p1"]},
                "confidence": 1.0,
            },
        ]

    def _build_common_presets(self) -> List[Dict[str, Any]]:
        return [
            # ========== Common Patterns ==========
            {
                "key": "c1",
                "surface_forms": {"zh": "在忙吗", "en": "are you busy"},
                "contexts": [{"context_id": "small_talk", "topic": "status"}],
                "relations": {"mapping": ["e5", "r1"]},
                "confidence": 1.0,
            },
            {
                "key": "c2",
                "surface_forms": {"zh": "心情", "en": "mood"},
                "contexts": [{"context_id": "small_talk", "topic": "emotion"}],
                "relations": {"mapping": ["e1", "e2", "e3", "e5"]},
                "confidence": 1.0,
            },
            {
                "key": "c3",
                "surface_forms": {"zh": "今天", "en": "today"},
                "contexts": [{"context_id": "small_talk", "topic": "time"}],
                "relations": {"mapping": ["g2", "g3", "c1"]},
                "confidence": 1.0,
            },
            {
                "key": "c4",
                "surface_forms": {"zh": "名字", "en": "name"},
                "contexts": [{"context_id": "small_talk", "topic": "identity"}],
                "relations": {"mapping": ["g1"]},
                "confidence": 1.0,
            },
            {
                "key": "c5",
                "surface_forms": {"zh": "做什么", "en": "what are you doing"},
                "contexts": [{"context_id": "small_talk", "topic": "activity"}],
                "relations": {"mapping": ["c1", "e5"]},
                "confidence": 1.0,
            },
        ]

    def _build_emotion_presets(self) -> List[Dict[str, Any]]:
        return [
            # ========== Emotional States ==========
            {
                "key": "e1",
                "surface_forms": {"zh": "开心", "en": "happy"},
                "contexts": [{"context_id": "emotion", "valence": "positive", "arousal": "high"}],
                "relations": {"synonym": ["e5"], "mapping": ["c2"]},
                "confidence": 1.0,
            },
            {
                "key": "e2",
                "surface_forms": {"zh": "难过", "en": "sad"},
                "contexts": [{"context_id": "emotion", "valence": "negative", "arousal": "low"}],
                "relations": {"mapping": ["p2", "c2"]},
                "confidence": 1.0,
            },
            {
                "key": "e3",
                "surface_forms": {"zh": "烦恼", "en": "annoyed"},
                "contexts": [{"context_id": "emotion", "valence": "negative", "arousal": "high"}],
                "relations": {"mapping": ["e2", "c2"]},
                "confidence": 1.0,
            },
            {
                "key": "e4",
                "surface_forms": {"zh": "无聊", "en": "bored"},
                "contexts": [{"context_id": "emotion", "valence": "negative", "arousal": "low"}],
                "relations": {"mapping": ["e2", "c1"]},
                "confidence": 1.0,
            },
            {
                "key": "e5",
                "surface_forms": {"zh": "兴奋", "en": "excited"},
                "contexts": [{"context_id": "emotion", "valence": "positive", "arousal": "high"}],
                "relations": {"synonym": ["e1"], "mapping": ["c2"]},
                "confidence": 1.0,
            },
        ]

    def _build_response_presets(self) -> List[Dict[str, Any]]:
        return [
            # ========== Responses ==========
            {
                "key": "r1",
                "surface_forms": {"zh": "嗯", "en": "uh-huh"},
                "contexts": [{"context_id": "response", "type": "acknowledgment"}],
                "relations": {"synonym": ["r2", "r3"], "mapping": ["p1"]},
                "confidence": 1.0,
            },
            {
                "key": "r2",
                "surface_forms": {"zh": "好的", "en": "okay"},
                "contexts": [{"context_id": "response", "type": "agreement"}],
                "relations": {"synonym": ["r1", "r3", "r4"]},
                "confidence": 1.0,
            },
            {
                "key": "r3",
                "surface_forms": {"zh": "明白", "en": "understood"},
                "contexts": [{"context_id": "response", "type": "acknowledgment"}],
                "relations": {"synonym": ["r1", "r2", "r4"]},
                "confidence": 1.0,
            },
            {
                "key": "r4",
                "surface_forms": {"zh": "可以", "en": "sure"},
                "contexts": [{"context_id": "response", "type": "agreement"}],
                "relations": {"synonym": ["r2"]},
                "confidence": 1.0,
            },
        ]

    def _build_math_presets(self) -> List[Dict[str, Any]]:
        return [
            # ========== Math: Numbers ==========
            {
                "key": "m1",
                "surface_forms": {"zh": "零", "en": "0"},
                "contexts": [{"context_id": "arithmetic", "type": "number"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "m2",
                "surface_forms": {"zh": "一", "en": "1"},
                "contexts": [{"context_id": "arithmetic", "type": "number"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "m3",
                "surface_forms": {"zh": "二", "en": "2"},
                "contexts": [{"context_id": "arithmetic", "type": "number"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "m4",
                "surface_forms": {"zh": "三", "en": "3"},
                "contexts": [{"context_id": "arithmetic", "type": "number"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "m5",
                "surface_forms": {"zh": "四", "en": "4"},
                "contexts": [{"context_id": "arithmetic", "type": "number"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "m6",
                "surface_forms": {"zh": "五", "en": "5"},
                "contexts": [{"context_id": "arithmetic", "type": "number"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "m7",
                "surface_forms": {"zh": "六", "en": "6"},
                "contexts": [{"context_id": "arithmetic", "type": "number"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "m8",
                "surface_forms": {"zh": "七", "en": "7"},
                "contexts": [{"context_id": "arithmetic", "type": "number"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "m9",
                "surface_forms": {"zh": "八", "en": "8"},
                "contexts": [{"context_id": "arithmetic", "type": "number"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "m10",
                "surface_forms": {"zh": "九", "en": "9"},
                "contexts": [{"context_id": "arithmetic", "type": "number"}],
                "relations": {},
                "confidence": 1.0,
            },
            # ========== Math: Operators ==========
            {
                "key": "m11",
                "surface_forms": {"zh": "加", "en": "plus"},
                "contexts": [{"context_id": "arithmetic", "type": "operator"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "m12",
                "surface_forms": {"zh": "减", "en": "minus"},
                "contexts": [{"context_id": "arithmetic", "type": "operator"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "m13",
                "surface_forms": {"zh": "乘", "en": "times"},
                "contexts": [{"context_id": "arithmetic", "type": "operator"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "m14",
                "surface_forms": {"zh": "除", "en": "divided"},
                "contexts": [{"context_id": "arithmetic", "type": "operator"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "m15",
                "surface_forms": {"zh": "等於", "en": "equals"},
                "contexts": [{"context_id": "arithmetic", "type": "operator"}],
                "relations": {},
                "confidence": 1.0,
            },
        ]

    def _build_logic_presets(self) -> List[Dict[str, Any]]:
        return [
            # ========== Boolean Logic ==========
            {
                "key": "b1",
                "surface_forms": {"zh": "真", "en": "true"},
                "contexts": [{"context_id": "logic", "type": "boolean"}],
                "relations": {"antonym": ["b2"]},
                "confidence": 1.0,
            },
            {
                "key": "b2",
                "surface_forms": {"zh": "假", "en": "false"},
                "contexts": [{"context_id": "logic", "type": "boolean"}],
                "relations": {"antonym": ["b1"]},
                "confidence": 1.0,
            },
            {
                "key": "b3",
                "surface_forms": {"zh": "且", "en": "and"},
                "contexts": [{"context_id": "logic", "type": "operator"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "b4",
                "surface_forms": {"zh": "或", "en": "or"},
                "contexts": [{"context_id": "logic", "type": "operator"}],
                "relations": {},
                "confidence": 1.0,
            },
            {
                "key": "b5",
                "surface_forms": {"zh": "非", "en": "not"},
                "contexts": [{"context_id": "logic", "type": "operator"}],
                "relations": {},
                "confidence": 1.0,
            },
        ]

    def _build_presets(self) -> List[Dict[str, Any]]:
        result = []
        result.extend(self._build_greeting_presets())
        result.extend(self._build_farewell_presets())
        result.extend(self._build_politeness_presets())
        result.extend(self._build_common_presets())
        result.extend(self._build_emotion_presets())
        result.extend(self._build_response_presets())
        result.extend(self._build_math_presets())
        result.extend(self._build_logic_presets())
        return result
