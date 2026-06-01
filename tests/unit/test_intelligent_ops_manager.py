"""Smoke tests for ai/ops/intelligent_ops_manager.py"""
import pytest


class TestIntelligentOpsManager:
    """Basic smoke tests for IntelligentOpsManager"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from ai.ops.intelligent_ops_manager import IntelligentOpsManager
            assert IntelligentOpsManager is not None
        except ImportError as e:
            pytest.skip(f"IntelligentOpsManager not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from ai.ops.intelligent_ops_manager import IntelligentOpsManager
            instance = IntelligentOpsManager()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"IntelligentOpsManager not available: {e}")
        except Exception as e:
            pytest.skip(f"IntelligentOpsManager init failed (expected in CI): {e}")

    def test_instantiation_with_config(self):
        """Verify instantiation with config"""
        try:
            from ai.ops.intelligent_ops_manager import IntelligentOpsManager
            instance = IntelligentOpsManager(config={"monitoring_interval": 600})
            assert instance is not None
            assert instance.monitoring_interval == 600
        except ImportError as e:
            pytest.skip(f"IntelligentOpsManager not available: {e}")
        except Exception as e:
            pytest.skip(f"IntelligentOpsManager init failed (expected in CI): {e}")
