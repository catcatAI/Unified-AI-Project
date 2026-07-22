import pytest

pytest.importorskip("core.managers.system_manager")
from core.managers.system_manager import SystemManager


class TestSystemLevelIntegration:
    @pytest.mark.asyncio
    async def test_system_manager_instantiation(self):
        manager = SystemManager()
        assert manager is not None
        assert manager.initialized is False

    @pytest.mark.asyncio
    async def test_system_manager_status(self):
        manager = SystemManager()
        status = manager.get_status()
        assert status is not None
        assert status["initialized"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
