import importlib
import asyncio
import time
import inspect
from collections.abc import Callable
from typing import Any

from typing import Any, Optional

from .models import ModuleDescriptor, ModuleInstance, ModuleStatus, InitResult, StartResult
from .events import EventBus


class ModuleLifecycle:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    async def init_all(
        self, descriptors: list[ModuleDescriptor], deps_map: dict[str, dict]
    ) -> tuple[list[ModuleInstance], list[InitResult]]:
        instances: list[ModuleInstance] = []
        results: list[InitResult] = []

        for descriptor in descriptors:
            start = time.perf_counter()
            deps = deps_map.get(descriptor.name, {})
            try:
                if descriptor.lifecycle.init:
                    handler = self._resolve_handler(descriptor.lifecycle.init)
                    if inspect.iscoroutinefunction(handler):
                        instance = await handler(deps)
                    else:
                        instance = handler(deps)
                else:
                    instance = object()
                module_instance = ModuleInstance(
                    descriptor=descriptor, instance=instance, status=ModuleStatus.INITIALIZING
                )
                elapsed = (time.perf_counter() - start) * 1000
                instances.append(module_instance)
                results.append(
                    InitResult(name=descriptor.name, success=True, instance=module_instance, elapsed_ms=elapsed)
                )
                self._event_bus.emit(f"{descriptor.name}.init")
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                results.append(
                    InitResult(name=descriptor.name, success=False, error=str(e), elapsed_ms=elapsed)
                )
                self._event_bus.emit(f"{descriptor.name}.failed", error=str(e))

        return instances, results

    async def start_all(
        self, instances: list[ModuleInstance], deps_map: dict[str, dict]
    ) -> list[StartResult]:
        results: list[StartResult] = []

        for inst in instances:
            start = time.perf_counter()
            deps = deps_map.get(inst.name, {})
            try:
                if inst.descriptor.lifecycle.start:
                    handler = self._resolve_handler(inst.descriptor.lifecycle.start)
                    if inspect.iscoroutinefunction(handler):
                        await handler(inst.instance, deps)
                    else:
                        handler(inst.instance, deps)
                inst.status = ModuleStatus.RUNNING
                elapsed = (time.perf_counter() - start) * 1000
                results.append(StartResult(name=inst.name, success=True, elapsed_ms=elapsed))
                self._event_bus.emit(f"{inst.name}.ready")
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                inst.status = ModuleStatus.START_FAILED
                results.append(StartResult(name=inst.name, success=False, error=str(e), elapsed_ms=elapsed))
                self._event_bus.emit(f"{inst.name}.failed", error=str(e))

        return results

    async def stop_all(self, instances: list[ModuleInstance]) -> list[StartResult]:
        results: list[StartResult] = []

        for inst in reversed(instances):
            start = time.perf_counter()
            try:
                if inst.descriptor.lifecycle.stop:
                    handler = self._resolve_handler(inst.descriptor.lifecycle.stop)
                    if inspect.iscoroutinefunction(handler):
                        await handler(inst.instance)
                    else:
                        handler(inst.instance)
                elapsed = (time.perf_counter() - start) * 1000
                results.append(StartResult(name=inst.name, success=True, elapsed_ms=elapsed))
                self._event_bus.emit(f"{inst.name}.stopped")
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                results.append(StartResult(name=inst.name, success=False, error=str(e), elapsed_ms=elapsed))

        return results

    async def call(
        self,
        instances: list[ModuleInstance],
        module_name: str,
        method: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        for inst in instances:
            if inst.name == module_name:
                func = getattr(inst.instance, method)
                if inspect.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                if inst.descriptor.lifecycle.thread_safe:
                    return await asyncio.to_thread(func, *args, **kwargs)
                return func(*args, **kwargs)
        raise ValueError(f"Module '{module_name}' not found")

    def _resolve_handler(self, dotted_path: str) -> Callable:
        parts = dotted_path.split(".")
        module_path = ".".join(parts[:-1])
        func_name = parts[-1]
        module = importlib.import_module(module_path)
        return getattr(module, func_name)

    def _build_deps(
        self,
        descriptor: ModuleDescriptor,
        instances: list[ModuleInstance],
        registry: Any = None,
    ) -> dict:
        deps: dict = {}
        name_map = {inst.name: inst.instance for inst in instances}
        for dep_name in descriptor.depends_on.required:
            if dep_name in name_map:
                deps[dep_name] = name_map[dep_name]
            elif registry is not None:
                svc = registry.get(dep_name)
                if svc is not None:
                    deps[dep_name] = svc
        for dep_name in descriptor.depends_on.optional:
            if dep_name in name_map:
                deps[dep_name] = name_map[dep_name]
            elif registry is not None:
                svc = registry.get(dep_name)
                if svc is not None:
                    deps[dep_name] = svc
        return deps
