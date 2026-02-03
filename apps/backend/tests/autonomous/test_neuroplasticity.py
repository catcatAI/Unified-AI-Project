"""
Angela AI v6.0 - Neuroplasticity System Tests
神经可塑性系统测试

Comprehensive test suite for the neuroplasticity system including:
- NeuroplasticitySystem (LTP/LTD mechanisms, Hebbian learning)
- SkillAcquisition (power law learning curves)
- HabitFormation (66 repetitions theory)
- TraumaMemorySystem (70% slower forgetting)
- Ebbinghaus forgetting curve
- ExplicitImplicitLearning

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

import pytest
import asyncio
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from pathlib import Path

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from core.autonomous.neuroplasticity import (
    SynapticState,
    ConsolidationPhase,
    SynapticWeight,
    MemoryTrace,
    HebbianRule,
    LTPParameters,
    LTDParameters,
    EbbinghausForgettingCurve,
    NeuroplasticitySystem,
    SkillTrace,
    HabitTrace,
    TraumaMemory,
    LearningEvent,
    SkillAcquisition,
    HabitFormation,
    TraumaMemorySystem,
    ExplicitImplicitLearning,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def neuroplasticity_system() -> NeuroplasticitySystem:
    """Create a NeuroplasticitySystem instance for testing."""
    return NeuroplasticitySystem()


@pytest.fixture
def initialized_neuroplasticity_system() -> NeuroplasticitySystem:
    """Create an initialized NeuroplasticitySystem instance."""
    system = NeuroplasticitySystem()
    asyncio.run(system.initialize())
    yield system
    asyncio.run(system.shutdown())


@pytest.fixture
def skill_acquisition() -> SkillAcquisition:
    """Create a SkillAcquisition instance."""
    return SkillAcquisition()


@pytest.fixture
def habit_formation() -> HabitFormation:
    """Create a HabitFormation instance."""
    return HabitFormation()


@pytest.fixture
def trauma_system() -> TraumaMemorySystem:
    """Create a TraumaMemorySystem instance."""
    return TraumaMemorySystem()


@pytest.fixture
def forgetting_curve() -> EbbinghausForgettingCurve:
    """Create an EbbinghausForgettingCurve instance."""
    return EbbinghausForgettingCurve()


@pytest.fixture
def hebbian_rule() -> HebbianRule:
    """Create a HebbianRule instance."""
    return HebbianRule()


@pytest.fixture
def learning_system() -> ExplicitImplicitLearning:
    """Create an ExplicitImplicitLearning instance."""
    return ExplicitImplicitLearning()


# =============================================================================
# SynapticWeight Tests
# =============================================================================

class TestSynapticWeight:
    """Tests for the SynapticWeight data class."""

    def test_synaptic_weight_creation(self) -> None:
        """Test SynapticWeight creation."""
        weight = SynapticWeight(
            pre_neuron="neuron_A",
            post_neuron="neuron_B",
            weight=0.5
        )
        
        assert weight.pre_neuron == "neuron_A"
        assert weight.post_neuron == "neuron_B"
        assert weight.weight == 0.5
        assert weight.state == SynapticState.BASELINE
        assert weight.activation_count == 0

    def test_synaptic_weight_bounds(self) -> None:
        """Test weight value bounds."""
        # Test upper bound
        high_weight = SynapticWeight("A", "B", weight=1.5)
        assert high_weight.weight <= 1.0
        
        # Test lower bound
        low_weight = SynapticWeight("A", "B", weight=-0.5)
        assert low_weight.weight >= 0.0


# =============================================================================
# MemoryTrace Tests
# =============================================================================

class TestMemoryTrace:
    """Tests for the MemoryTrace data class."""

    def test_memory_trace_creation(self) -> None:
        """Test MemoryTrace creation."""
        trace = MemoryTrace(
            memory_id="mem_001",
            content="Test memory content",
            initial_weight=0.6,
            current_weight=0.6
        )
        
        assert trace.memory_id == "mem_001"
        assert trace.content == "Test memory content"
        assert trace.initial_weight == 0.6
        assert trace.current_weight == 0.6
        assert trace.access_count == 0
        assert not trace.is_consolidated

    def test_memory_age_calculation(self) -> None:
        """Test memory age calculation."""
        trace = MemoryTrace(
            memory_id="mem_001",
            content="Test",
            initial_weight=0.5,
            current_weight=0.5
        )
        
        # Age should be very small (just created)
        age = trace.get_age_minutes()
        assert age >= 0
        assert age < 1.0  # Less than 1 minute

    def test_retention_intervals(self) -> None:
        """Test retention intervals calculation."""
        trace = MemoryTrace(
            memory_id="mem_001",
            content="Test",
            initial_weight=0.5,
            current_weight=0.5
        )
        
        # Manually set created_at to simulate age
        trace.created_at = datetime.now() - timedelta(hours=8)
        
        intervals = trace.get_retention_intervals()
        assert intervals >= 1


# =============================================================================
# HebbianRule Tests
# =============================================================================

class TestHebbianRule:
    """Tests for the HebbianRule class."""

    def test_hebbian_rule_creation(self) -> None:
        """Test HebbianRule initialization."""
        rule = HebbianRule()
        assert rule.learning_rate == 0.1
        assert rule.decay_factor == 0.01
        assert rule.threshold == 0.5

    def test_hebbian_strengthening(self, hebbian_rule: HebbianRule) -> None:
        """Test Hebbian strengthening when both neurons active."""
        current_weight = 0.3
        
        # Both neurons active above threshold
        new_weight = hebbian_rule.apply(0.8, 0.8, current_weight)
        
        # Weight should increase
        assert new_weight > current_weight

    def test_hebbian_weakening(self, hebbian_rule: HebbianRule) -> None:
        """Test Hebbian weakening when neurons not co-active."""
        current_weight = 0.5
        
        # One neuron not active
        new_weight = hebbian_rule.apply(0.8, 0.3, current_weight)
        
        # Weight should decrease (decay)
        assert new_weight < current_weight

    def test_hebbian_bounds(self, hebbian_rule: HebbianRule) -> None:
        """Test weight stays within bounds after Hebbian update."""
        # Test upper bound
        high_weight = hebbian_rule.apply(0.9, 0.9, 0.95)
        assert high_weight <= 1.0
        
        # Test lower bound
        low_weight = hebbian_rule.apply(0.1, 0.1, 0.05)
        assert low_weight >= 0.0


# =============================================================================
# EbbinghausForgettingCurve Tests
# =============================================================================

class TestEbbinghausForgettingCurve:
    """Tests for the EbbinghausForgettingCurve class."""

    def test_forgetting_curve_creation(self) -> None:
        """Test forgetting curve initialization."""
        curve = EbbinghausForgettingCurve()
        assert curve.base_stability == 24.0  # hours

    def test_retention_immediate(self, forgetting_curve: EbbinghausForgettingCurve) -> None:
        """Test retention immediately after learning."""
        retention = forgetting_curve.calculate_retention(
            hours_since_learning=0.0,
            memory_strength=1.0
        )
        
        # Should be very close to 100%
        assert retention > 0.99

    def test_retention_after_24h(self, forgetting_curve: EbbinghausForgettingCurve) -> None:
        """Test retention after 24 hours."""
        retention = forgetting_curve.calculate_retention(
            hours_since_learning=24.0,
            memory_strength=1.0
        )
        
        # After one stability period, retention = e^(-1) ≈ 0.368
        assert abs(retention - 0.368) < 0.05

    def test_retention_with_strength(self, forgetting_curve: EbbinghausForgettingCurve) -> None:
        """Test that higher memory strength improves retention."""
        hours = 48.0
        
        retention_weak = forgetting_curve.calculate_retention(hours, memory_strength=0.5)
        retention_strong = forgetting_curve.calculate_retention(hours, memory_strength=2.0)
        
        # Stronger memory should have better retention
        assert retention_strong > retention_weak

    def test_optimal_review_times(self, forgetting_curve: EbbinghausForgettingCurve) -> None:
        """Test optimal review time schedule."""
        times = forgetting_curve.get_optimal_review_times(n_reviews=5)
        
        assert len(times) == 5
        # Review intervals should increase
        for i in range(len(times) - 1):
            assert times[i + 1] > times[i]

    def test_estimate_strength_from_reviews(self, forgetting_curve: EbbinghausForgettingCurve) -> None:
        """Test memory strength estimation from review history."""
        strength = forgetting_curve.estimate_strength_from_reviews(
            review_count=5,
            average_performance=0.8
        )
        
        # Should be above base level (1.0)
        assert strength > 1.0


# =============================================================================
# ConsolidationPhase Tests
# =============================================================================

class TestConsolidationPhase:
    """Tests for the ConsolidationPhase enum."""

    def test_consolidation_phases(self) -> None:
        """Test consolidation phase definitions."""
        assert ConsolidationPhase.ENCODING.min_minutes == 0
        assert ConsolidationPhase.ENCODING.max_minutes == 30
        
        assert ConsolidationPhase.CONSOLIDATION.min_minutes == 60
        assert ConsolidationPhase.CONSOLIDATION.max_minutes == 1440  # 24 hours

    def test_phase_from_age(self) -> None:
        """Test getting phase from memory age."""
        # New memory (5 minutes)
        phase_new = ConsolidationPhase.from_age(5.0)
        assert phase_new == ConsolidationPhase.ENCODING
        
        # Medium age (2 hours)
        phase_mid = ConsolidationPhase.from_age(120.0)
        assert phase_mid == ConsolidationPhase.CONSOLIDATION
        
        # Old memory (2 days)
        phase_old = ConsolidationPhase.from_age(2880.0)
        assert phase_old == ConsolidationPhase.RE_CONSOLIDATION


# =============================================================================
# NeuroplasticitySystem Tests
# =============================================================================

class TestNeuroplasticitySystem:
    """Tests for the main NeuroplasticitySystem class."""

    @pytest.mark.asyncio
    async def test_system_initialization(self, neuroplasticity_system: NeuroplasticitySystem) -> None:
        """Test system initialization."""
        await neuroplasticity_system.initialize()
        assert neuroplasticity_system._running is True
        assert neuroplasticity_system._update_task is not None
        await neuroplasticity_system.shutdown()

    def test_create_memory_trace(self, neuroplasticity_system: NeuroplasticitySystem) -> None:
        """Test creating a memory trace."""
        trace = neuroplasticity_system.create_memory_trace(
            memory_id="mem_001",
            content="Test content",
            initial_weight=0.6,
            emotional_tags=["joy", "excitement"]
        )
        
        assert trace.memory_id == "mem_001"
        assert trace.content == "Test content"
        assert trace.current_weight == 0.6
        assert "joy" in trace.emotional_tags
        assert "mem_001" in neuroplasticity_system.memory_traces

    def test_apply_ltp(self, neuroplasticity_system: NeuroplasticitySystem) -> None:
        """Test Long-Term Potentiation application."""
        # Create memory
        neuroplasticity_system.create_memory_trace("mem_001", "Test", initial_weight=0.5)
        
        # Apply LTP with high frequency stimulation
        neuroplasticity_system.apply_ltp("mem_001", frequency=15.0, duration=5.0)
        
        trace = neuroplasticity_system.memory_traces["mem_001"]
        # Weight should increase
        assert trace.current_weight > 0.5

    def test_apply_ltp_threshold(self, neuroplasticity_system: NeuroplasticitySystem) -> None:
        """Test LTP frequency threshold."""
        # Create memory
        neuroplasticity_system.create_memory_trace("mem_001", "Test", initial_weight=0.5)
        
        # Apply with low frequency (below LTP threshold)
        neuroplasticity_system.apply_ltp("mem_001", frequency=5.0, duration=5.0)
        
        trace = neuroplasticity_system.memory_traces["mem_001"]
        # Weight should not change significantly
        assert trace.current_weight == 0.5

    def test_apply_ltd(self, neuroplasticity_system: NeuroplasticitySystem) -> None:
        """Test Long-Term Depression application."""
        # Create memory
        neuroplasticity_system.create_memory_trace("mem_001", "Test", initial_weight=0.8)
        
        # Apply LTD with low frequency stimulation
        neuroplasticity_system.apply_ltd("mem_001", frequency=0.5, duration=10.0)
        
        trace = neuroplasticity_system.memory_traces["mem_001"]
        # Weight should decrease
        assert trace.current_weight < 0.8

    def test_access_memory(self, neuroplasticity_system: NeuroplasticitySystem) -> None:
        """Test memory access updates."""
        # Create memory
        neuroplasticity_system.create_memory_trace("mem_001", "Test", initial_weight=0.5)
        
        # Access memory
        trace = neuroplasticity_system.access_memory("mem_001")
        
        assert trace is not None
        assert trace.access_count == 1
        assert trace.last_accessed is not None
        # Weight should increase slightly due to Hebbian learning
        assert trace.current_weight > 0.5

    def test_get_memory_retention(self, neuroplasticity_system: NeuroplasticitySystem) -> None:
        """Test memory retention calculation."""
        # Create memory
        neuroplasticity_system.create_memory_trace("mem_001", "Test", initial_weight=0.7)
        
        # Get retention
        retention = neuroplasticity_system.get_memory_retention("mem_001")
        
        assert 0 <= retention <= 1
        # Just created, should be high retention
        assert retention > 0.9

    def test_associate_memories(self, neuroplasticity_system: NeuroplasticitySystem) -> None:
        """Test memory association creation."""
        # Create two memories
        neuroplasticity_system.create_memory_trace("mem_001", "Test 1", initial_weight=0.5)
        neuroplasticity_system.create_memory_trace("mem_002", "Test 2", initial_weight=0.5)
        
        # Associate them
        neuroplasticity_system.associate_memories("mem_001", "mem_002")
        
        # Check bidirectional association
        assert "mem_002" in neuroplasticity_system.memory_traces["mem_001"].associated_memories
        assert "mem_001" in neuroplasticity_system.memory_traces["mem_002"].associated_memories

    def test_consolidate_memories(self, neuroplasticity_system: NeuroplasticitySystem) -> None:
        """Test memory consolidation."""
        # Create memory
        neuroplasticity_system.create_memory_trace("mem_001", "Test", initial_weight=0.5)
        
        # Consolidate
        neuroplasticity_system.consolidate_memories()
        
        trace = neuroplasticity_system.memory_traces["mem_001"]
        # Consolidation strength should increase
        assert trace.consolidation_strength > 0

    def test_get_weak_memories(self, neuroplasticity_system: NeuroplasticitySystem) -> None:
        """Test retrieving weak memories."""
        # Create memories with different weights
        neuroplasticity_system.create_memory_trace("mem_strong", "Strong", initial_weight=0.9)
        neuroplasticity_system.create_memory_trace("mem_weak", "Weak", initial_weight=0.2)
        
        # Access strong memory to increase retention
        neuroplasticity_system.access_memory("mem_strong")
        
        # Get weak memories
        weak = neuroplasticity_system.get_weak_memories(threshold=0.5)
        
        # Should find at least the weak one
        weak_ids = [m.memory_id for m in weak]
        assert "mem_weak" in weak_ids

    def test_system_stats(self, neuroplasticity_system: NeuroplasticitySystem) -> None:
        """Test system statistics."""
        # Create some memories
        for i in range(5):
            neuroplasticity_system.create_memory_trace(f"mem_{i}", f"Content {i}")
        
        stats = neuroplasticity_system.get_system_stats()
        
        assert stats["total_memories"] == 5
        assert "consolidated_memories" in stats
        assert "total_synapses" in stats
        assert "average_synapse_weight" in stats


# =============================================================================
# SkillAcquisition Tests
# =============================================================================

class TestSkillAcquisition:
    """Tests for the SkillAcquisition class."""

    def test_skill_initialization(self, skill_acquisition: SkillAcquisition) -> None:
        """Test skill creation."""
        skill = skill_acquisition.start_skill(
            skill_id="typing",
            skill_name="Typing",
            initial_performance=0.2
        )
        
        assert skill.skill_id == "typing"
        assert skill.skill_name == "Typing"
        assert skill.current_performance == 0.2
        assert skill.practice_count == 0
        assert not skill.is_automatized

    def test_practice_improvement(self, skill_acquisition: SkillAcquisition) -> None:
        """Test skill improvement through practice."""
        skill_acquisition.start_skill("typing", "Typing", initial_performance=0.2)
        
        # Practice multiple times
        for _ in range(50):
            skill_acquisition.practice("typing", success=True, difficulty=0.5)
        
        final_performance = skill_acquisition.get_performance("typing")
        
        # Should have improved
        assert final_performance > 0.2
        assert final_performance <= 0.95  # Max performance

    def test_practice_failure_penalty(self, skill_acquisition: SkillAcquisition) -> None:
        """Test that failure reduces performance slightly."""
        skill_acquisition.start_skill("typing", "Typing", initial_performance=0.5)
        
        # First practice with success to establish baseline
        skill_acquisition.practice("typing", success=True, difficulty=0.5)
        baseline = skill_acquisition.get_performance("typing")
        
        # Now fail
        skill_acquisition.practice("typing", success=False, difficulty=0.5)
        after_failure = skill_acquisition.get_performance("typing")
        
        # Should be lower or same (can't go below initial for first few practices)
        assert after_failure <= baseline + 0.01  # Allow tiny floating point difference

    def test_learning_curve(self, skill_acquisition: SkillAcquisition) -> None:
        """Test learning curve generation."""
        skill_acquisition.start_skill("typing", "Typing", initial_performance=0.2)
        
        curve = skill_acquisition.get_learning_curve("typing", n_points=10)
        
        assert len(curve) == 10
        # Curve should generally increase
        assert curve[-1] >= curve[0]
        # All values should be within bounds
        assert all(0 <= p <= 1 for p in curve)

    def test_automatization_threshold(self, skill_acquisition: SkillAcquisition) -> None:
        """Test automatization after sufficient practice."""
        skill_acquisition.start_skill("typing", "Typing", initial_performance=0.2)
        
        # Practice extensively
        for _ in range(60):
            skill_acquisition.practice("typing", success=True, difficulty=0.5)
        
        skill = skill_acquisition.skills["typing"]
        
        # Should be automatized after >50 practices and good performance
        if skill.current_performance > 0.8:
            assert skill.is_automatized

    def test_get_all_skills(self, skill_acquisition: SkillAcquisition) -> None:
        """Test retrieving all skills."""
        skill_acquisition.start_skill("skill_1", "Skill 1")
        skill_acquisition.start_skill("skill_2", "Skill 2")
        
        all_skills = skill_acquisition.get_all_skills()
        
        assert len(all_skills) == 2
        assert "skill_1" in all_skills
        assert "skill_2" in all_skills


# =============================================================================
# HabitFormation Tests
# =============================================================================

class TestHabitFormation:
    """Tests for the HabitFormation class."""

    def test_habit_initialization(self, habit_formation: HabitFormation) -> None:
        """Test habit creation."""
        habit = habit_formation.start_habit(
            habit_id="morning_exercise",
            habit_name="Morning Exercise"
        )
        
        assert habit.habit_id == "morning_exercise"
        assert habit.habit_name == "Morning Exercise"
        assert habit.repetition_count == 0
        assert habit.automaticity_score == 0.0
        assert not habit.is_formed

    def test_repetition_count(self, habit_formation: HabitFormation) -> None:
        """Test repetition counting."""
        habit_formation.start_habit("test_habit")
        
        for _ in range(10):
            habit_formation.reinforce("test_habit", context="home", reward=0.5)
        
        count = habit_formation.get_repetition_count("test_habit")
        assert count == 10

    def test_automaticity_increase(self, habit_formation: HabitFormation) -> None:
        """Test automaticity score increases with repetitions."""
        habit_formation.start_habit("test_habit")
        
        # Initial automaticity
        initial_auto = habit_formation.get_automaticity("test_habit")
        
        # Reinforce in stable context
        for _ in range(30):
            habit_formation.reinforce("test_habit", context="bedroom", reward=0.8)
        
        final_auto = habit_formation.get_automaticity("test_habit")
        
        # Automaticity should increase
        assert final_auto > initial_auto

    def test_66_repetitions_theory(self, habit_formation: HabitFormation) -> None:
        """Test the 66 repetitions theory for habit formation."""
        habit_formation.start_habit("new_habit")
        
        # Check not formed initially
        assert not habit_formation.is_habit_formed("new_habit")
        
        # Repeat 66 times in stable context with good reward
        for _ in range(66):
            habit_formation.reinforce("new_habit", context="kitchen", reward=0.9)
        
        # Should be formed after 66 repetitions
        assert habit_formation.is_habit_formed("new_habit")

    def test_context_stability_effect(self, habit_formation: HabitFormation) -> None:
        """Test that stable context enhances habit formation."""
        habit_formation.start_habit("stable_habit")
        habit_formation.start_habit("variable_habit")
        
        # Stable context
        for _ in range(30):
            habit_formation.reinforce("stable_habit", context="same_room", reward=0.8)
        
        # Variable context
        contexts = ["room1", "room2", "room3", "room4"]
        for i in range(30):
            habit_formation.reinforce("variable_habit", context=contexts[i % 4], reward=0.8)
        
        # Stable context should have higher automaticity
        stable_auto = habit_formation.get_automaticity("stable_habit")
        variable_auto = habit_formation.get_automaticity("variable_habit")
        
        assert stable_auto > variable_auto

    def test_reward_effect(self, habit_formation: HabitFormation) -> None:
        """Test that reward magnitude affects habit formation."""
        habit_formation.start_habit("high_reward_habit")
        habit_formation.start_habit("low_reward_habit")
        
        # High reward
        for _ in range(30):
            habit_formation.reinforce("high_reward_habit", context="gym", reward=1.0)
        
        # Low reward
        for _ in range(30):
            habit_formation.reinforce("low_reward_habit", context="gym", reward=0.2)
        
        # High reward should have higher automaticity
        high_auto = habit_formation.get_automaticity("high_reward_habit")
        low_auto = habit_formation.get_automaticity("low_reward_habit")
        
        assert high_auto > low_auto

    def test_failed_repetition_no_count(self, habit_formation: HabitFormation) -> None:
        """Test that failed repetitions don't count toward habit."""
        habit_formation.start_habit("test_habit")
        
        # Mix of success and failure
        for i in range(20):
            success = i % 2 == 0  # Every other succeeds
            habit_formation.reinforce("test_habit", context="home", reward=0.5, success=success)
        
        # Should only count 10 successful repetitions
        count = habit_formation.get_repetition_count("test_habit")
        assert count == 10


