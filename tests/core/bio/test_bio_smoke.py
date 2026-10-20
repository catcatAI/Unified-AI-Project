"""
ANGELA-MATRIX: [L3] [βγδ] [B] [L2]
Smoke-level coverage for core/bio.

The gap-closure plan listed "薄弱檔按域補測（先 agent_workspace_routes、
core/bio、core/engine 的冒烟級）" as open work: core/bio has ~20 modules
whose only coverage was an import line, so a constructor that raised or a
method that returned the wrong shape would not have failed anything.

These tests are deliberately smoke-level: each subsystem is constructed and
its main entry point is exercised, and the *observable* contract (the
returned types and the clamping) is asserted.
"""

import pytest


class TestAutonomicNervousSystem:
    def test_arousal_maps_to_a_state(self):
        from core.bio.autonomic_nervous_system import ANSState

        assert ANSState.from_arousal(0.0) is not None
        assert ANSState.from_arousal(1.0) is not None

    def test_setting_the_arousal_is_clamped(self):
        from core.bio.autonomic_nervous_system import AutonomicNervousSystem

        system = AutonomicNervousSystem()
        system.set_arousal_directly(200.0)
        assert system.arousal_level == 100
        system.set_arousal_directly(-50.0)
        assert system.arousal_level == 0


class TestCerebellumEngine:
    def test_posture_is_reported(self):
        from core.bio.cerebellum_engine import CerebellumEngine

        engine = CerebellumEngine()
        engine.update_proprioception([0.0] * 6)
        posture = engine.get_posture("default")
        assert isinstance(posture, dict)


class TestEmotionalBlending:
    def test_blending_two_emotions(self):
        from core.bio.emotional_blending import BasicEmotion, PADEmotion

        a = PADEmotion.from_basic_emotion(BasicEmotion.JOY, 0.8)
        b = PADEmotion.from_basic_emotion(BasicEmotion.SADNESS, 0.8)
        blended = a.blend_with(b, 0.5)
        assert isinstance(blended, PADEmotion)
        assert 0.0 <= blended.pleasure <= 1.0

    def test_the_distance_to_itself_is_zero(self):
        from core.bio.emotional_blending import BasicEmotion, PADEmotion

        a = PADEmotion.from_basic_emotion(BasicEmotion.JOY, 0.5)
        assert a.distance_to(a) == pytest.approx(0.0, abs=1e-6)


class TestFeedbackLoop:
    def test_the_hpa_axis_step_returns_a_cortisol_level(self):
        from core.bio.feedback_loop import FeedbackLoop

        loop = FeedbackLoop()
        cortisol = loop.hpa_axis_step(0.5)
        assert isinstance(cortisol, (int, float))
        assert cortisol >= 0.0


class TestHabitFormation:
    def test_a_habit_needs_reinforcement_to_form(self):
        from core.bio.habit_formation import HabitFormation

        formation = HabitFormation()
        formation.start_habit("h1", "Habit one")
        assert formation.is_habit_formed("h1") is False
        for _ in range(30):
            formation.reinforce("h1", 1.0)
        assert formation.get_automaticity("h1") >= 0.0


class TestHormoneKinetics:
    def test_metabolism_decays_the_level(self):
        from core.bio.endocrine_types import HormoneType
        from core.bio.hormone_kinetics import HormoneKinetics

        kinetics = HormoneKinetics()
        level = kinetics.metabolize(100.0, HormoneType.CORTISOL, 1.0)
        assert isinstance(level, (int, float))
        assert 0.0 < level < 100.0, "metabolism must reduce the level"


class TestInputSensor:
    def test_activity_metrics_are_reported(self):
        from core.bio.input_sensor import GlobalInputSensor

        sensor = GlobalInputSensor()
        sensor.start()
        try:
            metrics = sensor.get_activity_metrics()
            assert isinstance(metrics, dict)
        finally:
            sensor.stop()


class TestKineticValidator:
    def test_an_unconstrained_action_is_allowed(self):
        from core.bio.kinetic_validator import KineticValidator

        validator = KineticValidator()
        ok, reason = validator.validate_action("not_a_real_action", {})
        assert ok is True
        assert reason == ""

    def test_a_movement_over_the_velocity_limit_is_rejected(self):
        import time

        from core.bio.kinetic_validator import KineticValidator

        validator = KineticValidator()
        validator.validate_action("move", {"x": 0.0, "y": 0.0})
        time.sleep(0.01)
        ok, reason = validator.validate_action("move", {"x": 10_000.0, "y": 0.0})
        assert ok is False
        assert "Velocity" in reason

    def test_strain_grows_with_velocity(self):
        from core.bio.kinetic_validator import KineticValidator

        validator = KineticValidator()
        slow = validator.calculate_strain(0.1)
        fast = validator.calculate_strain(10.0)
        assert fast >= slow


class TestMultidimensionalTrigger:
    def test_a_trigger_evaluates_to_a_score(self):
        from core.bio.multidimensional_trigger import (
            DimensionValue,
            MultidimensionalTrigger,
            TriggerCondition,
            TriggerDimension,
        )

        trigger = MultidimensionalTrigger(
            trigger_id="t1",
            name="test",
            behavior_id="b1",
            conditions=[
                TriggerCondition(
                    dimension=TriggerDimension.ENVIRONMENT,
                    operator="gt",
                    threshold=0.5,
                )
            ],
        )
        score = trigger.evaluate(
            [
                DimensionValue(
                    dimension=TriggerDimension.ENVIRONMENT,
                    value=0.9,
                    raw_value=0.9,
                )
            ]
        )
        assert 0.0 <= score <= 1.0


class TestNeuroplasticityCore:
    def test_a_weight_changes_with_activation(self):
        from core.bio.neuroplasticity_core import HebbianRule

        rule = HebbianRule()
        # Both neurons above the threshold → the weight is strengthened.
        strengthened = rule.apply(0.9, 0.8, 0.5)
        assert strengthened > 0.5
        # One neuron below the threshold → the weight decays.
        weakened = rule.apply(0.9, 0.1, 0.5)
        assert weakened < 0.5


class TestExplicitImplicitLearning:
    def test_an_explicit_event_is_remembered(self):
        from core.bio.explicit_implicit_learning import ExplicitImplicitLearning

        learning = ExplicitImplicitLearning()
        event = learning.learn_explicit("e1", "remember the milk", "milk is in the fridge")
        assert learning.get_explicit_memory(event.event_id) is not None


class TestTheJsonStoreAdapterSaysItIsAStub:
    """The compatibility proxies must not fail silently.

    They returned an empty result, so a caller asking for a resonance
    profile or the best axis could not tell "no answer" from "real answer".
    """

    def test_the_stub_warns_and_names_the_live_implementation(self, caplog):
        import logging

        from core.engine.state_matrix_adapter import StateMatrixAdapter

        adapter = StateMatrixAdapter()
        with caplog.at_level(logging.WARNING):
            assert adapter.resonance_engine.compute_profile() == {}
        assert any("compatibility stub" in r.message for r in caplog.records)
        assert any("ResonanceEngine" in r.message for r in caplog.records)
