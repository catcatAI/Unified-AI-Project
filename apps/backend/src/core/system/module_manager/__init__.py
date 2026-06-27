import logging
from pathlib import Path
from typing import Optional

from .models import (
    HotplugResult,
    InitResult,
    ModuleDescriptor,
    ModuleInstance,
    ModuleStatus,
    StartResult,
)

try:
    from .scanner import ModuleScanner
except ImportError:
    ModuleScanner = None
from .events import EventBus, HealthMonitor
from .resolver import CycleError, DependencyResolver

try:
    from .lifecycle import ModuleLifecycle
except ImportError:
    ModuleLifecycle = None

logger = logging.getLogger(__name__)


class ModuleManager:
    def __init__(
        self,
        scan_paths: Optional[list[Path]] = None,
        registry=None,
    ) -> None:
        self._scan_paths = scan_paths or [Path("modules/")]
        self._registry = registry
        self._event_bus = EventBus()
        self._health_monitor = HealthMonitor(self._event_bus)
        self._scanner = ModuleScanner(self._scan_paths)
        self._resolver = DependencyResolver()
        self._lifecycle = ModuleLifecycle(self._event_bus)
        self._instances: list[ModuleInstance] = []
        self._started = False

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def health_monitor(self) -> HealthMonitor:
        return self._health_monitor

    def _build_deps_map(self, descriptors, instances) -> str:
        return {
            d.name: self._lifecycle._build_deps(d, instances, registry=self._registry)
            for d in descriptors
        }

    async def start(self) -> None:
        """Start the component."""
        descriptors = self._scanner.discover()
        resolved = self._resolver.resolve(descriptors)
        deps_map = self._build_deps_map(resolved, self._instances)
        instances, init_results = await self._lifecycle.init_all(resolved, deps_map)
        self._instances = instances
        if self._registry is not None:
            for inst in instances:
                self._registry.register(inst.name, inst.instance)
        deps_map = self._build_deps_map(resolved, self._instances)
        await self._lifecycle.start_all(instances, deps_map)
        for inst in instances:
            self._health_monitor.check(
                name=inst.name,
                status=inst.status,
                alive=inst.status == ModuleStatus.RUNNING,
            )
        self._started = True

    async def stop(self) -> None:
        """Stop the component."""
        await self._lifecycle.stop_all(self._instances)
        if self._registry is not None:
            for inst in self._instances:
                self._registry.unregister(inst.name)
        self._instances.clear()
        self._event_bus.clear()
        self._started = False

    async def hotplug(self, path: Path) -> HotplugResult:
        """Log a diagnostic message."""
        try:
            scanner = ModuleScanner([path.parent if path.is_file() else path])
            descriptors = scanner.discover()
            if not descriptors:
                return HotplugResult(name=path.name, success=False, error="no descriptor found")
            descriptor = descriptors[0]
            missing = self._resolver.check_deps(descriptor, [i.descriptor for i in self._instances])
            if missing:
                return HotplugResult(name=descriptor.name, success=False, error=f"missing deps: {missing}")
            deps = self._lifecycle._build_deps(descriptor, self._instances, registry=self._registry)
            instances, init_results = await self._lifecycle.init_all([descriptor], {descriptor.name: deps})
            if not instances:
                return HotplugResult(name=descriptor.name, success=False, error=init_results[0].error if init_results else "init failed")
            inst = instances[0]
            self._instances.append(inst)
            if self._registry is not None:
                self._registry.register(inst.name, inst.instance)
            deps = self._lifecycle._build_deps(descriptor, self._instances, registry=self._registry)
            start_results = await self._lifecycle.start_all([inst], {descriptor.name: deps})
            if not start_results or not start_results[0].success:
                self._instances = [i for i in self._instances if i.name != inst.name]
                if self._registry is not None:
                    self._registry.unregister(inst.name)
                error = start_results[0].error if start_results else "start failed"
                return HotplugResult(name=descriptor.name, success=False, error=error)
            return HotplugResult(name=descriptor.name, success=True)
        except Exception as e:
            logger.warning(f"hotplug failed for {path.name}: {e}", exc_info=True)
            return HotplugResult(name=path.name, success=False, error=str(e))

    async def unplug(self, name: str) -> HotplugResult:
        """Log a diagnostic message."""
        inst = self.get_module(name)
        if inst is None:
            return HotplugResult(name=name, success=False, error="not found")
        for other in self._instances:
            if other.name != name and name in other.descriptor.depends_on.required:
                return HotplugResult(name=name, success=False, error=f"module in use by {other.name}")
        try:
            await self._lifecycle.stop_all([inst])
        except Exception:
            logger.warning("Failed to stop module %s on uninstall", name, exc_info=True)
        self._instances = [i for i in self._instances if i.name != name]
        if self._registry is not None:
            self._registry.unregister(name)
        self._event_bus.emit(f"{name}.stopped")
        return HotplugResult(name=name, success=True)

    def get_module(self, name: str) -> Optional[ModuleInstance]:
        """Get the module by self."""
        for inst in self._instances:
            if inst.name == name:
                return inst
        return None

    def has(self, name: str) -> bool:
        """Execute the has operation."""
        return self.get_module(name) is not None

    def list_modules(self) -> dict[str, ModuleInstance]:
        """List modules items."""
        return {inst.name: inst for inst in self._instances}

    def get_status(self, name: str) -> Optional[ModuleStatus]:
        """Get the status by self."""
        inst = self.get_module(name)
        return inst.status if inst is not None else None

    def get_dependency_graph(self) -> dict[str, dict]:
        """Get the dependency graph by self."""
        graph: dict[str, dict] = {}
        for inst in self._instances:
            d = inst.descriptor
            graph[d.name] = {
                "required": list(d.depends_on.required),
                "optional": list(d.depends_on.optional),
                "provides": [s.name for s in d.provides.services],
                "status": inst.status.value,
            }
        return graph

    def get_health_report(self) -> dict:
        """Get the health report by self."""
        report: dict[str, dict] = {}
        for inst in self._instances:
            hs = self._health_monitor.get_status(inst.name)
            report[inst.name] = {
                "status": inst.status.value,
                "alive": hs.alive if hs else (inst.status == ModuleStatus.RUNNING),
                "latency_ms": hs.latency_ms if hs else 0.0,
                "error": hs.error if hs else inst.error,
                "consecutive_fails": hs.consecutive_fails if hs else 0,
            }
        return {
            "modules": report,
            "summary": {
                "total": len(self._instances),
                "running": sum(1 for i in self._instances if i.status == ModuleStatus.RUNNING),
                "failed": sum(1 for i in self._instances if i.status in (ModuleStatus.INIT_FAILED, ModuleStatus.START_FAILED, ModuleStatus.DEAD)),
                "started": self._started,
            },
        }


__all__ = [
    "ModuleManager", "ModuleScanner", "DependencyResolver",
    "EventBus", "HealthMonitor", "ModuleLifecycle",
    "CycleError",
    "ModuleDescriptor", "ModuleInstance", "ModuleStatus", "ModuleKind",
    "InitResult", "StartResult", "HotplugResult",
]
