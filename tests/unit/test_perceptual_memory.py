"""Smoke tests for PerceptualMemory"""
import pytest
pytest.importorskip("core.perception.perceptual_memory")


class TestPerceptualMemory:
    """Basic smoke tests for PerceptualMemory"""

    def test_import(self):
        from core.perception.perceptual_memory import PerceptualMemory
        assert PerceptualMemory is not None

    def test_instantiation_with_capacity(self):
        from core.perception.perceptual_memory import PerceptualMemory
        instance = PerceptualMemory(capacity=100)
        assert instance is not None
        assert instance.capacity == 100
        assert len(instance.objects) == 0

    def test_perceived_object_import(self):
        from core.perception.perceptual_memory import PerceivedObject
        obj = PerceivedObject()
        assert obj is not None
        assert obj.name == "unknown"

    def test_add_or_update_object(self):
        from core.perception.perceptual_memory import PerceptualMemory
        instance = PerceptualMemory(capacity=10)
        obj = instance.add_or_update({"label": "test_obj", "features": [0.1, 0.2]})
        assert obj is not None

    def test_get_by_label(self):
        from core.perception.perceptual_memory import PerceptualMemory
        instance = PerceptualMemory(capacity=10)
        instance.add_or_update({"label": "obj_a", "features": [1.0, 0.0]})
        retrieved = instance.get_by_label("obj_a")
        assert len(retrieved) > 0
