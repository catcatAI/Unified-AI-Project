"""Unit tests for CausalReasoningEngine — core causal inference methods."""
import pytest

from apps.backend.src.ai.reasoning.causal_reasoning_engine import (
    CausalReasoningEngine,
)


class TestCausalReasoningEngine:
    """Unit tests for CausalReasoningEngine core methods."""

    def test_init_defaults(self):
        engine = CausalReasoningEngine()
        assert engine._causality_threshold == 0.3
        assert len(engine.get_relationships()) == 0

    def test_init_custom_threshold(self):
        engine = CausalReasoningEngine({"causality_threshold": 0.7})
        assert engine._causality_threshold == 0.7

    def test_learn_without_data(self):
        engine = CausalReasoningEngine()
        engine.learn({"id": "obs1", "variables": ["a", "b"]})
        assert len(engine.get_relationships()) == 2

    def test_learn_with_correlation_data(self):
        engine = CausalReasoningEngine({"causality_threshold": 0.3})
        obs = {
            "id": "test_corr",
            "variables": ["x", "y", "z"],
            "data": {
                "x": [1, 2, 3, 4, 5],
                "y": [2, 4, 6, 8, 10],
                "z": [5, 4, 3, 2, 1],
            },
        }
        engine.learn(obs)
        rels = engine.get_relationships()
        assert len(rels) >= 4

    def test_predict_and_explain(self):
        engine = CausalReasoningEngine({"causality_threshold": 0.1})
        obs = {
            "id": "t",
            "variables": ["a", "b", "c"],
            "data": {"a": [1], "b": [2], "c": [3]},
        }
        engine.learn(obs)
        pred = engine.predict("a")
        assert len(pred) >= 1
        all_effects = {r["effect"] for r in pred if r["cause"] == "a"}
        assert "b" in all_effects or "c" in all_effects

    def test_explain_returns_causes(self):
        engine = CausalReasoningEngine({"causality_threshold": 0.1})
        obs = {
            "id": "t",
            "variables": ["a", "b"],
            "data": {"a": [1], "b": [2]},
        }
        engine.learn(obs)
        expl = engine.explain("b")
        assert any(r["cause"] == "a" for r in expl)

    def test_graph_maintained(self):
        engine = CausalReasoningEngine()
        obs = {
            "id": "t",
            "variables": ["p", "q"],
            "data": {"p": [1], "q": [2]},
        }
        engine.learn(obs)
        graph = engine.get_graph()
        assert "p" in graph
        assert "q" in graph

    def test_learn_with_existing_relationships(self):
        engine = CausalReasoningEngine()
        obs = {
            "id": "t",
            "variables": ["a", "b"],
            "relationships": [
                {"cause": "a", "effect": "b", "strength": 0.9},
            ],
        }
        engine.learn(obs)
        rels = engine.get_relationships()
        assert len(rels) == 1
        assert rels[0]["strength"] == 0.9

    def test_granger_detects_temporal_precedence(self):
        engine = CausalReasoningEngine({"causality_threshold": 0.3})
        x = [float(i) for i in range(10)]
        y = [v * 2.0 + 0.5 for v in x]
        obs = {
            "id": "granger_test",
            "variables": ["x", "y"],
            "data": {"x": x, "y": y},
        }
        engine.learn(obs)
        x_to_y = [r for r in engine.get_relationships()
                  if r["cause"] == "x" and r["effect"] == "y"]
        assert len(x_to_y) >= 1
        assert x_to_y[0]["strength"] > 0.3

    def test_do_calculus_intervention(self):
        engine = CausalReasoningEngine({"causality_threshold": 0.1})
        obs = {
            "id": "do_test",
            "variables": ["x", "y"],
            "data": {"x": [1, 2, 3], "y": [2, 4, 6]},
        }
        engine.learn(obs)
        context = {"data": obs["data"]}
        results = engine._do_calculus_intervene("x", 5.0, context)
        assert len(results) >= 1
        assert any(r["effect"] == "y" for r in results)

    def test_confounding_detection(self):
        engine = CausalReasoningEngine({"causality_threshold": 0.3})
        data = {
            "temp": [20, 25, 30, 35],
            "ice_cream": [10, 15, 20, 25],
            "crime": [5, 6, 7, 8],
        }
        conf = engine._find_confounders(
            "temp", "crime", data, ["temp", "ice_cream", "crime"]
        )
        assert isinstance(conf, list)

    def test_pearson_edge_cases(self):
        assert CausalReasoningEngine._pearson([], []) == 0.0
        assert CausalReasoningEngine._pearson([1.0], [2.0]) == 0.0
        assert abs(CausalReasoningEngine._pearson([1, 2, 3], [4, 5, 6]) - 1.0) < 1e-10
        assert abs(CausalReasoningEngine._pearson([1, 2, 3], [6, 5, 4]) + 1.0) < 1e-10

    @pytest.mark.asyncio
    async def test_learn_causal_relationships_async(self):
        engine = CausalReasoningEngine()
        obs = {
            "id": "async_test",
            "variables": ["a", "b"],
            "relationships": [{"cause": "a", "effect": "b", "strength": 0.8}],
        }
        rels = await engine.learn_causal_relationships([obs])
        assert len(rels) == 1

    @pytest.mark.asyncio
    async def test_plan_intervention_async(self):
        engine = CausalReasoningEngine({"causality_threshold": 0.1})
        obs = {
            "id": "plan_test",
            "variables": ["x", "y", "z"],
            "data": {"x": [1, 2, 3], "y": [2, 4, 6], "z": [3, 6, 9]},
        }
        engine.learn(obs)
        plans = await engine.plan_intervention("x", "z")
        assert isinstance(plans, list)


