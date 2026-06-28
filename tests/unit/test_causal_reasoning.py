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
