"""斷言推理（帶條件與例外）與多重事實組合的測試。

兩件事都屬於「推理層缺的那一級」：
- 斷言題（「X 這句話對嗎？」）要帶著**條件**與**例外**回答——那是「最正確」
  與「近似正確」的差別；
- 多重事實的問題要一次回答**多個**事實，而不是只挑一個。
"""

from __future__ import annotations

import os
import tempfile
from typing import Any, Dict, List

import pytest

# The recall reads the vector store (its path is resolved when the store is
# created) — the test must not touch the user's real memory.
_SANDBOX = tempfile.mkdtemp(prefix="angela-claim-test-")
os.environ["ANGELA_DATA_DIR"] = _SANDBOX
os.environ["VECTOR_STORE_PATH"] = os.path.join(_SANDBOX, "vector_store")


@pytest.fixture(autouse=True)
def _isolate_vector_store():
    """The vector store is a process-wide singleton — point it at the sandbox.

    Its default path is resolved at *import* time, so setting the env var in
    the test is not enough: the store instance itself has to be replaced.
    """
    from ai.memory import vector_store

    previous = vector_store._VECTOR_STORE_SINGLETON
    vector_store._VECTOR_STORE_SINGLETON = vector_store.VectorMemoryStore(
        persist_directory=os.path.join(_SANDBOX, "vector_store")
    )
    try:
        yield
    finally:
        vector_store._VECTOR_STORE_SINGLETON = previous


from ai.reasoning.claims import (
    answer_claim_question,
    find_claim,
    is_claim_question,
    load_claims,
)


# --------------------------------------------------------------------------- #
# The claim library
# --------------------------------------------------------------------------- #
def test_the_claim_library_loads() -> None:
    claims = load_claims()
    assert len(claims) >= 10
    for claim in claims:
        assert claim.statement and claim.condition and claim.exception
        assert claim.keywords


def test_a_claim_question_is_recognised() -> None:
    assert is_claim_question("酒精的沸點是 78°C，這句話對嗎？")
    assert is_claim_question("在台灣開車，血液酒精濃度上限是 0.15%，這項規定正確嗎？")
    assert not is_claim_question("Tell me about the sky's color.")
    assert not is_claim_question("我今天很累")


def test_a_claim_answer_states_the_condition_and_the_exception() -> None:
    answer = answer_claim_question("酒精的沸點是 78°C，這句話對嗎？")
    assert answer is not None
    claim = find_claim("酒精的沸點是 78°C，這句話對嗎？")
    assert claim is not None
    assert claim.condition.split("，")[0] in answer
    assert claim.exception[:6] in answer


def test_an_unknown_claim_has_no_answer() -> None:
    """The library is knowledge, not reasoning: an unknown claim abstains."""
    assert answer_claim_question("水的沸點是 100°C，這句話對嗎？") is None


def test_the_standard_set_topics_are_not_seeded() -> None:
    """The measurement must not teach the implementation.

    The standard set's state items measure the *knowledge* gap; if the
    claim library answered them, the measurement would be circular.
    """
    from ai.response.human_speech import build_standard_set

    seeded = {claim.statement for claim in load_claims()}
    for item in build_standard_set():
        if item.kind != "state":
            continue
        for statement in seeded:
            assert (
                statement not in item.message
            ), f"the standard set's topic {item.message!r} is seeded in the claim library"


# --------------------------------------------------------------------------- #
# The multi-fact combination
# --------------------------------------------------------------------------- #
class _Memory:
    def __init__(self, content: Any) -> None:
        self.content = content
        self.memory_id = "m1"
        self.metadata: Dict[str, Any] = {}
        self.data_type = "conversation"


class _Manager:
    def __init__(self, conversations: List[Dict[str, str]]) -> None:
        self._conversations = conversations

    async def query_core_memory(self, **kwargs: Any) -> List[_Memory]:
        return [_Memory(c) for c in self._conversations]


class _Service:
    def __init__(self, conversations: List[Dict[str, str]]) -> None:
        self.memory_manager = _Manager(conversations)


def _integration(conversations: List[Dict[str, str]]):
    from services.llm.memory_integration import MemoryIntegration

    return MemoryIntegration(_Service(conversations))  # type: ignore[arg-type]


def test_a_combined_question_answers_every_fact() -> None:
    """「我剛才說我叫什麼名字、還有我住哪裡？」→ 兩個都要提到。"""
    integration = _integration(
        [
            {"user": "我叫小明", "assistant": "記住囉！"},
            {"user": "我住在台北", "assistant": "記住囉！"},
        ]
    )
    import asyncio

    response = asyncio.run(
        integration.try_conversation_recall("我剛才說我叫什麼名字、還有我住哪裡？", {})
    )
    assert response is not None
    assert "小明" in response.text
    assert "台北" in response.text


def test_a_single_fact_question_answers_that_fact_only() -> None:
    integration = _integration(
        [
            {"user": "我叫小明", "assistant": "記住囉！"},
            {"user": "我住在台北", "assistant": "記住囉！"},
        ]
    )
    import asyncio

    response = asyncio.run(integration.try_conversation_recall("我剛才說我住哪裡？", {}))
    assert response is not None
    assert "台北" in response.text
    assert "小明" not in response.text


def test_a_question_without_a_matching_fact_is_not_answered() -> None:
    """No content-word match → no answer (a wrong answer dressed as a memory)."""
    integration = _integration([{"user": "我住在台北", "assistant": "記住囉！"}])
    import asyncio

    response = asyncio.run(integration.try_conversation_recall("我剛才說我養的狗叫什麼？", {}))
    assert response is None
