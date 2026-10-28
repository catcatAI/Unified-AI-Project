"""
ANGELA-MATRIX: [L4] [αβγδ] [A] [L3]
HAM (Hierarchical Associative Memory) Manager — minimal JSON-backed implementation.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from utils.text_utils import bigram_jaccard as _bigram_jaccard_util
from utils.text_utils import char_bigrams as _char_bigrams_util

_TEMPLATE_STOPWORDS = frozenset(
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
        # Generic meta words from a fossilized filler template
        # ("User, the question you're asking is about the current
        # state…"): without these, any English query containing
        # "question" matches that template and gets served garbage.
        "question",
        "asking",
        "asked",
        "current",
        "state",
        "about",
        "re",
        # English question fillers (2026-10-19 audit): without these, the
        # subject-coverage guard false-rejects real matches like
        # "what's the weather like?" (filler tokens look "distinctive").
        "like",
        "please",
        "tell",
        "show",
        "explain",
        "would",
        "could",
        "can",
        "let",
        "us",
        "get",
        "give",
        "need",
        "know",
        "think",
        "something",
        "anything",
        "there",
        "here",
        "really",
        "just",
        "maybe",
        "what's",
        "whats",
        "that's",
        "thats",
        "there's",
        "theres",
    }
)

# Public alias — shared with router._extract_keywords so store-time keyword
# filtering and retrieve-time gating use the SAME stopword set.
TEMPLATE_STOPWORDS = _TEMPLATE_STOPWORDS

logger = logging.getLogger(__name__)

# Content markers that make a stored template UNSERVABLE as an answer.
# Measured live 2026-10-09: unverified LLM/fallback generations fossilized
# into the template pool and replayed verbatim (greetings for recall
# questions, "I'm Gemma" identity leaks, destructive-action claims,
# prompt echoes, honest refusals). Retrieval must skip these even if their
# keywords score high (fossilized keywords self-match the same query).
_UNSERVABLE_CONTENT_MARKERS = (
    "i'm gemma",
    "i am gemma",
    "as gemma",
    "redirecting you to look up",
    "haven't been able to find the information",
    "還沒有足夠",
    "目前還沒有足夠",
    "幫不上忙",
    "暫時無法",
    "沒有答案",
    # English honest-abstain copy（router._HONEST_NO_ANSWER/_HONEST_CANNOT_DO 鏡像）
    "don't have enough knowledge",
    "can't complete this task",
    # Destructive-action claims replay "done" for deletes that may never
    # have executed ("Got it! Deleting the files …").
    "got it! deleting",
    "deleting the files",
)


def is_unservable_template(content: Any, keywords: Any = None) -> bool:
    """True when a stored template must never be served as an answer.

    Covers content classes that are never valid answers regardless of the
    query (refusals, identity leaks, destructive-action claims, prompt
    echoes). Greeting-for-wrong-question poison is NOT covered here — a
    greeting is a fine answer to a greeting — it is removed by the purge
    (keyword analysis) and stopped at store time (verified-only gate).
    """
    text = content if isinstance(content, str) else str(content or "")
    lowered = text.strip().lower()
    if not lowered or lowered.startswith("{"):
        return True
    if any(m in lowered for m in _UNSERVABLE_CONTENT_MARKERS):
        return True
    if lowered.startswith("user:"):
        # Prompt echo fossilized as an answer ("User: X\nAngela: …").
        return True
    return False


class HAMMemoryManager:
    """Minimal JSON-backed hierarchical associative memory manager."""

    def __init__(
        self,
        memory_file: Optional[str] = None,
        auto_save: bool = True,
        core_storage_filename: Optional[str] = None,
    ):
        if memory_file is None:
            # Default to <data dir>/memory/ham_memory.json. The data dir is
            # overridable (ANGELA_DATA_DIR) so a sandboxed run (a probe, a
            # test) never writes into the user's real memory.
            try:
                from path_config import DATA_DIR

                memory_file = os.path.join(str(DATA_DIR), "memory", "ham_memory.json")
            except Exception:
                project_root = self._find_project_root()
                memory_file = os.path.join(project_root, "data", "memory", "ham_memory.json")
        self.memory_file = Path(memory_file)
        self.auto_save = auto_save
        self._data: Dict[str, Any] = {"templates": [], "conversations": [], "metadata": {}}
        self._max_entries_per_bucket = 5000
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
            except (json.JSONDecodeError, IOError):
                self._data = {"templates": [], "conversations": [], "metadata": {}}

    def _write_to_disk(self) -> None:
        """Synchronous disk write — called from _save or save_async."""
        # P1-9: top-level metadata had NO writer anywhere (永遠 {}).
        # Stamp self-describing provenance on every save; merge so any
        # caller-set keys survive.
        meta = self._data.get("metadata")
        if not isinstance(meta, dict):
            meta = {}
        meta.update(
            {
                "schema_version": 1,
                "saved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "conversation_count": len(self._data.get("conversations", [])),
                "template_count": len(self._data.get("templates", [])),
                "bucket_cap": self._max_entries_per_bucket,
            }
        )
        self._data["metadata"] = meta
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def _save(self) -> None:
        if not self.auto_save or not self.memory_file:
            return
        try:
            self._write_to_disk()
        except (OSError, TypeError) as e:
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
        except (OSError, TypeError) as e:
            logger.warning(f"HAMMemoryManager async save failed: {e}")

    def _enforce_cap(self, bucket: str) -> None:
        """Keep bucket bounded to prevent unbounded growth (long-running server)."""
        bucket_data = self._data.get(bucket, [])
        if len(bucket_data) > self._max_entries_per_bucket:
            self._data[bucket] = bucket_data[-int(self._max_entries_per_bucket * 0.8) :]
            logger.debug(f"HAM {bucket} capped to {len(self._data[bucket])} entries")

    # ------------------------------------------------------------------
    # Retention (age / importance / access)
    # ------------------------------------------------------------------
    # The hard cap above bounds the *size*; these rules bound the *staleness*.
    # A year-old, never-used, low-importance memory is noise, not memory.
    _RETENTION_DAYS_LOW = 30
    _RETENTION_DAYS_MID = 90
    _RETENTION_KEEP_IMPORTANCE = 0.7
    _RETENTION_DROP_IMPORTANCE = 0.3
    _RETENTION_MIN_RECENT = 50

    def _entry_age_days(self, entry: Dict[str, Any], now: datetime) -> Optional[float]:
        """Age in days of a stored entry; None when the timestamp is unusable."""
        meta = entry.get("metadata")
        raw = meta.get("timestamp") if isinstance(meta, dict) else None
        if not raw:
            raw = entry.get("timestamp")
        if not raw:
            return None
        try:
            stamp = datetime.fromisoformat(str(raw))
        except (TypeError, ValueError):
            return None
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return (now - stamp).total_seconds() / 86400.0

    @staticmethod
    def _entry_importance(entry: Dict[str, Any]) -> float:
        """保留決策用的**有效重要性** = 原評分 × 編碼時的 AL 權重（clamp [0,1]）。

        ``al_weight``（§10 policy 的「多重」，state 觀測才有戳記）只影響
        保留決策，不改寫 metadata 原值 —— caller 的內容評分保持真實，兩層
        分開可取證。沒有 ``al_weight`` 的記憶 = 原評分（既有行為不變）。
        """
        base = 0.5
        weight = 1.0
        meta = entry.get("metadata")
        if isinstance(meta, dict):
            try:
                base = float(meta.get("importance", 0.5))
            except (TypeError, ValueError):
                base = 0.5
            raw_weight = meta.get("al_weight")
            if raw_weight is not None:
                try:
                    weight = float(raw_weight)
                except (TypeError, ValueError):
                    weight = 1.0
        return min(max(base * weight, 0.0), 1.0)

    def _should_prune_entry(self, entry: Dict[str, Any], now: datetime) -> bool:
        """True when an entry is stale enough to drop.

        Protected entries and high-importance entries are kept regardless of
        age; low-importance entries die after 30 days, medium ones after 90.

        §10（item ④）：帶 ``al_retain_days`` 戳記的記憶，保留期由 AL 的
        policy 決定（取代 30/90 分層）—— ``protected`` 與 keep-floor
        （有效重要性 ≥ 0.7）仍先判：固化與高價值優先於保留期。戳記損壞
        → 退回預設分層（一個壞值不該誤殺記憶）。
        """
        meta = entry.get("metadata")
        if isinstance(meta, dict) and meta.get("protected"):
            return False
        age = self._entry_age_days(entry, now)
        if age is None:
            return False
        importance = self._entry_importance(entry)
        if importance >= self._RETENTION_KEEP_IMPORTANCE:
            return False
        if isinstance(meta, dict) and meta.get("al_retain_days") is not None:
            try:
                policy_days = float(meta["al_retain_days"])
            except (TypeError, ValueError):
                policy_days = None
            if policy_days is not None:
                return age > policy_days
        limit = (
            self._RETENTION_DAYS_LOW
            if importance < self._RETENTION_DROP_IMPORTANCE
            else self._RETENTION_DAYS_MID
        )
        return age > limit

    def prune(self, now: Optional[datetime] = None) -> Dict[str, int]:
        """Drop stale, low-importance memories; return what was removed.

        The most recent entries are always kept, so a fresh install never
        ends up with an empty memory.
        """
        now = now or datetime.now(timezone.utc)
        removed = {"templates": 0, "conversations": 0}
        for bucket in ("templates", "conversations"):
            entries = self._data.get(bucket)
            if not isinstance(entries, list) or not entries:
                continue
            # The most recent entries are protected from pruning: a fresh
            # install must not end up with an empty memory, and the newest
            # memories are the ones that matter.
            protected_from = max(0, len(entries) - self._RETENTION_MIN_RECENT)
            kept: List[Any] = []
            for index, entry in enumerate(entries):
                if not isinstance(entry, dict) or index >= protected_from:
                    kept.append(entry)
                    continue
                if self._should_prune_entry(entry, now):
                    removed[bucket] += 1
                    continue
                kept.append(entry)
            self._data[bucket] = kept
        if removed["templates"] or removed["conversations"]:
            logger.info(
                "HAM retention pruned %d templates / %d conversations",
                removed["templates"],
                removed["conversations"],
            )
        return removed

    def _apply_retention_policy(self, entry_meta: Dict[str, Any]) -> Dict[str, Any]:
        """§10：把 AL 的 retention/decay policy 執行進這筆記憶（item ④）。

        三個量與執行方式：

        - ``retention``（state 觀測）→ 戳記 ``al_retain_days``：
          ``_should_prune_entry`` 用它取代預設 30/90 天分層。
        - ``weight``（state 觀測）→ 戳記 ``al_weight``：保留決策的有效
          重要性 = 原評分 × al_weight（``_entry_importance``）。
          **不改寫 caller 的 ``importance`` 原值** —— 內容評分與生命調制
          兩層分開，各自可取證（panel 契約釘住原值）。
        - ``consolidate`` → ``protected = True``（現行規則：不論年齡保留
          ＝固化；固化只在 ``life_phase == CONSOLIDATION`` 時發生）。

        AL 缺席（import 失敗、快照讀不到）→ 回 ``{}`` 且不動任何規則、
        debug 留痕 —— 記憶層不能因為 AL 不在就存不下東西。回傳值同時是
        給 ``submit_event`` 的執行摘要（統計，無內容 —— §8）。
        """
        try:
            from core.life.al_memory_policy import retention_policy
            from core.life.al_state import get_al_state

            policy = retention_policy(get_al_state())
        except Exception as exc:
            logger.debug("HAM retention policy unavailable, storing plain: %s", exc, exc_info=True)
            return {}

        applied: Dict[str, Any] = {
            "policy": policy.as_dict(),
            "stamped": {},
        }
        if policy.source["retention"] == "state":
            days = policy.retention_seconds / 86400.0
            entry_meta["al_retain_days"] = days
            applied["stamped"]["al_retain_days"] = days
        if policy.source["weight"] == "state":
            entry_meta["al_weight"] = policy.weight
            applied["stamped"]["al_weight"] = policy.weight
        if policy.consolidate:
            entry_meta["protected"] = True
            applied["stamped"]["protected"] = True
        return applied

    def _report_policy_result(
        self, mem_id: str, applied: Dict[str, Any], pruned: Dict[str, int]
    ) -> None:
        """§10 的「回報結果事件」：執行摘要進 AL 事件流（原文不進 AL —— §8）。"""
        try:
            from core.life.al_state import EventType, submit_event

            submit_event(
                EventType.MEMORY_RESULT,
                {"mem_id": mem_id, "applied": applied, "pruned": dict(pruned)},
            )
        except Exception as exc:
            logger.debug("HAM policy result event failed: %s", exc, exc_info=True)

    async def store_template(self, template: Any) -> None:
        self._data["templates"].append(
            {
                "content": getattr(template, "content", str(template)),
                "id": getattr(template, "id", None),
                "keywords": getattr(template, "keywords", []),
            }
        )
        self._enforce_cap("templates")
        await asyncio.to_thread(self._save)

    def _score_keyword_match(self, kw_lower: str, query_lower: str) -> float:
        """Score a single keyword against the query."""
        import re as _kw_re

        if kw_lower not in query_lower:
            return _bigram_jaccard_util(kw_lower, query_lower)
        if len(kw_lower) <= 1:
            return 0.0
        if len(kw_lower) <= 2:
            pattern = r"(?<![\w])" + _kw_re.escape(kw_lower) + r"(?![\w])"
            if _kw_re.search(pattern, query_lower):
                return 0.9
            return 0.0
        return 0.9

    def _relevance_gate(
        self,
        keywords: List[str],
        query_lower: str,
        best_score: float,
        min_score: float,
        content: str = "",
    ) -> float:
        """Apply relevance gate: penalize single-keyword match on long query.

        主體守衛（2026-10-19 稽核）：查詢自帶 ≥2 個非停用詞、模板只覆蓋 ≤1 個，
        且模板內容也未提到任何未覆蓋詞 → 模板回答的是另一個主體
        （"capital of Australia" 命中 "capital of Japan: Tokyo"）→ 拒絕。
        """
        query_tokens = query_lower.split()
        matched_kws = set()
        total_non_stop = 0
        for kw in keywords:
            k = kw.lower().strip()
            if not k or k in _TEMPLATE_STOPWORDS:
                continue
            total_non_stop += 1
            if k in query_lower:
                matched_kws.add(k)
        if len(query_tokens) <= 3:
            if len(matched_kws) <= 1:
                return 0.0
        elif len(matched_kws) <= 1 and total_non_stop > 1:
            best_score *= 1.0 / max(total_non_stop, 2)
            if best_score < min_score:
                return 0.0
        # Subject-coverage guard: reject wrong-subject replay.
        if self._subject_coverage_rejects(query_tokens, matched_kws, content):
            return 0.0
        return best_score

    @staticmethod
    def _subject_coverage_rejects(query_tokens: List[str], matched_kws: set, content: str) -> bool:
        """主體覆蓋守衛（語意見 _relevance_gate docstring）。

        查詢 ≥2 個非停用詞、模板只覆蓋 ≤1 個、且模板內容未提任何未覆蓋詞
        → 模板回答的是另一個主體 → 拒絕。
        """
        if len(matched_kws) > 1 or len(query_tokens) <= 3:
            return False
        content_lower = (content or "").lower()
        query_distinctive = [
            t
            for t in query_tokens
            if t.strip("?!.,'\";:") not in _TEMPLATE_STOPWORDS and t not in _TEMPLATE_STOPWORDS
        ]
        unmatched = [t for t in query_distinctive if t not in matched_kws]
        if len(query_distinctive) >= 2 and unmatched:
            if not any(t.strip("?!.,'\";:") in content_lower for t in unmatched):
                return True
        return False

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
        query_lower = query.lower()
        for tpl in candidates:
            if is_unservable_template(tpl.get("content", "")):
                continue
            keywords = tpl.get("keywords", [])
            if not keywords:
                continue
            best_score = 0.0
            for kw in keywords:
                kw_lower = kw.lower().strip()
                if not kw_lower or kw_lower in _TEMPLATE_STOPWORDS:
                    continue
                best_score = max(best_score, self._score_keyword_match(kw_lower, query_lower))
            if best_score < min_score:
                continue
            gated_score = self._relevance_gate(
                keywords, query_lower, best_score, min_score, tpl.get("content", "")
            )
            if gated_score >= min_score:
                scored.append((tpl, gated_score))

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
        namespace: Optional[str] = None,
    ) -> Optional[str]:
        """Store a raw experience entry into the memory store.

        Args:
            raw_data: Content to store — str, dict, or any object.
            data_type: Category label for the experience.
            metadata: Optional metadata dict.
            namespace: Optional memory namespace (default: none = legacy
                unscoped bucket). Role play passes the role id so one role's
                experiences never surface in another's recall.
            keywords: Optional explicit keywords. If not provided,
                      keywords are auto-extracted from raw_data.
        """
        resolved_keywords = keywords if keywords is not None else self._extract_keywords(raw_data)
        entry_meta = dict(metadata or {})
        if namespace is not None:
            entry_meta.setdefault("namespace", namespace)
        # 面板（/context/memory/recent）與時間衰減都讀 metadata.timestamp；
        # 沒人送時在這裡補一個，否則每列記憶的 timestamp 都是 null。
        if entry_meta.get("timestamp") in (None, ""):
            entry_meta["timestamp"] = datetime.now(timezone.utc).isoformat()
        entry = {
            "content": raw_data if isinstance(raw_data, dict) else str(raw_data),
            "data_type": data_type,
            "metadata": entry_meta,
            "keywords": resolved_keywords,
        }
        # §10（Phase 2 item ④）：AL 的 retention/decay policy 在此執行進
        # metadata（三量各自標觀測歸因；未觀測的量不動現行規則 —— D11）。
        applied = self._apply_retention_policy(entry_meta)
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
        self._enforce_cap(bucket)
        # id = 寫入當下的位置（在 prune 之前取，避免清舊後編號回撞）
        mem_id = f"exp_{len(self._data.get(bucket, []))}"
        # 保留規則的生產執行點（2026-10-27 前零呼叫 —— 30/90 天分層與
        # policy 戳記自此真的會跑）：本次 store 順帶清掉過期的舊記憶，
        # 隨後 _save 把清完的狀態落盤。
        pruned = self.prune()
        if applied:
            self._report_policy_result(mem_id, applied, pruned)
        await asyncio.to_thread(self._save)
        return mem_id

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
            and _re_fallback.search(r"[\w]", frag)  # must contain at least one word char
        ][:max_keywords]

    def store_conversation(self, conversation: Dict[str, Any]) -> None:
        self._data["conversations"].append(conversation)
        self._enforce_cap("conversations")
        self._save()

    async def store_conversation_async(self, conversation: Dict[str, Any]) -> None:
        """Non-blocking store — offloads disk write to a worker thread.

        Callers in async contexts (FastAPI endpoints, integration loops)
        should prefer this over store_conversation() to avoid blocking
        the event loop with synchronous JSON file I/O.
        """
        self._data["conversations"].append(conversation)
        self._enforce_cap("conversations")
        await self.save_async()

    def get_stats(self) -> Dict[str, Any]:
        return {
            "template_count": len(self._data["templates"]),
            "conversation_count": len(self._data["conversations"]),
        }

    # ------------------------------------------------------------------
    # §11.3 #8 — 補齊 LLMDecisionLoop 需要的 3 方法
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
        namespace: Optional[str] = None,
    ) -> List[Any]:
        """依 keywords（任一命中）與 type/metadata 篩選核心記憶。

        回傳含 `.content` 屬性的輕量物件。``namespace`` 是硬分割：給了就
        只回該命名空間的條目，未標 namespace 的舊資料不會混進來。
        """
        conversations = self._data.get("conversations", [])
        kws = [k.lower() for k in (keywords or []) if k]
        results: List[Any] = []
        for c in reversed(conversations):
            content = str(c.get("content", ""))
            if namespace is not None:
                if (c.get("metadata") or {}).get("namespace") != namespace:
                    continue
            if data_type_filter:
                # store_experience 寫的是 data_type；type 是舊 conversation 物件的鍵
                ctype = str(c.get("data_type") or c.get("type") or "")
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
            """Dict-like wrapper: attribute access for API callers, ``get()`` for
            callers that treat the result as a mapping (e.g. cli/repl.py)."""

            def __init__(self, content, memory_id="", metadata=None, data_type=""):
                self.content = content
                self.memory_id = memory_id
                self.metadata = metadata or {}
                self.data_type = data_type

            def get(self, key, default=None):
                if hasattr(self, key):
                    value = getattr(self, key)
                    if value not in (None, ""):
                        return value
                return self.metadata.get(key, default)

        # content is returned RAW (dict stays dict). Stringifying here made the
        # MemoryViewer render Python repr, and left game_memory_bridge's
        # isinstance(content, dict) branch permanently dead.
        return _Mem(
            conversation.get("content", ""),
            memory_id=str(conversation.get("id", "")),
            metadata=conversation.get("metadata") or {},
            data_type=str(conversation.get("data_type") or conversation.get("type") or ""),
        )
