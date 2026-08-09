# =============================================================================
# ANGELA-MATRIX: [L1-L6] [αβγδεθζη] [A] [L2+]
# =============================================================================

"""記憶登錄器測試（§11.3 #2 步驟 B7 — backbone.memory('ham') 統一單例）。"""

import pytest
from core.backbone.memory import MemoryRegistry


class _FakeMemory:
    def __init__(self, tag=None):
        self.tag = tag
        self.ops = []

    def store(self, x):
        self.ops.append(x)


@pytest.fixture
def registry():
    return MemoryRegistry()


class TestMemoryRegistry:
    def test_register_class_lazy_singleton(self):
        registry = MemoryRegistry()
        registry.register("ham", _FakeMemory)
        first = registry.get("ham")
        second = registry.get("ham")
        assert isinstance(first, _FakeMemory)
        assert first is second  # 單例

    def test_register_instance_direct(self):
        registry = MemoryRegistry()
        mem = _FakeMemory("a")
        registry.register("custom", mem)
        assert registry.get("custom") is mem

    def test_register_factory_new_each_time(self):
        registry = MemoryRegistry()
        registry.register_factory("stream", lambda: _FakeMemory())
        first = registry.get("stream")
        second = registry.get("stream")
        assert first is not second

    def test_ham_default_auto_register(self):
        registry = MemoryRegistry()
        ham = registry.get("ham")
        assert ham is not None
        # 再次取得同一實例
        assert registry.get("ham") is ham

    def test_unregister(self):
        registry = MemoryRegistry()
        registry.register("ham", _FakeMemory)
        assert registry.unregister("ham")
        assert not registry.has("ham")
        assert not registry.unregister("ham")

    def test_names_and_has(self):
        registry = MemoryRegistry()
        registry.register("ham", _FakeMemory)
        registry.register("custom", _FakeMemory())
        names = registry.names()
        assert "ham" in names and "custom" in names
        assert registry.has("ham")
        assert registry.has("CUSTOM")  # 大小寫正規化
        assert not registry.has("missing")

    def test_clear(self):
        registry = MemoryRegistry()
        registry.register("ham", _FakeMemory)
        registry.get("ham")
        registry.clear()
        assert registry.names() == []

    def test_unknown_memory_returns_none(self):
        registry = MemoryRegistry()
        assert registry.get("nope") is None


class TestBackboneMemory:
    def test_backbone_memory_unified_singleton(self):
        from core.backbone import get_backbone, reset_backbone

        reset_backbone()
        bb = get_backbone()
        first = bb.memory("ham")
        second = bb.memory("ham")
        assert first is second  # 統一單例，不分片
        reset_backbone()

    def test_backbone_register_memory(self):
        from core.backbone import get_backbone, reset_backbone

        reset_backbone()
        bb = get_backbone()
        mem = _FakeMemory("x")
        assert bb.register_memory("custom", mem)
        assert bb.memory("custom") is mem
        assert "custom" in bb.memories.names()
        reset_backbone()
