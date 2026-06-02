"""Tests for MetabolicHeartbeat"""
import pytest


class TestMetabolicHeartbeat:
    """Tests for MetabolicHeartbeat"""

    def test_import(self):
        from core.life.heartbeat import MetabolicHeartbeat
        assert MetabolicHeartbeat is not None

    def test_instantiation(self):
        from core.life.heartbeat import MetabolicHeartbeat
        instance = MetabolicHeartbeat(update_interval=60.0)
        assert instance is not None
        assert instance.update_interval == 60.0
        assert instance._running is False

    def test_instantiation_default_interval(self):
        from core.life.heartbeat import MetabolicHeartbeat
        instance = MetabolicHeartbeat()
        assert instance.update_interval == 30.0

    def test_initial_position(self):
        from core.life.heartbeat import MetabolicHeartbeat
        instance = MetabolicHeartbeat()
        assert instance.x == 200.0
        assert instance.y == 0.0
        assert instance.screen_w == 1920
