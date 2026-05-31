import logging
from pathlib import Path
from typing import Callable, Optional

import yaml

logger = logging.getLogger(__name__)

from .models import (
    AdapterDecl,
    DependencySpec,
    HealthConfig,
    HookDecl,
    LifecycleHooks,
    ModuleDescriptor,
    ModuleKind,
    ProvidedServices,
    ServiceDecl,
)


class ValidationError(Exception):
    pass


class ModuleScanner:
    def __init__(self, scan_paths: list[Path]) -> None:
        self.scan_paths = scan_paths

    def discover(self) -> list[ModuleDescriptor]:
        descriptors: list[ModuleDescriptor] = []
        for base_path in self.scan_paths:
            resolved = Path(base_path).resolve()
            for yaml_path in sorted(resolved.glob("*/module.yaml")):
                with open(yaml_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    raise ValidationError(f"{yaml_path}: root must be a mapping")
                descriptor = self._parse_descriptor(data)
                self._validate(descriptor)
                descriptors.append(descriptor)
        return descriptors

    def _validate(self, descriptor: ModuleDescriptor) -> None:
        if not descriptor.name:
            raise ValidationError("name is required and must be non-empty")
        if not descriptor.version:
            raise ValidationError("version is required")
        if not descriptor.lifecycle.init:
            raise ValidationError("lifecycle.init is required")

    def _parse_descriptor(self, data: dict) -> ModuleDescriptor:
        raw_kind = data.get("kind", "service")
        try:
            kind = ModuleKind(raw_kind)
        except ValueError:
            raise ValidationError(f"unknown kind: {raw_kind}")

        raw_depends = data.get("depends_on", {}) or {}
        required_deps: list[str] = []
        optional_deps: list[str] = []
        constraints: dict[str, str] = {}
        for item in raw_depends.get("required", []) or []:
            if isinstance(item, dict):
                required_deps.append(item["name"])
                if "version" in item:
                    constraints[item["name"]] = str(item["version"])
            else:
                required_deps.append(item)
        for item in raw_depends.get("optional", []) or []:
            if isinstance(item, dict):
                optional_deps.append(item["name"])
                if "version" in item:
                    constraints[item["name"]] = str(item["version"])
            else:
                optional_deps.append(item)
        depends_on = DependencySpec(
            required=required_deps,
            optional=optional_deps,
        )

        raw_provides = data.get("provides", {}) or {}
        raw_services = raw_provides.get("services", []) or []
        raw_adapters = raw_provides.get("adapters", []) or []
        services = [
            ServiceDecl(
                name=s.get("name", ""),
                interface=s.get("interface", ""),
                type=s.get("type", "singleton"),
            )
            for s in raw_services
        ]
        adapters = [
            AdapterDecl(
                name=a.get("name", ""),
                interface=a.get("interface", ""),
            )
            for a in raw_adapters
        ]
        provides = ProvidedServices(services=services, adapters=adapters)

        raw_lifecycle = data.get("lifecycle", {}) or {}
        raw_health = raw_lifecycle.get("health", {}) or {}
        raw_hooks = raw_lifecycle.get("hooks", []) or []
        health = HealthConfig(
            endpoint=raw_health.get("endpoint", ""),
            interval=raw_health.get("interval", 30),
            timeout=raw_health.get("timeout", 5),
        )
        hooks = [
            HookDecl(event=h.get("event", ""), handler=h.get("handler", ""))
            for h in raw_hooks
        ]
        lifecycle = LifecycleHooks(
            init=raw_lifecycle.get("init", ""),
            start=raw_lifecycle.get("start", ""),
            stop=raw_lifecycle.get("stop", ""),
            health=health,
            hooks=hooks,
            thread_safe=raw_lifecycle.get("thread_safe", True),
        )

        return ModuleDescriptor(
            name=data.get("name", ""),
            version=data.get("version", ""),
            kind=kind,
            description=data.get("description", ""),
            depends_on=depends_on,
            provides=provides,
            lifecycle=lifecycle,
            config=data.get("config", {}),
            constraints=constraints,
        )

    def watch(self, callback: Callable) -> None:
        logger.warning("[ModuleScanner.watch] Not implemented — file watching disabled")
