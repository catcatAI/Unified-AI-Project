import pytest
from pathlib import Path
from apps.backend.src.core.system.module_manager import ModuleManager
from apps.backend.src.core.system.module_manager.models import ModuleStatus


@pytest.fixture
def manager():
    return ModuleManager(scan_paths=[Path("non_existent_path_for_testing")])


@pytest.mark.asyncio
async def test_manager_start_empty(manager):
    await manager.start()
    assert manager._started is True
    assert manager.list_modules() == {}


@pytest.mark.asyncio
async def test_manager_stop_empty(manager):
    await manager.start()
    await manager.stop()
    assert manager._started is False
    assert manager.list_modules() == {}


@pytest.mark.asyncio
async def test_manager_has_and_get(manager):
    await manager.start()
    assert manager.has("nonexistent") is False
    assert manager.get_module("nonexistent") is None


@pytest.mark.asyncio
async def test_manager_get_status(manager):
    await manager.start()
    status = manager.get_status("nonexistent")
    assert status is None


@pytest.mark.asyncio
async def test_manager_event_bus(manager):
    assert manager.event_bus is not None


@pytest.mark.asyncio
async def test_manager_health_monitor(manager):
    assert manager.health_monitor is not None


@pytest.mark.asyncio
async def test_manager_hotplug_no_descriptor(manager):
    await manager.start()
    result = await manager.hotplug(Path("non_existent_path_for_testing"))
    assert result.success is False