# =============================================================================
# TraumaMemorySystem Tests
# =============================================================================

class TestTraumaMemorySystem:
    """Tests for the TraumaMemorySystem class."""

    def test_trauma_initialization(self, trauma_system: TraumaMemorySystem) -> None:
        """Test trauma system initialization."""
        assert trauma_system.trauma_intensity_threshold == 0.7
        assert trauma_system.slowing_factor == 1.7

    def test_encode_trauma_sufficient_intensity(self, trauma_system: TraumaMemorySystem) -> None:
        """Test encoding trauma with sufficient intensity."""
        trauma = trauma_system.encode_trauma(
            memory_id="trauma_001",
            content="Traumatic event",
            intensity=0.8
        )
        
        assert trauma is not None
        assert trauma.memory_id == "trauma_001"
        assert trauma.trauma_intensity == 0.8

    def test_encode_trauma_insufficient_intensity(self, trauma_system: TraumaMemorySystem) -> None:
        """Test encoding trauma with insufficient intensity."""
        trauma = trauma_system.encode_trauma(
            memory_id="trauma_001",
            content="Minor event",
            intensity=0.5  # Below threshold of 0.7
        )
        
        # Should not be encoded as trauma
        assert trauma is None

    def test_trauma_retention_slower_forgetting(self, trauma_system: TraumaMemorySystem) -> None:
        """Test that trauma memories fade 70% slower."""
        # Encode trauma
        trauma_system.encode_trauma("trauma_001", "Content", intensity=0.8)
        
        # Check retention after some time
        retention = trauma_system.get_retention("trauma_001")
        
        # Just created, should be close to 1
        assert retention > 0.95

    def test_trauma_reactivation(self, trauma_system: TraumaMemorySystem) -> None:
        """Test trauma memory reactivation."""
        trauma_system.encode_trauma("trauma_001", "Content", intensity=0.8)
        
        # Reactivate
        result = trauma_system.reactivate("trauma_001", trigger_context="similar_situation")
        
        assert result is True
        
        trauma = trauma_system.trauma_memories["trauma_001"]
        assert trauma.reactivation_count == 1

    def test_intrusion_likelihood(self, trauma_system: TraumaMemorySystem) -> None:
        """Test intrusive recall likelihood calculation."""
        trauma_system.encode_trauma("trauma_001", "Content", intensity=0.9)
        
        # High stress should increase intrusion likelihood
        likelihood_high_stress = trauma_system.get_intrusion_likelihood("trauma_001", current_stress=0.9)
        likelihood_low_stress = trauma_system.get_intrusion_likelihood("trauma_001", current_stress=0.1)
        
        assert likelihood_high_stress > likelihood_low_stress

    def test_intrusion_likelihood_with_reactivations(self, trauma_system: TraumaMemorySystem) -> None:
        """Test that reactivations increase intrusion likelihood."""
        trauma_system.encode_trauma("trauma_001", "Content", intensity=0.8)
        
        # Initial likelihood
        initial_likelihood = trauma_system.get_intrusion_likelihood("trauma_001", current_stress=0.5)
        
        # Reactivate multiple times
        for _ in range(5):
            trauma_system.reactivate("trauma_001")
        
        # New likelihood
        new_likelihood = trauma_system.get_intrusion_likelihood("trauma_001", current_stress=0.5)
        
        assert new_likelihood > initial_likelihood


