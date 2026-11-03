# -*- coding: utf-8 -*-
"""
Memory Integration - Extracted from AngelaLLMService
====================================================
Handles memory retrieval, precompute service management, and memory integration.

ANGELA-MATRIX: L3 [β] [A] [L0-L11]
"""

from __future__ import annotations

import logging
import math
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
#
# The list of verb prefixes that used to be here was written from the
# phrasings the standard set happens to use, so a fact said any other way
# ("我今年三十五歲", "我每週三跑步") fell through to a canned line — that is
# teaching the test, not the model. Any first-person declarative is a fact
# about the user; what must be excluded is what is *not* a fact: a question,
# a feeling (it gets the empathetic reply) and a request ("我想…", "幫我…").
_TEACHING_FIRST_PERSON = re.compile(r"^(?:我|我們|my\b|i\b)", re.IGNORECASE)
_TEACHING_NOT_A_REQUEST = re.compile(
    r"幫我|請你|請幫|麻煩|可以嗎|能不能|要不要|好不好|嗎[？?]?$"
    r"|^(?:我想|我要|我需要|我想要|我不知道|我不確定)"
)
# A question without a question mark ("我的電話是幾號") is still a question.
_TEACHING_INTERROGATIVE = re.compile(r"什麼|甚麼|哪|幾|多少|誰|怎麼|如何|嗎|呢")
# The feelings are not facts: they get the empathetic template, not "記住囉".
_EMOTION_WORDS = (
    "累",
    "難過",
    "傷心",
    "開心",
    "焦慮",
    "孤單",
    "壓力",
    "生氣",
    "害怕",
    "累死",
    "心情",
    "不舒服",
    "疲憊",
)

# The backends that can actually *generate* an answer. The acknowledgment
# below is a fixed frame ("記住囉！X。") — a surface-layer line. It exists
# because the native path has nothing better, not because a canned frame is a
# good answer: letting it pre-empt a backend that can answer is exactly the
# "templates replace the core" regression this project already paid for once.
_GENERATIVE_BACKENDS = {"openai", "deepseek", "anthropic", "google", "ollama", "llama_cpp"}


def _has_generative_backend(service: Any) -> bool:
    """True when a backend that can generate is registered on the service."""
    backends = getattr(service, "backends", None)
    if not backends:
        return False
    for name in backends:
        key = str(getattr(name, "value", name)).lower()
        if key in _GENERATIVE_BACKENDS:
            return True
    return False


# The value a fact sentence states. Only the shapes a grammar gives you —
# a copula, a naming verb, a residence, a workplace, a number. Everything
# else gets a bare acknowledgment: quoting the user's sentence back is a
# parrot (the standard set names it as a defect), and a parrot is not a reply.
_VALUE_COPULA = re.compile(r"^.+?是\s*(.+)$")
_VALUE_NAMED = re.compile(r"^.+?叫\s*(.+)$")
_VALUE_RESIDENCE = re.compile(r"^.+?住在\s*(.+)$")
_VALUE_WORKPLACE = re.compile(r"^.+?在\s*(.+?)(?:工作|上班|上學|讀書)$")
_NUMBER_VALUE = re.compile(
    r"[0-9]+(?:\.[0-9]+)?[點號歲元塊分秒年月日]?"
    r"|[零一二三四五六七八九十百千兩]+[點歲號元塊分秒年月日]"
)
# A frequency expression states its value as a weekday ("我每週三跑步" → 三).
_WEEKDAY_VALUE = re.compile(r"(?:每|每個)?(?:週|周|星期|禮拜)([一二三四五六日天])")


# A value is a *word* (a name, a place, a time, a number), and an
# acknowledgment can say it. A value long enough to be a clause is the user's
# own sentence again — repeating it is the parroting shape the standard set
# measures (a reply is a parrot when what it copies makes up 60% of it), so
# those get the bare "記住囉！" instead: it says less, but it does not echo.
_VALUE_MAX_TOKENS = 6


def _value_tokens(value: str) -> int:
    """How many words a value is (a CJK character is a word, so is a number)."""
    return len(re.findall(r"[A-Za-z0-9_']+|[\u4e00-\u9fff]", value or ""))


