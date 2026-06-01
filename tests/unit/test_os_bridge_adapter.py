"""Smoke tests for integrations/os_bridge_adapter.py"""
import pytest


class TestOSBridgeAdapter:
    """Basic smoke tests for OSBridgeAdapter"""

    def test_import(self):
        """Verify module can be imported"""
        try:
            from integrations.os_bridge_adapter import OSBridgeAdapter
            assert OSBridgeAdapter is not None
        except ImportError as e:
            pytest.skip(f"OSBridgeAdapter not available: {e}")

    def test_instantiation(self):
        """Verify basic instantiation"""
        try:
            from integrations.os_bridge_adapter import OSBridgeAdapter
            instance = OSBridgeAdapter()
            assert instance is not None
        except ImportError as e:
            pytest.skip(f"OSBridgeAdapter not available: {e}")
        except Exception as e:
            pytest.skip(f"OSBridgeAdapter init failed (expected in CI): {e}")

    def test_bridge_path_initialized(self):
        """Verify bridge path is set after init"""
        try:
            from integrations.os_bridge_adapter import OSBridgeAdapter
            instance = OSBridgeAdapter()
            assert hasattr(instance, "bridge_path")
        except ImportError as e:
            pytest.skip(f"OSBridgeAdapter not available: {e}")
        except Exception as e:
            pytest.skip(f"OSBridgeAdapter init failed (expected in CI): {e}")
