"""Tests for AuditoryMemory."""
import pytest
from core.perception.auditory_memory import AuditoryMemory


class TestAuditoryMemory:
    def test_init_default(self):
        am = AuditoryMemory()
        assert am.config == {}
        assert am.memory_store == {}

    def test_init_with_config(self):
        am = AuditoryMemory(config={"key": "val"})
        assert am.config["key"] == "val"

    def test_memory_store_dict(self):
        am = AuditoryMemory()
        am.memory_store["audio_001"] = {"type": "frequency", "value": 440.0}
        assert len(am.memory_store) == 1

    def test_memory_store_isolated(self):
        am1 = AuditoryMemory()
        am2 = AuditoryMemory()
        am1.memory_store["a"] = 1
        assert "a" not in am2.memory_store
