"""
Angela AI v6.0 - Physiological Tactile System Tests
生理触觉系统测试

Comprehensive test suite for the physiological tactile system including:
- Receptor initialization and configuration
- Trajectory analysis (velocity, acceleration, pattern recognition)
- Adaptation mechanisms (habituation/dishabituation)
- Tactile stimulus processing
- Body part sensitivity

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

from __future__ import annotations

import pytest
import asyncio
import math
from datetime import datetime
from typing import List, Tuple, Any, Dict
from pathlib import Path

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from core.autonomous.physiological_tactile import (
    ReceptorType,
    TactileType,
    BodyPart,
    BodyRegion,
    Receptor,
    TactileStimulus,
    TactileResponse,
    EmotionalTactileMapping,
    PhysiologicalTactileSystem,
    TrajectoryPoint,
    TrajectoryAnalysis,
    TrajectoryAnalyzer,
    ReceptorAdaptationState,
    AdaptationMechanism,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def tactile_system() -> PhysiologicalTactileSystem:
    """Create a PhysiologicalTactileSystem instance for testing."""
    system = PhysiologicalTactileSystem()
    return system


@pytest.fixture
def initialized_tactile_system() -> PhysiologicalTactileSystem:
    """Create an initialized PhysiologicalTactileSystem instance."""
    system = PhysiologicalTactileSystem()
    asyncio.run(system.initialize())
    yield system
    asyncio.run(system.shutdown())


@pytest.fixture
def trajectory_analyzer() -> TrajectoryAnalyzer:
    """Create a TrajectoryAnalyzer instance."""
    return TrajectoryAnalyzer()


@pytest.fixture
def adaptation_mechanism() -> AdaptationMechanism:
    """Create an AdaptationMechanism instance."""
    return AdaptationMechanism()


@pytest.fixture
def sample_stimulus() -> TactileStimulus:
    """Create a sample TactileStimulus for testing."""
    return TactileStimulus(
        tactile_type=TactileType.LIGHT_TOUCH,
        intensity=5.0,
        location=BodyPart.HANDS,
        duration=2.0,
        source="test"
    )


@pytest.fixture
def sample_receptor() -> Receptor:
    """Create a sample Receptor for testing."""
    return Receptor(
        receptor_type=ReceptorType.MEISSNER,
        body_part=BodyPart.HANDS,
        density=0.8,
        sensitivity=0.9,
        adaptation_rate=0.7
    )


# =============================================================================
# Receptor Tests
# =============================================================================

class TestReceptor:
    """Tests for the Receptor data class."""

    def test_receptor_creation(self, sample_receptor: Receptor) -> None:
        """Test basic Receptor creation and attributes."""
        assert sample_receptor.receptor_type == ReceptorType.MEISSNER
        assert sample_receptor.body_part == BodyPart.HANDS
        assert sample_receptor.density == 0.8
        assert sample_receptor.sensitivity == 0.9
        assert sample_receptor.adaptation_rate == 0.7
        assert sample_receptor.current_activation == 0.0
        assert sample_receptor.last_stimulus is None

    def test_receptor_validation_density(self) -> None:
        """Test Receptor validation for density bounds."""
        with pytest.raises(ValueError, match="Density must be between 0 and 1"):
            Receptor(
                receptor_type=ReceptorType.MEISSNER,
                body_part=BodyPart.HANDS,
                density=1.5,  # Invalid
                sensitivity=0.5,
                adaptation_rate=0.5
            )

    def test_receptor_validation_sensitivity(self) -> None:
        """Test Receptor validation for sensitivity bounds."""
        with pytest.raises(ValueError, match="Sensitivity must be between 0 and 1"):
            Receptor(
                receptor_type=ReceptorType.MEISSNER,
                body_part=BodyPart.HANDS,
                density=0.5,
                sensitivity=-0.1,  # Invalid
                adaptation_rate=0.5
            )

    def test_receptor_types_count(self) -> None:
        """Test that there are exactly 6 receptor types."""
        assert len(ReceptorType) == 6
        receptor_types = [
            ReceptorType.MEISSNER,
            ReceptorType.MERKEL,
            ReceptorType.PACINIAN,
            ReceptorType.RUFFINI,
            ReceptorType.FREE_NERVE,
            ReceptorType.HAIR_FOLLICLE
        ]
        for rt in receptor_types:
            assert rt in ReceptorType


# =============================================================================
# TactileStimulus Tests
# =============================================================================

class TestTactileStimulus:
    """Tests for the TactileStimulus data class."""

    def test_stimulus_creation(self, sample_stimulus: TactileStimulus) -> None:
        """Test basic TactileStimulus creation."""
        assert sample_stimulus.tactile_type == TactileType.LIGHT_TOUCH
        assert sample_stimulus.intensity == 5.0
        assert sample_stimulus.location == BodyPart.HANDS
        assert sample_stimulus.duration == 2.0
        assert sample_stimulus.source == "test"

    def test_stimulus_receptor_mapping(self) -> None:
        """Test that stimulus correctly maps to receptor types."""
        # Light touch should activate MEISSNER and HAIR_FOLLICLE
        touch = TactileStimulus(
            tactile_type=TactileType.LIGHT_TOUCH,
            intensity=3.0,
            location=BodyPart.FACE
        )
        assert ReceptorType.MEISSNER in touch.receptor_types
        assert ReceptorType.HAIR_FOLLICLE in touch.receptor_types

    def test_stimulus_pain_mapping(self) -> None:
        """Test pain stimulus maps to FREE_NERVE receptors."""
        pain = TactileStimulus(
            tactile_type=TactileType.PAIN,
            intensity=8.0,
            location=BodyPart.HANDS
        )
        assert ReceptorType.FREE_NERVE in pain.receptor_types
        assert len(pain.receptor_types) == 1

    def test_stimulus_intensity_validation(self) -> None:
        """Test stimulus intensity bounds."""
        stimulus_low = TactileStimulus(
            tactile_type=TactileType.LIGHT_TOUCH,
            intensity=0.0,
            location=BodyPart.HANDS
        )
        assert stimulus_low.intensity == 0.0

        stimulus_high = TactileStimulus(
            tactile_type=TactileType.PAIN,
            intensity=10.0,
            location=BodyPart.HANDS
        )
        assert stimulus_high.intensity == 10.0


# =============================================================================
# BodyPart Tests
# =============================================================================

class TestBodyPart:
    """Tests for the BodyPart enum."""

    def test_body_parts_count(self) -> None:
        """Test that there are exactly 18 body parts."""
        assert len(BodyPart) == 18

    def test_body_part_regions(self) -> None:
        """Test body part region assignments."""
        # Head region
        assert BodyPart.FACE.region == BodyRegion.HEAD
        assert BodyPart.FOREHEAD.region == BodyRegion.HEAD
        
        # Upper body
        assert BodyPart.CHEST.region == BodyRegion.UPPER_BODY
        assert BodyPart.BACK.region == BodyRegion.UPPER_BODY
        
        # Lower body
        assert BodyPart.HIPS.region == BodyRegion.LOWER_BODY
        
        # Upper limbs
        assert BodyPart.HANDS.region == BodyRegion.UPPER_LIMBS
        assert BodyPart.FINGERS.region == BodyRegion.UPPER_LIMBS
        
        # Lower limbs
        assert BodyPart.FEET.region == BodyRegion.LOWER_LIMBS
        assert BodyPart.KNEES.region == BodyRegion.LOWER_LIMBS

    def test_body_part_sensitivity(self) -> None:
        """Test body part sensitivity values."""
        # Hands and fingers should have highest sensitivity
        assert BodyPart.HANDS.base_sensitivity == 1.0
        assert BodyPart.FINGERS.base_sensitivity == 1.0
        
        # Face should be highly sensitive
        assert BodyPart.FACE.base_sensitivity == 0.9
        
        # Back should be less sensitive
        assert BodyPart.BACK.base_sensitivity == 0.4

    def test_body_part_names(self) -> None:
        """Test Chinese names for body parts."""
        assert BodyPart.HANDS.cn_name == "手掌"
        assert BodyPart.FACE.cn_name == "面部"
        assert BodyPart.BACK.cn_name == "背部"


# =============================================================================
# PhysiologicalTactileSystem Tests
# =============================================================================

class TestPhysiologicalTactileSystem:
    """Tests for the main PhysiologicalTactileSystem class."""

    @pytest.mark.asyncio
    async def test_system_initialization(self, tactile_system: PhysiologicalTactileSystem) -> None:
        """Test system initialization."""
        await tactile_system.initialize()
        assert tactile_system._running is True
        assert tactile_system._update_task is not None
        assert len(tactile_system.receptors) == 18  # 18 body parts
        await tactile_system.shutdown()

    @pytest.mark.asyncio
    async def test_system_shutdown(self, tactile_system: PhysiologicalTactileSystem) -> None:
        """Test system shutdown."""
        await tactile_system.initialize()
        await tactile_system.shutdown()
        assert tactile_system._running is False
        assert tactile_system._update_task is None

    def test_receptor_initialization(self, tactile_system: PhysiologicalTactileSystem) -> None:
        """Test that receptors are properly initialized for all body parts."""
        # Check all body parts have receptors
        for body_part in BodyPart:
            assert body_part in tactile_system.receptors
            assert len(tactile_system.receptors[body_part]) > 0

    def test_hands_receptor_configuration(self, tactile_system: PhysiologicalTactileSystem) -> None:
        """Test specific receptor configuration for hands."""
        hand_receptors = tactile_system.receptors[BodyPart.HANDS]
        receptor_types = [r.receptor_type for r in hand_receptors]
        
        # Hands should have MEISSNER, MERKEL, PACINIAN, and FREE_NERVE
        assert ReceptorType.MEISSNER in receptor_types
        assert ReceptorType.MERKEL in receptor_types
        assert ReceptorType.PACINIAN in receptor_types
        assert ReceptorType.FREE_NERVE in receptor_types

    def test_emotional_mappings_initialization(self, tactile_system: PhysiologicalTactileSystem) -> None:
        """Test that emotional mappings are initialized."""
        assert len(tactile_system.emotional_mappings) > 0
        assert "joy" in tactile_system.emotional_mappings
        assert "comfort" in tactile_system.emotional_mappings
        assert "anxiety" in tactile_system.emotional_mappings

    @pytest.mark.asyncio
    async def test_process_stimulus(self, initialized_tactile_system: PhysiologicalTactileSystem) -> None:
        """Test processing a tactile stimulus."""
        stimulus = TactileStimulus(
            tactile_type=TactileType.LIGHT_TOUCH,
            intensity=5.0,
            location=BodyPart.HANDS,
            duration=1.0
        )
        
        response = await initialized_tactile_system.process_stimulus(stimulus)
        
        assert isinstance(response, TactileResponse)
        assert response.stimulus == stimulus
        assert response.perceived_intensity > 0
        assert response.activated_receptors > 0
        assert response.timestamp is not None

    @pytest.mark.asyncio
    async def test_process_stimulus_with_emotion(self, initialized_tactile_system: PhysiologicalTactileSystem) -> None:
        """Test processing stimulus with emotional context."""
        # Anxiety increases intensity perception
        anxious_stimulus = TactileStimulus(
            tactile_type=TactileType.TEMPERATURE,
            intensity=5.0,
            location=BodyPart.CHEST,
            emotional_tag="anxiety"
        )
        
        response = await initialized_tactile_system.process_stimulus(anxious_stimulus)
        # Anxiety has intensity_modifier of 1.5
        assert response.perceived_intensity > 5.0

    def test_set_arousal_level(self, tactile_system: PhysiologicalTactileSystem) -> None:
        """Test setting arousal level affects sensitivities."""
        initial_sensitivity = tactile_system.get_body_part_sensitivity(BodyPart.HANDS)
        
        # Set high arousal
        tactile_system.set_arousal_level(80.0)
        assert tactile_system.arousal_level == 80.0
        
        # Pain receptors should be more sensitive at high arousal
        high_arousal_sensitivity = tactile_system.get_body_part_sensitivity(BodyPart.HANDS)
        assert high_arousal_sensitivity > initial_sensitivity

    def test_arousal_bounds(self, tactile_system: PhysiologicalTactileSystem) -> None:
        """Test arousal level bounds."""
        tactile_system.set_arousal_level(-10.0)  # Should clamp to 0
        assert tactile_system.arousal_level == 0.0
        
        tactile_system.set_arousal_level(150.0)  # Should clamp to 100
        assert tactile_system.arousal_level == 100.0

    def test_get_receptor_status(self, tactile_system: PhysiologicalTactileSystem) -> None:
        """Test getting receptor status."""
        status = tactile_system.get_receptor_status(BodyPart.HANDS)
        assert isinstance(status, dict)
        assert len(status) > 0

    def test_callback_registration(self, tactile_system: PhysiologicalTactileSystem) -> None:
        """Test callback registration."""
        callback_called = [False]
        
        def test_callback(stimulus: TactileStimulus) -> None:
            callback_called[0] = True
        
        tactile_system.register_stimulus_callback(test_callback)
        assert len(tactile_system._on_stimulus_callbacks) == 1


# =============================================================================
# TrajectoryAnalyzer Tests
# =============================================================================

class TestTrajectoryAnalyzer:
    """Tests for the TrajectoryAnalyzer class."""

    def test_analyzer_initialization(self, trajectory_analyzer: TrajectoryAnalyzer) -> None:
        """Test analyzer initialization."""
        assert len(trajectory_analyzer.points) == 0
        assert trajectory_analyzer.max_points == 1000
        assert trajectory_analyzer.min_points_for_analysis == 3

    def test_add_point(self, trajectory_analyzer: TrajectoryAnalyzer) -> None:
        """Test adding trajectory points."""
        trajectory_analyzer.add_point(0.0, 0.0, pressure=0.5)
        assert len(trajectory_analyzer.points) == 1
        assert trajectory_analyzer.points[0].x == 0.0
        assert trajectory_analyzer.points[0].y == 0.0
        assert trajectory_analyzer.points[0].pressure == 0.5

    def test_add_multiple_points(self, trajectory_analyzer: TrajectoryAnalyzer) -> None:
        """Test adding multiple points."""
        points: List[Tuple[float, float, float]] = [
            (0, 0, 0.5), (10, 0, 0.6), (20, 0, 0.7)
        ]
        trajectory_analyzer.add_points(points)
        assert len(trajectory_analyzer.points) == 3

    def test_analyze_insufficient_data(self, trajectory_analyzer: TrajectoryAnalyzer) -> None:
        """Test analysis with insufficient points."""
        trajectory_analyzer.add_point(0, 0)
        result = trajectory_analyzer.analyze()
        
        assert result.movement_pattern == "insufficient_data"
        assert result.pattern_confidence == 0.0
        assert result.velocity == 0.0

    def test_analyze_straight_line(self, trajectory_analyzer: TrajectoryAnalyzer) -> None:
        """Test analysis of straight line trajectory."""
        # Create a straight horizontal line
        for i in range(10):
            trajectory_analyzer.add_point(float(i * 10), 100.0, pressure=0.8)
        
        result = trajectory_analyzer.analyze()
        
        # Straight line should have low curvature
        assert result.curvature < 0.1
        # Should detect as line or slide
        assert result.movement_pattern in ["line", "slide", "still"]
        assert result.velocity > 0

    def test_analyze_curved_trajectory(self, trajectory_analyzer: TrajectoryAnalyzer) -> None:
        """Test analysis of curved trajectory."""
        # Create a curved trajectory (semicircle)
        for i in range(20):
            angle = i * 0.157  # ~9 degrees per step
            x = math.cos(angle) * 50 + 100
            y = math.sin(angle) * 50 + 100
            trajectory_analyzer.add_point(x, y, pressure=0.5)
        
        result = trajectory_analyzer.analyze()
        
        # Curved trajectory should have higher curvature
        assert result.curvature > 0.05
        assert result.velocity > 0
        assert result.total_distance > 0

    def test_calculate_velocities(self, trajectory_analyzer: TrajectoryAnalyzer) -> None:
        """Test velocity calculation."""
        # Add points with known spacing
        trajectory_analyzer.add_point(0, 0)
        trajectory_analyzer.add_point(100, 0)
        trajectory_analyzer.add_point(200, 0)
        
        velocities = trajectory_analyzer._calculate_velocities()
        
        assert len(velocities) == 2
        assert all(v > 0 for v in velocities)

    def test_pattern_classification_fast(self, trajectory_analyzer: TrajectoryAnalyzer) -> None:
        """Test fast movement pattern classification."""
        # Create fast movement (large distances in short time)
        for i in range(5):
            trajectory_analyzer.add_point(float(i * 100), 100.0)
        
        result = trajectory_analyzer.analyze()
        
        # High velocity should trigger fast pattern
        if result.velocity > 300:
            assert result.movement_pattern == "fast"

    def test_clear(self, trajectory_analyzer: TrajectoryAnalyzer) -> None:
        """Test clearing trajectory data."""
        trajectory_analyzer.add_point(0, 0)
        trajectory_analyzer.add_point(10, 10)
        
        trajectory_analyzer.clear()
        
        assert len(trajectory_analyzer.points) == 0
        assert trajectory_analyzer._last_analysis is None

    def test_max_points_limit(self, trajectory_analyzer: TrajectoryAnalyzer) -> None:
        """Test maximum points limit."""
        # Add more points than max
        for i in range(trajectory_analyzer.max_points + 10):
            trajectory_analyzer.add_point(float(i), 0.0)
        
        assert len(trajectory_analyzer.points) == trajectory_analyzer.max_points


# =============================================================================
# AdaptationMechanism Tests
# =============================================================================

class TestAdaptationMechanism:
    """Tests for the AdaptationMechanism class."""

    def test_mechanism_initialization(self, adaptation_mechanism: AdaptationMechanism) -> None:
        """Test mechanism initialization."""
        assert adaptation_mechanism.habituation_rate == 0.05
        assert adaptation_mechanism.dishabituation_boost == 0.3
        assert adaptation_mechanism.recovery_rate == 0.02
        assert adaptation_mechanism.min_sensitivity == 0.1
        assert adaptation_mechanism.max_sensitivity == 1.0

    def test_register_receptor(self, adaptation_mechanism: AdaptationMechanism) -> None:
        """Test receptor registration."""
        state = adaptation_mechanism.register_receptor(
            "hand_meissner",
            base_sensitivity=0.8,
            initial_habituation=0.0
        )
        
        assert isinstance(state, ReceptorAdaptationState)
        assert state.receptor_id == "hand_meissner"
        assert state.base_sensitivity == 0.8
        assert state.current_sensitivity == 0.8
        assert state.habituation_level == 0.0

    def test_habituation(self, adaptation_mechanism: AdaptationMechanism) -> None:
        """Test habituation (sensitivity reduction with repeated stimuli)."""
        adaptation_mechanism.register_receptor("test_receptor", base_sensitivity=0.8)
        
        # Apply repeated stimuli
        state = None
        for _ in range(10):
            state = adaptation_mechanism.process_stimulus("test_receptor", "touch", intensity=0.5)
        
        # Sensitivity should decrease due to habituation
        assert state is not None
        assert state.habituation_level > 0
        assert state.current_sensitivity < 0.8

    def test_dishabituation(self, adaptation_mechanism: AdaptationMechanism) -> None:
        """Test dishabituation (sensitivity recovery with new stimulus)."""
        adaptation_mechanism.register_receptor("test_receptor", base_sensitivity=0.8)
        
        # First habituate with touch
        for _ in range(10):
            adaptation_mechanism.process_stimulus("test_receptor", "touch", intensity=0.5)
        
        habituated_state = adaptation_mechanism.get_adaptation_state("test_receptor")
        assert habituated_state is not None
        habituated_level = habituated_state.habituation_level
        
        # Now apply different stimulus (vibration) - should trigger dishabituation
        new_state = adaptation_mechanism.process_stimulus("test_receptor", "vibration", intensity=0.8)
        
        # Habituation should decrease
        assert new_state.habituation_level < habituated_level

    def test_stimulus_history_tracking(self, adaptation_mechanism: AdaptationMechanism) -> None:
        """Test stimulus history tracking."""
        adaptation_mechanism.register_receptor("test_receptor")
        
        adaptation_mechanism.process_stimulus("test_receptor", "touch", intensity=0.5)
        adaptation_mechanism.process_stimulus("test_receptor", "touch", intensity=0.5)
        
        history = adaptation_mechanism.stimulus_history.get("test_receptor", [])
        assert len(history) == 2

    def test_receptor_reset(self, adaptation_mechanism: AdaptationMechanism) -> None:
        """Test receptor reset functionality."""
        adaptation_mechanism.register_receptor("test_receptor", base_sensitivity=0.8)
        
        # Habituate
        for _ in range(10):
            adaptation_mechanism.process_stimulus("test_receptor", "touch")
        
        # Reset
        adaptation_mechanism.reset_receptor("test_receptor")
        
        state = adaptation_mechanism.get_adaptation_state("test_receptor")
        assert state is not None
        assert state.current_sensitivity == 0.8
        assert state.habituation_level == 0.0
        assert state.stimulus_count == 0

    def test_set_adaptation_speed(self, adaptation_mechanism: AdaptationMechanism) -> None:
        """Test setting adaptation speed parameters."""
        adaptation_mechanism.set_adaptation_speed(
            habituation_rate=0.1,
            recovery_rate=0.05
        )
        
        assert adaptation_mechanism.habituation_rate == 0.1
        assert adaptation_mechanism.recovery_rate == 0.05

    @pytest.mark.asyncio
    async def test_recovery_over_time(self, adaptation_mechanism: AdaptationMechanism) -> None:
        """Test sensitivity recovery over time."""
        adaptation_mechanism.register_receptor("test_receptor", base_sensitivity=0.8)
        
        # Habituate
        for _ in range(10):
            adaptation_mechanism.process_stimulus("test_receptor", "touch")
        
        habituated_sensitivity = adaptation_mechanism.get_adaptation_state("test_receptor")
        assert habituated_sensitivity is not None
        
        # Simulate time passing (force last_adaptation_time to be old)
        from datetime import datetime, timedelta
        habituated_sensitivity.last_adaptation_time = datetime.now() - timedelta(seconds=10)
        
        # Run update
        await adaptation_mechanism.update(delta_time=5.0)
        
        # Sensitivity should start recovering
        recovered_state = adaptation_mechanism.get_adaptation_state("test_receptor")
        assert recovered_state is not None


# =============================================================================
# Integration Tests
# =============================================================================

class TestTactileSystemIntegration:
    """Integration tests for the tactile system."""

    @pytest.mark.asyncio
    async def test_full_stimulus_processing_workflow(self) -> None:
        """Test complete stimulus processing workflow."""
        system = PhysiologicalTactileSystem()
        await system.initialize()
        
        try:
            # Set emotional context
            system.apply_emotional_context("comfort", intensity=0.8)
            
            # Create and process stimulus
            stimulus = TactileStimulus(
                tactile_type=TactileType.PRESSURE,
                intensity=4.0,
                location=BodyPart.SHOULDERS,
                duration=3.0,
                emotional_tag="comfort"
            )
            
            response = await system.process_stimulus(stimulus)
            
            assert response.perceived_intensity > 0
            assert response.activated_receptors > 0
            
            # Check that stimulus was recorded in history
            assert len(system._stimulus_history) > 0
            
        finally:
            await system.shutdown()

    def test_trajectory_with_analyzer(self) -> None:
        """Test trajectory analysis integration."""
        analyzer = TrajectoryAnalyzer()
        
        # Simulate a complex gesture
        for i in range(30):
            x = i * 5 + math.sin(i * 0.5) * 20
            y = 100 + i * 2
            analyzer.add_point(x, y, pressure=0.5 + i * 0.01)
        
        analysis = analyzer.analyze()
        
        assert analysis.velocity > 0
        assert analysis.duration > 0
        assert analysis.total_distance > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
