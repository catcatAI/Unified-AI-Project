"""Tests for TactileMemory."""
import pytest
from core.perception.tactile_memory import TactileMemory


class TestTactileMemory:
    def test_init_default(self):
        tm = TactileMemory()
        assert tm.config == {}
        assert tm.memory_store == {}

    def test_init_with_config(self):
        tm = TactileMemory(config={"key": "val"})
        assert tm.config["key"] == "val"

    def test_memory_store_dict(self):
        tm = TactileMemory()
        tm.memory_store["touch_001"] = {"type": "pressure", "value": 0.8}
        assert len(tm.memory_store) == 1

    def test_memory_store_isolated(self):
        tm1 = TactileMemory()
        tm2 = TactileMemory()
        tm1.memory_store["a"] = 1
        assert "a" not in tm2.memory_store
