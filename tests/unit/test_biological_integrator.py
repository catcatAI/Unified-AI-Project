"""Tests for BiologicalIntegrator — stress/relaxation methods (production dependency via §X #80)."""
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def _mock_heavy_modules():
    """Pre-mock heavy sub-modules BEFORE import to avoid slow transitive torch imports."""
    heavy_modules = [
        "core.bio.cerebellum_engine",
        "core.engine.art_learning_workflow",
        "core.life.env_dynamics",
        "core.system.config.tiered_loader",
        "core.system.config.magic_numbers",
    ]
    mocks = {}
    for name in heavy_modules:
        if name not in sys.modules:
            mocks[name] = MagicMock()
            sys.modules[name] = mocks[name]
    yield
    for name in mocks:
        if name in sys.modules:
            del sys.modules[name]


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset BiologicalIntegrator singleton between tests."""
    import core.bio.biological_integrator as bi_mod
    bi_mod.BiologicalIntegrator._instance = None
    bi_mod.BiologicalIntegrator._initialized = False
    yield
    bi_mod.BiologicalIntegrator._instance = None
    bi_mod.BiologicalIntegrator._initialized = False


@pytest.fixture
def mock_subsystems():
    """Patch all 5 subsystem imports (module-level) to avoid heavy transitive deps."""
    patches = [
        patch("core.bio.biological_integrator.PhysiologicalTactileSystem"),
        patch("core.bio.biological_integrator.EndocrineSystem"),
        patch("core.bio.biological_integrator.AutonomicNervousSystem"),
        patch("core.bio.biological_integrator.NeuroplasticitySystem"),
        patch("core.bio.biological_integrator.EmotionalBlendingSystem"),
    ]
    mocks = [p.start() for p in patches]
    for m in mocks:
        m.return_value = MagicMock()

    yield dict(zip(
        ["tactile", "endocrine", "nervous", "neuroplasticity", "emotional"], mocks
    ))

    for p in patches:
        p.stop()


@pytest.fixture
def integrator(mock_subsystems):
    """Create a BiologicalIntegrator with mocked subsystems."""
    import core.bio.biological_integrator as bi
    inst = bi.BiologicalIntegrator()
    inst.tactile_system = mock_subsystems["tactile"].return_value
    inst.endocrine_system = mock_subsystems["endocrine"].return_value
    inst.nervous_system = mock_subsystems["nervous"].return_value
    inst.neuroplasticity_system = mock_subsystems["neuroplasticity"].return_value
    inst.emotional_system = mock_subsystems["emotional"].return_value
    inst.endocrine_system.trigger_stress_response = AsyncMock()
    inst.endocrine_system.trigger_emotional_response = AsyncMock()
    inst.nervous_system.apply_stimulus = AsyncMock()
    return inst


class TestBiologicalEventPublisher:
    """Test standalone BiologicalEventPublisher (no heavy dependencies)."""

    @pytest.fixture
    def publisher(self):
        from core.bio.biological_integrator import BiologicalEventPublisher, BiologicalEvent
        return BiologicalEventPublisher(), BiologicalEvent

    def test_subscribe_and_publish(self, publisher):
        pub, BioEvent = publisher
        callback = MagicMock()
        pub.subscribe(BioEvent.STRESS_CHANGED.value, callback)
        assert pub.get_subscribers_count(BioEvent.STRESS_CHANGED.value)[BioEvent.STRESS_CHANGED.value] == 1

    def test_unsubscribe(self, publisher):
        pub, BioEvent = publisher
        callback = MagicMock()
        pub.subscribe(BioEvent.STRESS_CHANGED.value, callback)
        pub.unsubscribe(BioEvent.STRESS_CHANGED.value, callback)
        assert pub.get_subscribers_count(BioEvent.STRESS_CHANGED.value)[BioEvent.STRESS_CHANGED.value] == 0

    @pytest.mark.asyncio
    async def test_publish_calls_callback(self, publisher):
        pub, BioEvent = publisher
        callback = MagicMock()
        pub.subscribe(BioEvent.ENERGY_CHANGED.value, callback)
        await pub.publish(BioEvent.ENERGY_CHANGED, {"energy": 0.5})
        callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_publish_sync_and_async_callbacks(self, publisher):
        pub, BioEvent = publisher
        sync_cb = MagicMock()
        async_cb = AsyncMock()
        pub.subscribe(BioEvent.HORMONE_CHANGED.value, sync_cb)
        pub.subscribe(BioEvent.HORMONE_CHANGED.value, async_cb)
        await pub.publish(BioEvent.HORMONE_CHANGED, {"hormone": "test"})
        sync_cb.assert_called_once()
        async_cb.assert_awaited_once()

    def test_subscribe_count_all(self, publisher):
        pub, BioEvent = publisher
        pub.subscribe(BioEvent.EMOTION_CHANGED.value, MagicMock())
        pub.subscribe(BioEvent.MOOD_CHANGED.value, MagicMock())
        counts = pub.get_subscribers_count()
        assert counts[BioEvent.EMOTION_CHANGED.value] == 1
        assert counts[BioEvent.MOOD_CHANGED.value] == 1


class TestBiologicalIntegratorInit:
    """Test initialization with mocked subsystems."""

    def test_singleton(self, mock_subsystems):
        from core.bio.biological_integrator import BiologicalIntegrator
        a = BiologicalIntegrator()
        b = BiologicalIntegrator()
        assert a is b

    def test_subsystems_created(self, integrator):
        assert integrator.tactile_system is not None
        assert integrator.endocrine_system is not None
        assert integrator.nervous_system is not None
        assert integrator.neuroplasticity_system is not None
        assert integrator.emotional_system is not None

    def test_default_interactions(self, integrator):
        assert len(integrator.interactions) == 8


class TestProcessStressEvent:
    """Core tests for process_stress_event — called by §X #80 chain."""

    @pytest.mark.asyncio
    async def test_calls_nervous_system(self, integrator):
        await integrator.process_stress_event(0.5, 15.0)
        integrator.nervous_system.apply_stimulus.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_calls_endocrine_system(self, integrator):
        await integrator.process_stress_event(0.3, 10.0)
        integrator.endocrine_system.trigger_stress_response.assert_awaited_once_with(
            0.3, stress_type="acute"
        )

    @pytest.mark.asyncio
    async def test_calls_emotional_system(self, integrator):
        await integrator.process_stress_event(0.7, 20.0)
        integrator.emotional_system.apply_influence.assert_called_once_with(
            "physiological", "stress", 0.7, 0.8
        )

    @pytest.mark.asyncio
    async def test_intensity_float_guard(self, integrator):
        """Non-finite intensity should be clamped to 0."""
        await integrator.process_stress_event(float("nan"), 10.0)
        integrator.nervous_system.apply_stimulus.assert_awaited_once()
        call_args = integrator.nervous_system.apply_stimulus.await_args
        assert call_args[0][2] == 0.0

    @pytest.mark.asyncio
    async def test_chronic_vs_acute(self, integrator):
        """Duration >= 30 should mark stress as chronic."""
        await integrator.process_stress_event(0.5, 60.0)
        integrator.endocrine_system.trigger_stress_response.assert_awaited_once_with(
            0.5, stress_type="chronic"
        )


