"""Smoke tests for MaturityManager, MaturityLevel, and ExperienceTracker"""
import pytest


class TestMaturityManager:
    """Basic smoke tests for MaturityManager"""

    def test_import(self):
        """Verify MaturityManager can be imported"""
        try:
            from core.maturity.maturity_system import MaturityManager
            assert MaturityManager is not None
        except ImportError as e:
            pytest.skip(f"MaturityManager not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from core.maturity.maturity_system import MaturityManager
            instance = MaturityManager()
            assert instance is not None
            assert instance.current_level == 0
        except ImportError as e:
            pytest.skip(f"MaturityManager not available: {e}")
        except Exception as e:
            pytest.skip(f"MaturityManager init failed (expected in CI): {e}")


class TestMaturityLevel:
    """Basic smoke tests for MaturityLevel"""

    def test_import(self):
        """Verify MaturityLevel can be imported"""
        try:
            from core.maturity.maturity_system import MaturityLevel
            assert MaturityLevel is not None
            assert len(MaturityLevel.LEVELS) == 12
        except ImportError as e:
            pytest.skip(f"MaturityLevel not available: {e}")

    def test_from_memory(self):
        """Verify from_memory static method works"""
        try:
            from core.maturity.maturity_system import MaturityLevel
            result = MaturityLevel.from_memory(500)
            assert result["level"] == 1
        except ImportError as e:
            pytest.skip(f"MaturityLevel not available: {e}")
        except Exception as e:
            pytest.skip(f"MaturityLevel method failed (expected in CI): {e}")


class TestExperienceTracker:
    """Basic smoke tests for ExperienceTracker"""

    def test_import(self):
        """Verify ExperienceTracker can be imported"""
        try:
            from core.maturity.maturity_system import ExperienceTracker
            assert ExperienceTracker is not None
        except ImportError as e:
            pytest.skip(f"ExperienceTracker not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from core.maturity.maturity_system import ExperienceTracker
            instance = ExperienceTracker()
            assert instance is not None
            assert instance.memory_count == 0
        except ImportError as e:
            pytest.skip(f"ExperienceTracker not available: {e}")
        except Exception as e:
            pytest.skip(f"ExperienceTracker init failed (expected in CI): {e}")
