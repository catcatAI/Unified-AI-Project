# ANGELA-MATRIX: L0[基础层] [A] L1

import logging
from pathlib import Path

import yaml

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

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    pass


class ModuleScanner:
    def __init__(self, scan_paths: list[Path]) -> None:
        self._scan_paths = scan_paths

    def discover(self) -> list[ModuleDescriptor]:
        descriptors = []
        for scan_path in self._scan_paths:
            if not scan_path.is_dir():
                continue
            for yaml_path in sorted(scan_path.rglob("module.yaml")):
                try:
                    desc = self._parse_yaml(yaml_path)
                    descriptors.append(desc)
                except ValidationError:
                    raise
                except Exception as e:
                    logger.warning("failed to parse %s: %s", yaml_path, e)
        descriptors.sort(key=lambda d: d.name)
        return descriptors

    def _parse_yaml(self, yaml_path: Path) -> ModuleDescriptor:
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            raise ValidationError("root must be a mapping")

        name = data.get("name")
        if not name:
            raise ValidationError("name is required")

        version = data.get("version")
        if not version:
            raise ValidationError("version is required")

        kind_str = data.get("kind", "service")
        try:
            kind = ModuleKind(kind_str)
        except ValueError:
            raise ValidationError(f"unknown kind: {kind_str}")

        lifecycle_data = data.get("lifecycle", {})
        init_hook = lifecycle_data.get("init") if isinstance(lifecycle_data, dict) else None
        if not init_hook:
            raise ValidationError("lifecycle.init is required")

        descriptor = ModuleDescriptor(
            name=name,
            version=version,
            kind=kind,
            description=data.get("description", ""),
            depends_on=self._parse_depends(data.get("depends_on", {})),
            provides=self._parse_provides(data.get("provides", {})),
            lifecycle=self._parse_lifecycle(lifecycle_data),
            config=data.get("config", {}),
            constraints=self._parse_constraints(data.get("depends_on", {})),
        )
        return descriptor

    @staticmethod
    def _parse_depends(depends_data: dict) -> DependencySpec:
        required = []
        optional = []
        for raw in depends_data.get("required", []):
            if isinstance(raw, dict):
                required.append(raw["name"])
            else:
                required.append(str(raw))
        for raw in depends_data.get("optional", []):
            if isinstance(raw, dict):
                optional.append(raw["name"])
            else:
                optional.append(str(raw))
        return DependencySpec(required=required, optional=optional)

    @staticmethod
    def _parse_constraints(depends_data: dict) -> dict[str, str]:
        constraints = {}
        for key in ("required", "optional"):
            for raw in depends_data.get(key, []):
                if isinstance(raw, dict) and "version" in raw:
                    constraints[raw["name"]] = raw["version"]
        return constraints

    @staticmethod
    def _parse_provides(provides_data: dict) -> ProvidedServices:
        services = []
        for svc in provides_data.get("services", []):
            services.append(
                ServiceDecl(
                    name=svc["name"],
                    interface=svc.get("interface", ""),
                    type=svc.get("type", "singleton"),
                )
            )
        adapters = []
        for adp in provides_data.get("adapters", []):
            adapters.append(
                AdapterDecl(
                    name=adp["name"],
                    interface=adp.get("interface", ""),
                )
            )
        return ProvidedServices(services=services, adapters=adapters)

    @staticmethod
    def _parse_lifecycle(lifecycle_data) -> LifecycleHooks:
        if isinstance(lifecycle_data, str):
            return LifecycleHooks(init=lifecycle_data)
        health_data = lifecycle_data.get("health", {})
        health = HealthConfig(
            endpoint=health_data.get("endpoint", ""),
            interval=health_data.get("interval", 30),
            timeout=health_data.get("timeout", 5),
        ) if isinstance(health_data, dict) else HealthConfig()
        hooks = []
        for hook in lifecycle_data.get("hooks", []):
            hooks.append(HookDecl(event=hook["event"], handler=hook["handler"]))
        return LifecycleHooks(
            init=lifecycle_data.get("init", ""),
            start=lifecycle_data.get("start", ""),
            stop=lifecycle_data.get("stop", ""),
            health=health,
            hooks=hooks,
            thread_safe=lifecycle_data.get("thread_safe", True),
        )