def _statement_value(statement: str) -> Optional[str]:
    """The value a fact sentence states ("我的貓叫小花" → 小花).

    ``None`` when the sentence has no such shape — then the acknowledgment
    stays a bare "記住囉！" rather than repeating what the user just said.
    """
    text = (statement or "").strip().rstrip("。！!?？")
    if not text:
        return None
    value: Optional[str] = None
    match = _VALUE_COPULA.match(text)
    if match:
        value = match.group(1).strip().rstrip("的").strip() or None
    if value is None:
        match = _VALUE_NAMED.match(text)
        if match:
            # "我養了一隻叫豆豆的狗" → the value is 豆豆, not 豆豆的狗.
            value = match.group(1).split("的", 1)[0].strip() or None
    if value is None:
        match = _VALUE_RESIDENCE.match(text)
        if match:
            value = match.group(1).strip() or None
    if value is None:
        match = _VALUE_WORKPLACE.match(text)
        if match:
            value = match.group(1).strip() or None
    if value is None:
        match = _WEEKDAY_VALUE.search(text)
        if match:
            value = match.group(1).strip() or None
    if value is None:
        match = _NUMBER_VALUE.search(text)
        if match:
            value = match.group(0).strip() or None
    if value is None or _value_tokens(value) > _VALUE_MAX_TOKENS:
        return None
    return value


def _is_teaching_statement(message: str) -> bool:
    """True when the user tells Angela a fact about themselves."""
    text = (message or "").strip()
    if not text or text.endswith(("?", "？")):
        return False
    if any(word in text for word in _EMOTION_WORDS):
        return False
    if _TEACHING_NOT_A_REQUEST.search(text):
        return False
    if _TEACHING_INTERROGATIVE.search(text):
        return False
    return bool(_TEACHING_FIRST_PERSON.match(text))


def _taught_this_turn(statement: str) -> bool:
    """True when the sentence was just stored as a taught fact.

    A third-person statement ("Zorblax 的首都是 Quuxville。") teaches memory a
    fact, but it is not the user talking about themselves — the first-person
    acknowledgment above does not cover it, and without this the native path
    answered it with an unrelated canned line (measured 2026-11-02: the fact
    was stored, then the reply was a weather template).
    """
    try:
        from ai.memory.taught_facts import get_taught_facts

        return get_taught_facts().learned_from(statement)
    except Exception as exc:  # pragma: no cover - optional store
        logger.debug("taught-facts check unavailable: %s", exc)
        return False


# The questions that ask for *the user's* name. "我的貓叫什麼" also contains
# 叫什麼 but asks about the cat, so the pattern requires 名字／姓名 (or the
# English "my name"): the name lookup must not answer the cat with the user.
_NAME_QUESTION = re.compile(
    r"名字|姓名|我叫什麼|我叫甚麼|my name|what.*name|called me", re.IGNORECASE
)


# The separators of a combined question ("我叫什麼名字、還有我住哪裡？").
_CLAUSE_SPLIT = re.compile(r"[、,，]|還有|以及|而且|跟|和(?![和])")


def _recall_clauses(question: str) -> List[str]:
    """The question's clauses (a combined question asks several facts)."""
    parts = [part.strip() for part in _CLAUSE_SPLIT.split(question or "")]
    clauses = [part for part in parts if len(part) >= 2]
    return clauses or [question or ""]


# The keyword index matches *any* keyword (OR), and the CJK attribute words
# are single characters, so the net has to be wide: the pool is ranked by
# attribute coverage afterwards, and a narrow limit would let a common word
# ("喜歡") push the statement that actually answers the question out of it.
_RECALL_POOL_LIMIT = 64

# How much of the question's information weight an answer has to carry. Half
# is the line between "this statement is about what was asked" and "this
# statement merely shares a character with the question".
_RECALL_COVERAGE = 0.5


def _attribute_coverage(statements: List[str], query_words: List[str]) -> List[float]:
    """The share of the question's information weight each statement carries.

    A statement answers a recall question only if it carries the attribute the
    question names — and "carries" cannot mean "shares one character": 叫／
    天／色 appear in most self-statements, so a weak match is how "我剛才說我
    的貓叫什麼？" came back as the *dog*, and "我的生日是哪天？" as "我今天用
    紅色背包".

    Each attribute word is therefore weighted by how rare it is **in the
    candidate pool** (idf). The rare words are the ones that pick a statement
    out; a statement that only carries the common ones covers little. Words
    that appear nowhere in the pool keep the largest weight — a question about
    something nobody said cannot be answered by something else.
    """
    total_statements = len(statements)
    documents = [(statement or "").lower() for statement in statements]
    weights: Dict[str, float] = {}
    for word in query_words:
        if word in weights:
            continue
        occurrences = sum(1 for document in documents if word in document)
        weights[word] = math.log((total_statements + 1) / (occurrences + 0.5))
    total = sum(weights.values())
    if total <= 0:
        return [0.0] * total_statements
    return [
        sum(weight for word, weight in weights.items() if word in document) / total
        for document in documents
    ]


