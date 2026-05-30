import enum
from dataclasses import dataclass, field
from typing import Any, Optional


class ModuleKind(str, enum.Enum):
    SERVICE = "service"
    ADAPTER = "adapter"
    PROVIDER = "provider"
    CLI = "cli"


class ModuleStatus(str, enum.Enum):
    DISCOVERED = "discovered"
    INITIALIZING = "initializing"
    INIT_FAILED = "init_failed"
    STARTING = "starting"
    RUNNING = "running"
    START_FAILED = "start_failed"
    STOPPED = "stopped"
    DEAD = "dead"


@dataclass
class ServiceDecl:
    name: str
    interface: str = ""
    type: str = "singleton"


@dataclass
class AdapterDecl:
    name: str
    interface: str = ""


@dataclass
class HealthConfig:
    endpoint: str = ""
    interval: int = 30
    timeout: int = 5


@dataclass
class HookDecl:
    event: str
    handler: str


@dataclass
class LifecycleHooks:
    init: str = ""
    start: str = ""
    stop: str = ""
    health: HealthConfig = field(default_factory=HealthConfig)
    hooks: list[HookDecl] = field(default_factory=list)
    thread_safe: bool = True


@dataclass
class DependencySpec:
    required: list[str] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)


@dataclass
class ProvidedServices:
    services: list[ServiceDecl] = field(default_factory=list)
    adapters: list[AdapterDecl] = field(default_factory=list)


@dataclass
class ModuleDescriptor:
    name: str
    version: str
    kind: ModuleKind = ModuleKind.SERVICE
    description: str = ""
    depends_on: DependencySpec = field(default_factory=DependencySpec)
    provides: ProvidedServices = field(default_factory=ProvidedServices)
    lifecycle: LifecycleHooks = field(default_factory=LifecycleHooks)
    config: dict = field(default_factory=dict)


@dataclass
class ModuleInstance:
    descriptor: ModuleDescriptor
    instance: Any
    status: ModuleStatus = ModuleStatus.DISCOVERED
    error: Optional[str] = None

    @property
    def name(self) -> str:
        return self.descriptor.name


@dataclass
class InitResult:
    name: str
    success: bool
    instance: Optional[ModuleInstance] = None
    error: Optional[str] = None
    elapsed_ms: float = 0.0


@dataclass
class StartResult:
    name: str
    success: bool
    error: Optional[str] = None
    elapsed_ms: float = 0.0


@dataclass
class HealthStatus:
    name: str
    status: ModuleStatus
    alive: bool
    latency_ms: float = 0.0
    error: Optional[str] = None
    consecutive_fails: int = 0


@dataclass
class HotplugResult:
    name: str
    success: bool
    error: Optional[str] = None


__all__ = [
    "ModuleKind", "ModuleStatus",
    "ServiceDecl", "AdapterDecl", "HealthConfig", "HookDecl",
    "LifecycleHooks", "DependencySpec", "ProvidedServices",
    "ModuleDescriptor", "ModuleInstance",
    "InitResult", "StartResult", "HealthStatus", "HotplugResult",
]
