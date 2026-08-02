"""TrustManager 多维信任评分系统测试"""

from apps.backend.src.ai.core.trust_manager import (
    RiskCategory,
    TrustDimension,
    TrustLevel,
    TrustManager,
)


def _seeded_manager():
    tm = TrustManager()
    tm.update_trust_score("entity-1", TrustDimension.RELIABILITY, 0.9)
    tm.update_trust_score("entity-1", TrustDimension.EXPERTISE, 0.7)
    tm.update_trust_score("entity-1", TrustDimension.COMPLIANCE, 0.8)
    return tm


class TestUpdateTrustScore:
    def test_returns_trust_score(self):
        tm = TrustManager()
        score = tm.update_trust_score("e1", TrustDimension.RELIABILITY, 0.8)
        assert score.dimension == TrustDimension.RELIABILITY
        assert score.score == 0.8
        assert 0.0 <= score.confidence <= 1.0

    def test_rejects_out_of_range(self):
        tm = TrustManager()
        try:
            tm.update_trust_score("e1", TrustDimension.RELIABILITY, 1.5)
        except ValueError:
            pass
        else:
            raise AssertionError("out-of-range score should raise ValueError")


class TestGetOverallTrustScore:
    def test_weighted_average(self):
        result = _seeded_manager().get_overall_trust_score("entity-1")
        assert result["entity_id"] == "entity-1"
        assert 0.0 <= result["overall_score"] <= 1.0
        assert result["trust_level"] in [l.value for l in TrustLevel]
        assert result["interaction_count"] >= 1

    def test_unknown_entity_default(self):
        result = _seeded_manager().get_overall_trust_score("unknown")
        assert result["overall_score"] == 0.0
        assert result["trust_level"] == TrustLevel.VERY_LOW.value

    def test_include_history(self):
        result = _seeded_manager().get_overall_trust_score("entity-1", include_history=True)
        assert "history" in result


class TestAssessInteractionRisk:
    def test_returns_assessment_without_error(self):
        tm = _seeded_manager()
        result = tm.assess_interaction_risk(
            "entity-1", {"history": [], "characteristics": {"behavior_risk": 0.5}}
        )
        assert "error" not in result
        assert 0.0 <= result["overall_risk_level"] <= 1.0
        assert result["category_assessments"]
        assert isinstance(result["recommendations"], list)

    def test_high_risk_categorization(self):
        tm = TrustManager()
        tm.update_trust_score("risky", TrustDimension.RELIABILITY, 0.1)
        result = tm.assess_interaction_risk(
            "risky", {"history": [], "characteristics": {"behavior_risk": 1.0}}
        )
        assert result["overall_risk_level"] > 0.0


class TestInteractionHistory:
    def test_update_and_track(self):
        tm = _seeded_manager()
        tm.update_interaction_history("entity-1", "chat", {"trust_impact": {}})
        relationship = tm.relationship_cache["entity-1"]
        assert len(relationship.interaction_history) == 1
        assert relationship.interaction_history[0]["type"] == "chat"


class TestTrustRelationship:
    def test_relationship_between_entities(self):
        tm = _seeded_manager()
        tm.update_trust_score("entity-2", TrustDimension.RELIABILITY, 0.6)
        rel = tm.get_trust_relationship("entity-1", "entity-2")
        assert rel["source_entity"] == "entity-1"
        assert rel["target_entity"] == "entity-2"
        assert "relationship_type" in rel
        assert 0.0 <= rel["mutual_trust"] <= 1.0


class TestTrustAnalytics:
    def test_dimension_trends(self):
        tm = _seeded_manager()
        result = tm.get_trust_analytics("entity-1")
        assert "reliability" in result["dimension_trends"]
        assert result["dimension_trends"]["reliability"]["current"] == 0.9


class TestThresholdsConsistency:
    def test_risk_thresholds_keyed_by_value(self):
        tm = TrustManager()
        for category in RiskCategory:
            assert category.value in tm.risk_thresholds
            assert tm.risk_thresholds[category.value] > 0.0

    def test_dimension_weights_keyed_by_enum(self):
        tm = TrustManager()
        for dim in TrustDimension:
            assert dim in tm.dimension_weights