def _semantic_match(statements: List[str], query_words: set) -> Optional[str]:
    """The statement that carries the attribute the question asks about.

    A recall question names *what* it wants ("我幾歲", "我住哪裡"). The answer
    must be a statement that carries that attribute; among statements that
    carry it equally well, the **most recent** wins — "剛才說" is deictic,
    it points at the last thing said.

    The previous order — encoder similarity first, overlap as a bonus — is
    how "我剛才說我幾歲？" came back as an unrelated sentence that merely
    started with "我剛". A pronoun is not an attribute: two statements that
    share only 我/你 are not about the same thing.
    """
    if not statements or not query_words:
        return None
    coverages = _attribute_coverage(statements, list(query_words))
    best = max(coverages)
    if best < _RECALL_COVERAGE:
        # Nothing carries the asked-about attribute: a wrong answer dressed as
        # a memory is worse than an honest "I don't know".
        return None
    for index, coverage in enumerate(coverages):
        if coverage >= best - 1e-9:
            # ``statements`` is ordered most-recent-first, so the first
            # maximum is the last thing the user said.
            return statements[index]
    return None


# The meta-question prefix ("我剛才說…", "我剛剛說過…") is about the act of
# speaking, not about the attribute being asked for.
_RECALL_META = re.compile(
    r"^(?:我|你)?(?:剛才|剛剛|之前|先前|早先|前面)?(?:有)?(?:說|講|提)(?:過)?"
)
_EN_ATTRIBUTE_STOP = {
    "what",
    "when",
    "where",
    "which",
    "who",
    "whom",
    "how",
    "did",
    "does",
    "say",
    "said",
    "tell",
    "told",
    "you",
    "your",
    "the",
    "and",
    "for",
    "about",
    "that",
    "this",
    "was",
    "were",
    "are",
    "earlier",
    "before",
    "again",
    "just",
    "now",
    "have",
    "had",
}


# The interrogative phrases are the *shape* of the ask, not its subject:
# "我住哪裡" asks about 住, "我幾點起床" about 起床, "我的生日是哪天" about 生日.
# Stripping the phrase (not just its characters) keeps the content around it
# intact — a char-level stop would turn "哪種球類" into 種球類.
_INTERROGATIVE_PHRASE = re.compile(
    r"什麼時候|什麼時間|甚麼時候|哪一天|哪個|哪一種|哪種|哪裡|哪兒|哪里|"
    r"怎麼|如何|為什麼|為何|多少|什麼|甚麼|誰|幾|哪天|哪年|哪"
)
# The words that shape the ask instead of naming its subject.
_ATTRIBUTE_STOP = set("的得了是有會要想在去過來個這那我你他她牠它嗎呢吧啊喔哦嘛呀咧裡裏")


