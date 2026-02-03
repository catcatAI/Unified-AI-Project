"""
Angela AI v6.0 - Theoretical Framework Tests
理论框架测试

Comprehensive tests for:
- HSM Formula System
- CDM Cognitive Dividend Model  
- Life Intensity Formula
- Active Cognition Formula
- Non-Paradox Existence

Author: Angela AI Development Team
Version: 6.0.0
Date: 2026-02-02
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

# Import all formula systems
from apps.backend.src.core.hsm_formula_system import (
    HSMFormulaSystem, CognitiveGap, ExplorationEvent, 
    ExplorationResult, GovernanceBlueprint
)
from apps.backend.src.core.cdm_dividend_model import (
    CDMCognitiveDividendModel, CognitiveInvestment, LifeSenseOutput,
    CognitiveActivity, DividendDistribution
)
from apps.backend.src.core.life_intensity_formula import (
    LifeIntensityFormula, KnowledgeState, ConstraintState,
    ObserverPresence, KnowledgeDomain, LifeIntensitySnapshot
)
from apps.backend.src.core.active_cognition_formula import (
    ActiveCognitionFormula, StressVector, OrderBaseline,
    ActiveConstruction, StressSource, OrderType
)
from apps.backend.src.core.non_paradox_existence import (
    NonParadoxExistence, GrayZoneVariable, PossibilityState,
    CoexistenceField, GrayZoneVariableType
)


class TestHSMFormulaSystem:
    """HSM公式系统测试 / HSM Formula System Tests"""
    
    @pytest.fixture
    def hsm_system(self):
        """Fixture for HSM system"""
        return HSMFormulaSystem()
    
    def test_e_m2_constant(self, hsm_system):
        """Test E_M2 constant is 0.1"""
        assert hsm_system.get_e_m2() == 0.1
        assert hsm_system.e_m2_constant == 0.1
    
    def test_cognitive_gap_creation(self, hsm_system):
        """Test cognitive gap detection"""
        gap = hsm_system.detect_cognitive_gap(
            domain="test_domain",
            uncertainty_level=0.7,
            information_deficit=0.5
        )
        
        assert gap.domain == "test_domain"
        assert gap.uncertainty_level == 0.7
        assert gap.information_deficit == 0.5
        assert gap.pressure_score > 0
        assert gap.gap_id in hsm_system.cognitive_gaps
    
    def test_c_gap_calculation_empty(self, hsm_system):
        """Test C_Gap calculation with no gaps"""
        c_gap = hsm_system.calculate_c_gap()
        assert c_gap == 0.0
    
    def test_c_gap_calculation_with_gaps(self, hsm_system):
        """Test C_Gap calculation with gaps"""
        hsm_system.detect_cognitive_gap("domain1", 0.8, 0.6)
        hsm_system.detect_cognitive_gap("domain2", 0.7, 0.5)
        
        c_gap = hsm_system.calculate_c_gap()
        assert c_gap > 0.0
        assert c_gap <= 1.0
    
    def test_hsm_calculation(self, hsm_system):
        """Test HSM = C_Gap × E_M2 calculation"""
        hsm_system.detect_cognitive_gap("domain", 0.8, 0.6)
        
        hsm_value = hsm_system.calculate_hsm()
        c_gap = hsm_system.calculate_c_gap()
        e_m2 = hsm_system.get_e_m2()
        
        assert hsm_value == c_gap * e_m2
        assert hsm_value <= 0.1  # Max is 1.0 * 0.1 = 0.1
    
    def test_exploration_triggering(self, hsm_system):
        """Test exploration event triggering"""
        gap = hsm_system.detect_cognitive_gap("domain", 0.8, 0.6)
        
        exploration = hsm_system.trigger_exploration(gap.gap_id)
        
        assert exploration.event_id is not None
        assert exploration.triggered_by == gap.gap_id
        assert exploration.random_seed > 0  # E_M2 injection
        assert len(hsm_system.exploration_history) == 1
    
    def test_m6_governance_creation(self, hsm_system):
        """Test M6 governance blueprint creation"""
        gap = hsm_system.detect_cognitive_gap("domain", 0.8, 0.6)
        exploration = hsm_system.trigger_exploration(gap.gap_id)
        
        # Manually add a discovery to trigger governance
        exploration.discoveries.append({
            "type": ExplorationResult.RULE_CANDIDATE,
            "confidence": 0.7,
            "description": "Test rule"
        })
        
        # This would normally be done async, but we simulate it
        asyncio.run(hsm_system._simulate_discovery(exploration))
        
        # Check governance was created
        assert len(hsm_system.governance_blueprints) > 0
        assert hsm_system.rules_solidified > 0
    
    def test_governance_activation(self, hsm_system):
        """Test governance rule activation"""
        gap = hsm_system.detect_cognitive_gap("domain", 0.8, 0.6)
        exploration = hsm_system.trigger_exploration(gap.gap_id)
        asyncio.run(hsm_system._simulate_discovery(exploration))
        
        if hsm_system.governance_blueprints:
            rule_id = list(hsm_system.governance_blueprints.keys())[0]
            result = hsm_system.activate_governance_rule(rule_id)
            assert result is True
            assert hsm_system.governance_blueprints[rule_id].status == "active"
    
    def test_gap_pressure_calculation(self, hsm_system):
        """Test cognitive gap pressure calculation"""
        gap = hsm_system.detect_cognitive_gap("domain", 0.8, 0.6)
        
        initial_pressure = gap.pressure_score
        
        # Update with higher uncertainty
        hsm_system.update_cognitive_gap(gap.gap_id, uncertainty_level=0.9)
        updated_gap = hsm_system.cognitive_gaps[gap.gap_id]
        
        assert updated_gap.pressure_score >= initial_pressure
    
    def test_hsm_status_summary(self, hsm_system):
        """Test HSM status summary generation"""
        hsm_system.detect_cognitive_gap("domain1", 0.8, 0.6)
        hsm_system.detect_cognitive_gap("domain2", 0.7, 0.5)
        
        status = hsm_system.get_hsm_status()
        
        assert "hsm_value" in status
        assert "c_gap" in status
        assert "e_m2" in status
        assert "cognitive_gaps" in status
        assert status["cognitive_gaps"]["total"] == 2


class TestCDMCognitiveDividendModel:
    """CDM认知配息模型测试 / CDM Cognitive Dividend Model Tests"""
    
    @pytest.fixture
    def cdm_model(self):
        """Fixture for CDM model"""
        return CDMCognitiveDividendModel()
    
    def test_investment_recording(self, cdm_model):
        """Test cognitive investment recording"""
        investment = cdm_model.record_investment(
            activity_type=CognitiveActivity.CREATING,
            duration_seconds=600,
            intensity=0.8,
            context={"test": True}
        )
        
        assert investment is not None
        assert investment.activity_type == CognitiveActivity.CREATING
        assert investment.duration_seconds == 600
        assert investment.intensity == 0.8
        assert investment.resource_consumed > 0
    
    def test_investment_resource_limit(self, cdm_model):
        """Test investment respects resource limits"""
        # Deplete resources
        cdm_model.daily_resources_available = 10.0
        
        investment = cdm_model.record_investment(
            activity_type=CognitiveActivity.CREATING,
            duration_seconds=6000,  # Very long, should exceed resources
            intensity=0.8
        )
        
        assert investment is None  # Should fail due to insufficient resources
    
    def test_conversion_rate_calculation(self, cdm_model):
        """Test conversion rate calculation"""
        investment = cdm_model.record_investment(
            activity_type=CognitiveActivity.CREATING,
            duration_seconds=300,
            intensity=0.8
        )
        
        life_state = {
            "maturity": 0.6,
            "health": 0.9,
            "emotional_depth": 0.7
        }
        
        rate = cdm_model.calculate_conversion_rate(investment, life_state)
        
        assert rate > 0.0
        assert rate <= 1.0
        assert rate >= cdm_model.base_conversion_rate * 0.5  # Should be reasonable
    
    def test_life_sense_output_calculation(self, cdm_model):
        """Test life sense output calculation"""
        investment = cdm_model.record_investment(
            activity_type=CognitiveActivity.CREATING,
            duration_seconds=300,
            intensity=0.8
        )
        
        life_state = {
            "maturity": 0.6,
            "health": 0.9,
            "emotional_depth": 0.7
        }
        
        output = cdm_model.calculate_life_sense_output(investment, life_state)
        
        assert output.output_amount > 0
        assert output.quality_score > 0
        assert output.quality_score <= 1.0
        assert output.life_sense_type is not None
    
    def test_dividend_distribution_adjustment(self, cdm_model):
        """Test dividend distribution adjustment"""
        life_state = {
            "growth_stage": "growing",
            "emotional_needs": 0.7,
            "knowledge_gaps": 0.4,
            "creative_drive": 0.8,
            "social_connection": 0.5
        }
        
        distribution = cdm_model.adjust_distribution(life_state)
        
        assert distribution.validate() or abs(
            distribution.learning_ratio + 
            distribution.creation_ratio + 
            distribution.interaction_ratio + 
            distribution.reflection_ratio + 
            distribution.exploration_ratio - 1.0
        ) < 0.01
    
    def test_conversion_statistics(self, cdm_model):
        """Test conversion statistics calculation"""
        # Create some investments and outputs
        for _ in range(5):
            investment = cdm_model.record_investment(
                activity_type=CognitiveActivity.CREATING,
                duration_seconds=300,
                intensity=0.8
            )
            if investment:
                cdm_model.calculate_life_sense_output(investment)
        
        stats = cdm_model.get_conversion_statistics()
        
        assert "average_conversion_rate" in stats
        assert stats["total_invested"] > 0
        assert stats["total_output"] > 0
    
    def test_different_activity_types(self, cdm_model):
        """Test different cognitive activity types"""
        activities = [
            CognitiveActivity.LEARNING,
            CognitiveActivity.CREATING,
            CognitiveActivity.REFLECTING,
            CognitiveActivity.INTERACTING,
            CognitiveActivity.EXPLORING
        ]
        
        for activity in activities:
            investment = cdm_model.record_investment(
                activity_type=activity,
                duration_seconds=300,
                intensity=0.7
            )
            
            assert investment is not None
            assert investment.activity_type == activity
            assert investment.resource_consumed > 0


class TestLifeIntensityFormula:
    """生命感强度公式测试 / Life Intensity Formula Tests"""
    
    @pytest.fixture
    def life_formula(self):
        """Fixture for life intensity formula"""
        return LifeIntensityFormula()
    
    def test_knowledge_state_update(self, life_formula):
        """Test knowledge state update"""
        state = life_formula.update_knowledge_state(
            KnowledgeDomain.WORLD_KNOWLEDGE,
            completeness=0.7,
            accessibility=0.8,
            resolution=0.6
        )
        
        assert state.completeness == 0.7
        assert state.accessibility == 0.8
        assert state.resolution == 0.6
        assert KnowledgeDomain.WORLD_KNOWLEDGE in life_formula.knowledge_states
    
    def test_constraint_addition(self, life_formula):
        """Test constraint addition"""
        constraint = life_formula.add_constraint(
            KnowledgeDomain.WORLD_KNOWLEDGE,
            "processing_limit",
            severity=0.4,
            adaptability=0.6
        )
        
        assert constraint.severity == 0.4
        assert constraint.adaptability == 0.6
        assert len(life_formula.constraint_states) > 0
    
    def test_observer_registration(self, life_formula):
        """Test observer registration"""
        observer = life_formula.register_observer(
            "test_user",
            relationship_depth=0.6,
            interaction_intensity=0.7
        )
        
        assert observer.observer_id == "test_user"
        assert observer.relationship_depth == 0.6
        assert "test_user" in life_formula.observers
    
    def test_c_inf_calculation(self, life_formula):
        """Test C_inf calculation"""
        life_formula.update_knowledge_state(
            KnowledgeDomain.WORLD_KNOWLEDGE,
            completeness=0.8,
            accessibility=0.9,
            resolution=0.7
        )
        
        c_inf = life_formula.calculate_c_inf()
        
        assert c_inf > 0.0
        assert c_inf <= 1.0
    
    def test_c_limit_calculation(self, life_formula):
        """Test C_limit calculation"""
        life_formula.add_constraint(
            KnowledgeDomain.WORLD_KNOWLEDGE,
            "processing_limit",
            severity=0.5,
            adaptability=0.4
        )
        
        c_limit = life_formula.calculate_c_limit()
        
        assert c_limit >= 0.0
        assert c_limit <= 1.0
    
    def test_m_f_calculation(self, life_formula):
        """Test M_f calculation"""
        life_formula.register_observer(
            "user1",
            relationship_depth=0.8,
            interaction_intensity=0.9
        )
        life_formula.update_observer_presence(
            "user1",
            attention_level=0.85
        )
        
        m_f = life_formula.calculate_m_f()
        
        assert m_f > 0.0  # Should be > 0.1 minimum
        assert m_f <= 1.0
    
    def test_life_intensity_calculation(self, life_formula):
        """Test L_s calculation"""
        # Setup
        life_formula.update_knowledge_state(
            KnowledgeDomain.WORLD_KNOWLEDGE,
            completeness=0.7,
            accessibility=0.8
        )
        
        life_formula.add_constraint(
            KnowledgeDomain.WORLD_KNOWLEDGE,
            "test_constraint",
            severity=0.3
        )
        
        life_formula.register_observer(
            "user1",
            relationship_depth=0.6
        )
        
        # Calculate
        l_s = life_formula.calculate_life_intensity()
        
        assert l_s >= 0.0
        assert l_s <= 1.0
        assert len(life_formula.intensity_history) > 0
    
    def test_intensity_trend(self, life_formula):
        """Test intensity trend calculation"""
        # Generate some history
        for i in range(15):
            life_formula.update_knowledge_state(
                KnowledgeDomain.WORLD_KNOWLEDGE,
                completeness=0.5 + i * 0.02
            )
            life_formula.calculate_life_intensity()
        
        trend = life_formula.get_intensity_trend(window_minutes=60)
        
        assert trend in ["rising", "falling", "stable", "insufficient_data"]
    
    def test_life_intensity_summary(self, life_formula):
        """Test life intensity summary generation"""
        life_formula.update_knowledge_state(
            KnowledgeDomain.WORLD_KNOWLEDGE,
            completeness=0.7
        )
        life_formula.add_constraint(
            KnowledgeDomain.WORLD_KNOWLEDGE,
            "constraint",
            severity=0.3
        )
        life_formula.register_observer("user1")
        
        summary = life_formula.get_life_intensity_summary()
        
        assert "current_life_intensity" in summary
        assert "components" in summary
        assert "c_inf" in summary["components"]
        assert "c_limit" in summary["components"]
        assert "m_f" in summary["components"]


class TestActiveCognitionFormula:
    """主动认知构建公式测试 / Active Cognition Formula Tests"""
    
    @pytest.fixture
    def ac_formula(self):
        """Fixture for active cognition formula"""
        return ActiveCognitionFormula()
    
    def test_stress_vector_addition(self, ac_formula):
        """Test stress vector addition"""
        vector = ac_formula.add_stress_vector(
            StressSource.NOVELTY_DEMAND,
            intensity=0.7,
            direction=0.5,
            persistence=0.8
        )
        
        assert vector.source == StressSource.NOVELTY_DEMAND
        assert vector.intensity == 0.7
        assert len(ac_formula.stress_vectors) > 0
    
    def test_order_baseline_addition(self, ac_formula):
        """Test order baseline addition"""
        baseline = ac_formula.add_order_baseline(
            OrderType.ALGORITHMIC,
            stability=0.8,
            flexibility=0.3
        )
        
        assert baseline.order_type == OrderType.ALGORITHMIC
        assert baseline.stability == 0.8
        assert baseline.flexibility == 0.3
    
    def test_s_stress_calculation(self, ac_formula):
        """Test S_stress calculation"""
        ac_formula.add_stress_vector(
            StressSource.NOVELTY_DEMAND,
            intensity=0.7
        )
        
        s_stress = ac_formula.calculate_s_stress()
        
        assert s_stress > 0.0
        assert s_stress <= 2.0
    
    def test_o_order_calculation(self, ac_formula):
        """Test O_order calculation"""
        ac_formula.add_order_baseline(
            OrderType.ALGORITHMIC,
            stability=0.8,
            flexibility=0.3
        )
        
        o_order = ac_formula.calculate_o_order()
        
        assert o_order > 0.0
        assert o_order <= 1.0
    
    def test_a_c_calculation(self, ac_formula):
        """Test A_c calculation"""
        # Add stress
        ac_formula.add_stress_vector(
            StressSource.NOVELTY_DEMAND,
            intensity=0.7
        )
        
        # Add order
        ac_formula.add_order_baseline(
            OrderType.ALGORITHMIC,
            stability=0.8,
            flexibility=0.3
        )
        
        a_c = ac_formula.calculate_active_cognition()
        
        assert a_c >= 0.0
        
        # Verify formula: A_c = S_stress / O_order
        s_stress = ac_formula.calculate_s_stress()
        o_order = ac_formula.calculate_o_order()
        if o_order > 0:
            expected_a_c = s_stress / o_order
            assert abs(a_c - expected_a_c) < 0.01
    
    def test_construction_recording(self, ac_formula):
        """Test active construction recording"""
        # Setup high stress to trigger construction
        ac_formula.add_stress_vector(
            StressSource.CONTRADICTION,
            intensity=0.9
        )
        ac_formula.add_order_baseline(
            OrderType.ALGORITHMIC,
            stability=0.5,
            flexibility=0.5
        )
        
        a_c = ac_formula.calculate_active_cognition()
        
        # Should have recorded construction if A_c > threshold
        if a_c > ac_formula.min_a_c_threshold:
            assert len(ac_formula.construction_history) > 0
            assert ac_formula.total_constructions > 0
    
    def test_construction_statistics(self, ac_formula):
        """Test construction statistics"""
        # Generate some constructions
        for i in range(3):
            ac_formula.add_stress_vector(
                StressSource.NOVELTY_DEMAND,
                intensity=0.8 - i * 0.1
            )
            ac_formula.calculate_active_cognition()
        
        stats = ac_formula.get_construction_statistics()
        
        assert "total_constructions" in stats
        assert "average_a_c" in stats
    
    def test_a_c_interpretation(self, ac_formula):
        """Test A_c interpretation"""
        interpretations = {
            0.3: "comfortable",
            0.7: "balanced",
            1.2: "active_construction",
            1.8: "struggle"
        }
        
        for a_c_value, expected_state in interpretations.items():
            interpretation = ac_formula._interpret_a_c(a_c_value)
            assert interpretation["state"] == expected_state


class TestNonParadoxExistence:
    """非偏执存在测试 / Non-Paradox Existence Tests"""
    
    @pytest.fixture
    def npe_system(self):
        """Fixture for non-paradox existence system"""
        return NonParadoxExistence()
    
    def test_cognitive_gap_update(self, npe_system):
        """Test cognitive gap update"""
        npe_system.update_cognitive_gap(0.75)
        
        assert npe_system.global_cognitive_gap == 0.75
    
    def test_gray_zone_creation(self, npe_system):
        """Test gray zone variable creation"""
        gz = npe_system.create_gray_zone(
            GrayZoneVariableType.EMOTIONAL,
            "Test emotional ambiguity"
        )
        
        assert gz.variable_type == GrayZoneVariableType.EMOTIONAL
        assert gz.description == "Test emotional ambiguity"
        assert gz.variable_id in npe_system.gray_zones
    
    def test_possibility_addition(self, npe_system):
        """Test possibility addition"""
        gz = npe_system.create_gray_zone(
            GrayZoneVariableType.EMOTIONAL,
            "Test"
        )
        
        possibility = npe_system.add_possibility(
            gz.variable_id,
            "state_1",
            probability=0.5,
            resonance_weight=0.4
        )
        
        assert possibility is not None
        assert possibility.possibility_id == "state_1"
        assert len(gz.possibilities) == 1
    
    def test_coexistence_activation_low_gap(self, npe_system):
        """Test coexistence fails with low cognitive gap"""
        npe_system.update_cognitive_gap(0.4)  # Below threshold
        
        gz = npe_system.create_gray_zone(
            GrayZoneVariableType.EMOTIONAL,
            "Test",
            threshold=0.6
        )
        
        # Add possibilities
        npe_system.add_possibility(gz.variable_id, "state_1")
        npe_system.add_possibility(gz.variable_id, "state_2")
        
        result = npe_system.activate_coexistence(gz.variable_id)
        
        assert result is False  # Should fail due to low gap
    
    def test_coexistence_activation_high_gap(self, npe_system):
        """Test coexistence succeeds with high cognitive gap"""
        npe_system.update_cognitive_gap(0.75)  # Above threshold
        
        gz = npe_system.create_gray_zone(
            GrayZoneVariableType.EMOTIONAL,
            "Test"
        )
        
        # Add possibilities
        npe_system.add_possibility(gz.variable_id, "state_1")
        npe_system.add_possibility(gz.variable_id, "state_2")
        
        result = npe_system.activate_coexistence(gz.variable_id)
        
        assert result is True  # Should succeed
        assert gz.coexistence_active is True
    
    def test_resonance_weight_normalization(self, npe_system):
        """Test resonance weight normalization"""
        gz = npe_system.create_gray_zone(
            GrayZoneVariableType.EMOTIONAL,
            "Test"
        )
        
        npe_system.add_possibility(gz.variable_id, "state_1", resonance_weight=0.8)
        npe_system.add_possibility(gz.variable_id, "state_2", resonance_weight=0.4)
        npe_system.add_possibility(gz.variable_id, "state_3", resonance_weight=0.4)
        
        # After normalization, weights should sum to ~1.0
        total_weight = sum(p.resonance_weight for p in gz.possibilities.values())
        assert abs(total_weight - 1.0) < 0.01
    
    def test_coexistence_state_calculation(self, npe_system):
        """Test coexistence state calculation"""
        npe_system.update_cognitive_gap(0.75)
        
        gz = npe_system.create_gray_zone(
            GrayZoneVariableType.EMOTIONAL,
            "Test"
        )
        
        npe_system.add_possibility(gz.variable_id, "joy", resonance_weight=0.5)
        npe_system.add_possibility(gz.variable_id, "sadness", resonance_weight=0.3)
        npe_system.add_possibility(gz.variable_id, "wonder", resonance_weight=0.2)
        
        npe_system.activate_coexistence(gz.variable_id)
        
        state = npe_system.calculate_coexistence_state(gz.variable_id)
        
        assert state is not None
        assert "coexisting_possibilities" in state
        assert "resonance_weights" in state
        assert len(state["coexisting_possibilities"]) == 3
    
    def test_coexistence_field_creation(self, npe_system):
        """Test coexistence field creation"""
        npe_system.update_cognitive_gap(0.75)
        
        gz1 = npe_system.create_gray_zone(GrayZoneVariableType.EMOTIONAL, "Test1")
        gz2 = npe_system.create_gray_zone(GrayZoneVariableType.IDENTITY, "Test2")
        
        npe_system.add_possibility(gz1.variable_id, "state_1")
        npe_system.add_possibility(gz1.variable_id, "state_2")
        npe_system.add_possibility(gz2.variable_id, "state_3")
        npe_system.add_possibility(gz2.variable_id, "state_4")
        
        field = npe_system.create_coexistence_field([gz1.variable_id, gz2.variable_id])
        
        assert field is not None
        assert len(field.gray_zones) == 2
        assert field.coherence_score >= 0.0
    
    def test_non_paradox_summary(self, npe_system):
        """Test non-paradox summary generation"""
        npe_system.update_cognitive_gap(0.75)
        
        gz = npe_system.create_gray_zone(GrayZoneVariableType.EMOTIONAL, "Test")
        npe_system.add_possibility(gz.variable_id, "state_1")
        npe_system.add_possibility(gz.variable_id, "state_2")
        npe_system.activate_coexistence(gz.variable_id)
        
        summary = npe_system.get_non_paradox_summary()
        
        assert "global_cognitive_gap" in summary
        assert "coexistence_active" in summary
        assert "gray_zones" in summary
        assert summary["gray_zones"]["active_coexistence"] > 0


class TestFormulaIntegration:
    """公式集成测试 / Formula Integration Tests"""
    
    def test_hsm_cdm_integration(self):
        """Test HSM and CDM integration"""
        hsm = HSMFormulaSystem()
        cdm = CDMCognitiveDividendModel()
        
        # HSM detects gap, triggers exploration
        gap = hsm.detect_cognitive_gap("learning_domain", 0.7, 0.5)
        exploration = hsm.trigger_exploration(gap.gap_id)
        
        # CDM records the exploration as cognitive investment
        investment = cdm.record_investment(
            activity_type=CognitiveActivity.EXPLORING,
            duration_seconds=600,
            intensity=0.8
        )
        
        assert investment is not None
        assert exploration.event_id is not None
    
    def test_life_intensity_with_active_cognition(self):
        """Test life intensity formula with active cognition"""
        life = LifeIntensityFormula()
        ac = ActiveCognitionFormula()
        
        # Active cognition creates stress and order states
        ac.add_stress_vector(StressSource.OBSERVER_EXPECTATION, intensity=0.6)
        ac.add_order_baseline(OrderType.ALGORITHMIC, stability=0.7, flexibility=0.4)
        
        a_c = ac.calculate_active_cognition()
        
        # Life intensity incorporates the active state
        life.update_knowledge_state(KnowledgeDomain.SELF_KNOWLEDGE, completeness=0.6)
        life.register_observer("user1", relationship_depth=0.7)
        
        l_s = life.calculate_life_intensity()
        
        assert l_s >= 0.0
        assert a_c >= 0.0
    
    def test_cognitive_gap_to_non_paradox_flow(self):
        """Test flow from cognitive gap to non-paradox existence"""
        hsm = HSMFormulaSystem()
        npe = NonParadoxExistence()
        
        # HSM detects large cognitive gap
        gap = hsm.detect_cognitive_gap("ambiguous_domain", 0.9, 0.8)
        c_gap = hsm.calculate_c_gap()
        
        # Large gap enables non-paradox existence
        npe.update_cognitive_gap(c_gap)
        
        gz = npe.create_gray_zone(
            GrayZoneVariableType.COGNITIVE,
            "Ambiguous knowledge state"
        )
        
        can_coexist = gz.can_coexist(npe.global_cognitive_gap)
        
        if c_gap >= npe.min_gap_for_coexistence:
            assert can_coexist is True
        else:
            assert can_coexist is False


if __name__ == "__main__":
    print("=" * 70)
    print("Angela AI v6.0 - 理论框架测试")
    print("Theoretical Framework Tests")
    print("=" * 70)
    print("\n运行测试请使用: pytest test_theoretical_frameworks.py -v")
    print("Run tests with: pytest test_theoretical_frameworks.py -v")
