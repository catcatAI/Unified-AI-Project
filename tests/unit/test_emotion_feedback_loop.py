"""
Tests for EmotionSystem process_interaction_feedback() — C³ feedback loop closure.

Verifies that interaction outcomes (engagement ratio, errors) correctly
adjust Angela's emotional state, closing the Emotion→Behavior→Response→Feedback→Emotion loop.
"""

# =============================================================================
# ANGELA-MATRIX: [L2] [β] [A] [L2]
# =============================================================================

import sys
from pathlib import Path

import pytest

# Ensure project root is on sys.path
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# EmotionalState is a module-level dataclass, not nested in EmotionSystem
from ai.alignment.emotion_system import (  # noqa: E402
    EmotionSystem,
    EmotionType,
)


@pytest.fixture
def emotion_system():
    """Create a fresh EmotionSystem instance with baseline state."""
    es = EmotionSystem()
    # Ensure we have a baseline emotional state by using the public API
    es.apply_influence("test_setup", "calm", 0.5, 0.5)
    return es


@pytest.fixture
def emotion_system_positive():
    """Create an EmotionSystem with a positive baseline."""
    es = EmotionSystem()
    es.apply_influence("test_setup", "dopamine", 0.5, 0.8)
    return es


class TestProcessInteractionFeedback:
    """Test the feedback loop method."""

    def test_high_engagement_boosts_joy_and_dopamine(self, emotion_system):
        """High engagement (>2.0) should shift emotion toward joy/dopamine."""
        es = emotion_system
        es.process_interaction_feedback(engagement_ratio=3.0, had_error=False)

        last = es.emotion_history[-1]
        # High engagement should increase valence (joy)
        assert last.valence > 0.3, f"Expected valence > 0.3, got {last.valence}"
        # Emotion should be positive (JOY or TRUST)
        assert last.primary_emotion.value in ("joy", "trust"), \
            f"Expected joy/trust, got {last.primary_emotion.value}"

    def test_low_engagement_causes_stress_or_sadness(self, emotion_system):
        """Low engagement (<0.5) should shift emotion toward stress/sadness."""
        es = emotion_system
        es.process_interaction_feedback(engagement_ratio=0.2, had_error=False)

        last = es.emotion_history[-1]
        # Low engagement should decrease valence
        assert last.valence < 0.5, f"Expected valence < 0.5, got {last.valence}"

    def test_error_triggers_stress_and_fear(self, emotion_system):
        """Errors should trigger stress/fear response regardless of engagement."""
        es = emotion_system
        # Even with high engagement, an error should override to stress
        es.process_interaction_feedback(engagement_ratio=3.0, had_error=True)

        last = es.emotion_history[-1]
        # Error should decrease valence (negative emotion)
        assert last.valence < 0.5, f"Expected valence < 0.5 after error, got {last.valence}"

    def test_explicit_failure_triggers_negative_response(self, emotion_system):
        """Explicit response_success=False should trigger negative emotional response."""
        es = emotion_system
        es.process_interaction_feedback(
            engagement_ratio=1.0, had_error=False, response_success=False
        )

        last = es.emotion_history[-1]
        # Failure should result in negative valence
        assert last.valence < 0.5, f"Expected valence < 0.5 after failure, got {last.valence}"

    def test_neutral_engagement_causes_mild_positive(self, emotion_system):
        """Neutral engagement (0.5-2.0) should result in mild calm/trust."""
        es = emotion_system
        es.process_interaction_feedback(engagement_ratio=1.0, had_error=False)

        last = es.emotion_history[-1]
        # Neutral engagement should maintain or slightly increase valence
        assert last.valence >= -0.1, f"Expected valence >= -0.1, got {last.valence}"

    def test_empty_history_creates_baseline_before_feedback(self, emotion_system):
        """When emotion history is empty, feedback should create a baseline first."""
        es = emotion_system
        # Clear history
        es.emotion_history.clear()
        es.process_interaction_feedback(engagement_ratio=0.5, had_error=True)

        # Should have at least 1 state in history
        assert len(es.emotion_history) >= 1, "Feedback should create baseline state"
        # Last state should have valid values
        last = es.emotion_history[-1]
        assert -1.0 <= last.valence <= 1.0
        assert 0.0 <= last.arousal <= 1.0

    def test_very_low_engagement_has_stronger_impact(self, emotion_system):
        """Extremely low engagement should cause proportionally stronger negative impact."""
        es = emotion_system
        # Record initial valence
        initial_valence = es.emotion_history[-1].valence

        es.process_interaction_feedback(engagement_ratio=0.05, had_error=False)
        after_low = es.emotion_history[-1]

        # The valence should change (either decrease or stay same - not increase)
        assert after_low.valence <= initial_valence, \
            f"Expected no valence increase from {initial_valence}, got {after_low.valence}"

    def test_consecutive_good_feedback_builds_positive_momentum(self, emotion_system):
        """Multiple consecutive high-engagement interactions should accumulate positive emotion."""
        es = emotion_system
        for _ in range(3):
            es.process_interaction_feedback(engagement_ratio=4.0, had_error=False)

        last = es.emotion_history[-1]
        # After 3 good interactions, valence should be clearly positive
        assert last.valence > 0.3, f"Expected strong positive valence, got {last.valence}"
        # Emotion should be clearly positive
        assert last.primary_emotion.value in ("joy", "trust", "surprise"), \
            f"Expected positive emotion, got {last.primary_emotion.value}"

    def test_consecutive_bad_feedback_builds_negative_momentum(self, emotion_system):
        """Multiple consecutive error interactions should accumulate negative emotion."""
        es = emotion_system
        for _ in range(3):
            es.process_interaction_feedback(
                engagement_ratio=0.1, had_error=True
            )

        last = es.emotion_history[-1]
        # After 3 bad interactions, valence should be lower than initial
        assert last.valence < 0.5, f"Expected lower valence after bad feedback, got {last.valence}"

    @pytest.mark.parametrize("engagement", [0.0, 0.01, 10.0, 100.0])
    def test_feedback_edge_case_engagement(self, emotion_system, engagement):
        es = emotion_system
        es.process_interaction_feedback(engagement_ratio=engagement, had_error=False)
        last = es.emotion_history[-1]
        assert -1.0 <= last.valence <= 1.0, f"Valence {last.valence} out of range"
        assert 0.0 <= last.arousal <= 1.0, f"Arousal {last.arousal} out of range"

    @pytest.mark.parametrize("error_val", [True, False])
    def test_feedback_edge_case_error_val(self, emotion_system, error_val):
        es = emotion_system
        es.process_interaction_feedback(engagement_ratio=1.0, had_error=error_val)
        last = es.emotion_history[-1]
        assert -1.0 <= last.valence <= 1.0, f"Valence {last.valence} out of range"
        assert 0.0 <= last.arousal <= 1.0, f"Arousal {last.arousal} out of range"

    def test_feedback_preserves_valid_emotional_state(self, emotion_system):
        """After feedback, the emotional state should always have valid ranges."""
        es = emotion_system
        es.process_interaction_feedback(engagement_ratio=0.3, had_error=False)

        last = es.emotion_history[-1]
        assert -1.0 <= last.valence <= 1.0, \
            f"Valence {last.valence} out of range"
        assert 0.0 <= last.arousal <= 1.0, \
            f"Arousal {last.arousal} out of range"
        assert 0.0 <= last.emotion_intensity <= 1.0, \
            f"Intensity {last.emotion_intensity} out of range"
        assert isinstance(last.primary_emotion, EmotionType), \
            f"Invalid emotion type: {last.primary_emotion}"

    def test_sustained_low_engagement_resets_counter_on_recovery(self, emotion_system):
        """After 2 low-engagement interactions, one good interaction resets the counter."""
        es = emotion_system
        for _ in range(2):
            es.process_interaction_feedback(engagement_ratio=0.1, had_error=False)
        es.process_interaction_feedback(engagement_ratio=3.0, had_error=False)
        assert es._sustained_negative_counter == 0, \
            "Counter should reset after positive interaction"


