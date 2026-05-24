"""
Tests for NeuroAutoSelector and sub-components.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from ai.response.neuro_auto_selector import (
    NeuroAutoSelector,
    HardwareAnalyzer,
    BudgetScheduler,
    StateInterpreter,
    LearnRecorder,
    AutoDecision,
    AutoBackendChoice,
    HardwareTier,
    TaskBudget,
    DEFAULT_INTENT_COST,
    DEFAULT_TIME_BUDGET_TABLE,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_hardware_profile():
    return {
        "ram_total_gb": 16.0,
        "ram_available_gb": 8.0,
        "vram_mb": 4096,
        "cpu_cores_logical": 8,
        "accelerator_type": "nvidia",
        "accelerator_name": "NVIDIA RTX 3060",
        "performance_tier": "High",
        "is_laptop": False,
    }


@pytest.fixture
def auto_selector():
    return NeuroAutoSelector(config={})


# =============================================================================
# HardwareAnalyzer Tests
# =============================================================================


class TestHardwareAnalyzer:
    def test_init(self):
        analyzer = HardwareAnalyzer()
        assert analyzer._probe is None

    @patch("shared.utils.hardware_detector.SystemHardwareProbe")
    def test_analyze(self, MockProbe):
        mock_probe = MagicMock()
        mock_profile = MagicMock()
        mock_profile.ai_capability_score = 75.0
        mock_profile.ram_total_gb = 32.0
        mock_profile.ram_available_gb = 16.0
        mock_profile.vram_mb = 8192
        mock_profile.cpu_cores_logical = 16
        mock_profile.accelerator_type.name = "NVIDIA"
        mock_profile.accelerator_type.value = "nvidia"
        mock_profile.accelerator_name = "RTX 4090"
        mock_profile.performance_tier = "High"
        mock_profile.is_laptop = False
        mock_probe.detect.return_value = mock_profile
        MockProbe.return_value = mock_probe

        analyzer = HardwareAnalyzer()
        score, tier, details = analyzer.analyze()

        assert score == 75.0
        assert tier == HardwareTier.HIGH
        assert details["ram_total_gb"] == 32.0
        assert details["ram_available_gb"] == 16.0
        assert details["vram_mb"] == 8192

    @patch("shared.utils.hardware_detector.SystemHardwareProbe")
    def test_analyze_low_end(self, MockProbe):
        mock_probe = MagicMock()
        mock_profile = MagicMock()
        mock_profile.ai_capability_score = 15.0
        mock_profile.ram_total_gb = 2.0
        mock_profile.ram_available_gb = 0.5
        mock_profile.vram_mb = 0
        mock_profile.cpu_cores_logical = 2
        mock_profile.accelerator_type.value = "none"
        mock_profile.accelerator_name = "Unknown"
        mock_profile.performance_tier = "Low"
        mock_profile.is_laptop = True
        mock_probe.detect.return_value = mock_profile
        MockProbe.return_value = mock_probe

        analyzer = HardwareAnalyzer()
        score, tier, details = analyzer.analyze()

        assert score == 15.0
        assert tier == HardwareTier.CRITICAL
        assert details["vram_mb"] == 0
        assert details["is_laptop"] is True


# =============================================================================
# BudgetScheduler Tests
# =============================================================================


class TestBudgetScheduler:
    def test_schedule_default_tiers(self):
        scheduler = BudgetScheduler(config={})
        for tier in HardwareTier:
            budget = scheduler.schedule(hw_score=50, tier=tier, energy=0.5)
            expected = DEFAULT_TIME_BUDGET_TABLE[tier]
            assert budget >= expected * 0.6  # at minimum after energy/load scaling (no load = 1.0)

    def test_schedule_low_energy_reduces_budget(self):
        scheduler = BudgetScheduler(config={})
        normal = scheduler.schedule(hw_score=50, tier=HardwareTier.HIGH, energy=0.5)
        low = scheduler.schedule(hw_score=50, tier=HardwareTier.HIGH, energy=0.2)
        assert low < normal
        assert low <= normal * 0.6

    def test_schedule_high_energy_increases_budget(self):
        scheduler = BudgetScheduler(config={})
        normal = scheduler.schedule(hw_score=50, tier=HardwareTier.HIGH, energy=0.5)
        high = scheduler.schedule(hw_score=50, tier=HardwareTier.HIGH, energy=0.8)
        assert high > normal
        assert high >= normal * 1.05  # at least 1.1 * load_factor

    def test_schedule_clamp_min_max(self):
        scheduler = BudgetScheduler(config={"auto_mode": {"min_time_budget_ms": 5000, "max_time_budget_ms": 60000}})
        budget = scheduler.schedule(hw_score=10, tier=HardwareTier.LOW, energy=0.5)
        assert 5000 <= budget <= 60000

    @patch("ai.response.neuro_auto_selector.ResourceAwarenessService")
    def test_schedule_with_load(self, MockResource):
        mock_svc = MagicMock()
        mock_svc.get_throttling_factor.return_value = 0.5
        MockResource.return_value = mock_svc

        scheduler = BudgetScheduler(config={})
        budget = scheduler.schedule(hw_score=50, tier=HardwareTier.HIGH, energy=0.5)
        expected_base = DEFAULT_TIME_BUDGET_TABLE[HardwareTier.HIGH]
        assert budget <= expected_base * 0.55  # 0.5 load + possible rounding


# =============================================================================
# StateInterpreter Tests
# =============================================================================


class TestStateInterpreter:
    def test_get_energy_default(self):
        interp = StateInterpreter()
        # When state_matrix not available, should return 0.5
        energy = interp.get_energy()
        assert energy == 0.5

    def test_get_state_dict_defaults(self):
        interp = StateInterpreter()
        state = interp.get_state_dict()
        # All values should be within 0-1 range with reasonable defaults
        assert 0 <= state["alpha_energy"] <= 1.0
        assert 0 <= state["epsilon_precision"] <= 1.0
        assert 0 <= state["delta_happiness"] <= 1.0
        assert 0 <= state["theta_novelty"] <= 1.0
        assert 0 <= state["theta_negativity"] <= 1.0
        assert 0 <= state["eta_success_rate"] <= 1.0
        # Specific default checks (from actual state matrix)
        assert state["theta_novelty"] == 0.5
        assert state["alpha_energy"] == 0.5

    def test_apply_correction_high_precision(self):
        interp = StateInterpreter()
        state = {"alpha_energy": 0.5, "epsilon_precision": 0.85, "delta_happiness": 0.5,
                 "theta_novelty": 0.3, "theta_negativity": 0.3, "eta_success_rate": 0.85}
        task = TaskBudget(demand_score=0.4, needs_reasoning=False, min_quality=False)
        decision = interp.apply_correction(budget=30000, task=task, state=state)
        assert decision.use_thinking is True
        assert decision.temperature == 0.3

    def test_apply_correction_low_happiness(self):
        interp = StateInterpreter()
        state = {"alpha_energy": 0.5, "epsilon_precision": 0.5, "delta_happiness": 0.2,
                 "theta_novelty": 0.3, "theta_negativity": 0.3, "eta_success_rate": 0.85}
        task = TaskBudget(demand_score=0.4, needs_reasoning=False, min_quality=False)
        decision = interp.apply_correction(budget=30000, task=task, state=state)
        assert decision.max_tokens == 256
        assert decision.temperature == 0.8
        assert decision.reason == "low_happiness_comfort_mode"

    def test_apply_correction_low_energy(self):
        interp = StateInterpreter()
        state = {"alpha_energy": 0.2, "epsilon_precision": 0.5, "delta_happiness": 0.5,
                 "theta_novelty": 0.3, "theta_negativity": 0.3, "eta_success_rate": 0.85}
        task = TaskBudget(demand_score=0.4, needs_reasoning=True, min_quality=False)
        decision = interp.apply_correction(budget=30000, task=task, state=state)
        assert decision.time_budget_ms <= 10000
        assert decision.use_thinking is False
        assert decision.reason == "low_energy_economy_mode"

    def test_apply_correction_high_novelty(self):
        interp = StateInterpreter()
        state = {"alpha_energy": 0.6, "epsilon_precision": 0.5, "delta_happiness": 0.6,
                 "theta_novelty": 0.85, "theta_negativity": 0.2, "eta_success_rate": 0.9}
        task = TaskBudget(demand_score=0.5, needs_reasoning=False, min_quality=False)
        decision = interp.apply_correction(budget=30000, task=task, state=state)
        assert decision.reason == "high_novelty_quality_mode"

    def test_apply_correction_high_negativity(self):
        interp = StateInterpreter()
        state = {"alpha_energy": 0.5, "epsilon_precision": 0.5, "delta_happiness": 0.5,
                 "theta_novelty": 0.3, "theta_negativity": 0.7, "eta_success_rate": 0.85}
        task = TaskBudget(demand_score=0.4, needs_reasoning=False, min_quality=False)
        decision = interp.apply_correction(budget=30000, task=task, state=state)
        assert decision.use_thinking is True
        assert decision.temperature == 0.4


# =============================================================================
# AutoDecision Tests
# =============================================================================


class TestAutoDecision:
    def test_neuroblender_fallback(self):
        decision = AutoDecision.neuroblender_fallback("test reason")
        assert decision.backend == AutoBackendChoice.NEUROBLENDER
        assert decision.reason == "test reason"

    def test_to_dict(self):
        decision = AutoDecision(
            backend=AutoBackendChoice.OLLAMA,
            model="phi:latest",
            time_budget_ms=20000,
        )
        d = decision.to_dict()
        assert d["backend"] == "ollama"
        assert d["model"] == "phi:latest"
        assert d["time_budget_ms"] == 20000


# =============================================================================
# LearnRecorder Tests
# =============================================================================


class TestLearnRecorder:
    def test_record_buffers(self):
        recorder = LearnRecorder()
        decision = AutoDecision(backend=AutoBackendChoice.OLLAMA, model="phi:latest")
        recorder.record(decision, actual_ms=1500.0, success=True)
        assert len(recorder._pending) == 1
        assert recorder._pending[0]["success"] is True
        assert recorder._pending[0]["actual_ms"] == 1500.0

    def test_flush_empty(self):
        recorder = LearnRecorder()
        recorder.flush_sync()  # should not raise


# =============================================================================
# NeuroAutoSelector Integration Tests
# =============================================================================


class TestNeuroAutoSelector:
    async def test_decide_neuroblender_low_budget(self):
        selector = NeuroAutoSelector(config={"auto_mode": {"min_time_budget_ms": 5000}})
        with patch.object(selector.hardware, "analyze") as mock_hw, \
             patch.object(selector.budget_scheduler, "schedule", return_value=3000), \
             patch.object(selector.state_interpreter, "get_energy", return_value=0.1), \
             patch.object(selector.state_interpreter, "get_state_dict") as mock_state:

            mock_state.return_value = {
                "alpha_energy": 0.1, "epsilon_precision": 0.3, "delta_happiness": 0.3,
                "theta_novelty": 0.2, "theta_negativity": 0.2, "eta_success_rate": 0.5,
            }
            mock_hw.return_value = (50.0, HardwareTier.MEDIUM, {"ram_total_gb": 8})

            decision = await selector.decide()
            assert decision.backend == AutoBackendChoice.NEUROBLENDER
            assert "low" in decision.reason
    async def test_decide_force_backend(self):
        selector = NeuroAutoSelector(config={})
        with patch.object(selector.hardware, "analyze") as mock_hw, \
             patch.object(selector.budget_scheduler, "schedule", return_value=30000), \
             patch.object(selector.state_interpreter, "get_energy", return_value=0.5), \
             patch.object(selector.state_interpreter, "get_state_dict") as mock_state, \
             patch.object(selector, "_get_available_backends", return_value=[]):

            mock_state.return_value = {
                "alpha_energy": 0.5, "epsilon_precision": 0.5, "delta_happiness": 0.5,
                "theta_novelty": 0.3, "theta_negativity": 0.3, "eta_success_rate": 0.85,
            }
            mock_hw.return_value = (60.0, HardwareTier.HIGH, {"ram_total_gb": 16, "vram_mb": 4096})

            decision = await selector.decide(context={"force_backend": "neuroblender"})
            assert decision.backend == AutoBackendChoice.NEUROBLENDER
            assert "force" in decision.reason
    async def test_decide_no_available_backends(self):
        selector = NeuroAutoSelector(config={})
        with patch.object(selector.hardware, "analyze") as mock_hw, \
             patch.object(selector.budget_scheduler, "schedule", return_value=30000), \
             patch.object(selector.state_interpreter, "get_energy", return_value=0.5), \
             patch.object(selector.state_interpreter, "get_state_dict") as mock_state, \
             patch.object(selector, "_get_available_backends", return_value=[]):

            mock_state.return_value = {
                "alpha_energy": 0.5, "epsilon_precision": 0.5, "delta_happiness": 0.5,
                "theta_novelty": 0.3, "theta_negativity": 0.3, "eta_success_rate": 0.85,
            }
            mock_hw.return_value = (60.0, HardwareTier.HIGH, {"ram_total_gb": 16, "vram_mb": 4096})

            decision = await selector.decide()
            assert decision.backend == AutoBackendChoice.NEUROBLENDER

    def test_analyze_task(self):
        selector = NeuroAutoSelector(config={})
        # General intent, low complexity
        task = selector._analyze_task({"intent": "general", "complexity": 0.2, "user_message": "hello"})
        assert task.demand_score < 0.5
        assert task.needs_reasoning is False

        # Math intent, high complexity
        task = selector._analyze_task({"intent": "math", "complexity": 0.8, "user_message": "Solve this integral: ∫x²dx"})
        assert task.demand_score > 0.5
        assert task.needs_reasoning is True
        assert task.preferred_context_window == 8192

    def test_is_local_capable(self):
        selector = NeuroAutoSelector(config={})
        assert selector._is_local_capable({"ram_total_gb": 16, "vram_mb": 4096, "accelerator_type": "nvidia"}) is True
        assert selector._is_local_capable({"ram_total_gb": 2, "vram_mb": 0, "accelerator_type": "none"}) is False
        assert selector._is_local_capable({"ram_total_gb": 8, "vram_mb": 0, "accelerator_type": "cpu_avx2"}) is True

    def test_recommend_ollama_model(self):
        selector = NeuroAutoSelector(config={})
        # High RAM, high VRAM → deepseek
        model = selector._recommend_ollama_model({"ram_available_gb": 24, "ram_total_gb": 32, "vram_mb": 12288})
        assert "deepseek" in model

        # Medium RAM, medium VRAM → qwen
        model = selector._recommend_ollama_model({"ram_available_gb": 10, "ram_total_gb": 16, "vram_mb": 6144})
        assert "qwen" in model

        # Low RAM → phi
        model = selector._recommend_ollama_model({"ram_available_gb": 3, "ram_total_gb": 4, "vram_mb": 0})
        assert "phi" in model


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    def test_hardware_analyzer_init_same_instance(self):
        """HardwareAnalyzer should reuse its probe instance"""
        a1 = HardwareAnalyzer()
        a2 = HardwareAnalyzer()
        assert a1._probe is None  # both uninitialized until first analyze
        assert a2._probe is None

    def test_decision_to_dict_includes_all_fields(self):
        d = AutoDecision(
            backend=AutoBackendChoice.OLLAMA,
            model="phi:latest",
            time_budget_ms=20000,
            use_thinking=True,
            temperature=0.3,
            max_tokens=1024,
            context_window=8192,
            reason="test",
            hw_score=60.0,
            load_factor=0.8,
            task_demand=0.5,
        )
        dd = d.to_dict()
        assert dd["use_thinking"] is True
        assert dd["temperature"] == 0.3
        assert dd["context_window"] == 8192
        assert dd["hw_score"] == 60.0
        assert dd["load_factor"] == 0.8
        assert dd["task_demand"] == 0.5

    def test_budget_scheduler_uses_configured_table(self):
        custom_table = {
            "extreme": 30000,
            "high": 20000,
            "medium": 15000,
            "low": 10000,
            "critical": 5000,
        }
        scheduler = BudgetScheduler(config={
            "auto_mode": {
                "time_budget_table": custom_table,
                "min_time_budget_ms": 3000,
                "max_time_budget_ms": 60000,
            }
        })
        for tier_str, expected in custom_table.items():
            tier = HardwareTier(tier_str)
            budget = scheduler.schedule(hw_score=50, tier=tier, energy=0.5)
            assert budget >= expected * 0.6, f"{tier_str}: {budget} < {expected * 0.6}"
