"""Tests for SystemManager"""
import pytest


class TestSystemManager:
    """Tests for SystemManager"""

    def test_import(self):
        from core.managers.system_manager import SystemManager
        assert SystemManager is not None

    def test_instantiation(self):
        from core.managers.system_manager import SystemManager
        instance = SystemManager()
        assert instance is not None
        assert instance.initialized is False
        assert instance.components == {}

    @pytest.mark.asyncio
    async def test_initialize(self):
        from core.managers.system_manager import SystemManager
        instance = SystemManager()
        assert instance.initialized is False
        await instance.initialize()
        assert instance.initialized is True

    @pytest.mark.asyncio
    async def test_shutdown(self):
        from core.managers.system_manager import SystemManager
        instance = SystemManager()
        await instance.initialize()
        await instance.shutdown()
        assert instance.initialized is False

    def test_register_component(self):
        from core.managers.system_manager import SystemManager
        instance = SystemManager()
        instance.register_component("test", {"key": "value"})
        assert "test" in instance.components
        assert instance.components["test"]["key"] == "value"

    def test_get_status_before_init(self):
        from core.managers.system_manager import SystemManager
        instance = SystemManager()
        status = instance.get_status()
        assert status["initialized"] is False
        assert status["status"] == "stopped"
        assert status["component_count"] == 0

    @pytest.mark.asyncio
    async def test_get_status_after_init(self):
        from core.managers.system_manager import SystemManager
        instance = SystemManager()
        await instance.initialize()
        status = instance.get_status()
        assert status["initialized"] is True
        assert status["status"] == "running"
