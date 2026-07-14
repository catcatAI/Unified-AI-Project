"""Tests for the grounded learning manager (offline)."""

import pytest

from ai.memory.grounded_learning_manager import (
    GroundedLearningManager,
    get_grounded_learning_manager,
)
from ai.memory.grounded_knowledge import VerificationStatus
from ai.meta.knowledge_verifier import KnowledgeVerifier


class FakeSearchTool:
    def __init__(self, results):
        self._results = results

    def search(self, query, num_results=5):
        return self._results


SUPPORT = [
    {"title": "Speed of light", "url": "https://en.wikipedia.org/wiki/Speed_of_light",
     "snippet": "The speed of light in vacuum is exactly 299792458 m/s."},
]


def _manager_with_support():
    store = __import__("ai.memory.grounded_knowledge", fromlist=["GroundedKnowledgeStore"]).GroundedKnowledgeStore()
    verifier = KnowledgeVerifier(search_tool=FakeSearchTool(SUPPORT))
    return GroundedLearningManager(store=store, verifier=verifier)


def test_enqueue_claims_extracts_and_adds():
    mgr = GroundedLearningManager()
    added = mgr.enqueue_claims("The speed of light is 299792458 m/s. How are you?")
    assert len(added) == 1
    assert added[0].status == VerificationStatus.UNVERIFIED
    assert mgr.store.count() == 1


async def test_verify_claim_records_outcome():
    mgr = _manager_with_support()
    mgr.enqueue_claims("The speed of light is 299792458 m/s")
    pending = [c for c in mgr.store.all() if c.status == VerificationStatus.UNVERIFIED]
    assert pending
    await mgr.verify_claim(pending[0])
    updated = mgr.store.get(pending[0].claim_key)
    assert updated.status == VerificationStatus.VERIFIED
    assert updated.confidence > 0.0


async def test_run_pending_verifications():
    mgr = _manager_with_support()
    mgr.enqueue_claims("The speed of light is 299792458 m/s")
    done = await mgr.run_pending_verifications()
    assert done == 1
    assert mgr.store.stats()["verified"] == 1


def test_get_grounded_context_only_verified():
    mgr = _manager_with_support()
    claim = mgr.enqueue_claims("The speed of light is 299792458 m/s")[0]
    # before verification -> empty
    assert mgr.get_grounded_context("speed of light") == ""
    # simulate verification result applied
    mgr.store.record_verification(
        claim.claim_key, VerificationStatus.VERIFIED,
        [__import__("ai.memory.grounded_knowledge", fromlist=["SourceRef"]).SourceRef(
            url="https://en.wikipedia.org/wiki/Speed_of_light")],
        0.9,
    )
    block = mgr.get_grounded_context("speed of light")
    assert block.startswith("[已查證知識]")
    assert "299792458" in block
    assert "https://en.wikipedia.org/wiki/Speed_of_light" in block


def test_learn_verified_from_search_records_verified():
    mgr = _manager_with_support()
    results = [
        {"title": "Taipei", "url": "https://en.wikipedia.org/wiki/Taipei",
         "snippet": "Capital of Taiwan."},
        {"title": "Other", "url": "https://example.com", "snippet": "x"},
    ]
    claim = mgr.learn_verified_from_search("What is the capital of Taiwan?", results)
    assert claim is not None
    stored = mgr.store.get(claim.claim_key)
    assert stored is not None
    assert stored.status == VerificationStatus.VERIFIED
    assert stored.confidence > 0.5
    block = mgr.get_grounded_context("What is the capital of Taiwan?")
    assert "Taipei" in block


def test_learn_verified_from_search_skips_errors():
    mgr = GroundedLearningManager()
    result = mgr.learn_verified_from_search("nonsense query?", [{"error": "no results"}])
    assert result is None
    assert mgr.store.count() == 0


def test_persistence_roundtrip(tmp_path):
    path = str(tmp_path / "gk.json")
    mgr = GroundedLearningManager(data_path=path)
    results = [{"title": "Taipei", "url": "https://en.wikipedia.org/wiki/Taipei",
                "snippet": "Capital of Taiwan."}]
    mgr.learn_verified_from_search("What is the capital of Taiwan?", results)
    # reload from a fresh manager on the same path
    mgr2 = GroundedLearningManager(data_path=path)
    loaded = mgr2.load()
    assert loaded == 1
    block = mgr2.get_grounded_context("capital of Taiwan")
    assert "Taipei" in block


async def test_queue_claims_runs_background_verification():
    mgr = _manager_with_support()
    # queue_claims schedules asyncio tasks; run them to completion
    await mgr.queue_claims("The speed of light is 299792458 m/s.", "Thanks!")
    # allow background tasks to finish
    import asyncio
    for _ in range(20):
        if mgr.store.stats()["verified"] >= 1:
            break
        await asyncio.sleep(0.01)
    assert mgr.store.stats()["verified"] == 1


def test_singleton_factory():
    a = get_grounded_learning_manager()
    b = get_grounded_learning_manager()
    assert a is b
