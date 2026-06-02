"""Tests for HotReloadService"""
import pytest


class TestHotReloadService:
    """Tests for HotReloadService"""

    def test_import(self):
        from services.hot_reload_service import HotReloadService
        assert HotReloadService is not None

    def test_instantiation(self):
        from services.hot_reload_service import HotReloadService
        instance = HotReloadService()
        assert instance is not None
        assert instance._draining is False

    @pytest.mark.asyncio
    async def test_begin_draining(self):
        from services.hot_reload_service import HotReloadService
        instance = HotReloadService()
        result = await instance.begin_draining()
        assert result["draining"] is True
        assert instance._draining is True

    @pytest.mark.asyncio
    async def test_end_draining(self):
        from services.hot_reload_service import HotReloadService
        instance = HotReloadService()
        await instance.begin_draining()
        result = await instance.end_draining()
        assert result["draining"] is False
        assert instance._draining is False

    @pytest.mark.asyncio
    async def test_status(self):
        from services.hot_reload_service import HotReloadService
        instance = HotReloadService()
        status = await instance.status()
        assert isinstance(status, dict)
        assert "status" in status
