"""Tests for the knowledge verifier (offline fake search backend)."""

import pytest

from ai.meta.knowledge_verifier import (
    KnowledgeVerifier,
    VerificationResult,
    heuristic_assess,
)
from ai.memory.grounded_knowledge import VerificationStatus


class FakeSearchTool:
    """Configurable offline search backend for tests."""

    def __init__(self, results=None, call_count=None):
        self._results = results if results is not None else []
        self.call_count = call_count if call_count is not None else {"n": 0}

    def search(self, query, num_results=5):
        self.call_count["n"] += 1
        return self._results


SUPPORT = [
    {"title": "Speed of light", "url": "https://en.wikipedia.org/wiki/Speed_of_light",
     "snippet": "The speed of light in vacuum is exactly 299792458 m/s."},
]
CONTRADICT = [
    {"title": "Flat Earth debunked", "url": "https://example.com/flat",
     "snippet": "The Earth is not flat. That claim is false and debunked."},
]
EMPTY = []


async def test_verify_returns_verified_when_sources_support():
    tool = FakeSearchTool(SUPPORT)
    v = KnowledgeVerifier(search_tool=tool)
    res = await v.verify("The speed of light is 299792458 m/s")
    assert isinstance(res, VerificationResult)
    assert res.status == VerificationStatus.VERIFIED
    assert res.confidence > 0.0
    assert len(res.sources) == 1


async def test_verify_returns_contradicted_when_sources_negate():
    tool = FakeSearchTool(CONTRADICT)
    v = KnowledgeVerifier(search_tool=tool)
    res = await v.verify("The Earth is flat")
    assert res.status == VerificationStatus.CONTRADICTED
    assert res.confidence > 0.0


async def test_verify_returns_unverified_when_insufficient():
    tool = FakeSearchTool(EMPTY)
    v = KnowledgeVerifier(search_tool=tool)
    res = await v.verify("The speed of light is 299792458 m/s")
    assert res.status == VerificationStatus.UNVERIFIED


async def test_verify_skips_error_results():
    tool = FakeSearchTool([{"error": "timeout"}])
    v = KnowledgeVerifier(search_tool=tool)
    res = await v.verify("Some claim about the moon")
    assert res.status == VerificationStatus.UNVERIFIED


async def test_verify_caches_and_avoids_second_search():
    calls = {"n": 0}
    tool = FakeSearchTool(SUPPORT, calls)
    v = KnowledgeVerifier(search_tool=tool)
    await v.verify("The speed of light is 299792458 m/s")
    await v.verify("The speed of light is 299792458 m/s")
    assert calls["n"] == 1  # cached, search not called again


def test_heuristic_assess_directly():
    status, conf = heuristic_assess(
        "The speed of light is 299792458 m/s", SUPPORT
    )
    assert status == VerificationStatus.VERIFIED
    status2, _ = heuristic_assess("The Earth is flat", CONTRADICT)
    assert status2 == VerificationStatus.CONTRADICTED
    status3, _ = heuristic_assess("The moon is made of cheese", EMPTY)
    assert status3 == VerificationStatus.UNVERIFIED
