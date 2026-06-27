from apps.backend.src.core.system.module_manager.models import (
    AdapterDecl,
    DependencySpec,
    HealthConfig,
    HealthStatus,
    HookDecl,
    HotplugResult,
    InitResult,
    LifecycleHooks,
    ModuleDescriptor,
    ModuleInstance,
    ModuleKind,
    ModuleStatus,
    ProvidedServices,
    ServiceDecl,
    StartResult,
)


def test_module_kind_values():
    assert ModuleKind.SERVICE.value == "service"
    assert ModuleKind.ADAPTER.value == "adapter"
    assert ModuleKind.PROVIDER.value == "provider"
    assert ModuleKind.CLI.value == "cli"
    assert len(ModuleKind) == 4


def test_module_status_values():
    assert ModuleStatus.DISCOVERED.value == "discovered"
    assert ModuleStatus.INITIALIZING.value == "initializing"
    assert ModuleStatus.INIT_FAILED.value == "init_failed"
    assert ModuleStatus.STARTING.value == "starting"
    assert ModuleStatus.RUNNING.value == "running"
    assert ModuleStatus.START_FAILED.value == "start_failed"
    assert ModuleStatus.STOPPED.value == "stopped"
    assert ModuleStatus.DEAD.value == "dead"
    assert len(ModuleStatus) == 8


def test_module_descriptor_defaults():
    desc = ModuleDescriptor(name="test", version="1.0.0")
    assert desc.description == ""
    assert desc.config == {}


def test_module_descriptor_required_fields():
    hooks = LifecycleHooks(init="init_fn")
    desc = ModuleDescriptor(
        name="test", version="1.0.0", kind=ModuleKind.SERVICE, lifecycle=hooks
    )
    assert desc.name == "test"
    assert desc.version == "1.0.0"
    assert desc.kind == ModuleKind.SERVICE
    assert desc.lifecycle.init == "init_fn"


def test_service_decl_default_type():
    decl = ServiceDecl(name="svc")
    assert decl.type == "singleton"


def test_module_instance_property():
    desc = ModuleDescriptor(name="test_mod", version="1.0")
    inst = ModuleInstance(descriptor=desc, instance=object())
    assert inst.name == "test_mod"


def test_init_result():
    ok = InitResult(name="ok", success=True)
    assert ok.success is True
    assert ok.error is None
    fail = InitResult(name="fail", success=False, error="boom")
    assert fail.success is False
    assert fail.error == "boom"


def test_health_status_defaults():
    hs = HealthStatus(name="h", status=ModuleStatus.RUNNING, alive=True)
    assert hs.latency_ms == 0.0
    assert hs.error is None


def test_hotplug_result():
    ok = HotplugResult(name="plug", success=True)
    assert ok.success is True
    assert ok.error is None
    fail = HotplugResult(name="plug", success=False, error="fail")
    assert fail.success is False
    assert fail.error == "fail"


def test_module_descriptor_full():
    hooks = LifecycleHooks(
        init="init", start="start", stop="stop",
        health=HealthConfig(endpoint="/health", interval=10, timeout=3),
        hooks=[HookDecl(event="evt", handler="hdl")],
        thread_safe=False,
    )
    deps = DependencySpec(required=["a"], optional=["b"])
    svcs = ProvidedServices(
        services=[ServiceDecl(name="s", interface="i", type="pool")],
        adapters=[AdapterDecl(name="a", interface="i")],
    )
    desc = ModuleDescriptor(
        name="full", version="2.0", kind=ModuleKind.ADAPTER,
        description="full desc", depends_on=deps, provides=svcs,
        lifecycle=hooks, config={"key": "val"},
    )
    assert desc.name == "full"
    assert desc.version == "2.0"
    assert desc.kind == ModuleKind.ADAPTER
    assert desc.description == "full desc"
    assert desc.depends_on.required == ["a"]
    assert desc.depends_on.optional == ["b"]
    assert desc.provides.services[0].name == "s"
    assert desc.provides.adapters[0].name == "a"
    assert desc.lifecycle.init == "init"
    assert desc.lifecycle.health.endpoint == "/health"
    assert desc.lifecycle.hooks[0].event == "evt"
    assert desc.lifecycle.thread_safe is False
    assert desc.config == {"key": "val"}
