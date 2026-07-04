"""Tests for AngelaModelCore — GlobalSystemClock integration."""
import asyncio
import pytest

pytestmark = pytest.mark.slow


@pytest.fixture
def model():
    from core.engine.angela_model_core import AngelaModelCore
    m = AngelaModelCore()
    yield m


@pytest.mark.asyncio
async def test_model_core_clock_created(model):
    """Clock is created on instantiation."""
    assert hasattr(model, "clock")
    assert model.clock.tick_rate_hz == 10.0


@pytest.mark.asyncio
async def test_model_core_clock_starts_on_initialize(model):
    """Clock starts when initialize() is called."""
    await model.initialize()
    assert model.clock.is_running
    await model.shutdown()


@pytest.mark.asyncio
async def test_model_core_clock_stops_on_shutdown(model):
    """Clock stops when shutdown() is called."""
    await model.initialize()
    await model.shutdown()
    assert not model.clock.is_running


@pytest.mark.asyncio
async def test_model_core_metabolic_loop_uses_clock(model):
    """Metabolic loop advances clock ticks."""
    await model.initialize()
    start = model.clock.tick_count
    await asyncio.sleep(0.3)
    await model.shutdown()
    assert model.clock.tick_count > start


@pytest.mark.asyncio
async def test_model_core_consciousness_snapshot(model):
    """get_consciousness_snapshot returns expected structure with real values."""
    snapshot = model.get_consciousness_snapshot()
    assert "internal_state" in snapshot
    assert "spatial_awareness" in snapshot
    assert "system_integrity" in snapshot
    assert isinstance(snapshot["internal_state"], dict)
    assert isinstance(snapshot["spatial_awareness"], dict)
    assert isinstance(snapshot["system_integrity"], str)


@pytest.mark.asyncio
async def test_model_core_generate_prompt_prefix(model):
    """generate_prompt_prefix returns a string."""
    prefix = model.generate_prompt_prefix()
    assert isinstance(prefix, str)
    assert "Angela Internal State" in prefix


@pytest.mark.skip(reason="BiologicalIntegrator.initialize() requires runtime deps")
@pytest.mark.asyncio
async def test_model_core_full_lifecycle(model):
    """Full init→run→shutdown cycle."""
    await model.initialize()
    snapshot = model.get_consciousness_snapshot()
    assert snapshot["system_integrity"] in ("Optimal", "Degraded")
    await asyncio.sleep(0.5)
    prefix = model.generate_prompt_prefix()
    assert "Energy" in prefix
    await model.shutdown()
