"""Tests for core.engine.influence_applicator"""
import pytest

class TestInfluenceApplicator:
    def test_import(self):
        from apps.backend.src.core.engine.influence_applicator import (
            InfluenceApplicator, INFLUENCE_RULES, apply_influence_to_axis, get_applicator,
        )
        assert hasattr(InfluenceApplicator, 'apply')
        assert isinstance(INFLUENCE_RULES, dict)

    def test_instantiation(self):
        from apps.backend.src.core.engine.influence_applicator import InfluenceApplicator
        instance = InfluenceApplicator()
        assert instance._rules is not None
        assert "alpha" in instance._rules

    def test_custom_rules(self):
        from apps.backend.src.core.engine.influence_applicator import InfluenceApplicator
        custom = {"alpha": {"beta": [("energy", "focus", 0.5)]}}
        instance = InfluenceApplicator(rules=custom)
        assert instance._rules == custom

    def test_apply_unknown_source_does_nothing(self):
        from apps.backend.src.core.engine.influence_applicator import InfluenceApplicator
        instance = InfluenceApplicator(rules={"alpha": {"beta": []}})
        source = type("Dim", (), {"values": {"energy": 0.8}})()
        target = type("Dim", (), {"values": {"focus": 0.5}})()
        instance.apply("unknown", "beta", source, target, 1.0)
        assert target.values["focus"] == 0.5

    def test_apply_known_rule_updates_target(self):
        from apps.backend.src.core.engine.influence_applicator import InfluenceApplicator
        instance = InfluenceApplicator(rules={"alpha": {"beta": [("energy", "focus", 0.5)]}})
        source = type("Dim", (), {"values": {"energy": 0.8}})()
        target = type("Dim", (), {"values": {"focus": 0.5}})()
        instance.apply("alpha", "beta", source, target, 1.0)
        assert target.values["focus"] == pytest.approx(0.9, rel=1e-3)

    def test_get_applicator_returns_singleton(self):
        from apps.backend.src.core.engine.influence_applicator import get_applicator
        a1 = get_applicator()
        a2 = get_applicator()
        assert a1 is a2

    def test_influence_rules_have_expected_keys(self):
        from apps.backend.src.core.engine.influence_applicator import INFLUENCE_RULES
        for source in ["alpha", "beta", "gamma", "delta", "epsilon", "theta", "zeta"]:
            assert source in INFLUENCE_RULES
            for target, rules in INFLUENCE_RULES[source].items():
                for src_f, tgt_f, w in rules:
                    assert isinstance(src_f, str)
                    assert isinstance(tgt_f, str)
                    assert isinstance(w, float)