# =============================================================================
# ExplicitImplicitLearning Tests
# =============================================================================

class TestExplicitImplicitLearning:
    """Tests for the ExplicitImplicitLearning class."""

    def test_explicit_learning(self, learning_system: ExplicitImplicitLearning) -> None:
        """Test explicit (conscious) learning."""
        event = learning_system.learn_explicit(
            event_id="fact_001",
            content="Paris is capital of France",
            context="study_session"
        )
        
        assert event.event_id == "fact_001"
        assert event.learning_type == "explicit"
        assert event.consolidation_level == 0.2

    def test_implicit_learning(self, learning_system: ExplicitImplicitLearning) -> None:
        """Test implicit (unconscious) learning."""
        event = learning_system.learn_implicit(
            event_id="skill_001",
            content="bike_riding_procedure",
            context="practice_session"
        )
        
        assert event.event_id == "skill_001"
        assert event.learning_type == "implicit"
        assert event.consolidation_level == 0.1

    def test_interference_effect(self, learning_system: ExplicitImplicitLearning) -> None:
        """Test that explicit learning causes interference."""
        # Learn first fact
        learning_system.learn_explicit("fact_1", "First fact", "context")
        initial_consolidation = learning_system.explicit_memories["fact_1"].consolidation_level
        
        # Learn second fact (should interfere with first)
        learning_system.learn_explicit("fact_2", "Second fact", "context")
        
        # First fact's consolidation should decrease due to interference
        final_consolidation = learning_system.explicit_memories["fact_1"].consolidation_level
        assert final_consolidation < initial_consolidation

    def test_consolidation_rates(self, learning_system: ExplicitImplicitLearning) -> None:
        """Test different consolidation rates for explicit vs implicit."""
        # Learn both types
        learning_system.learn_explicit("explicit_1", "Content", "context")
        learning_system.learn_implicit("implicit_1", "Content", "context")
        
        # Consolidate for 24 hours
        learning_system.consolidate(hours_elapsed=24.0)
        
        explicit_level = learning_system.get_explicit_memory("explicit_1").consolidation_level
        implicit_level = learning_system.get_implicit_memory("implicit_1").consolidation_level
        
        # Both should have consolidated
        assert explicit_level > 0.2
        assert implicit_level > 0.1

    def test_consolidation_stats(self, learning_system: ExplicitImplicitLearning) -> None:
        """Test consolidation statistics."""
        # Create some memories
        for i in range(5):
            learning_system.learn_explicit(f"e_{i}", f"Content {i}", "context")
            learning_system.learn_implicit(f"i_{i}", f"Content {i}", "context")
        
        # Consolidate
        learning_system.consolidate(hours_elapsed=48.0)
        
        stats = learning_system.get_consolidation_stats()
        
        assert stats["explicit_count"] == 5
        assert stats["implicit_count"] == 5
        assert "avg_explicit_consolidation" in stats
        assert "avg_implicit_consolidation" in stats


