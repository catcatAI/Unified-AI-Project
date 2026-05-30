import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
import yaml

from apps.backend.src.core.system.module_manager import ModuleManager
from apps.backend.src.core.system.module_manager.models import (
    ModuleStatus, ModuleDescriptor, ModuleInstance, ModuleKind, DependencySpec, LifecycleHooks,
)


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


class TestUnplug:
    @pytest.mark.asyncio
    async def test_unplug_not_found(self, manager):
        await manager.start()
        result = await manager.unplug("nonexistent")
        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_unplug_in_use(self, manager):
        await manager.start()
        base = ModuleInstance(
            descriptor=ModuleDescriptor(name="base", version="1.0.0", depends_on=DependencySpec()),
            instance=object(),
            status=ModuleStatus.RUNNING,
        )
        consumer = ModuleInstance(
            descriptor=ModuleDescriptor(name="consumer", version="1.0.0",
                                        depends_on=DependencySpec(required=["base"])),
            instance=object(),
            status=ModuleStatus.RUNNING,
        )
        manager._instances = [base, consumer]
        result = await manager.unplug("base")
        assert result.success is False
        assert "in use by" in result.error

    @pytest.mark.asyncio
    async def test_unplug_success(self, manager):
        await manager.start()
        base = ModuleInstance(
            descriptor=ModuleDescriptor(name="base", version="1.0.0", depends_on=DependencySpec()),
            instance=object(),
            status=ModuleStatus.RUNNING,
        )
        manager._instances = [base]
        result = await manager.unplug("base")
        assert result.success is True
        assert manager.has("base") is False


class TestHotplugRollback:
    @pytest.mark.asyncio
    async def test_hotplug_rollback_on_start_failure(self):
        with TemporaryDirectory() as tmpdir:
            mod_dir = Path(tmpdir) / "failmod"
            mod_dir.mkdir()
            yaml_path = mod_dir / "module.yaml"
            with open(yaml_path, "w") as f:
                yaml.dump({
                    "name": "failmod",
                    "version": "1.0.0",
                    "kind": "service",
                    "lifecycle": {
                        "init": "tests.core.module_manager.test_manager._fake_init",
                        "start": "tests.core.module_manager.test_manager._fake_start_fail",
                    },
                }, f)
            m = ModuleManager(scan_paths=[Path("non_existent_path_for_testing")])
            await m.start()
            result = await m.hotplug(yaml_path)
            assert result.success is False
            assert m.has("failmod") is False


def _fake_init(deps):
    return object()


def _fake_start_fail(instance, deps):
    raise RuntimeError("simulated start failure")
