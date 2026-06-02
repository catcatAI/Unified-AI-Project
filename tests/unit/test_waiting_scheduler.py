"""Tests for WaitingScheduler"""
import pytest


class TestWaitingScheduler:
    """Tests for WaitingScheduler"""

    def test_import(self):
        from core.waiting_scheduler import WaitingScheduler
        assert WaitingScheduler is not None

    def test_instantiation_and_shutdown(self):
        from core.waiting_scheduler import WaitingScheduler
        instance = WaitingScheduler(max_wait_seconds=5.0)
        assert instance is not None
        assert instance.max_wait_seconds == 5.0
        assert instance.is_alive()
        instance.shutdown()
        assert not instance.is_alive()

    def test_shutdown_idempotent(self):
        from core.waiting_scheduler import WaitingScheduler
        instance = WaitingScheduler(max_wait_seconds=5.0)
        instance.shutdown()
        instance.shutdown()

    def test_clear(self):
        from core.waiting_scheduler import WaitingScheduler
        instance = WaitingScheduler(max_wait_seconds=5.0)
        instance.clear()
        instance.shutdown()

    def test_is_alive_initial_state(self):
        from core.waiting_scheduler import WaitingScheduler
        instance = WaitingScheduler(max_wait_seconds=5.0)
        assert instance.is_alive() is True
        instance.shutdown()
        assert instance.is_alive() is False
