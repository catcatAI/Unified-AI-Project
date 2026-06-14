"""
ANGELA-MATRIX: [L4] [αβγδ] [A] [L3]
HAM (Hierarchical Associative Memory) Manager — minimal JSON-backed implementation.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.text_utils import char_bigrams as _char_bigrams_util
from utils.text_utils import bigram_jaccard as _bigram_jaccard_util

logger = logging.getLogger(__name__)


class HAMMemoryManager:
    """Minimal JSON-backed hierarchical associative memory manager."""

    def __init__(
        self,
        memory_file: str = "angela_memory.json",
        auto_save: bool = True,
        core_storage_filename: Optional[str] = None,
    ):
        self.memory_file = Path(memory_file)
        self.auto_save = auto_save
        self._data: Dict[str, Any] = {"templates": [], "conversations": [], "metadata": {}}
        self._load()

    def _load(self) -> None:
        if self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError, IOError):
                self._data = {"templates": [], "conversations": [], "metadata": {}}

    def _save(self) -> None:
        if not self.auto_save:
            return
        try:
            self.memory_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except (IOError, OSError, TypeError) as e:
            logger.warning(f"HAMMemoryManager save failed: {e}")

    async def store_template(self, template: Any) -> None:
        self._data["templates"].append({
            "content": getattr(template, "content", str(template)),
            "id": getattr(template, "id", None),
            "keywords": getattr(template, "keywords", []),
        })
        self._save()

    async def retrieve_response_templates(
        self,
        query: str,
        top_k: int = 5,
        angela_state=None,
        user_impression=None,
        limit: int = 5,
        min_score: float = 0.3,
    ) -> List[Any]:
        candidates = self._data.get("templates", [])
        if not candidates:
            return []

        scored = []
        for tpl in candidates:
            keywords = tpl.get("keywords", [])
            if not keywords:
                continue
            best_score = 0.0
            for kw in keywords:
                kw_lower = kw.lower()
                query_lower = query.lower()
                # Exact substring match
                if kw_lower in query_lower:
                    best_score = max(best_score, 0.9)
                else:
                    # Bigram Jaccard
                    best_score = max(best_score, _bigram_jaccard_util(kw_lower, query_lower))
            if best_score >= min_score:
                scored.append((tpl, best_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit or top_k]

    @staticmethod
    def _char_bigrams(text: str) -> set:
        """Generate character-level bigrams for Chinese text similarity."""
        return _char_bigrams_util(text)

    async def store_experience(
        self,
        raw_data: Any,
        data_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        keywords: Optional[List[str]] = None,
    ) -> Optional[str]:
        """Store a raw experience entry into the memory store.

        Args:
            raw_data: Content to store — str, dict, or any object.
            data_type: Category label for the experience.
            metadata: Optional metadata dict.
            keywords: Optional explicit keywords. If not provided,
                      keywords are auto-extracted from raw_data.
        """
        resolved_keywords = keywords if keywords is not None else self._extract_keywords(raw_data)
        entry = {
            "content": str(raw_data),
            "data_type": data_type,
            "metadata": metadata or {},
            "keywords": resolved_keywords,
        }
        self._data["templates"].append(entry)
        self._save()
        return f"exp_{len(self._data['templates'])}"

    def _extract_keywords(self, raw_data: Any, max_keywords: int = 8) -> List[str]:
        """Auto-extract keywords from raw_data.

        - dict: uses string values and keys as keywords.
        - str: takes first N meaningful characters, filtering stopwords.
        - other: converts to str then applies str logic.
        """
        _STOPWORDS = {
            "你", "我", "他", "她", "的", "了", "吗", "呢", "吧",
            "啊", "是", "在", "有", "和", "与", "the", "a", "an",
            "is", "are", "was", "were", "it", "to", "of", "in",
            "for", "on", "with", "at", "by", "from", "as", "this",
            "that", "not", "be", "have", "has", "had", "do", "does",
        }

        if isinstance(raw_data, dict):
            keywords: List[str] = []
            for key, value in raw_data.items():
                keywords.append(str(key))
                if isinstance(value, str) and value:
                    keywords.append(value[:30])
                if len(keywords) >= max_keywords * 2:
                    break
            return keywords[:max_keywords]

        text = str(raw_data) if raw_data is not None else ""
        if not text:
            return []

        # For Chinese text: split on whitespace and punctuation boundaries,
        # keep tokens >= 2 chars that aren't stopwords.
        import re
        # Match Chinese char sequences (1+ chars) and English word sequences
        tokens = re.findall(r"[\u4e00-\u9fff]{2,}|[a-zA-Z]{2,}", text)
        filtered = [t for t in tokens if t.lower() not in _STOPWORDS]
        if filtered:
            return filtered[:max_keywords]

        # Fallback: first N non-stopword chars from text
        return [text[i:i+2] for i in range(0, min(len(text), max_keywords * 2), 2)
                if text[i:i+2].lower() not in _STOPWORDS][:max_keywords]

    def store_conversation(self, conversation: Dict[str, Any]) -> None:
        self._data["conversations"].append(conversation)
        self._save()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "template_count": len(self._data["templates"]),
            "conversation_count": len(self._data["conversations"]),
        }
