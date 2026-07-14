"""Tests for the grounded knowledge store (no network)."""

import os
import tempfile

import pytest

from ai.memory.grounded_knowledge import (
    GroundedClaim,
    GroundedKnowledgeStore,
    SourceRef,
    VerificationStatus,
    claim_key,
)


def test_add_or_update_dedupes_normalized_text():
    store = GroundedKnowledgeStore()
    c1 = store.add_or_update("The speed of light is 299792458 m/s")
    c2 = store.add_or_update("the speed of light is 299792458 m/s.")  # same, normalized
    assert store.count() == 1
    assert c1.claim_key == c2.claim_key
    assert c1.status == VerificationStatus.UNVERIFIED


def test_record_verification_transitions_state_and_counts():
    store = GroundedKnowledgeStore()
    c = store.add_or_update("Water is H2O")
    assert store.stats()["unverified"] == 1

    src = SourceRef(url="https://en.wikipedia.org/wiki/Water", title="Water")
    store.record_verification(c.claim_key, VerificationStatus.VERIFIED, [src], 0.8)
    updated = store.get(c.claim_key)
    assert updated.status == VerificationStatus.VERIFIED
    assert updated.confidence == 0.8
    assert updated.verify_count == 1
    assert len(updated.sources) == 1
    assert store.stats()["verified"] == 1

    store.record_verification(c.claim_key, VerificationStatus.CONTRADICTED, [src], 0.5)
    updated = store.get(c.claim_key)
    assert updated.status == VerificationStatus.CONTRADICTED
    assert updated.contradict_count == 1
    # sources are merged, not duplicated
    assert len(updated.sources) == 1


def test_find_related_and_verified_for():
    store = GroundedKnowledgeStore()
    a = store.add_or_update("The speed of light is 299792458 m/s")
    b = store.add_or_update("Water has the chemical formula H2O")
    store.record_verification(a.claim_key, VerificationStatus.VERIFIED, confidence=0.9)
    # b stays unverified

    related = store.find_related("speed of light")
    keys = {c.claim_key for c in related}
    assert a.claim_key in keys

    verified = store.verified_for("speed of light")
    assert all(c.status == VerificationStatus.VERIFIED for c in verified)
    assert a.claim_key in {c.claim_key for c in verified}
    # unverified b must not appear in verified_for
    assert b.claim_key not in {c.claim_key for c in verified}


def test_confidence_clamped():
    store = GroundedKnowledgeStore()
    c = store.add_or_update("X")
    store.record_verification(c.claim_key, VerificationStatus.VERIFIED, confidence=5.0)
    assert store.get(c.claim_key).confidence == 1.0


def test_save_and_load_roundtrip():
    store = GroundedKnowledgeStore()
    c = store.add_or_update("Gold has atomic number 79")
    store.record_verification(c.claim_key, VerificationStatus.VERIFIED,
                              [SourceRef(url="https://example.com/gold")], 0.7)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "gk.json")
        store.save(path)
        assert os.path.exists(path)

        store2 = GroundedKnowledgeStore()
        n = store2.load(path)
        assert n == 1
        loaded = store2.get(c.claim_key)
        assert loaded is not None
        assert loaded.status == VerificationStatus.VERIFIED
        assert loaded.confidence == 0.7
        assert loaded.sources[0].url == "https://example.com/gold"
