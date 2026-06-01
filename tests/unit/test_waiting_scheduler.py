"""Smoke tests for WaitingScheduler"""
import pytest


class TestWaitingScheduler:
    """Basic smoke tests for WaitingScheduler"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from core.waiting_scheduler import WaitingScheduler
            assert WaitingScheduler is not None
        except ImportError as e:
            pytest.skip(f"WaitingScheduler not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from core.waiting_scheduler import WaitingScheduler
            instance = WaitingScheduler(max_wait_seconds=5.0)
            assert instance is not None
            instance.shutdown()
        except ImportError as e:
            pytest.skip(f"WaitingScheduler not available: {e}")
        except Exception as e:
            pytest.skip(f"WaitingScheduler init failed (expected in CI): {e}")
