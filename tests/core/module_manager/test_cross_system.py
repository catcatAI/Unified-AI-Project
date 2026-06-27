"""Phase 3: Cross-system module dependency tests."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from apps.backend.src.core.system.module_manager import ModuleManager
from apps.backend.src.core.system.module_manager.events import EventBus
from apps.backend.src.core.system.module_manager.models import (
    DependencySpec,
    LifecycleHooks,
    ModuleDescriptor,
    ModuleInstance,
    ModuleKind,
    ModuleStatus,
)

try:
    from apps.backend.src.core.system.module_manager.lifecycle import ModuleLifecycle
except ImportError:
    import pytest; pytest.skip("ModuleLifecycle is empty", allow_module_level=True)


class TestBuildDepsWithRegistry:

    @pytest.fixture
    def lifecycle(self):
        return ModuleLifecycle(EventBus())

    def make_desc(self, name, required=None, optional=None):
        return ModuleDescriptor(
            name=name,
            version="1.0.0",
            kind=ModuleKind.SERVICE,
            depends_on=DependencySpec(
                required=required or [],
                optional=optional or [],
            ),
        )

    def test_dep_resolved_from_module_instance(self, lifecycle):
        desc = self.make_desc("consumer", required=["provider"])
        provider_mod = ModuleInstance(
            descriptor=self.make_desc("provider"),
            instance="provider_instance",
            status=ModuleStatus.RUNNING,
        )
        deps = lifecycle._build_deps(desc, [provider_mod])
        assert deps["provider"] == "provider_instance"

    def test_dep_resolved_from_registry(self, lifecycle):
        desc = self.make_desc("consumer", required=["external_service"])
        registry = MagicMock()
        registry.get.return_value = "service_instance"
        deps = lifecycle._build_deps(desc, [], registry=registry)
        assert deps["external_service"] == "service_instance"
        registry.get.assert_called_once_with("external_service")

    def test_optional_dep_not_resolved_from_registry(self, lifecycle):
        desc = self.make_desc("consumer", optional=["optional_svc"])
        registry = MagicMock()
        registry.get.return_value = "opt_instance"
        deps = lifecycle._build_deps(desc, [], registry=registry)
        assert "optional_svc" not in deps

    def test_missing_optional_skipped(self, lifecycle):
        desc = self.make_desc("consumer", optional=["missing_svc"])
        registry = MagicMock()
        registry.get.return_value = None
        deps = lifecycle._build_deps(desc, [], registry=registry)
        assert "missing_svc" not in deps

    def test_missing_required_not_in_module_or_registry(self, lifecycle):
        desc = self.make_desc("consumer", required=["nowhere"])
        registry = MagicMock()
        registry.get.return_value = None
        deps = lifecycle._build_deps(desc, [], registry=registry)
        assert "nowhere" not in deps

    def test_module_takes_precedence_over_registry(self, lifecycle):
        desc = self.make_desc("consumer", required=["shared"])
        provider_mod = ModuleInstance(
            descriptor=self.make_desc("shared"),
            instance="from_module",
            status=ModuleStatus.RUNNING,
        )
        registry = MagicMock()
        registry.get.return_value = "from_registry"
        deps = lifecycle._build_deps(desc, [provider_mod], registry=registry)
        assert deps["shared"] == "from_module"


class TestDependencyGraph:

    @pytest.fixture
    def manager(self):
        return ModuleManager(scan_paths=[Path("non_existent_path_for_testing")])

    async def test_get_dependency_graph_empty(self, manager):
        await manager.start()
        graph = manager.get_dependency_graph()
        assert graph == {}

    async def test_get_dependency_graph_populated(self):
        from apps.backend.src.core.system.module_manager import ModuleManager
        from apps.backend.src.core.system.module_manager.models import (
            DependencySpec,
            LifecycleHooks,
            ModuleDescriptor,
            ModuleInstance,
            ModuleKind,
            ModuleStatus,
        )
        mod_path = Path(__file__).resolve().parent.parent.parent.parent / "apps/backend/src/modules"
        m = ModuleManager(scan_paths=[mod_path])
        await m.start()
        graph = m.get_dependency_graph()
        assert "card_pipeline" in graph
        assert "intent_registry" in graph
        assert graph["card_pipeline"]["status"] == "running"
        assert graph["intent_registry"]["status"] == "running"
        await m.stop()


class TestCrossSystemWiring:

    async def test_module_manager_registers_in_registry(self):
        registry = MagicMock()
        mod_path = Path(__file__).resolve().parent.parent.parent.parent / "apps/backend/src/modules"
        m = ModuleManager(registry=registry, scan_paths=[mod_path])
        await m.start()
        assert registry.register.call_count >= 2
        registered_names = {call.args[0] for call in registry.register.call_args_list}
        assert "card_pipeline" in registered_names
        assert "intent_registry" in registered_names
        await m.stop()

    async def test_dependency_graph_keys(self):
        mod_path = Path(__file__).resolve().parent.parent.parent.parent / "apps/backend/src/modules"
        m = ModuleManager(scan_paths=[mod_path])
        await m.start()
        graph = m.get_dependency_graph()
        for name, info in graph.items():
            assert "required" in info
            assert "optional" in info
            assert "provides" in info
            assert "status" in info
        await m.stop()

    async def test_list_modules_returns_instances(self):
        mod_path = Path(__file__).resolve().parent.parent.parent.parent / "apps/backend/src/modules"
        m = ModuleManager(scan_paths=[mod_path])
        await m.start()
        modules = m.list_modules()
        for name, entry in modules.items():
            from apps.backend.src.core.system.module_manager.models import ModuleInstance
            assert isinstance(entry, ModuleInstance)
            assert entry.instance is not None
        await m.stop()
