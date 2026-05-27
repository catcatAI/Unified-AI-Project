"""C4 — SystemManager unit tests"""

import pytest


class TestSystemManager:

    def setup_method(self):
        from core.managers.system_manager import SystemManager
        self.mgr = SystemManager()

    def test_initial_state_not_initialized(self):
        assert not self.mgr.initialized
        assert self.mgr.components == {}

    def test_initialize_sets_flag(self):
        import asyncio
        asyncio.run(self.mgr.initialize())
        assert self.mgr.initialized

    def test_get_status_stopped_before_init(self):
        status = self.mgr.get_status()
        assert status["initialized"] is False
        assert status["status"] == "stopped"
        assert status["components"] == []

    def test_get_status_running_after_init(self):
        import asyncio
        asyncio.run(self.mgr.initialize())
        status = self.mgr.get_status()
        assert status["initialized"] is True
        assert status["status"] == "running"

    def test_register_component(self):
        mock = {"name": "logger"}
        self.mgr.register_component("logger", mock)
        assert self.mgr.components["logger"] == mock

    def test_get_status_shows_registered_components(self):
        self.mgr.register_component("db", object())
        self.mgr.register_component("cache", object())
        status = self.mgr.get_status()
        assert "db" in status["components"]
        assert "cache" in status["components"]
        assert status["component_count"] == 2

    def test_shutdown_resets_initialized(self):
        import asyncio
        asyncio.run(self.mgr.initialize())
        asyncio.run(self.mgr.shutdown())
        assert not self.mgr.initialized

    def test_shutdown_clears_components(self):
        import asyncio
        self.mgr.register_component("svc", object())
        asyncio.run(self.mgr.shutdown())
        assert not self.mgr.initialized

    def test_shutdown_with_shutdown_method(self):
        import asyncio
        class ShutdownMock:
            def __init__(self):
                self.shutdown_called = False
            async def shutdown(self):
                self.shutdown_called = True
        mock = ShutdownMock()
        self.mgr.register_component("mock", mock)
        asyncio.run(self.mgr.shutdown())
        assert mock.shutdown_called

    def test_shutdown_with_component_error_does_not_raise(self):
        import asyncio
        class FailingComponent:
            async def shutdown(self):
                raise RuntimeError("shutdown failed")
        self.mgr.register_component("failing", FailingComponent())
        asyncio.run(self.mgr.shutdown())  # should not raise
        assert not self.mgr.initialized