class TestIngestTemporalState:
    """Edge cases for ingest_temporal_state bridge."""

    def test_ingest_non_temporal_returns_zero(self):
        engine = CausalReasoningEngine()
        count = engine.ingest_temporal_state("not_a_temporal_state")
        assert count == 0

    def test_ingest_none_returns_zero(self):
        engine = CausalReasoningEngine()
        count = engine.ingest_temporal_state(None)
        assert count == 0

    def test_ingest_empty_temporal_returns_zero(self):
        engine = CausalReasoningEngine()
        from core.state.temporal import TemporalState
        ts = TemporalState()
        count = engine.ingest_temporal_state(ts)
        assert count == 0

    def test_ingest_with_snapshots_learns_observations(self):
        engine = CausalReasoningEngine()
        from core.state.temporal import TemporalState
        ts = TemporalState()
        ts.record({"axis_a": {"field_x": 1.0, "field_y": 2.0}})
        ts.record({"axis_a": {"field_x": 3.0, "field_y": 4.0}})
        count = engine.ingest_temporal_state(ts)
        assert count > 0
        assert len(engine.get_relationships()) >= 1

    def test_ingest_window_limits_observations(self):
        engine = CausalReasoningEngine()
        from core.state.temporal import TemporalState
        ts = TemporalState()
        for i in range(20):
            ts.record({"axis_b": {"val": float(i)}})
        count_small_window = engine.ingest_temporal_state(ts, window=5)
        assert count_small_window <= 5


class TestRetrospectiveWarmStart:
    """Tests for retrospective_warm_start() — baseline relationship seeding."""

    def test_warm_start_creates_baseline_relationships(self):
        engine = CausalReasoningEngine()
        count = engine.retrospective_warm_start()
        assert count > 0
        rels = engine.get_relationships()
        assert len(rels) == count

    def test_warm_start_predict_user_input_from_round_one(self):
        """The core C³ goal: predict('user_input') works from the start."""
        engine = CausalReasoningEngine()
        engine.retrospective_warm_start()
        preds = engine.predict("user_input")
        assert len(preds) > 0
        assert all(r["cause"] == "user_input" for r in preds)
        assert all(r["strength"] > 0 for r in preds)

    def test_warm_start_idempotent(self):
        """Calling warm-start twice does not duplicate relationships."""
        engine = CausalReasoningEngine()
        count1 = engine.retrospective_warm_start()
        count2 = engine.retrospective_warm_start()
        assert count2 == 0  # Second call skips
        assert len(engine.get_relationships()) == count1

    def test_warm_start_graph_includes_all_variables(self):
        engine = CausalReasoningEngine()
        engine.retrospective_warm_start()
        graph = engine.get_graph()
        # Baseline variables: user_input, angela_response, conversation_momentum,
        # query_complexity, interaction_value
        assert "user_input" in graph
        assert "angela_response" in graph
        assert "conversation_momentum" in graph

    def test_warm_start_does_not_overwrite_existing_relationships(self):
        """If the engine already has relationships, warm-start skips."""
        engine = CausalReasoningEngine({"causality_threshold": 0.1})
        engine.learn({
            "id": "pre_existing",
            "variables": ["custom_a", "custom_b"],
            "data": {"custom_a": [1], "custom_b": [2]},
        })
        before = len(engine.get_relationships())
        count = engine.retrospective_warm_start()
        assert count == 0  # Skips because relationships exist
        assert len(engine.get_relationships()) == before

    def test_warm_start_predict_before_any_live_data(self):
        """Warm-start enables predict() BEFORE any learn() call from live data."""
        engine = CausalReasoningEngine()
        engine.retrospective_warm_start()
        # No live learn() calls yet
        preds = engine.predict("user_input")
        assert len(preds) >= 2  # At least 2 baseline user_input→angela_response
        # angela_response should appear in the top predictions
        effects = [r["effect"] for r in preds]
        assert "angela_response" in effects

    def test_warm_start_explain_works(self):
        """explain() also works after warm-start."""
        engine = CausalReasoningEngine()
        engine.retrospective_warm_start()
        expl = engine.explain("angela_response")
        assert len(expl) > 0
        assert expl[0]["effect"] == "angela_response"
