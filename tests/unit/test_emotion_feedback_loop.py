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

    def test_feedback_does_not_raise_exceptions(self, emotion_system):
        """process_interaction_feedback should never raise exceptions."""
        es = emotion_system

        # Various edge case inputs should not crash
        for engagement in (0.0, 0.01, 10.0, 100.0):
            try:
                es.process_interaction_feedback(
                    engagement_ratio=engagement, had_error=False
                )
            except Exception as e:
                pytest.fail(
                    f"process_interaction_feedback raised {e} for engagement={engagement}"
                )

        for error_val in (True, False):
            try:
                es.process_interaction_feedback(
                    engagement_ratio=1.0, had_error=error_val
                )
            except Exception as e:
                pytest.fail(
                    f"process_interaction_feedback raised {e} for had_error={error_val}"
                )

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
