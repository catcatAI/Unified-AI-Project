"""Integration tests: TemporalState ↔ CausalReasoningEngine bridge.
Tests the to_observations() export method and ingest_trend_buffer() consumer.
"""
import pytest
from core.state.temporal import TemporalState
from ai.reasoning.causal_reasoning_engine import CausalReasoningEngine


class TestTemporalStateToObservations:
    """Tests for TemporalState.to_observations() export method."""

    def test_empty_state_returns_empty(self):
        ts = TemporalState()
        assert ts.to_observations() == []

    def test_single_record_no_dict_axes(self):
        ts = TemporalState()
        ts.record({"msg": "hello"})
        assert ts.to_observations() == []

    def test_single_axis_two_fields(self):
        ts = TemporalState()
        ts.record({"sensor": {"temp": 22.0, "humidity": 0.6}})
        obs = ts.to_observations()
        assert len(obs) == 1
        assert obs[0]["id"] == "trend_sensor"
        assert "temp" in obs[0]["variables"]
        assert "humidity" in obs[0]["variables"]

    def test_multi_snapshot_time_series(self):
        ts = TemporalState()
        for t in range(10, 20):
            ts.record({"climate": {"temp": t, "humidity": t * 0.5}})
        obs = ts.to_observations()
        assert len(obs) == 1
        assert len(obs[0]["data"]["temp"]) == 10
        assert obs[0]["data"]["temp"] == [float(v) for v in range(10, 20)]

    def test_multiple_axes(self):
        ts = TemporalState()
        ts.record({"a": {"x": 1.0}, "b": {"y": 2.0}})
        ts.record({"a": {"x": 3.0}, "b": {"y": 4.0}})
        obs = ts.to_observations()
        assert len(obs) == 2
        ids = {o["id"] for o in obs}
        assert ids == {"trend_a", "trend_b"}

    def test_window_limits_data(self):
        ts = TemporalState()
        for t in range(100):
            ts.record({"m": {"v": float(t)}})
        obs = ts.to_observations(window=10)
        assert len(obs[0]["data"]["v"]) == 10


class TestCausalIngestTemporalState:
    """Tests for CausalReasoningEngine.ingest_temporal_state()."""

    def test_ingest_adds_relationships(self):
        cre = CausalReasoningEngine({"causality_threshold": 0.1})
        ts = TemporalState()
        for t in range(1, 11):
            ts.record({"eco": {"temp": float(t), "ice": float(t * 2)}})
        count = cre.ingest_temporal_state(ts)
        assert count >= 1
        assert len(cre.get_relationships()) >= 2

    def test_ingest_invalid_type_returns_zero(self):
        cre = CausalReasoningEngine()
        count = cre.ingest_temporal_state("not_a_state")
        assert count == 0

    def test_ingest_empty_state(self):
        cre = CausalReasoningEngine({"causality_threshold": 0.1})
        ts = TemporalState()
        count = cre.ingest_temporal_state(ts)
        assert count == 0

    def test_ingest_twice_accumulates(self):
        cre = CausalReasoningEngine({"causality_threshold": 0.1})
        ts = TemporalState()
        for t in range(1, 6):
            ts.record({"s": {"a": float(t), "b": float(t * 2)}})
        cre.ingest_temporal_state(ts)
        r1 = len(cre.get_relationships())
        for t in range(6, 11):
            ts.record({"s": {"a": float(t), "b": float(t * 2)}})
        cre.ingest_temporal_state(ts)
        r2 = len(cre.get_relationships())
        assert r2 >= r1

    def test_granger_from_temporal_data(self):
        cre = CausalReasoningEngine({"causality_threshold": 0.3})
        ts = TemporalState()
        x = [float(i) for i in range(20)]
        y = [v * 2.0 + 0.5 for v in x]
        for i in range(20):
            ts.record({"ts": {"x": x[i], "y": y[i]}})
        cre.ingest_temporal_state(ts)
        x_to_y = [r for r in cre.get_relationships()
                  if r["cause"] == "x" and r["effect"] == "y"]
        assert len(x_to_y) >= 1
        assert x_to_y[0]["strength"] > 0.3


class TestEndToEndPipeline:
    """End-to-end: TemporalState → CausalReasoningEngine → predict/explain."""

    def test_predict_after_ingest(self):
        cre = CausalReasoningEngine({"causality_threshold": 0.1})
        ts = TemporalState()
        for t in range(1, 15):
            ts.record({"stats": {"cpu": float(t), "mem": float(t * 0.5)}})
        cre.ingest_temporal_state(ts)
        pred = cre.predict("cpu")
        assert len(pred) >= 1

    def test_explain_after_ingest(self):
        cre = CausalReasoningEngine({"causality_threshold": 0.1})
        ts = TemporalState()
        for t in range(1, 15):
            ts.record({"stats": {"load": float(t), "resp": float(t * 3)}})
        cre.ingest_temporal_state(ts)
        expl = cre.explain("resp")
        assert len(expl) >= 1

    def test_graph_after_ingest(self):
        cre = CausalReasoningEngine({"causality_threshold": 0.1})
        ts = TemporalState()
        for t in range(1, 10):
            ts.record({"m": {"a": float(t), "b": float(t + 1)}})
        cre.ingest_temporal_state(ts)
        graph = cre.get_graph()
        assert "a" in graph or "b" in graph
