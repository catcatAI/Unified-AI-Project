import asyncio
import importlib
import logging
import time
from typing import Any, Optional

from .models import (
    InitResult,
    ModuleInstance,
    ModuleStatus,
    StartResult,
)

logger = logging.getLogger(__name__)


class ModuleLifecycle:
    def __init__(self, event_bus) -> None:
        self._event_bus = event_bus

    def _build_deps(self, descriptor, instances, registry=None):
        deps = {}
        for inst in instances:
            if inst.name != descriptor.name:
                deps[inst.name] = inst.instance
        if registry is not None:
            getter = getattr(registry, "get", None)
            if getter is not None:
                for name in descriptor.depends_on.required:
                    if name not in deps:
                        reg_val = getter(name)
                        if reg_val is not None:
                            deps[name] = reg_val
        return deps

    async def init_all(self, descriptors, deps_map):
        instances = []
        results = []
        for desc in descriptors:
            t0 = time.monotonic()
            try:
                inst = self._call_init(desc, deps_map.get(desc.name, {}))
                instance = ModuleInstance(
                    descriptor=desc,
                    instance=inst,
                    status=ModuleStatus.INITIALIZING,
                )
                instances.append(instance)
                results.append(
                    InitResult(
                        name=desc.name,
                        success=True,
                        instance=instance,
                        elapsed_ms=(time.monotonic() - t0) * 1000,
                    )
                )
            except Exception as e:
                logger.warning("init failed for %s: %s", desc.name, e)
                results.append(
                    InitResult(
                        name=desc.name,
                        success=False,
                        error=str(e),
                        elapsed_ms=(time.monotonic() - t0) * 1000,
                    )
                )
        return instances, results

    async def start_all(self, instances, deps_map):
        results = []
        for inst in instances:
            t0 = time.monotonic()
            try:
                self._call_start(inst, deps_map.get(inst.name, {}))
                inst.status = ModuleStatus.RUNNING
                results.append(
                    StartResult(
                        name=inst.name,
                        success=True,
                        elapsed_ms=(time.monotonic() - t0) * 1000,
                    )
                )
            except Exception as e:
                logger.warning("start failed for %s: %s", inst.name, e)
                inst.status = ModuleStatus.START_FAILED
                results.append(
                    StartResult(
                        name=inst.name,
                        success=False,
                        error=str(e),
                        elapsed_ms=(time.monotonic() - t0) * 1000,
                    )
                )
        return results

    async def stop_all(self, instances):
        results = []
        for inst in reversed(instances):
            t0 = time.monotonic()
            try:
                self._call_stop(inst)
                inst.status = ModuleStatus.STOPPED
                results.append(
                    StartResult(
                        name=inst.name,
                        success=True,
                        elapsed_ms=(time.monotonic() - t0) * 1000,
                    )
                )
            except Exception as e:
                logger.warning("stop failed for %s: %s", inst.name, e)
                results.append(
                    StartResult(
                        name=inst.name,
                        success=False,
                        error=str(e),
                        elapsed_ms=(time.monotonic() - t0) * 1000,
                    )
                )
        return results

    async def call(self, instances, name, method):
        for inst in instances:
            if inst.name == name:
                fn = getattr(inst.instance, method, None)
                if fn is not None:
                    result = fn()
                    if asyncio.iscoroutine(result):
                        return await result
                    return result
                return None
        raise ValueError(f"module '{name}' not found")

    def _call_init(self, desc, deps):
        fn = self._import_fn(desc.lifecycle.init)
        return fn(deps=deps)

    def _call_start(self, inst, deps):
        if not inst.descriptor.lifecycle.start:
            return
        fn = self._import_fn(inst.descriptor.lifecycle.start)
        return fn(inst.instance, deps=deps)

    def _call_stop(self, inst):
        if not inst.descriptor.lifecycle.stop:
            return
        fn = self._import_fn(inst.descriptor.lifecycle.stop)
        return fn(inst.instance)

    @staticmethod
    def _import_fn(dotted_path):
        parts = dotted_path.split(".")
        module_path = ".".join(parts[:-1])
        fn_name = parts[-1]
        mod = importlib.import_module(module_path)
        return getattr(mod, fn_name)