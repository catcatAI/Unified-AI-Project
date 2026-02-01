"""
Angela AI v6.0 - Endocrine System Tests
内分泌系统测试

Comprehensive test suite for the endocrine system including:
- EndocrineSystem initialization and hormone regulation
- HormoneKinetics (receptor occupancy, Hill equation, metabolism)
- FeedbackLoop (HPA axis simulation, circadian rhythm)
- 12 hormone types and their interactions
- Hormone antagonism effects

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

import pytest
import asyncio
import math
from datetime import datetime
from typing import Dict, List, Optional, Any

# Import the modules under test
import sys
sys.path.insert(0, 'D:\\Projects\\Unified-AI-Project\\apps\\backend\\src')

from core.autonomous.endocrine_system import (
    HormoneType,
    Hormone,
    HormonalEffect,
    EndocrineSystem,
    ReceptorStatus,
    HormoneKinetics,
    FeedbackNode,
    FeedbackLoop,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def endocrine_system() -> EndocrineSystem:
    """Create an EndocrineSystem instance for testing."""
    return EndocrineSystem()


@pytest.fixture
def initialized_endocrine_system() -> EndocrineSystem:
    """Create an initialized EndocrineSystem instance."""
    system = EndocrineSystem()
    asyncio.run(system.initialize())
    yield system
    asyncio.run(system.shutdown())


@pytest.fixture
def hormone_kinetics() -> HormoneKinetics:
    """Create a HormoneKinetics instance."""
    return HormoneKinetics()


@pytest.fixture
def feedback_loop() -> FeedbackLoop:
    """Create a FeedbackLoop instance."""
    return FeedbackLoop()


@pytest.fixture
def sample_hormone() -> Hormone:
    """Create a sample Hormone for testing."""
    return Hormone(
        hormone_type=HormoneType.CORTISOL,
        base_level=20.0,
        current_level=25.0,
        production_rate=2.0,
        decay_rate=1.5,
        min_level=0.0,
        max_level=100.0
    )


# =============================================================================
# HormoneType Tests
# =============================================================================

class TestHormoneType:
    """Tests for the HormoneType enum."""

    def test_hormone_types_count(self) -> None:
        """Test that there are exactly 12 hormone types."""
        assert len(HormoneType) == 12

    def test_hormone_type_attributes(self) -> None:
        """Test hormone type has correct attributes."""
        dopamine = HormoneType.DOPAMINE
        assert dopamine.cn_name == "多巴胺"
        assert dopamine.en_name == "Dopamine"
        assert dopamine.primary_role == "reward"
        assert dopamine.secondary_role == "motivation"

    def test_all_hormones_have_names(self) -> None:
        """Test all hormone types have Chinese and English names."""
        for hormone in HormoneType:
            assert hormone.cn_name is not None
            assert len(hormone.cn_name) > 0
            assert hormone.en_name is not None
            assert len(hormone.en_name) > 0

    def test_stress_hormones(self) -> None:
        """Test stress-related hormone types."""
        stress_hormones = [
            HormoneType.ADRENALINE,
            HormoneType.CORTISOL,
            HormoneType.NOREPINEPHRINE
        ]
        for hormone in stress_hormones:
            assert "stress" in hormone.primary_role.lower() or \
                   "alertness" in hormone.primary_role.lower()


# =============================================================================
# Hormone Tests
# =============================================================================

class TestHormone:
    """Tests for the Hormone data class."""

    def test_hormone_creation(self, sample_hormone: Hormone) -> None:
        """Test basic Hormone creation."""
        assert sample_hormone.hormone_type == HormoneType.CORTISOL
        assert sample_hormone.base_level == 20.0
        assert sample_hormone.current_level == 25.0
        assert sample_hormone.production_rate == 2.0
        assert sample_hormone.decay_rate == 1.5

    def test_hormone_bounds_enforcement(self) -> None:
        """Test that hormone levels are bounded."""
        # Test upper bound
        high_hormone = Hormone(
            hormone_type=HormoneType.DOPAMINE,
            base_level=50.0,
            current_level=150.0,  # Above max
            production_rate=3.0,
            decay_rate=2.0,
            max_level=100.0
        )
        assert high_hormone.current_level <= high_hormone.max_level

        # Test lower bound
        low_hormone = Hormone(
            hormone_type=HormoneType.DOPAMINE,
            base_level=50.0,
            current_level=-10.0,  # Below min
            production_rate=3.0,
            decay_rate=2.0,
            min_level=0.0
        )
        assert low_hormone.current_level >= low_hormone.min_level

    def test_get_normalized_level(self, sample_hormone: Hormone) -> None:
        """Test normalized level calculation."""
        normalized = sample_hormone.get_normalized_level()
        assert 0 <= normalized <= 1
        # Current is 25, base is 20, max is 100, min is 0
        expected = 25.0 / 100.0
        assert abs(normalized - expected) < 0.01

    def test_hormone_update_decay(self) -> None:
        """Test hormone natural decay toward base level."""
        hormone = Hormone(
            hormone_type=HormoneType.ADRENALINE,
            base_level=10.0,
            current_level=50.0,  # Above base
            production_rate=5.0,
            decay_rate=3.0
        )
        
        initial_level = hormone.current_level
        hormone.update(minutes=1.0)
        
        # Should decay toward base level
        assert hormone.current_level < initial_level
        assert hormone.current_level >= hormone.base_level

    def test_hormone_update_recovery(self) -> None:
        """Test hormone recovery toward base level."""
        hormone = Hormone(
            hormone_type=HormoneType.SEROTONIN,
            base_level=50.0,
            current_level=20.0,  # Below base
            production_rate=2.5,
            decay_rate=1.0
        )
        
        initial_level = hormone.current_level
        hormone.update(minutes=1.0)
        
        # Should recover toward base level
        assert hormone.current_level > initial_level
        assert hormone.current_level <= hormone.base_level


# =============================================================================
# EndocrineSystem Tests
# =============================================================================

class TestEndocrineSystem:
    """Tests for the main EndocrineSystem class."""

    @pytest.mark.asyncio
    async def test_system_initialization(self, endocrine_system: EndocrineSystem) -> None:
        """Test system initialization."""
        await endocrine_system.initialize()
        assert endocrine_system._running is True
        assert len(endocrine_system.hormones) == 12
        await endocrine_system.shutdown()

    @pytest.mark.asyncio
    async def test_system_shutdown(self, endocrine_system: EndocrineSystem) -> None:
        """Test system shutdown."""
        await endocrine_system.initialize()
        await endocrine_system.shutdown()
        assert endocrine_system._running is False

    def test_default_hormone_configs(self, endocrine_system: EndocrineSystem) -> None:
        """Test default hormone configurations."""
        # Check all hormones are initialized
        for hormone_type in HormoneType:
            assert hormone_type in endocrine_system.hormones
            hormone = endocrine_system.hormones[hormone_type]
            assert hormone.base_level > 0
            assert hormone.current_level == hormone.base_level

    def test_get_hormone_level(self, endocrine_system: EndocrineSystem) -> None:
        """Test getting hormone levels."""
        level = endocrine_system.get_hormone_level(HormoneType.DOPAMINE)
        assert isinstance(level, float)
        assert level >= 0

    def test_get_all_hormone_levels(self, endocrine_system: EndocrineSystem) -> None:
        """Test getting all hormone levels."""
        levels = endocrine_system.get_all_hormone_levels()
        assert len(levels) == 12
        for hormone_type, level in levels.items():
            assert isinstance(hormone_type, HormoneType)
            assert isinstance(level, float)

    @pytest.mark.asyncio
    async def test_adjust_hormone(self, initialized_endocrine_system: EndocrineSystem) -> None:
        """Test adjusting hormone levels."""
        initial_level = initialized_endocrine_system.get_hormone_level(HormoneType.DOPAMINE)
        
        await initialized_endocrine_system.adjust_hormone(HormoneType.DOPAMINE, 10.0)
        
        new_level = initialized_endocrine_system.get_hormone_level(HormoneType.DOPAMINE)
        assert new_level == initial_level + 10.0

    @pytest.mark.asyncio
    async def test_adjust_hormone_bounds(self, initialized_endocrine_system: EndocrineSystem) -> None:
        """Test hormone adjustment respects bounds."""
        # Try to exceed max
        await initialized_endocrine_system.adjust_hormone(HormoneType.DOPAMINE, 200.0)
        level = initialized_endocrine_system.get_hormone_level(HormoneType.DOPAMINE)
        assert level <= 100.0

        # Try to go below min
        await initialized_endocrine_system.adjust_hormone(HormoneType.DOPAMINE, -200.0)
        level = initialized_endocrine_system.get_hormone_level(HormoneType.DOPAMINE)
        assert level >= 0.0

    @pytest.mark.asyncio
    async def test_emotional_response_joy(self, initialized_endocrine_system: EndocrineSystem) -> None:
        """Test emotional response triggers hormone changes (joy)."""
        initial_dopamine = initialized_endocrine_system.get_hormone_level(HormoneType.DOPAMINE)
        
        await initialized_endocrine_system.trigger_emotional_response("joy", intensity=0.8)
        
        # Joy should increase dopamine
        new_dopamine = initialized_endocrine_system.get_hormone_level(HormoneType.DOPAMINE)
        assert new_dopamine > initial_dopamine

    @pytest.mark.asyncio
    async def test_emotional_response_fear(self, initialized_endocrine_system: EndocrineSystem) -> None:
        """Test emotional response triggers hormone changes (fear)."""
        initial_adrenaline = initialized_endocrine_system.get_hormone_level(HormoneType.ADRENALINE)
        
        await initialized_endocrine_system.trigger_emotional_response("fear", intensity=0.8)
        
        # Fear should increase adrenaline
        new_adrenaline = initialized_endocrine_system.get_hormone_level(HormoneType.ADRENALINE)
        assert new_adrenaline > initial_adrenaline

    @pytest.mark.asyncio
    async def test_stress_response_acute(self, initialized_endocrine_system: EndocrineSystem) -> None:
        """Test acute stress response."""
        initial_adrenaline = initialized_endocrine_system.get_hormone_level(HormoneType.ADRENALINE)
        initial_cortisol = initialized_endocrine_system.get_hormone_level(HormoneType.CORTISOL)
        
        await initialized_endocrine_system.trigger_stress_response(0.6, stress_type="acute")
        
        # Acute stress should increase adrenaline significantly
        new_adrenaline = initialized_endocrine_system.get_hormone_level(HormoneType.ADRENALINE)
        assert new_adrenaline > initial_adrenaline

    @pytest.mark.asyncio
    async def test_activity_response_exercise(self, initialized_endocrine_system: EndocrineSystem) -> None:
        """Test physical exercise activity response."""
        initial_endorphin = initialized_endocrine_system.get_hormone_level(HormoneType.ENDORPHIN)
        
        await initialized_endocrine_system.trigger_activity_response("physical_exercise", intensity=0.7)
        
        # Exercise should increase endorphins
        new_endorphin = initialized_endocrine_system.get_hormone_level(HormoneType.ENDORPHIN)
        assert new_endorphin > initial_endorphin

    @pytest.mark.asyncio
    async def test_social_response_positive(self, initialized_endocrine_system: EndocrineSystem) -> None:
        """Test positive social interaction response."""
        initial_oxytocin = initialized_endocrine_system.get_hormone_level(HormoneType.OXYTOCIN)
        
        await initialized_endocrine_system.trigger_social_response("positive_interaction", intensity=0.8)
        
        # Positive interaction should increase oxytocin
        new_oxytocin = initialized_endocrine_system.get_hormone_level(HormoneType.OXYTOCIN)
        assert new_oxytocin > initial_oxytocin

    def test_calculate_systemic_effects(self, endocrine_system: EndocrineSystem) -> None:
        """Test calculation of systemic effects."""
        effects = endocrine_system.calculate_systemic_effects()
        
        # Check all expected effect categories
        expected_categories = [
            "energy", "mood", "stress_resilience", "social_desire",
            "focus", "creativity", "pain_tolerance", "alertness", "relaxation"
        ]
        
        for category in expected_categories:
            assert category in effects
            assert isinstance(effects[category], float)

    def test_get_hormonal_profile(self, endocrine_system: EndocrineSystem) -> None:
        """Test getting complete hormonal profile."""
        profile = endocrine_system.get_hormonal_profile()
        
        assert "hormones" in profile
        assert "circadian_phase" in profile
        assert "stress_level" in profile
        assert "systemic_effects" in profile
        
        assert len(profile["hormones"]) == 12


# =============================================================================
# HormoneKinetics Tests
# =============================================================================

class TestHormoneKinetics:
    """Tests for the HormoneKinetics class."""

    def test_kinetics_initialization(self, hormone_kinetics: HormoneKinetics) -> None:
        """Test kinetics model initialization."""
        assert len(hormone_kinetics.half_lives) == 12
        assert hormone_kinetics.default_kd == 20.0
        assert hormone_kinetics.default_hill == 1.0

    def test_half_life_values(self, hormone_kinetics: HormoneKinetics) -> None:
        """Test half-life values for hormones."""
        # Adrenaline should have short half-life (~6 minutes)
        assert hormone_kinetics.half_lives[HormoneType.ADRENALINE] == 0.1
        
        # Cortisol should have medium half-life (~90 minutes)
        assert hormone_kinetics.half_lives[HormoneType.CORTISOL] == 1.5
        
        # Thyroxine should have long half-life (~7 days)
        assert hormone_kinetics.half_lives[HormoneType.THYROXINE] == 168.0

    def test_metabolize(self, hormone_kinetics: HormoneKinetics) -> None:
        """Test hormone metabolism calculation."""
        initial_level = 50.0
        
        # After one half-life, level should be halved
        remaining = hormone_kinetics.metabolize(
            initial_level=initial_level,
            hormone_type=HormoneType.CORTISOL,
            time_hours=1.5  # One half-life for cortisol
        )
        
        assert abs(remaining - 25.0) < 1.0  # Allow small rounding error

    def test_metabolize_exponential_decay(self, hormone_kinetics: HormoneKinetics) -> None:
        """Test exponential decay over multiple half-lives."""
        initial_level = 100.0
        
        # After 2 half-lives, should be 25%
        remaining = hormone_kinetics.metabolize(
            initial_level=initial_level,
            hormone_type=HormoneType.CORTISOL,
            time_hours=3.0  # Two half-lives
        )
        
        assert abs(remaining - 25.0) < 1.0

    def test_calculate_metabolism_rate(self, hormone_kinetics: HormoneKinetics) -> None:
        """Test metabolism rate calculation."""
        current_level = 50.0
        rate = hormone_kinetics.calculate_metabolism_rate(
            current_level=current_level,
            hormone_type=HormoneType.CORTISOL
        )
        
        assert rate > 0
        # Rate should be proportional to current level
        assert rate < current_level

    def test_calculate_occupancy(self, hormone_kinetics: HormoneKinetics) -> None:
        """Test receptor occupancy calculation (Hill equation)."""
        # At KD, occupancy should be 50% (with Hill coefficient = 1)
        occupancy = hormone_kinetics.calculate_occupancy(
            hormone_level=20.0,
            kd=20.0,
            hill_coefficient=1.0
        )
        
        assert abs(occupancy - 0.5) < 0.01

    def test_calculate_occupancy_hill_coefficient(self, hormone_kinetics: HormoneKinetics) -> None:
        """Test Hill coefficient effect on occupancy curve."""
        level = 30.0
        kd = 20.0
        
        # Higher Hill coefficient = steeper curve
        occupancy_1 = hormone_kinetics.calculate_occupancy(level, kd, 1.0)
        occupancy_2 = hormone_kinetics.calculate_occupancy(level, kd, 2.0)
        
        # Level > KD, so higher Hill should give higher occupancy
        assert occupancy_2 > occupancy_1

    def test_calculate_occupancy_bounds(self, hormone_kinetics: HormoneKinetics) -> None:
        """Test occupancy is always between 0 and 1."""
        # Very high level should approach 1
        high_occupancy = hormone_kinetics.calculate_occupancy(1000.0, 20.0, 1.0)
        assert high_occupancy > 0.99
        
        # Very low level should approach 0
        low_occupancy = hormone_kinetics.calculate_occupancy(0.1, 20.0, 1.0)
        assert low_occupancy < 0.01

    def test_update_receptor_regulation_downregulation(self, hormone_kinetics: HormoneKinetics) -> None:
        """Test receptor downregulation with chronic high levels."""
        status = hormone_kinetics.update_receptor_regulation(
            hormone_type=HormoneType.CORTISOL,
            chronic_level=0.8,  # High chronic level
            time_days=5.0
        )
        
        # High levels should cause downregulation
        assert status.downregulation > 1.0

    def test_update_receptor_regulation_upregulation(self, hormone_kinetics: HormoneKinetics) -> None:
        """Test receptor upregulation with chronic low levels."""
        status = hormone_kinetics.update_receptor_regulation(
            hormone_type=HormoneType.SEROTONIN,
            chronic_level=0.2,  # Low chronic level
            time_days=5.0
        )
        
        # Low levels should cause upregulation
        assert status.upregulation > 1.0

    def test_calculate_secretion(self, hormone_kinetics: HormoneKinetics) -> None:
        """Test secretion calculation (basal + pulsatile)."""
        secretion = hormone_kinetics.calculate_secretion(
            basal_rate=10.0,
            stimulus=20.0,
            pulse_frequency=4.0,
            time_hours=0.0
        )
        
        # Should be basal + stimulus + pulse
        assert secretion > 10.0
        assert secretion > 20.0  # Basal + stimulus alone

    def test_get_receptor_status(self, hormone_kinetics: HormoneKinetics) -> None:
        """Test getting receptor status."""
        status = hormone_kinetics.get_receptor_status(HormoneType.DOPAMINE)
        
        assert status.receptor_type == "Dopamine_receptor"
        assert status.upregulation == 1.0
        assert status.downregulation == 1.0
        assert status.sensitivity == 1.0


# =============================================================================
# FeedbackLoop Tests
# =============================================================================

class TestFeedbackLoop:
    """Tests for the FeedbackLoop class."""

    def test_feedback_loop_initialization(self, feedback_loop: FeedbackLoop) -> None:
        """Test feedback loop initialization."""
        assert len(feedback_loop.feedback_nodes) == 12
        assert feedback_loop.hpa_crh_to_acth_gain == 2.0
        assert feedback_loop.hpa_acth_to_cortisol_gain == 3.0

    def test_hpa_axis_step_crh(self, feedback_loop: FeedbackLoop) -> None:
        """Test HPA axis step from CRH to ACTH."""
        crh_input = 10.0
        acth_output = feedback_loop.hpa_axis_step(
            crh_input,
            level_type="crh",
            cortisol_level=20.0
        )
        
        # CRH should stimulate ACTH release
        assert acth_output > crh_input

    def test_hpa_axis_step_acth(self, feedback_loop: FeedbackLoop) -> None:
        """Test HPA axis step from ACTH to Cortisol."""
        acth_input = 20.0
        cortisol_output = feedback_loop.hpa_axis_step(
            acth_input,
            level_type="acth"
        )
        
        # ACTH should stimulate cortisol release
        assert cortisol_output > acth_input

    def test_hpa_negative_feedback(self, feedback_loop: FeedbackLoop) -> None:
        """Test negative feedback in HPA axis."""
        # High cortisol should inhibit CRH
        high_cortisol = 80.0
        
        crh_output_1 = feedback_loop.hpa_axis_step(
            30.0, level_type="crh", cortisol_level=20.0
        )
        
        crh_output_2 = feedback_loop.hpa_axis_step(
            30.0, level_type="crh", cortisol_level=high_cortisol
        )
        
        # Higher cortisol should produce less CRH stimulation
        assert crh_output_2 < crh_output_1

    def test_simulate_hpa_axis(self, feedback_loop: FeedbackLoop) -> None:
        """Test full HPA axis simulation."""
        result = feedback_loop.simulate_hpa_axis(
            stress_input=30.0,
            simulation_hours=1.0,
            time_step=0.1
        )
        
        assert "crh" in result
        assert "acth" in result
        assert "cortisol" in result
        assert "time" in result
        
        # Cortisol should peak and then stabilize or decline
        cortisol_peak = max(result["cortisol"])
        assert cortisol_peak > 20.0  # Above baseline

    def test_negative_feedback(self, feedback_loop: FeedbackLoop) -> None:
        """Test negative feedback calculation."""
        # High level should produce inhibition
        high_inhibition = feedback_loop.negative_feedback(
            HormoneType.CORTISOL,
            HormoneType.ADRENALINE,
            current_level=80.0,
            setpoint=50.0
        )
        
        # Low level should produce no inhibition
        low_inhibition = feedback_loop.negative_feedback(
            HormoneType.CORTISOL,
            HormoneType.ADRENALINE,
            current_level=30.0,
            setpoint=50.0
        )
        
        assert high_inhibition > 0
        assert low_inhibition == 0

    def test_hormone_antagonism(self, feedback_loop: FeedbackLoop) -> None:
        """Test hormone antagonism calculation."""
        # Two opposing hormones
        level_a = 80.0
        level_b = 60.0
        
        adjusted_a, adjusted_b = feedback_loop.hormone_antagonism(
            HormoneType.ADRENALINE,
            HormoneType.SEROTONIN,
            level_a=level_a,
            level_b=level_b,
            antagonism_strength=0.5
        )
        
        # Both should be suppressed due to antagonism
        assert adjusted_a < level_a
        assert adjusted_b < level_b

    def test_circadian_rhythm_melatonin(self, feedback_loop: FeedbackLoop) -> None:
        """Test circadian rhythm for melatonin (night hormone)."""
        # Melatonin should be high at night (2 AM)
        melatonin_night = feedback_loop.circadian_rhythm(
            HormoneType.MELATONIN,
            hour_of_day=2.0,
            base_level=5.0
        )
        
        # Melatonin should be low during day (12 PM)
        melatonin_day = feedback_loop.circadian_rhythm(
            HormoneType.MELATONIN,
            hour_of_day=12.0,
            base_level=5.0
        )
        
        assert melatonin_night > melatonin_day
        assert melatonin_night > 5.0  # Above baseline at night

    def test_circadian_rhythm_cortisol(self, feedback_loop: FeedbackLoop) -> None:
        """Test circadian rhythm for cortisol (morning hormone)."""
        # Cortisol should peak in morning (8 AM)
        cortisol_morning = feedback_loop.circadian_rhythm(
            HormoneType.CORTISOL,
            hour_of_day=8.0,
            base_level=20.0
        )
        
        # Cortisol should be lower at night
        cortisol_night = feedback_loop.circadian_rhythm(
            HormoneType.CORTISOL,
            hour_of_day=2.0,
            base_level=20.0
        )
        
        assert cortisol_morning > cortisol_night
        assert cortisol_morning > 20.0  # Above baseline in morning

    def test_set_setpoint(self, feedback_loop: FeedbackLoop) -> None:
        """Test setting feedback setpoint."""
        feedback_loop.set_setpoint(HormoneType.DOPAMINE, 60.0)
        
        node = feedback_loop.get_feedback_node(HormoneType.DOPAMINE)
        assert node.setpoint == 60.0


# =============================================================================
# Integration Tests
# =============================================================================

class TestEndocrineIntegration:
    """Integration tests for the endocrine system."""

    @pytest.mark.asyncio
    async def test_emotional_cascade_effects(self) -> None:
        """Test how emotions cascade through hormone system."""
        system = EndocrineSystem()
        await system.initialize()
        
        try:
            # Get baseline
            baseline_dopamine = system.get_hormone_level(HormoneType.DOPAMINE)
            baseline_serotonin = system.get_hormone_level(HormoneType.SEROTONIN)
            
            # Trigger joy
            await system.trigger_emotional_response("joy", intensity=0.7)
            
            # Check multiple hormones affected
            new_dopamine = system.get_hormone_level(HormoneType.DOPAMINE)
            new_serotonin = system.get_hormone_level(HormoneType.SEROTONIN)
            
            assert new_dopamine > baseline_dopamine
            assert new_serotonin > baseline_serotonin
            
        finally:
            await system.shutdown()

    @pytest.mark.asyncio
    async def test_stress_then_relaxation(self) -> None:
        """Test stress response followed by relaxation."""
        system = EndocrineSystem()
        await system.initialize()
        
        try:
            # Trigger stress
            await system.trigger_stress_response(0.8, stress_type="acute")
            stress_adrenaline = system.get_hormone_level(HormoneType.ADRENALINE)
            stress_cortisol = system.get_hormone_level(HormoneType.CORTISOL)
            
            assert stress_adrenaline > 10.0  # Significantly elevated
            
            # Trigger relaxation
            await system.trigger_emotional_response("relaxation", intensity=0.8)
            relax_adrenaline = system.get_hormone_level(HormoneType.ADRENALINE)
            relax_cortisol = system.get_hormone_level(HormoneType.CORTISOL)
            
            # Relaxation should reduce stress hormones
            assert relax_adrenaline < stress_adrenaline
            
        finally:
            await system.shutdown()

    def test_hormone_kinetics_with_system(self) -> None:
        """Test hormone kinetics integration with endocrine system."""
        system = EndocrineSystem()
        kinetics = HormoneKinetics()
        
        # Get current cortisol level
        cortisol_level = system.get_hormone_level(HormoneType.CORTISOL)
        
        # Calculate what it would be after metabolism
        metabolized = kinetics.metabolize(
            initial_level=cortisol_level,
            hormone_type=HormoneType.CORTISOL,
            time_hours=2.0
        )
        
        # Should have decreased (assuming above base level)
        if cortisol_level > 20.0:  # Base level
            assert metabolized < cortisol_level


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
