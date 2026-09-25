# ANGELA-MATRIX: L3 [βγ] [A] [L2-L5]
"""長程一致性上下文排程器（Long-Horizon Consistency Context Scheduler）。

設計原則：上下文治理從「破壞性裁剪」升級為「非破壞性分配」——
小模型不該單獨工作，而是組成**消化工作者陣列**，由排程器統一管理
「哪些上下文、以什麼形式、進哪個工作者」：

- **工作者陣列**：專案自創的萃取工作者（確定性、零延遲、永遠可用）
  → ED3N／小模型（經 chat_completion，後端缺席時自動落到 ED3N）。
- **分配計畫（build_plan）**：保護 system 與最終 user；其餘中段訊息
  按工作者視窗（DIGEST_WORKER_WINDOW tokens）分塊，逐塊消化。
- **長程一致性帳本（ContextLedger）**：per conversation 的輪次編號
  與消化快取（內容雜湊 → 摘要），跨輪、跨重啟保持一致——同一段
  上下文不會被反覆重新消化，摘要格式輪次穩定。
- **消化優先、裁墌最後**：總量守門先嘗試把中段訊息消化成單一
  `[Digested Context]` 區塊（有界），仍不足才降級到既有裁剪階段。

對外介面：
- ``plan_query``：統一產生 preprocessing / routing hints
- ``digest_overflow_sync``：同步、確定性（預算守門直接使用）
- ``digest_with_llm``：非同步、小模型升級品質（ router 於啟用時呼叫）
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from services.llm.prompt_builder import estimate_tokens

logger = logging.getLogger(__name__)

# 消化結果的 token 上限（摘要區塊必須遠小於原內容才有意義）
DEFAULT_DIGEST_TOKENS = 300
# 每個消化工作者單次視窗（tokens）——超過就分塊
DIGEST_WORKER_WINDOW = 800
# 消化帳本預設位置（與學習日誌同屬 data/agent_workspace/）
DEFAULT_LEDGER_DIR = Path("data/agent_workspace/context_ledger")
LOCAL_KNOWLEDGE_QUERY_TYPES = frozenset({"math", "logic", "knowledge", "search"})


@dataclass
class DigestChunk:
    """分給消化工作者的一塊上下文。"""

    index: int
    content: str
    tokens: int
    cache_key: str


@dataclass
class AllocationPlan:
    """分配計畫：誰受保護、誰被消化、如何分塊。"""

    budget_tokens: int
    protected_indices: List[int] = field(default_factory=list)
    digested_indices: List[int] = field(default_factory=list)
    chunks: List[DigestChunk] = field(default_factory=list)
    digest_tokens: int = DEFAULT_DIGEST_TOKENS


@dataclass(frozen=True)
class QueryPreprocessingPlan:
    query_type: str
    confidence: float
    action_type: str
    actionability: float
    route_hint: str
    allow_context_enrichment: bool
    allow_knowledge_pipeline: bool
    allow_specialized_agents: bool
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_type": self.query_type,
            "confidence": self.confidence,
            "action_type": self.action_type,
            "actionability": self.actionability,
            "route_hint": self.route_hint,
            "allow_context_enrichment": self.allow_context_enrichment,
            "allow_knowledge_pipeline": self.allow_knowledge_pipeline,
            "allow_specialized_agents": self.allow_specialized_agents,
            "reason": self.reason,
        }


class ContextLedger:
    """長程一致性帳本：輪次編號＋消化快取，持久化到磁碟（重啟後仍一致）。"""

    def __init__(self, ledger_dir: Path = DEFAULT_LEDGER_DIR) -> None:
        self._dir = Path(ledger_dir)
        self._turns: Dict[str, int] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}  # f"{conv}:{hash}" -> {digest, ts}
        self._load()

    def _file(self) -> Path:
        return self._dir / "ledger.json"

    def _load(self) -> None:
        try:
            path = self._file()
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                self._turns = data.get("turns", {})
                self._cache = data.get("cache", {})
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("context ledger load failed: %s", exc)

    def save(self) -> None:
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            payload = {"turns": self._turns, "cache": self._cache}
            self._file().write_text(
                json.dumps(payload, ensure_ascii=False), encoding="utf-8"
            )
        except OSError as exc:
            logger.warning("context ledger save failed: %s", exc)

    def next_turn(self, conversation_id: str) -> int:
        self._turns[conversation_id] = self._turns.get(conversation_id, 0) + 1
        return self._turns[conversation_id]

    def cache_get(self, conversation_id: str, chunk_hash: str) -> Optional[str]:
        entry = self._cache.get(f"{conversation_id}:{chunk_hash}")
        return str(entry["digest"]) if entry else None

    def cache_put(self, conversation_id: str, chunk_hash: str, digest: str) -> None:
        self._cache[f"{conversation_id}:{chunk_hash}"] = {
            "digest": digest,
            "ts": datetime.now(timezone.utc).isoformat(),
        }

    def counts(self) -> Dict[str, int]:
        return {"conversations": len(self._turns), "cached_digests": len(self._cache)}


class ContextScheduler:
    """上下文排程器：分配計畫＋消化工作者陣列＋長程一致性帳本。"""

    def __init__(
        self,
        llm_service: Any = None,
        ledger_dir: Path = DEFAULT_LEDGER_DIR,
        digest_tokens: int = DEFAULT_DIGEST_TOKENS,
    ) -> None:
        self._llm_service = llm_service
        self.ledger = ContextLedger(ledger_dir)
        self.digest_tokens = digest_tokens
        self._stats: Dict[str, int] = {
            "digest_events": 0,
            "cache_hits": 0,
            "llm_digests": 0,
            "query_plans": 0,
        }

    def plan_query(
        self,
        text: str,
        context: Optional[Dict[str, Any]] = None,
        classifier: Any = None,
    ) -> QueryPreprocessingPlan:
        if context is not None and isinstance(context.get("_preprocessing_plan"), dict):
            return QueryPreprocessingPlan(**context["_preprocessing_plan"])
        from ai.core.query_classifier import (
            ROUTE_CAPABILITY_CATALOG,
            ROUTE_LLM_FIRST,
            QueryClassifier,
        )

        active_classifier = classifier
        if not isinstance(active_classifier, QueryClassifier):
            active_classifier = QueryClassifier()
        result = active_classifier.classify(text)
        route_hint = result.route_hint or "balanced"
        bypass_pre_llm = route_hint in (ROUTE_CAPABILITY_CATALOG, ROUTE_LLM_FIRST)
        allow_knowledge = (
            not bypass_pre_llm
            and result.primary_type.value in LOCAL_KNOWLEDGE_QUERY_TYPES
            and result.confidence >= 0.6
        )
        plan = QueryPreprocessingPlan(
            query_type=result.primary_type.value,
            confidence=result.confidence,
            action_type=result.action_type,
            actionability=result.actionability,
            route_hint=route_hint,
            allow_context_enrichment=not bypass_pre_llm,
            allow_knowledge_pipeline=allow_knowledge,
            allow_specialized_agents=not bypass_pre_llm,
            reason=result.reason,
        )
        if context is not None:
            context["_preprocessing_plan"] = plan.to_dict()
        self._stats["query_plans"] += 1
        return plan

    # ---------- 分配計畫 ----------

    def build_plan(self, messages: List[Dict], budget_tokens: int) -> AllocationPlan:
        """保護 system 與最終 user；中段訊息按工作者視窗分塊。"""
        last_idx = len(messages) - 1
        protected = [
            i
            for i, m in enumerate(messages)
            if m.get("role") == "system" or i == last_idx
        ]
        middle = [i for i in range(len(messages)) if i not in protected]
        chunks: List[DigestChunk] = []
        buf: List[str] = []
        buf_tokens = 0
        for i in middle:
            content = str(messages[i].get("content", ""))
            tokens = estimate_tokens(content)
            if buf and buf_tokens + tokens > DIGEST_WORKER_WINDOW:
                self._flush_chunk(buf, chunks)
                buf, buf_tokens = [], 0
            buf.append(content)
            buf_tokens += tokens
        if buf:
            self._flush_chunk(buf, chunks)
        return AllocationPlan(
            budget_tokens=budget_tokens,
            protected_indices=protected,
            digested_indices=middle,
            chunks=chunks,
            digest_tokens=self.digest_tokens,
        )

    def _flush_chunk(self, buf: List[str], chunks: List[DigestChunk]) -> None:
        content = "\n\n".join(buf)
        chunks.append(
            DigestChunk(
                index=len(chunks),
                content=content,
                tokens=estimate_tokens(content),
                cache_key=hashlib.sha1(content.encode("utf-8")).hexdigest()[:16],
            )
        )

    # ---------- 同步消化（自創萃取工作者——永遠可用） ----------

    def digest_overflow_sync(
        self,
        messages: List[Dict],
        budget_tokens: int,
        conversation_id: str = "default",
    ) -> Dict[str, Any]:
        """超預算時把中段訊息消化成單一 [Digested Context] 區塊（非破壞性）。

        回傳 {"digested": N, "freed_chars": N}；不值得消化（中段總量
        已小於摘要上限）或無中段時回 {"digested": 0}。
        """
        plan = self.build_plan(messages, budget_tokens)
        combined_tokens = sum(c.tokens for c in plan.chunks)
        if not plan.chunks or combined_tokens <= self.digest_tokens:
            return {"digested": 0, "freed_chars": 0}

        combined = "\n\n".join(c.content for c in plan.chunks)
        digest_text = self._digest_text_sync(combined, conversation_id)
        self.ledger.save()
        self._stats["digest_events"] += 1

        digest_msg = {
            "role": "system",
            "content": (
                f"[Digested Context]（收納 {len(plan.digested_indices)} 則的消化摘要）\n"
                f"{digest_text}"
            ),
        }
        freed_chars = 0
        first_idx = plan.digested_indices[0]
        for i in reversed(plan.digested_indices):
            freed_chars += len(str(messages[i].get("content", "")))
            messages.pop(i)
        messages.insert(first_idx, digest_msg)
        return {"digested": len(plan.digested_indices), "freed_chars": freed_chars}

    def _digest_text_sync(self, text: str, conversation_id: str) -> str:
        """萃取式消化：帳本快取命中直接回（摘要確定性——同內容永遠同摘要）；
        未命中按區段標頭＋要點萃取並寫回快取。"""
        text_hash = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
        cached = self.ledger.cache_get(conversation_id, text_hash)
        if cached is not None:
            self._stats["cache_hits"] += 1
            return cached
        self.ledger.next_turn(conversation_id)
        digest = self._extractive_digest(text, self.digest_tokens)
        self.ledger.cache_put(conversation_id, text_hash, digest)
        return digest

    def _extractive_digest(self, text: str, limit_tokens: int) -> str:
        """確定性萃取：保留區段標頭與每則要點，總量有界。"""
        kept: List[str] = []
        seen_headers: set = set()
        used = 0
        for raw in text.splitlines():
            line = raw.strip()
            if not line:
                continue
            is_header = line.startswith("[") and "]" in line
            if is_header:
                if line in seen_headers:
                    continue
                seen_headers.add(line)
            cost = estimate_tokens(line) + 1
            if used + cost > limit_tokens:
                break
            kept.append(line if is_header else f"- {line[:120]}")
            used += cost
        if not kept:  # 單行超長的極端情況：硬截首段
            return text[:200]
        return "\n".join(kept)

    # ---------- 非同步升級（小模型／ED3N 工作者） ----------

    async def digest_with_llm(
        self, text: str, conversation_id: str, llm_service: Any = None
    ) -> Optional[str]:
        """用小模型（無後端時自動落到專案自創的 ED3N）升級消化品質。

        成功時寫回帳本快取——下一輪同內容直接使用高品質摘要；
        失敗時回 None（萃取結果仍在，不影響運行）。
        """
        svc = llm_service or self._llm_service
        if svc is None:
            try:
                from services.llm.router import get_llm_service

                svc = await get_llm_service()
            except Exception as exc:
                logger.debug("llm service unavailable for digest: %s", exc)
                return None
        try:
            prompt = (
                "請將以下系統上下文壓縮為不超過 8 條要點的摘要，"
                "保留區段標題與關鍵數值，使用繁體中文：\n\n"
                f"{text[:4000]}"
            )
            response = await svc.chat_completion(
                [{"role": "user", "content": prompt}],
                max_tokens=256,
                temperature=0.3,
            )
            digest = str(getattr(response, "text", "") or "").strip()
            if not digest:
                return None
            chunk_hash = hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]
            self.ledger.cache_put(conversation_id, chunk_hash, digest)
            self.ledger.save()
            self._stats["llm_digests"] += 1
            return digest
        except Exception as exc:
            logger.debug("llm digest failed (extractive remains): %s", exc)
            return None

    # ---------- 觀測 ----------

    def stats(self) -> Dict[str, int]:
        out = dict(self._stats)
        out.update(self.ledger.counts())
        return out


_scheduler: Optional[ContextScheduler] = None


def get_context_scheduler() -> ContextScheduler:
    """排程器單例（帳本持久化於 data/agent_workspace/context_ledger/）。"""
    global _scheduler
    if _scheduler is None:
        _scheduler = ContextScheduler()
    return _scheduler


__all__ = [
    "AllocationPlan",
    "ContextLedger",
    "ContextScheduler",
    "DEFAULT_DIGEST_TOKENS",
    "DIGEST_WORKER_WINDOW",
    "DigestChunk",
    "QueryPreprocessingPlan",
    "get_context_scheduler",
]