class TestProcessRelaxationEvent:
    """Core tests for process_relaxation_event — called by §X #80 chain."""

    @pytest.mark.asyncio
    async def test_calls_nervous_system(self, integrator):
        await integrator.process_relaxation_event(0.4)
        integrator.nervous_system.apply_stimulus.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_calls_endocrine_system(self, integrator):
        await integrator.process_relaxation_event(0.6)
        integrator.endocrine_system.trigger_emotional_response.assert_awaited_once_with(
            "relaxation", 0.6
        )

    @pytest.mark.asyncio
    async def test_calls_emotional_system(self, integrator):
        await integrator.process_relaxation_event(0.5)
        integrator.emotional_system.set_emotion_from_basic.assert_called_once()

    @pytest.mark.asyncio
    async def test_intensity_float_guard(self, integrator):
        await integrator.process_relaxation_event(float("inf"))
        call_args = integrator.nervous_system.apply_stimulus.await_args
        assert call_args[0][2] == 0.0

    @pytest.mark.asyncio
    async def test_default_intensity(self, integrator):
        await integrator.process_relaxation_event()
        integrator.endocrine_system.trigger_emotional_response.assert_awaited_once_with(
            "relaxation", 0.5
        )


class TestGetBiologicalState:
    """Test state retrieval used by sync/integration."""

    @pytest.mark.asyncio
    async def test_returns_dict(self, integrator):
        integrator.emotional_system.get_current_emotion_summary = MagicMock(
            return_value={"dominant": "calm", "intensity": 0.3}
        )
        integrator.nervous_system.arousal_level = 35
        integrator.endocrine_system.stress_level = 0.2
        integrator.endocrine_system.get_hormone_summary = MagicMock(
            return_value={"cortisol": 0.15}
        )

        state = integrator.get_biological_state()
        assert isinstance(state, dict)
        assert "arousal" in state
        assert "stress_level" in state
        assert "emotion" in state or "dominant_emotion" in state
        assert state["arousal"] == 35


class TestInitialize:
    """Test async initialization path."""

    @pytest.mark.asyncio
    async def test_initialize_subsystems(self, integrator):
        integrator.tactile_system.initialize = AsyncMock()
        integrator.endocrine_system.initialize = AsyncMock()
        integrator.nervous_system.initialize = AsyncMock()
        integrator.neuroplasticity_system.initialize = AsyncMock()
        integrator.emotional_system.initialize = AsyncMock()

        await integrator.initialize()
        integrator.tactile_system.initialize.assert_awaited_once()
        integrator.endocrine_system.initialize.assert_awaited_once()
        integrator.nervous_system.initialize.assert_awaited_once()
        integrator.neuroplasticity_system.initialize.assert_awaited_once()
        integrator.emotional_system.initialize.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_initialize_idempotent(self, integrator):
        integrator.tactile_system.initialize = AsyncMock()
        integrator.endocrine_system.initialize = AsyncMock()
        integrator.nervous_system.initialize = AsyncMock()
        integrator.neuroplasticity_system.initialize = AsyncMock()
        integrator.emotional_system.initialize = AsyncMock()

        await integrator.initialize()
        # Second call should be skipped because _running is True
        integrator._running = True
        await integrator.initialize()
        integrator.tactile_system.initialize.assert_awaited_once()
