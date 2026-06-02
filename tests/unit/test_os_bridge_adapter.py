"""Tests for integrations/os_bridge_adapter.py"""
import pytest


class TestOSBridgeAdapter:
    """Tests for OSBridgeAdapter"""

    def test_import(self):
        from integrations.os_bridge_adapter import OSBridgeAdapter
        assert OSBridgeAdapter is not None

    def test_instantiation(self):
        from integrations.os_bridge_adapter import OSBridgeAdapter
        instance = OSBridgeAdapter()
        assert instance is not None
        assert instance.bridge_path is not None
        assert "gemini-os-bridge" in instance.bridge_path

    def test_bridge_path_initialized(self):
        from integrations.os_bridge_adapter import OSBridgeAdapter
        instance = OSBridgeAdapter()
        assert hasattr(instance, "bridge_path")
        assert isinstance(instance.bridge_path, str)
        assert instance.bridge_path.endswith(".py")

    def test_python_exe_set(self):
        from integrations.os_bridge_adapter import OSBridgeAdapter
        instance = OSBridgeAdapter()
        assert instance.python_exe is not None
        assert len(instance.python_exe) > 0

    def test_execute_async_returns_error_on_no_bridge(self):
        import pytest
        from integrations.os_bridge_adapter import OSBridgeAdapter
        instance = OSBridgeAdapter()
        import asyncio
        result = asyncio.run(instance._execute_async("summary"))
        assert isinstance(result, dict)
        assert "status" in result or "error" in result
