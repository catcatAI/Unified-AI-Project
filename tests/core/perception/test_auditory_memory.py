"""Tests for AuditoryMemory."""
import numpy as np
import pytest
from core.perception.auditory_memory import AuditoryMemory, VoiceprintProfile


class TestAuditoryMemory:
    def test_init_default(self):
        am = AuditoryMemory()
        assert am.capacity == 500
        assert am.profiles == {}
        assert am.threshold == 0.75

    def test_init_with_capacity(self):
        am = AuditoryMemory(capacity=10)
        assert am.capacity == 10

    def test_profiles_dict(self):
        am = AuditoryMemory()
        am.profiles["audio_001"] = VoiceprintProfile(embedding=np.zeros(8))
        assert len(am.profiles) == 1

    def test_profiles_isolated(self):
        am1 = AuditoryMemory()
        am2 = AuditoryMemory()
        am1.profiles["a"] = VoiceprintProfile(embedding=np.zeros(8))
        assert "a" not in am2.profiles

    def test_identify_registers_new(self):
        am = AuditoryMemory()
        emb = np.random.randn(16).astype(np.float32)
        prof = am.identify_or_register(emb, metadata={"is_speech": True})
        assert prof is not None
        assert prof.profile_id in am.profiles
        assert prof.label == "speaker"

    def test_get_user_profile(self):
        am = AuditoryMemory()
        emb = np.random.randn(16).astype(np.float32)
        prof = am.identify_or_register(emb, metadata={"is_speech": True})
        # Mark as user-like by label for lookup
        prof.label = "user"
        assert am.get_user_profile() is prof