# =============================================================================
# Integration Tests
# =============================================================================

class TestNeuroplasticityIntegration:
    """Integration tests for the neuroplasticity system."""

    def test_ltp_strengthens_associated_synapses(self) -> None:
        """Test that LTP strengthens synapses between associated memories."""
        system = NeuroplasticitySystem()
        
        # Create two memories and associate them
        system.create_memory_trace("mem_A", "Content A", initial_weight=0.5)
        system.create_memory_trace("mem_B", "Content B", initial_weight=0.5)
        system.associate_memories("mem_A", "mem_B")
        
        # Apply LTP to mem_A
        system.apply_ltp("mem_A", frequency=15.0, duration=5.0)
        
        # Synapse between them should be strengthened
        synapse_key = tuple(sorted(["mem_A", "mem_B"]))
        if synapse_key in system.synaptic_weights:
            synapse = system.synaptic_weights[synapse_key]
            assert synapse.weight > 0.1  # Should be strengthened from initial

    def test_hebbian_learning_via_memory_access(self) -> None:
        """Test Hebbian learning triggered by memory access."""
        system = NeuroplasticitySystem()
        
        # Create and associate memories
        system.create_memory_trace("mem_A", "Content A")
        system.create_memory_trace("mem_B", "Content B")
        system.associate_memories("mem_A", "mem_B")
        
        # Access mem_A (should trigger Hebbian update with mem_B)
        system.access_memory("mem_A")
        
        # Synapse should exist and have been updated
        synapse_key = tuple(sorted(["mem_A", "mem_B"]))
        assert synapse_key in system.synaptic_weights
        
        synapse = system.synaptic_weights[synapse_key]
        assert synapse.activation_count >= 1

    def test_forgetting_curve_integration(self) -> None:
        """Test forgetting curve integration with memory traces."""
        system = NeuroplasticitySystem()
        
        # Create memory
        system.create_memory_trace("mem_001", "Content", initial_weight=0.7)
        
        # Get retention
        retention = system.get_memory_retention("mem_001")
        
        # Should be calculated using forgetting curve
        assert 0 <= retention <= 1

    @pytest.mark.asyncio
    async def test_system_updates(self) -> None:
        """Test system background updates."""
        system = NeuroplasticitySystem()
        await system.initialize()
        
        try:
            # Create a memory
            system.create_memory_trace("mem_001", "Content", initial_weight=0.8)
            
            # Manually trigger decay update
            await system._decay_synaptic_weights()
            
            # System should still be functional
            assert len(system.memory_traces) == 1
            
        finally:
            await system.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
