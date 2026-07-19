# =============================================================================
# ANGELA-MATRIX: [L3] [αδ] [B] [L2]
# =============================================================================

"""
Dictionary-backed classifier that replaces hardcoded regex patterns.
Maps ED3N dictionary context_id to QueryType.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Tuple

from core.utils import any_keyword

logger = logging.getLogger(__name__)

# Map ED3N context_id to QueryType
CONTEXT_TO_QUERY_TYPE: Dict[str, str] = {
    "file": "file",
    "search": "search",
    "code": "code",
    "execute": "execute",
    "task": "task",
    "vision": "vision",
    "audio": "audio",
    "math": "math",
    "system": "system",
    "greeting": "greeting",
    "knowledge": "knowledge",
    "creative": "creative",
    "opinion": "opinion",
    "negation": "negation",
}

# Map context_id + type to action_type
CONTEXT_TYPE_TO_ACTION: Dict[Tuple[str, str], str] = {
    ("file", "action"): "modify",
    ("file", "object"): "read",
    ("search", "action"): "search",
    ("code", "action"): "modify",
    ("code", "object"): "read",
    ("execute", "action"): "execute",
    ("task", "action"): "modify",
    ("task", "object"): "read",
    ("vision", "action"): "read",
    ("vision", "object"): "read",
    ("audio", "action"): "read",
    ("audio", "object"): "read",
    ("math", "action"): "calculate",
    ("math", "operator"): "calculate",
    ("math", "query"): "calculate",
    ("system", "action"): "send",
    ("greeting", "greeting"): "none",
    ("greeting", "farewell"): "none",
    ("knowledge", "query"): "read",
    ("knowledge", "capability"): "read",
    ("creative", "action"): "modify",
    ("creative", "object"): "read",
    ("opinion", "query"): "read",
    ("negation", "modifier"): "none",
}

# Negation keywords that should reject
NEGATION_KEYWORDS = {"不要", "取消", "停止"}


class DictionaryClassifier:
    """Uses ED3N dictionary for intent classification instead of hardcoded regex."""

    def __init__(self):
        self._dictionary = None
        self._training_data = {}
        self._loaded = False
        self._keyword_index: Dict[str, List[str]] = {}  # keyword -> list of entry keys
        self._cache: Dict[str, Tuple[str, str, float]] = {}  # text -> (type, action, conf)

    def _ensure_loaded(self):
        if self._loaded:
            return
        self._loaded = True
        try:
            from ai.ed3n.dictionary_layer import DictionaryLayer

            self._dictionary = DictionaryLayer()
            self._dictionary.load_preset_responses_from_dir()
            self._load_training_data()
            self._build_keyword_index()
            logger.info(
                "DictionaryClassifier loaded: %d dictionary entries, %d training entries, %d keywords",
                len(self._dictionary.entries),
                len(self._training_data),
                len(self._keyword_index),
            )
        except Exception as e:
            logger.warning("DictionaryClassifier init failed: %s", e)
            self._dictionary = None

    def _build_keyword_index(self):
        """Build inverted index from keywords to entry keys for fast lookup."""
        if not self._dictionary:
            return
        for key, entry in self._dictionary.entries.items():
            for sf in entry.surface_forms.values():
                sf_lower = sf.lower().strip()
                if sf_lower:
                    if sf_lower not in self._keyword_index:
                        self._keyword_index[sf_lower] = []
                    self._keyword_index[sf_lower].append(key)

    def _load_training_data(self):
        """Load classifier training data and merge into dictionary."""
        training_path = os.path.join(
            os.path.dirname(__file__), "..", "ed3n", "config", "classifier_training.json"
        )
        if not os.path.exists(training_path):
            logger.warning("Training data not found: %s", training_path)
            return

        with open(training_path, encoding="utf-8") as f:
            data = json.load(f)

        entries = data.get("dictionary_entries", [])
        for entry_data in entries:
            key = entry_data["key"]
            from ai.ed3n.dictionary_layer import DictionaryEntry

            entry = DictionaryEntry(
                key=key,
                surface_forms=entry_data["surface_forms"],
                contexts=entry_data.get("contexts", []),
                relations=entry_data.get("relations", {}),
                confidence=entry_data.get("confidence", 1.0),
            )
            self._dictionary.entries[key] = entry
            self._training_data[key] = entry_data

    def classify(self, text: str) -> Tuple[str, str, float]:
        self._ensure_loaded()
        if not self._dictionary:
            return ("unknown", "none", 0.0)

        cached = self._check_cache(text)
        if cached:
            return cached

        neg_result = self._check_negation(text)
        if neg_result:
            return neg_result

        text_lower = text.lower().strip()
        best_key, best_score = self._match_keywords(text_lower)

        if best_score < 0.15 or not best_key:
            result = ("unknown", "none", 0.0)
            self._cache[text] = result
            return result

        query_type, action_type = self._resolve_entry(best_key)
        result = (query_type, action_type, round(best_score, 3))
        self._cache[text] = result
        return result

    def _check_cache(self, text: str) -> Optional[Tuple[str, str, float]]:
        if text in self._cache:
            return self._cache[text]
        return None

    def _check_negation(self, text: str) -> Optional[Tuple[str, str, float]]:
        if any_keyword(text, NEGATION_KEYWORDS):
            result = ("unknown", "none", 0.9)
            self._cache[text] = result
            return result
        return None

    def _match_keywords(self, text_lower: str) -> Tuple[Optional[str], float]:
        best_key = None
        best_score = 0.0

        if text_lower in self._keyword_index:
            keys = self._keyword_index[text_lower]
            if keys:
                best_key = keys[0]
                best_score = 1.0

        if best_score < 0.5:
            for keyword, keys in self._keyword_index.items():
                if any_keyword(text_lower, (keyword,)):
                    pos = text_lower.find(keyword)
                    len_ratio = len(keyword) / max(len(text_lower), 1)
                    position_boost = 1.3 if pos == 0 else 1.0
                    min_score = 0.6 if len(keyword) >= 2 else 0.4
                    score = max(min_score, min(1.0, len_ratio * position_boost * 2.0))
                    if score > best_score:
                        best_score = score
                        best_key = keys[0] if keys else None

        return best_key, best_score

    def _resolve_entry(self, best_key: str) -> Tuple[str, str]:
        entry = self._dictionary.entries.get(best_key)
        if not entry or not entry.contexts:
            return ("unknown", "none")

        primary_ctx = entry.contexts[0]
        context_id = primary_ctx.get("context_id", "")
        ctx_type = primary_ctx.get("type", "")

        query_type = CONTEXT_TO_QUERY_TYPE.get(context_id, "unknown")
        action_type = CONTEXT_TYPE_TO_ACTION.get((context_id, ctx_type), "none")

        if context_id == "file" and ctx_type == "action":
            action_type = self._map_file_action(entry, action_type)
        elif context_id == "execute" and ctx_type == "action":
            action_type = self._map_execute_action(entry, action_type)

        return query_type, action_type

    @staticmethod
    def _map_file_action(entry, action_type: str) -> str:
        action_map = {
            "删除": "delete",
            "刪除": "delete",
            "创建": "create",
            "建立": "create",
            "新增": "create",
            "读取": "read",
            "讀取": "read",
            "写入": "write",
            "寫入": "write",
            "移动": "move",
            "移動": "move",
            "复制": "copy",
            "複製": "copy",
            "重命名": "rename",
            "整理": "organize",
            "清理": "clean",
            "编辑": "modify",
            "編輯": "modify",
            "修改": "modify",
            "列出": "list",
        }
        zh = entry.surface_forms.get("zh", "")
        return action_map.get(zh, action_type)

    @staticmethod
    def _map_execute_action(entry, action_type: str) -> str:
        action_map = {
            "执行": "execute",
            "執行": "execute",
            "运行": "execute",
            "運行": "execute",
            "开启": "open",
            "開啟": "open",
            "关闭": "close",
            "關閉": "close",
            "启动": "start",
            "啟動": "start",
            "停止": "stop",
            "暂停": "pause",
            "暫停": "pause",
            "下载": "download",
            "下載": "download",
            "上传": "upload",
            "上傳": "upload",
        }
        zh = entry.surface_forms.get("zh", "")
        return action_map.get(zh, action_type)

    def learn(
        self,
        text: str,
        query_type: str,
        action_type: str = "none",
        confidence: float = 0.6,
        persist: bool = True,
    ) -> str:
        """Online incremental learning: add a new surface form→query_type mapping.

        Creates a new dictionary entry and rebuilds the keyword index so subsequent
        classify() calls will match the new keyword. Persists to JSON if persist=True.

        Args:
            text: The surface form (keyword) to learn.
            query_type: One of CONTEXT_TO_QUERY_TYPE values (e.g. "file", "search").
            action_type: Action type suffix (e.g. "action", "object", "query").
            confidence: Initial confidence 0.0-1.0.
            persist: Whether to persist to classifier_training.json immediately.

        Returns:
            The key of the newly created entry (e.g. "cls_learn_N").
        """
        self._ensure_loaded()
        text_stripped = text.strip().lower()
        if not text_stripped:
            return ""
        if not self._dictionary:
            return ""

        # Check if already in index
        if text_stripped in self._keyword_index:
            existing_key = self._keyword_index[text_stripped][0]
            existing = self._training_data.get(existing_key, {})
            existing_ctx = (existing.get("contexts") or [{}])[0]
            if existing_ctx.get("context_id") == query_type:
                return existing_key  # Already learned
            # Same keyword, different type → overwrite existing entry
            self._training_data.pop(existing_key, None)
            if self._dictionary and existing_key in self._dictionary.entries:
                del self._dictionary.entries[existing_key]
            key = existing_key

        if "key" not in locals():
            # Auto-increment key
            key_num = len(self._training_data) + 1
            key = f"cls_learn_{key_num}"

        from ai.ed3n.dictionary_layer import DictionaryEntry

        entry = DictionaryEntry(
            key=key,
            surface_forms={"zh": text_stripped},
            contexts=[{"context_id": query_type, "type": action_type}],
            relations={},
            confidence=confidence,
        )
        self._dictionary.entries[key] = entry

        entry_data = {
            "key": key,
            "surface_forms": {"zh": text_stripped},
            "contexts": [{"context_id": query_type, "type": action_type}],
            "relations": {},
            "confidence": confidence,
        }
        self._training_data[key] = entry_data

        # Rebuild index incrementally
        if text_stripped not in self._keyword_index:
            self._keyword_index[text_stripped] = []
        self._keyword_index[text_stripped].append(key)

        # Clear affected cache entries
        keys_to_clear = [k for k in self._cache if text_stripped in k]
        for k in keys_to_clear:
            del self._cache[k]

        if persist:
            self._persist_training_data()

        logger.info(f"Learned: '{text_stripped}' → {query_type}/{action_type} (key={key})")
        return key

    def _persist_training_data(self):
        """Persist current training data to classifier_training.json."""
        training_path = os.path.join(
            os.path.dirname(__file__), "..", "ed3n", "config", "classifier_training.json"
        )
        try:
            data = {
                "version": "1.1",
                "description": "Auto-generated from online learning. Merged with pattern-extracted data.",
                "dictionary_entries": list(self._training_data.values()),
            }
            with open(training_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"Persisted {len(self._training_data)} entries to {training_path}")
        except Exception as e:
            logger.warning(f"Failed to persist training data: {e}")

    def forget(self, key: str) -> bool:
        """Remove a learned entry by key. Used for calibration (e.g. low accuracy)."""
        if key not in self._training_data:
            return False
        entry_data = self._training_data.pop(key)
        if self._dictionary and key in self._dictionary.entries:
            del self._dictionary.entries[key]

        sf = entry_data.get("surface_forms", {}).get("zh", "")
        if sf and sf in self._keyword_index:
            self._keyword_index[sf] = [k for k in self._keyword_index[sf] if k != key]
            if not self._keyword_index[sf]:
                del self._keyword_index[sf]

        keys_to_clear = [k for k in self._cache if sf in k]
        for k in keys_to_clear:
            del self._cache[k]

        self._persist_training_data()
        logger.info(f"Forgot key={key} ('{sf}')")
        return True

    def get_all_matches(self, text: str, threshold: float = 0.15) -> List[Dict]:
        """Get all matching entries above threshold."""
        self._ensure_loaded()
        if not self._dictionary:
            return []

        scores = self._dictionary.encode_soft(text)
        results = []
        for key, score in scores.items():
            if score < threshold:
                continue
            entry = self._dictionary.entries.get(key)
            if not entry:
                continue
            results.append(
                {
                    "key": key,
                    "score": score,
                    "surface_forms": entry.surface_forms,
                    "contexts": entry.contexts,
                }
            )
        results.sort(key=lambda x: x["score"], reverse=True)
        return results


# Singleton instance
_classifier = None


def get_dictionary_classifier() -> DictionaryClassifier:
    global _classifier
    if _classifier is None:
        _classifier = DictionaryClassifier()
    return _classifier
