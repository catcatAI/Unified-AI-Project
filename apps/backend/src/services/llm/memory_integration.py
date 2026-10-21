# -*- coding: utf-8 -*-
"""
Memory Integration - Extracted from AngelaLLMService
====================================================
Handles memory retrieval, precompute service management, and memory integration.

ANGELA-MATRIX: L3 [β] [A] [L0-L11]
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from services.llm.router import AngelaLLMService, LLMResponse

logger = logging.getLogger("angela_llm.memory")

# Lazy imports for memory enhancement types
_memory_modules_loaded = False
_MEMORY_ENHANCED: Optional[bool] = None
AngelaState: Any = None
UserImpression: Any = None
PrecomputeTask: Any = None


def _load_memory_modules() -> bool:
    """Lazy load memory enhancement modules on first access."""
    global _memory_modules_loaded, _MEMORY_ENHANCED
    global AngelaState, UserImpression, PrecomputeTask

    if _memory_modules_loaded:
        return bool(_MEMORY_ENHANCED)

    _memory_modules_loaded = True

    try:
        from ai.memory.memory_template import AngelaState as _AS
        from ai.memory.memory_template import UserImpression as _UI
        from ai.memory.precompute_service import PrecomputeTask as _PT

        AngelaState = _AS
        UserImpression = _UI
        PrecomputeTask = _PT

        _MEMORY_ENHANCED = True
        logger.info("Memory modules loaded for memory integration")
    except ImportError as e:
        logger.warning("Memory modules not available for memory integration: %s", e, exc_info=True)
        _MEMORY_ENHANCED = False

    return _MEMORY_ENHANCED


def is_memory_enhanced():
    """Lazy check if memory enhancement is available."""
    if _MEMORY_ENHANCED is None:
        _load_memory_modules()
    return _MEMORY_ENHANCED


# --------------------------------------------------------------------------- #
# The conversation recall (the native path has no LLM to read the context)
# --------------------------------------------------------------------------- #
# A question that asks "what did I just say / what is my name" must be
# answered from what the user actually said — not from a greeting template.
_RECALL_QUESTION = re.compile(
    r"剛才|剛剛|之前|先前|說過|提過|講過|記得|我說過|什麼名字|叫什麼"
    r"|remember|what did i say|earlier|my name|said before|call me",
    re.IGNORECASE,
)
# The self-statements the recall understands (name / identity).
_ZH_NAME_STATEMENT = re.compile(r"(?:我叫|我的名字(?:是|叫))\s*([^\s，。！？、,.!?]{1,16})")
_EN_NAME_STATEMENT = re.compile(
    r"(?:my name is|i am called|call me)\s+([A-Za-z][A-Za-z'\- ]{0,30})", re.IGNORECASE
)


def _recall_keywords(message: str) -> List[str]:
    """The content words of a recall question (CJK 2-grams + English words)."""
    keywords = [w.lower() for w in re.findall(r"[A-Za-z]{3,}", message or "")]
    cjk = re.findall(r"[\u4e00-\u9fff]{2,}", message or "")
    for run in cjk:
        for size in (2, 3):
            for i in range(len(run) - size + 1):
                keywords.append(run[i : i + size])
    return keywords


# A statement that tells Angela a fact ("我住在台北"). The native path has
# no way to *acknowledge* it — without this the answer is a canned greeting
# (the QA-machine shape: 16 of 68 turns answered the same greeting).
_TEACHING_VERBS = (
    "我叫",
    "我住在",
    "我搬到",
    "我在",
    "我喜歡",
    "我最愛",
    "我的名字",
    "我的貓",
    "我的狗",
    "我的生日",
    "我的手機",
    "我的電話",
    "我的暱稱",
    "我上班",
    "我最近在學",
    "我養了",
    "我下週",
    "我明天",
    "我負責",
)
# The feelings are not facts: they get the empathetic template, not "記住囉".
_EMOTION_WORDS = ("累", "難過", "傷心", "開心", "焦慮", "孤單", "壓力", "生氣", "害怕", "累死")


def _is_teaching_statement(message: str) -> bool:
    """True when the user tells Angela a fact about themselves."""
    text = (message or "").strip()
    if not text or text.endswith(("?", "？")):
        return False
    if any(word in text for word in _EMOTION_WORDS):
        return False
    return any(text.startswith(verb) for verb in _TEACHING_VERBS)


# The questions that ask for a name (the name recall must not answer others).
_NAME_QUESTION = re.compile(
    r"什麼名字|甚麼名字|名字|姓名|叫什麼|叫什么|我叫|my name|what.*name|called me", re.IGNORECASE
)


def _overlap(query_words: set, statement: str) -> int:
    """How many of the query's content words appear in the statement."""
    statement_words = set(_recall_keywords(statement))
    return len(query_words & statement_words)


