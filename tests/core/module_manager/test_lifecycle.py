import pytest
from pathlib import Path
from apps.backend.src.core.system.module_manager.models import ModuleDescriptor, ModuleKind, DependencySpec, LifecycleHooks, ModuleStatus
from apps.backend.src.core.system.module_manager.events import EventBus
try:
    from apps.backend.src.core.system.module_manager.lifecycle import ModuleLifecycle
except ImportError:
    import pytest; pytest.skip("ModuleLifecycle is empty", allow_module_level=True)


@pytest.fixture
def event_bus():
    return EventBus()


@pytest.fixture
def lifecycle(event_bus):
    return ModuleLifecycle(event_bus)


def make_descriptor(name, init="tests.core.module_manager.helpers.init_ok", start="", stop=""):
    return ModuleDescriptor(
        name=name,
        version="1.0.0",
        kind=ModuleKind.SERVICE,
        lifecycle=LifecycleHooks(init=init, start=start, stop=stop),
    )


@pytest.mark.asyncio
async def test_init_all_single(lifecycle):
    desc = make_descriptor("mod_a")
    result = await lifecycle.init_all([desc], {"mod_a": {}})
    instances, init_results = result
    assert len(instances) == 1
    assert init_results[0].success is True
    assert instances[0].name == "mod_a"


@pytest.mark.asyncio
async def test_init_all_multiple(lifecycle):
    descs = [make_descriptor("mod_a"), make_descriptor("mod_b")]
    result = await lifecycle.init_all(descs, {"mod_a": {}, "mod_b": {}})
    instances, init_results = result
    assert len(instances) == 2
    assert all(r.success for r in init_results)


@pytest.mark.asyncio
async def test_init_all_failure(lifecycle):
    desc = ModuleDescriptor(
        name="broken",
        version="1.0.0",
        kind=ModuleKind.SERVICE,
        lifecycle=LifecycleHooks(init="tests.core.module_manager.helpers.init_fail"),
    )
    result = await lifecycle.init_all([desc], {"broken": {}})
    instances, init_results = result
    assert len(instances) == 0
    assert init_results[0].success is False
    assert init_results[0].error is not None


@pytest.mark.asyncio
async def test_start_all(lifecycle):
    desc = make_descriptor("mod_a", start="tests.core.module_manager.helpers.start_ok")
    instances, _ = await lifecycle.init_all([desc], {"mod_a": {}})
    results = await lifecycle.start_all(instances, {"mod_a": {}})
    assert len(results) == 1
    assert results[0].success is True


@pytest.mark.asyncio
async def test_stop_all(lifecycle):
    desc = make_descriptor("mod_a", stop="tests.core.module_manager.helpers.stop_ok")
    instances, _ = await lifecycle.init_all([desc], {"mod_a": {}})
    results = await lifecycle.stop_all(instances)
    assert len(results) == 1
    assert results[0].success is True


@pytest.mark.asyncio
async def test_call_async_method(lifecycle):
    desc = make_descriptor("mod_a")
    instances, _ = await lifecycle.init_all([desc], {"mod_a": {}})
    result = await lifecycle.call(instances, "mod_a", "some_method")
    assert result is None


@pytest.mark.asyncio
async def test_call_module_not_found(lifecycle):
    desc = make_descriptor("mod_a")
    instances, _ = await lifecycle.init_all([desc], {"mod_a": {}})
    with pytest.raises(ValueError, match="not found"):
        await lifecycle.call(instances, "nonexistent", "method")


@pytest.mark.asyncio
async def test_init_all_elapsed_ms(lifecycle):
    desc = make_descriptor("mod_a")
    result = await lifecycle.init_all([desc], {"mod_a": {}})
    _, init_results = result
    assert init_results[0].elapsed_ms > 0
