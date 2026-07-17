"""
Regression tests for MemoryIntegration.try_memory_retrieval.

Guards against a bug where conversation/interaction logs stored in the shared
`templates` bucket (via store_experience(data_type="conversation")) were
returned as answer templates, leaking raw interaction records such as
'{"user": ..., "assistant": ...}' instead of a real answer.
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [β] [A] [L0]
# =============================================================================

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apps", "backend", "src"))

from services.llm.memory_integration import MemoryIntegration


class _FakeMemoryManager:
    """Minimal stand-in exposing retrieve_response_templates."""

    def __init__(self, entries):
        self._entries = entries

    async def retrieve_response_templates(self, query="", limit=5, min_score=0.3):
        scored = []
        for e in self._entries:
            # Mirror ham_manager scoring: keyword substring match => 0.9
            for kw in e.get("keywords", []):
                if kw and kw.lower() in query.lower():
                    scored.append((e, 0.9))
                    break
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:limit]


class _FakeService:
    def __init__(self, manager):
        self.memory_manager = manager


def _make_integration(entries):
    return MemoryIntegration(_FakeService(_FakeMemoryManager(entries)))


def test_conversation_log_not_returned_as_answer():
    """A stored conversation/interaction record must NOT be returned as a response."""
    entries = [{
        "content": "{'user': 'what is the opposite of hot', 'assistant': 'cold'}",
        "data_type": "conversation",
        "keywords": ["hot", "opposite"],
    }]
    mi = _make_integration(entries)
    result = asyncio.run(mi.try_memory_retrieval("what is the opposite of hot", {}))
    assert result is None, "conversation log must not leak as an answer template"


def test_genuine_template_still_returned():
    """A real answer template (data_type != conversation) is still usable."""
    entries = [{
        "content": "The opposite of hot is cold.",
        "data_type": "response_template",
        "keywords": ["hot", "opposite"],
    }]
    mi = _make_integration(entries)
    result = asyncio.run(mi.try_memory_retrieval("what is the opposite of hot", {}))
    assert result is not None
    assert result.text == "The opposite of hot is cold."
    assert result.route == "MEMORY"


def test_dict_content_not_returned():
    """Even a non-conversation entry whose content is a dict must not leak."""
    entries = [{
        "content": {"user": "x", "assistant": "y"},
        "data_type": "answer",
        "keywords": ["x"],
    }]
    mi = _make_integration(entries)
    result = asyncio.run(mi.try_memory_retrieval("x", {}))
    assert result is None