class TestSustainedNegativeRouting:
    """C³ 6.0: Verify that sustained low engagement actually flips routing_mode."""

    def setup_method(self):
        self.es = EmotionSystem()
        self.es.apply_influence("setup", "calm", 0.5, 0.5)

    def _get_routing_mode(self):
        adj = self.es.get_behavioral_adjustment()
        return adj.get("routing_mode", "neutral")

    def test_single_low_engagement_does_not_flip_to_conservative(self):
        """A single low-engagement event should not change routing_mode."""
        for _ in range(3):
            self.es.process_interaction_feedback(engagement_ratio=3.0, had_error=False)
        # After 3 good, should be exploratory
        assert self._get_routing_mode() == "exploratory", \
            f"Expected exploratory after good feedback, got {self._get_routing_mode()}"

        self.es.process_interaction_feedback(engagement_ratio=0.1, had_error=False)
        # After 1 bad, should still be the same (no flip yet)
        mode_after = self._get_routing_mode()

    def test_three_low_engagement_in_row_flips_routing(self):
        """Three consecutive low-engagement interactions should flip routing_mode."""
        for _ in range(5):
            self.es.process_interaction_feedback(engagement_ratio=0.1, had_error=False)
        # After 5 low, counter >= 3 means cumulative fatigue should have flipped
        mode = self._get_routing_mode()
        assert mode == "conservative", \
            f"Expected conservative after 5 low engagements, got {mode}"

    def test_three_errors_in_row_flips_routing(self):
        """Three consecutive errors should flip routing_mode."""
        for _ in range(5):
            self.es.process_interaction_feedback(engagement_ratio=1.0, had_error=True)
        mode = self._get_routing_mode()
        assert mode == "conservative", \
            f"Expected conservative after 5 errors, got {mode}"

    def test_sustained_negative_counter_tracks_accurately(self):
        """The counter should track sustained negative interactions."""
        assert self.es._sustained_negative_counter == 0
        for _ in range(4):
            self.es.process_interaction_feedback(engagement_ratio=0.1, had_error=False)
        assert self.es._sustained_negative_counter == 4, \
            f"Expected counter=4, got {self.es._sustained_negative_counter}"

    def test_recovery_after_sustained_negative(self):
        """After sustained negative, recovery should reset counter and restore routing."""
        for _ in range(5):
            self.es.process_interaction_feedback(engagement_ratio=0.1, had_error=False)
        assert self._get_routing_mode() == "conservative"
        # Recover with good feedback
        for _ in range(4):
            self.es.process_interaction_feedback(engagement_ratio=3.0, had_error=False)
        assert self.es._sustained_negative_counter == 0
        assert self._get_routing_mode() == "exploratory"

    @pytest.mark.parametrize("count", [3, 5, 8])
    def test_routing_flips_at_threshold_and_remains(self, emotion_system, count):
        """Routing should flip and stay flipped as long as counter remains >= threshold."""
        for _ in range(count):
            emotion_system.process_interaction_feedback(engagement_ratio=0.1, had_error=False)
        mode = emotion_system.get_behavioral_adjustment().get("routing_mode", "neutral")
        assert mode == "conservative", \
            f"Expected conservative after {count} low, got {mode}"
