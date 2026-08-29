"""
ANGELA-MATRIX: [L4] [αβγδ] [A] [L3]
HAM (Hierarchical Associative Memory) Manager — minimal JSON-backed implementation.
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from utils.text_utils import bigram_jaccard as _bigram_jaccard_util
from utils.text_utils import char_bigrams as _char_bigrams_util

logger = logging.getLogger(__name__)


class HAMMemoryManager:
    """Minimal JSON-backed hierarchical associative memory manager."""

    def __init__(
        self,
        memory_file: Optional[str] = None,
        auto_save: bool = True,
        core_storage_filename: Optional[str] = None,
    ):
        if memory_file is None:
            # Default to data/memory/ham_memory.json relative to project root
            project_root = self._find_project_root()
            memory_file = os.path.join(project_root, "data", "memory", "ham_memory.json")
        self.memory_file = Path(memory_file)
        self.auto_save = auto_save
        self._data: Dict[str, Any] = {"templates": [], "conversations": [], "metadata": {}}
        self._load()

    @staticmethod
    def _find_project_root() -> str:
        """Find project root by walking up until a unique marker file is found.

        Note: Duplicated from ED3NEngine._find_project_root to avoid circular
        imports (memory module should not depend on ed3n module).
        """
        current = os.path.dirname(os.path.abspath(__file__))
        for _ in range(10):
            if os.path.exists(os.path.join(current, ".gitignore")):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        return os.getcwd()

    def _load(self) -> None:
        if self.memory_file and self.memory_file.exists():
            try:
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError, IOError):
                self._data = {"templates": [], "conversations": [], "metadata": {}}

    def _write_to_disk(self) -> None:
        """Synchronous disk write — called from _save or save_async."""
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def _save(self) -> None:
        if not self.auto_save or not self.memory_file:
            return
        try:
            self._write_to_disk()
        except (IOError, OSError, TypeError) as e:
            logger.warning(f"HAMMemoryManager save failed: {e}")

    async def save_async(self) -> None:
        """Non-blocking save — offloads disk I/O to a worker thread.

        Callers in async contexts (FastAPI endpoints, integration loops)
        should prefer this over _save() to avoid blocking the event loop.
        """
        if not self.auto_save or not self.memory_file:
            return
        try:
            await asyncio.to_thread(self._write_to_disk)
        except (IOError, OSError, TypeError) as e:
            logger.warning(f"HAMMemoryManager async save failed: {e}")

    async def store_template(self, template: Any) -> None:
        self._data["templates"].append(
            {
                "content": getattr(template, "content", str(template)),
                "id": getattr(template, "id", None),
                "keywords": getattr(template, "keywords", []),
            }
        )
        await asyncio.to_thread(self._save)

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

        # Generic stopwords must not trigger a template match on their own —
        # otherwise every query containing "what"/"is"/"the" matches the first
        # template that lists those words (e.g. "opposite of hot"), which then
        # gets served verbatim as the answer to unrelated queries.
        _STOPWORDS = frozenset(
            {
                "what",
                "is",
                "the",
                "a",
                "an",
                "of",
                "to",
                "do",
                "does",
                "did",
                "you",
                "your",
                "i",
                "my",
                "me",
                "are",
                "how",
                "why",
                "who",
                "when",
                "where",
                "which",
                "that",
                "this",
                "it",
                "in",
                "on",
                "at",
                "for",
            }
        )

        scored = []
        for tpl in candidates:
            keywords = tpl.get("keywords", [])
            if not keywords:
                continue
            best_score = 0.0
            for kw in keywords:
                kw_lower = kw.lower().strip()
                if not kw_lower or kw_lower in _STOPWORDS:
                    continue
                query_lower = query.lower()
                # Substring match — but reject single-char or symbol keywords
                # that would match any query containing that character
                # (e.g. "*" in "SELECT * FROM users").  For short keywords
                # (≤2 chars) we require word-boundary adjacency to avoid
                # false positives like "5" matching "123456".
                if kw_lower in query_lower:
                    if len(kw_lower) <= 1:
                        # Single-char keywords (operators, digits) are too
                        # noisy — never treat them as a match.
                        pass
                    elif len(kw_lower) <= 2:
                        # Require word-boundary context for short keywords
                        import re as _kw_re
                        pattern = r'(?<![\w])' + _kw_re.escape(kw_lower) + r'(?![\w])'
                        if _kw_re.search(pattern, query_lower):
                            best_score = max(best_score, 0.9)
                    else:
                        best_score = max(best_score, 0.9)
                else:
                    # Bigram Jaccard
                    best_score = max(best_score, _bigram_jaccard_util(kw_lower, query_lower))
            if best_score >= min_score:
                # Relevance gate: count how many non-stopword keywords
                # matched.  A single keyword match on a long query is often
                # a false positive (e.g. "capital" in "capital of Italy"
                # matching the "capital of France" template).
                query_tokens = query_lower.split()
                matched_kws = set()
                total_non_stop = 0
                for kw in keywords:
                    k = kw.lower().strip()
                    if not k or k in _STOPWORDS:
                        continue
                    total_non_stop += 1
                    if k in query_lower:
                        matched_kws.add(k)
                # Short query: reject if only 1 keyword matched
                if len(query_tokens) <= 3:
                    if len(matched_kws) <= 1:
                        continue
                # Long query: penalize single-keyword match proportionally
                # so unrelated templates don't win over honest fallback.
                # 1/N match → score × (1/N), e.g. 0.9 × 1/3 = 0.3 < 0.5
                elif len(matched_kws) <= 1 and total_non_stop > 1:
                    best_score *= (1.0 / max(total_non_stop, 2))
                    if best_score < min_score:
                        continue
                scored.append((tpl, best_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[: limit or top_k]

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
            "content": raw_data if isinstance(raw_data, dict) else str(raw_data),
            "data_type": data_type,
            "metadata": metadata or {},
            "keywords": resolved_keywords,
        }
        # Route experiences into the correct bucket. Only proper answer
        # templates belong in `templates` (used by TemplateMatcher to compose
        # responses). Conversation logs and other data types must NOT pollute
        # the template bucket, or they get served verbatim as answers.
        if data_type in ("template", "response_template"):
            bucket = "templates"
        elif data_type in ("conversation",):
            bucket = "conversations"
        else:
            bucket = "templates" if data_type in self._data else "conversations"
            bucket = self._data.get(bucket) is not None and bucket or "conversations"
        self._data.setdefault(bucket, []).append(entry)
        await asyncio.to_thread(self._save)
        return f"exp_{len(self._data.get(bucket, []))}"

    def _extract_keywords(self, raw_data: Any, max_keywords: int = 8) -> List[str]:
        """Auto-extract keywords from raw_data.

        - dict: uses string values and keys as keywords.
        - str: takes first N meaningful characters, filtering stopwords.
        - other: converts to str then applies str logic.
        """
        _STOPWORDS = {
            "你",
            "我",
            "他",
            "她",
            "的",
            "了",
            "吗",
            "呢",
            "吧",
            "啊",
            "是",
            "在",
            "有",
            "和",
            "与",
            "the",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "it",
            "to",
            "of",
            "in",
            "for",
            "on",
            "with",
            "at",
            "by",
            "from",
            "as",
            "this",
            "that",
            "not",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
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

        # Fallback: first N meaningful 2-char fragments from text.
        # Skip single-char or pure-symbol fragments ("*", " ", etc.).
        import re as _re_fallback
        return [
            frag.strip()
            for frag in (text[i : i + 2] for i in range(0, min(len(text), max_keywords * 2), 2))
            if len(frag.strip()) >= 2
            and frag.strip().lower() not in _STOPWORDS
            and _re_fallback.search(r'[\w]', frag)  # must contain at least one word char
        ][:max_keywords]

    def store_conversation(self, conversation: Dict[str, Any]) -> None:
        self._data["conversations"].append(conversation)
        self._save()

    async def store_conversation_async(self, conversation: Dict[str, Any]) -> None:
        """Non-blocking store — offloads disk write to a worker thread.

        Callers in async contexts (FastAPI endpoints, integration loops)
        should prefer this over store_conversation() to avoid blocking
        the event loop with synchronous JSON file I/O.
        """
        self._data["conversations"].append(conversation)
        await self.save_async()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "template_count": len(self._data["templates"]),
            "conversation_count": len(self._data["conversations"]),
        }

    # ------------------------------------------------------------------
    # §11.3 #8 — 補齊 LLMDecisionLoop / memory_integration_loop 需要的 3 方法
    # （原先缺失 → hasattr 防護跳過，記憶上下文/情感記憶拿不到）
    # ------------------------------------------------------------------
    async def get_recent_memories(self, limit: int = 5) -> List[str]:
        """回傳最近 conversations 的內容字串（最新優先）。"""
        conversations = self._data.get("conversations", [])
        recent = conversations[-limit:] if limit else conversations
        return [str(c.get("content", "")) for c in recent if c.get("content")]

    async def retrieve_emotional_memories(
        self,
        emotion: str = "",
        min_intensity: float = 0.0,
        limit: int = 3,
    ) -> List[Any]:
        """依 metadata.emotion / metadata.emotion_intensity 篩選情感記憶。

        回傳含 `.content` 屬性的輕量物件（與既有 HAMRecallResult 相容）。
        """
        if not emotion:
            return []
        conversations = self._data.get("conversations", [])
        results: List[Any] = []
        for c in reversed(conversations):
            meta = c.get("metadata") or {}
            mem_emotion = str(meta.get("emotion", "")).lower()
            mem_intensity = float(meta.get("emotion_intensity", 0.0) or 0.0)
            if mem_emotion == str(emotion).lower() and mem_intensity >= min_intensity:
                results.append(self._as_memory_object(c))
                if len(results) >= limit:
                    break
        return results

    async def query_core_memory(
        self,
        keywords: Optional[List[str]] = None,
        data_type_filter: Optional[str] = None,
        date_range: Optional[Tuple] = None,
        min_importance: float = 0.0,
        limit: int = 10,
    ) -> List[Any]:
        """依 keywords（任一命中）與 type/metadata 篩選核心記憶。

        回傳含 `.content` 屬性的輕量物件。
        """
        conversations = self._data.get("conversations", [])
        kws = [k.lower() for k in (keywords or []) if k]
        results: List[Any] = []
        for c in reversed(conversations):
            content = str(c.get("content", ""))
            if data_type_filter:
                ctype = str(c.get("type", ""))
                if ctype != data_type_filter:
                    continue
            if kws and not any(kw in content.lower() for kw in kws):
                continue
            importance = float((c.get("metadata") or {}).get("importance", 0.0) or 0.0)
            if importance < min_importance:
                continue
            results.append(self._as_memory_object(c))
            if len(results) >= limit:
                break
        return results

    @staticmethod
    def _as_memory_object(conversation: Dict[str, Any]) -> Any:
        """包成含 `.content` 的輕量物件（相容 HAMRecallResult 的取用方）。"""

        class _Mem:
            def __init__(self, content, memory_id="", metadata=None):
                self.content = content
                self.memory_id = memory_id
                self.metadata = metadata or {}

        return _Mem(
            str(conversation.get("content", "")),
            memory_id=str(conversation.get("id", "")),
            metadata=conversation.get("metadata") or {},
        )