def _statement_name(statement: str) -> Optional[str]:
    """The name in a self-statement ("我叫小明" → "小明")."""
    match = _ZH_NAME_STATEMENT.search(statement or "")
    if match:
        return match.group(1).strip()
    match = _EN_NAME_STATEMENT.search(statement or "")
    if match:
        return match.group(1).strip()
    return None


class MemoryIntegration:
    """Memory integration for AngelaLLMService - handles retrieval, precompute, and stats."""

    def __init__(self, service: "AngelaLLMService"):
        self._svc = service
        _load_memory_modules()

    def _validated_template_content(self, best_template: Any) -> Optional[str]:
        """Return servable memory-template content; None when the hit must not serve."""
        # Conversation/interaction logs are stored in the same `templates`
        # bucket by store_experience(data_type="conversation"), but they are
        # NOT answer templates — returning one as the response would leak a
        # raw interaction record. Only genuine template types are usable.
        tpl_type = best_template.get("data_type", "")
        if tpl_type == "conversation":
            return None

        template_content = best_template.get("content", "")
        template_id = best_template.get("id", "unknown")

        # Defensive: content must be a string answer, never a dict/log.
        if not isinstance(template_content, str):
            template_content = str(template_content)
        if not template_content or template_content.strip().startswith("{"):
            return None

        # Poisoned-template guard (defense in depth; HAM also filters):
        # fossilized refusals/echoes/identity-leaks must never serve.
        try:
            from ai.memory.ham_memory.ham_manager import is_unservable_template

            if is_unservable_template(template_content):
                logger.info("Skipped unservable memory template id=%s", template_id)
                return None
        except Exception:
            # Fail-closed: unverifiable guard must never serve a template.
            logger.warning(
                "Poison guard unavailable; refusing template id=%s",
                template_id,
                exc_info=True,
            )
            return None

        return template_content

    async def try_memory_retrieval(
        self, user_message: str, context: Dict[str, Any]
    ) -> Optional["LLMResponse"]:
        """
        Try to retrieve a response from the memory system.

        Args:
            user_message: User message
            context: Conversation context

        Returns:
            Optional[LLMResponse]: Response if memory hit, None otherwise
        """
        from core.interfaces.protocols import ChatResponse

        try:
            if not hasattr(self._svc, "memory_manager") or self._svc.memory_manager is None:
                return None

            results = await self._svc.memory_manager.retrieve_response_templates(
                query=user_message,
                limit=5,
                min_score=0.5,
            )

            recall = await self.try_conversation_recall(user_message, context)
            if recall is not None:
                return recall

            if results and len(results) > 0:
                best_template, score = results[0]

                template_content = self._validated_template_content(best_template)
                if template_content is None:
                    return None

                return ChatResponse(
                    text=template_content,
                    backend="memory-template",
                    model="template-based",
                    confidence=score,
                    hit_score=score,
                    hit_source="memory",
                    route="MEMORY",
                    metadata={
                        "template_id": best_template.get("id", "unknown"),
                        "template_score": score,
                        "memory_hit": True,
                    },
                )

            return None

        except Exception as e:
            logger.warning("Memory retrieval error: %s", e, exc_info=True)
            return None

    async def try_teaching_ack(self, user_message: str) -> Optional["LLMResponse"]:
        """Acknowledge a fact the user just told us.

        Without this the native path answers every statement with the same
        greeting (the QA-machine shape). The acknowledgment quotes the user's
        own words, so it is honest and it is not a canned line.
        """
        if not _is_teaching_statement(user_message):
            return None
        from core.interfaces.protocols import ChatResponse

        fact = (user_message or "").strip()
        text = f"記住囉！{fact}。"
        return ChatResponse(
            text=text,
            backend="memory-teaching",
            model="teaching-ack",
            confidence=0.7,
            hit_score=0.7,
            hit_source="memory",
            route="MEMORY",
            metadata={"memory_hit": True, "teaching": True},
        )

    async def try_conversation_recall(
        self, user_message: str, context: Dict[str, Any]
    ) -> Optional["LLMResponse"]:
        """Answer "what did I just say" from the stored conversations.

        The native path (no LLM) has no way to read the retrieved context, so
        a recall question used to fall through to a greeting template — the
        "chicken-and-duck" shape. This is the extractive answer: the user's
        own words, or the fact stated in them.
        """
        if not _RECALL_QUESTION.search(user_message or ""):
            return None
        manager = getattr(self._svc, "memory_manager", None)
        if manager is None:
            return None

        from core.interfaces.protocols import ChatResponse

        try:
            memories = await manager.query_core_memory(
                keywords=_recall_keywords(user_message),
                data_type_filter="conversation",
                limit=8,
            )
        except Exception as exc:
            logger.debug("conversation recall query failed: %s", exc)
            return None
        if not memories:
            return None

        statements: List[str] = []
        normalized_query = " ".join(re.findall(r"\w+", user_message or ""))
        for memory in memories:
            content = getattr(memory, "content", None)
            if isinstance(content, dict):
                user_text = str(content.get("user") or "")
            else:
                user_text = str(content or "")
            if not user_text:
                continue
            # The question itself is in the conversation history: quoting it
            # back is the parroting shape, not a memory.
            if " ".join(re.findall(r"\w+", user_text)) == normalized_query:
                continue
            # A question the user asked is not a statement they made.
            if user_text.rstrip().endswith(("?", "？")):
                continue
            statements.append(user_text)
        if not statements:
            return None

        try:
            from core.prompt_manager import detect_response_language

            language = detect_response_language(user_message)
        except Exception:
            language = "zh"

        # The statement that actually matches the question ("我住哪裡" → the
        # one about 住, not the one about 名字). A statement with *no* shared
        # content word is not an answer: quoting it would be a wrong answer
        # dressed as a memory.
        query_words = set(_recall_keywords(user_message))
        scored = [(st, _overlap(query_words, st)) for st in statements]
        scored = [(st, score) for st, score in scored if score > 0]
        if not scored:
            return None
        scored.sort(key=lambda item: -item[1])
        statements = [st for st, _score in scored]

        # 1. A fact the user stated about themselves ("我叫小明") — but only
        # when the question actually asks for a name. Otherwise every
        # "我剛才說…" got the same name answer (7/44 turns: the QA machine).
        asks_for_name = bool(_NAME_QUESTION.search(user_message or ""))
        for statement in statements:
            name = _statement_name(statement)
            if name and asks_for_name:
                text = f"你叫{name}。" if language == "zh" else f"Your name is {name}."
                return ChatResponse(
                    text=text,
                    backend="memory-recall",
                    model="conversation-recall",
                    confidence=0.85,
                    hit_score=0.85,
                    hit_source="memory",
                    route="MEMORY",
                    metadata={"memory_hit": True, "recall": "name"},
                )

        # 2. Otherwise quote what the user actually said.
        quoted = statements[0][:120]
        text = f"你剛才說過：「{quoted}」" if language == "zh" else f'You said earlier: "{quoted}"'
        return ChatResponse(
            text=text,
            backend="memory-recall",
            model="conversation-recall",
            confidence=0.65,
            hit_score=0.65,
            hit_source="memory",
            route="MEMORY",
            metadata={"memory_hit": True, "recall": "quote"},
        )

    async def start_precompute(self) -> None:
        """Start the precompute service."""
        if self._svc.enable_memory_enhancement and hasattr(self._svc, "precompute_service"):
            await self._svc.precompute_service.start()
            logger.info("Precompute service started")

    async def stop_precompute(self) -> None:
        """Stop the precompute service."""
        if self._svc.enable_memory_enhancement and hasattr(self._svc, "precompute_service"):
            await self._svc.precompute_service.stop()
            logger.info("Precompute service stopped")

    async def add_precompute_task(self, task: Any) -> bool:
        """Add a precompute task to the queue."""
        if self._svc.enable_memory_enhancement and hasattr(self._svc, "precompute_service"):
            self._svc.precompute_service.enqueue(task)
            return True
        return False

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        stats = {
            "enable_memory_enhancement": self._svc.enable_memory_enhancement,
            "llm_stats": self._svc.stats.copy(),
        }

        if self._svc.enable_memory_enhancement:
            if hasattr(self._svc, "precompute_service"):
                stats["precompute"] = self._svc.precompute_service.get_stats()
            if hasattr(self._svc, "template_library"):
                stats["templates"] = {
                    "total": self._svc.template_library.get_template_count(),
                    "by_category": {
                        cat.value: count
                        for cat, count in self._svc.template_library.get_category_counts().items()
                    },
                }

        template_matcher = getattr(self._svc, "template_matcher", None)
        if template_matcher is not None:
            stats["template_matcher"] = template_matcher.get_stats()

        response_composer = getattr(self._svc, "response_composer", None)
        if response_composer is not None:
            stats["response_composer"] = response_composer.get_stats()

        deviation_tracker = getattr(self._svc, "deviation_tracker", None)
        if deviation_tracker is not None:
            stats["deviation_tracker"] = deviation_tracker.get_stats()

        return stats

    def get_status(self) -> Dict[str, Any]:
        """Get LLM service status."""
        active_backend_type = getattr(self._svc, "active_backend_type", None)
        if active_backend_type and self._svc.active_backend:
            active_backend_name = active_backend_type.value
        else:
            active_backend_name = None
        return {
            "is_available": self._svc.is_available,
            "active_backend": active_backend_name,
            "available_backends": [b.value for b in self._svc.backends.keys()],
            "backends_health": {},
        }