def _attribute_words(question: str) -> List[str]:
    """The words that name *what* the question asks about ("我住哪裡" → 住).

    The recall question is a meta-question: strip the "我剛才說" prefix, the
    pronoun and the interrogative phrase, and what is left is the attribute
    ("住哪裡" → 住, "幾歲" → 歲, "叫什麼名字" → 叫／名／字). Matching on the
    attribute is what stops a statement that merely shares a pronoun from
    winning.
    """
    text = _RECALL_META.sub("", (question or "").strip())
    text = re.sub(r"^(?:我的|我|你的|你)\s*", "", text)
    text = _INTERROGATIVE_PHRASE.sub("", text)
    words: List[str] = []
    for word in re.findall(r"[A-Za-z]{3,}", text):
        lowered = word.lower()
        if lowered not in _EN_ATTRIBUTE_STOP:
            words.append(lowered)
    for char in re.findall(r"[\u4e00-\u9fff]", text):
        if char not in _ATTRIBUTE_STOP:
            words.append(char)
    return words


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

    async def _recall_candidates(self, question: str, manager: Any) -> List[str]:
        """The conversation statements worth answering from.

        Two retrievers, in this order:

        1. The attribute lookup. A recall question names what it wants
           ("我幾歲" → 歲, "我在做什麼產品" → 產品), so ask the keyword index
           for recent statements that carry it.
        2. The vector store's semantic search, for a paraphrase that shares no
           word with the question ("我幾歲" vs "我今年三十五歲").

        The semantic search alone is not enough, and not because of its
        ranking quality: the *other questions* look exactly like this one, so
        the top-k fills up with them, and they are then dropped ("a question
        the user asked is not a statement") — the fact never reaches the pool.
        That is how a stored fact was answered with an unrelated sentence.
        """
        candidates: List[str] = []

        attribute_words = _attribute_words(question) or _recall_keywords(question)
        if attribute_words:
            try:
                memories = await manager.query_core_memory(
                    keywords=attribute_words,
                    data_type_filter="conversation",
                    limit=_RECALL_POOL_LIMIT,
                )
                for memory in memories:
                    content = getattr(memory, "content", None)
                    if isinstance(content, dict):
                        candidates.append(str(content.get("user") or ""))
                    else:
                        candidates.append(str(content or ""))
            except Exception as exc:
                logger.debug("attribute recall query failed: %s", exc)

        try:
            from ai.memory.vector_store import get_vector_store

            store = get_vector_store()
            if store is not None:
                results = await store.semantic_search(question, 12)
                documents = (results.get("documents") or [[]])[0]
                for document in documents:
                    text = str(document or "")
                    if not text:
                        continue
                    user_part = text.split("\n", 1)[0]
                    if user_part.lower().startswith("user:"):
                        user_part = user_part.split(":", 1)[1].strip()
                    if user_part:
                        candidates.append(user_part)
        except Exception as exc:
            logger.debug("vector recall query failed: %s", exc)

        seen: set = set()
        unique: List[str] = []
        for candidate in candidates:
            if candidate and candidate not in seen:
                seen.add(candidate)
                unique.append(candidate)
        return unique

    async def try_teaching_ack(self, user_message: str) -> Optional["LLMResponse"]:
        """Acknowledge a fact the user just told us.

        Without this the native path answers every statement with the same
        greeting (the QA-machine shape). The acknowledgment quotes the user's
        own words, so it is honest and it is not a canned line.

        It is still a *surface* line, so it never pre-empts a backend that can
        actually generate: with a real LLM registered the user gets a real
        reply, and this frame stays what it is — the native path's fallback.
        """
        fact = (user_message or "").strip()
        if not _is_teaching_statement(fact) and not _taught_this_turn(fact):
            return None
        if _has_generative_backend(self._svc):
            return None
        from core.interfaces.protocols import ChatResponse

        value = _statement_value(fact)
        if value:
            text = f"記住囉，{value}！"
        elif re.search(r"[\u4e00-\u9fff]", fact):
            text = "記住囉！"
        else:
            text = "Got it — I'll remember that."
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

        statements: List[str] = []
        normalized_query = " ".join(re.findall(r"\w+", user_message or ""))
        for user_text in await self._recall_candidates(user_message, manager):
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
        # one about 住, not the one about 名字) is chosen per clause below;
        # a statement that does not carry the asked-about attribute is not an
        # answer, and quoting it would be a wrong answer dressed as a memory.

        # A combined question asks several facts ("我剛才說我叫什麼名字、還有我
        # 住哪裡？") — the answer must carry *all* of them, not just the first.
        clauses = _recall_clauses(user_message)
        answers: List[str] = []
        for clause in clauses:
            clause_words = set(_attribute_words(clause))
            best_statement: Optional[str] = None
            if _NAME_QUESTION.search(clause):
                # A name question is answered by the statement that states a
                # name ("我叫小明"), not by one that merely shares 叫.
                for candidate in statements:
                    if _statement_name(candidate):
                        best_statement = candidate
                        break
            if best_statement is None:
                best_statement = _semantic_match(statements, clause_words)
            if best_statement is None:
                continue
            name = _statement_name(best_statement)
            if name and _NAME_QUESTION.search(clause):
                answers.append(f"你叫{name}" if language == "zh" else f"your name is {name}")
            else:
                answers.append(
                    f"「{best_statement[:120]}」"
                    if language == "zh"
                    else f'"{best_statement[:120]}"'
                )
        if not answers:
            return None

        if len(answers) == 1:
            # A single fact: the name gets its own sentence, a quote is
            # introduced ("你剛才說過：…").
            only = answers[0]
            if language == "zh":
                text = only if only.startswith("你叫") else f"你剛才說過：{only}"
            else:
                text = only if only.startswith("your name") else f"You said earlier: {only}"
            confidence = 0.85 if only.startswith("你叫") or only.startswith("your name") else 0.65
        else:
            joined = "、".join(answers) if language == "zh" else ", ".join(answers)
            text = f"你剛才說過：{joined}" if language == "zh" else f"You said earlier: {joined}"
            confidence = 0.75
        return ChatResponse(
            text=text,
            backend="memory-recall",
            model="conversation-recall",
            confidence=confidence,
            hit_score=confidence,
            hit_source="memory",
            route="MEMORY",
            metadata={"memory_hit": True, "recall": "multi" if len(answers) > 1 else "single"},
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
