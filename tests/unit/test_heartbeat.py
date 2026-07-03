"""Tests for MetabolicHeartbeat"""
import pytest


class TestMetabolicHeartbeat:
    """Tests for MetabolicHeartbeat"""

    def test_import(self):
        from core.life.heartbeat import MetabolicHeartbeat
        assert MetabolicHeartbeat is not None

    def test_instantiation(self):
        from core.life.heartbeat import MetabolicHeartbeat
        instance = MetabolicHeartbeat(update_interval=60.0)
        assert instance is not None
        assert instance.update_interval == 60.0
        assert instance._running is False

    def test_instantiation_default_interval(self):
        from core.life.heartbeat import MetabolicHeartbeat
        instance = MetabolicHeartbeat()
        assert instance.update_interval == 30.0

    def test_initial_position(self):
        from core.life.heartbeat import MetabolicHeartbeat
        instance = MetabolicHeartbeat()
        assert instance.x == 200.0
        assert instance.y == 0.0
        assert instance.screen_w == 1920

    def test_cns_feedback_subscribes_and_tracks_emotion(self):
        from core.life.heartbeat import MetabolicHeartbeat
        hb = MetabolicHeartbeat()
        assert hb._system_health_score == 0.5
        assert hb._health_update_count == 0
        hb._handle_cns_event("emotion.updated", {"arousal": 0.5, "valence": 0.5})
        assert hb._health_update_count == 1
        assert len(hb._emotion_stability) == 1

    def test_cns_feedback_routing_event(self):
        from core.life.heartbeat import MetabolicHeartbeat
        hb = MetabolicHeartbeat()
        hb._handle_cns_event("routing.response_generated", {})
        assert hb._health_update_count == 1
        assert len(hb._response_quality) == 1

    def test_cns_feedback_lifecycle_success(self):
        from core.life.heartbeat import MetabolicHeartbeat
        hb = MetabolicHeartbeat()
        hb._handle_cns_event("lifecycle.decision_executed", {"success": True})
        assert hb._health_update_count == 1
        assert len(hb._lifecycle_success) == 1
        assert hb._lifecycle_success[0] == 1.0

    def test_cns_feedback_lifecycle_failure(self):
        from core.life.heartbeat import MetabolicHeartbeat
        hb = MetabolicHeartbeat()
        hb._handle_cns_event("lifecycle.decision_executed", {"success": False})
        assert hb._lifecycle_success[0] == 0.0

    def test_get_system_health_returns_all_keys(self):
        from core.life.heartbeat import MetabolicHeartbeat
        hb = MetabolicHeartbeat()
        health = hb.get_system_health()
        assert "system_health" in health
        assert "health_update_count" in health
        assert "emotion_stability_samples" in health
        assert "response_quality_samples" in health
        assert "lifecycle_success_samples" in health

    def test_get_system_health_after_events(self):
        from core.life.heartbeat import MetabolicHeartbeat
        hb = MetabolicHeartbeat()
        hb._handle_cns_event("emotion.updated", {"arousal": 0.8, "valence": 0.9})
        hb._handle_cns_event("routing.response_generated", {})
        hb._handle_cns_event("lifecycle.decision_executed", {"success": True})
        health = hb.get_system_health()
        assert health["emotion_stability_samples"] == 1
        assert health["response_quality_samples"] == 1
        assert health["lifecycle_success_samples"] == 1

    def test_heartbeat_voter_abstains_when_no_health(self):
        from ai.meta.priority_negotiator import heartbeat_voter
        result = heartbeat_voter({})
        assert result is None

    def test_heartbeat_voter_low_health_forces_conservative(self):
        from ai.meta.priority_negotiator import heartbeat_voter
        result = heartbeat_voter({"heartbeat_health": {"system_health": 0.2}})
        assert result is not None
        assert result.routing_mode == "conservative"

    def test_heartbeat_voter_healthy_does_not_force_mode(self):
        from ai.meta.priority_negotiator import heartbeat_voter
        result = heartbeat_voter({"heartbeat_health": {"system_health": 0.8}})
        assert result is not None
        assert result.routing_mode is None

    def test_pulse_event_includes_system_health(self):
        from core.life.heartbeat import MetabolicHeartbeat
        hb = MetabolicHeartbeat()
        hb._handle_cns_event("emotion.updated", {"arousal": 0.5, "valence": 0.5})
        health = hb.get_system_health()
        assert health["system_health"] > 0
