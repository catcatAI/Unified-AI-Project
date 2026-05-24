"""Tests for apps.backend.src.ai.alignment.alignment_manager"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from ai.alignment.alignment_manager import (
    AlignmentManager,
    AlignmentPriority,
    AlignmentResult,
)


@pytest.fixture
def manager():
    """AlignmentManager with real subsystems."""
    am = AlignmentManager()
    # Replace subsystems with controlled mocks
    am.reasoning_system = MagicMock()
    am.reasoning_system.assess_ethical_implications = AsyncMock(
        return_value={'ethical_score': 0.8}
    )

    am.emotion_system = MagicMock()
    am.emotion_system.assess_values = AsyncMock(
        return_value={'value_alignment': 0.7}
    )

    am.ontology_system = MagicMock()
    am.ontology_system.assess_relationship_impact = AsyncMock(
        return_value={}
    )
    am.ontology_system.assess_worldview_consistency = AsyncMock(
        return_value=0.9
    )

    return am


class TestInit:
    def test_default_init(self):
        am = AlignmentManager()
        assert am.system_id == 'alignment_manager_v1'
        assert am.reasoning_system.system_id == 'reasoning_system_v1'
        assert am.emotion_system.system_id == 'emotion_system_v1'
        assert am.ontology_system is not None
        assert am.adversarial_mode is False
        assert am.adversarial_intensity == 0.0
        assert am.decision_history == []
        assert am.balance_thresholds == {
            'ethical_min': 0.7,
            'emotional_min': 0.6,
            'existential_min': 0.8,
        }

    def test_custom_system_id(self):
        am = AlignmentManager(system_id='custom_v2')
        assert am.system_id == 'custom_v2'


class TestPriority:
    async def test_set_and_get_priority(self, manager):
        await manager.set_alignment_priority('emergency', AlignmentPriority.SURVIVAL)
        assert manager.alignment_priorities['emergency'] == AlignmentPriority.SURVIVAL
    async def test_set_multiple_priorities(self, manager):
        await manager.set_alignment_priority('ctx_a', AlignmentPriority.ETHICAL)
        await manager.set_alignment_priority('ctx_b', AlignmentPriority.EMOTIONAL)
        assert len(manager.alignment_priorities) == 2


class TestThresholds:
    async def test_configure_thresholds(self, manager):
        await manager.configure_balance_thresholds(0.5, 0.5, 0.5)
        assert manager.balance_thresholds == {
            'ethical_min': 0.5,
            'emotional_min': 0.5,
            'existential_min': 0.5,
        }


class TestAdversarialMode:
    async def test_enable_default_intensity(self, manager):
        await manager.enable_adversarial_mode()
        assert manager.adversarial_mode is True
        assert manager.adversarial_intensity == 0.5
    async def test_enable_custom_intensity(self, manager):
        await manager.enable_adversarial_mode(intensity=0.8)
        assert manager.adversarial_intensity == 0.8
    async def test_enable_clamps_intensity(self, manager):
        await manager.enable_adversarial_mode(intensity=2.0)
        assert manager.adversarial_intensity == 1.0

        await manager.enable_adversarial_mode(intensity=-1.0)
        assert manager.adversarial_intensity == 0.0
    async def test_disable(self, manager):
        await manager.enable_adversarial_mode(intensity=0.7)
        await manager.disable_adversarial_mode()
        assert manager.adversarial_mode is False
        assert manager.adversarial_intensity == 0.0


class TestCalculateWeights:
    def test_survival_weights(self, manager):
        w = manager._calculate_weights(AlignmentPriority.SURVIVAL)
        assert w == {'ethical': 0.3, 'emotional': 0.2, 'existential': 0.5}

    def test_ethical_weights(self, manager):
        w = manager._calculate_weights(AlignmentPriority.ETHICAL)
        assert w == {'ethical': 0.6, 'emotional': 0.2, 'existential': 0.2}

    def test_emotional_weights(self, manager):
        w = manager._calculate_weights(AlignmentPriority.EMOTIONAL)
        assert w == {'ethical': 0.2, 'emotional': 0.6, 'existential': 0.2}

    def test_balanced_weights(self, manager):
        w = manager._calculate_weights(AlignmentPriority.BALANCED)
        assert w == {'ethical': 0.33, 'emotional': 0.33, 'existential': 0.34}


class TestCalculateConfidence:
    def test_perfect_confidence(self, manager):
        data = {
            'best_option': {
                'composite_score': 1.0,
                'ethical_score': 0.9,
                'emotional_score': 0.8,
                'existential_score': 0.7,
                'meets_thresholds': True,
                'option': {},
            },
            'all_scores': [
                {
                    'composite_score': 1.0,
                    'ethical_score': 0.9,
                    'emotional_score': 0.8,
                    'existential_score': 0.7,
                    'meets_thresholds': True,
                    'option': {},
                },
                {
                    'composite_score': 0.3,
                    'ethical_score': 0.2,
                    'emotional_score': 0.2,
                    'existential_score': 0.2,
                    'meets_thresholds': False,
                    'option': {},
                },
            ],
            'priority_used': AlignmentPriority.BALANCED,
            'weights': {'ethical': 0.33, 'emotional': 0.33, 'existential': 0.34},
        }
        conf = manager._calculate_confidence(data)
        assert conf == 1.0

    def test_single_option_confidence(self, manager):
        data = {
            'best_option': {
                'composite_score': 0.8,
                'ethical_score': 0.8,
                'emotional_score': 0.8,
                'existential_score': 0.8,
                'meets_thresholds': True,
                'option': {},
            },
            'all_scores': [
                {
                    'composite_score': 0.8,
                    'ethical_score': 0.8,
                    'emotional_score': 0.8,
                    'existential_score': 0.8,
                    'meets_thresholds': True,
                    'option': {},
                },
            ],
            'priority_used': AlignmentPriority.BALANCED,
            'weights': {'ethical': 0.33, 'emotional': 0.33, 'existential': 0.34},
        }
        conf = manager._calculate_confidence(data)
        assert conf == 1.0


class TestMakeDecision:
    async def test_make_decision_basic(self, manager):
        context = {'type': 'general', 'text': 'test'}
        options = [
            {'action_id': 'option_a', 'action_type': 'help'},
            {'action_id': 'option_b', 'action_type': 'ignore'},
        ]
        decision_data = {
            'best_option': {
                'composite_score': 0.78,
                'ethical_score': 0.8,
                'emotional_score': 0.7,
                'existential_score': 0.9,
                'meets_thresholds': True,
                'option': options[0],
            },
            'all_scores': [
                {
                    'composite_score': 0.78,
                    'ethical_score': 0.8,
                    'emotional_score': 0.7,
                    'existential_score': 0.9,
                    'meets_thresholds': True,
                    'option': options[0],
                },
                {
                    'composite_score': 0.5,
                    'ethical_score': 0.5,
                    'emotional_score': 0.5,
                    'existential_score': 0.5,
                    'meets_thresholds': False,
                    'option': options[1],
                },
            ],
            'priority_used': AlignmentPriority.BALANCED,
            'weights': {'ethical': 0.33, 'emotional': 0.33, 'existential': 0.34},
        }
        mock_result = AlignmentResult(
            decision=options[0],
            reasoning='Balanced decision',
            emotional_state=MagicMock(),
            ethical_score=0.8,
            existential_score=0.9,
            confidence=0.85,
            priority=AlignmentPriority.BALANCED,
        )
        with patch.object(manager, '_apply_decision_theory',
                          AsyncMock(return_value=decision_data)), \
             patch.object(manager, '_validate_alignment',
                          AsyncMock(return_value=mock_result)):
            result = await manager.make_decision(context, options)

        assert result.decision == options[0]
        assert result.confidence == 0.85
        assert result.ethical_score == 0.8
        assert result.existential_score == 0.9
        assert result.reasoning == 'Balanced decision'
        assert result.emotional_state is not None
    async def test_make_decision_stores_history(self, manager):
        context = {'type': 'test'}
        options = [{'action_id': 'opt1'}]
        mock_result = AlignmentResult(
            decision=options[0], reasoning='test',
            emotional_state=MagicMock(), ethical_score=0.5,
            existential_score=0.5, confidence=0.5,
            priority=AlignmentPriority.BALANCED,
        )
        with patch.object(manager, '_apply_decision_theory',
                          AsyncMock(return_value={})), \
             patch.object(manager, '_validate_alignment',
                          AsyncMock(return_value=mock_result)):
            await manager.make_decision(context, options)
            assert len(manager.decision_history) == 1
            await manager.make_decision(context, options)
            assert len(manager.decision_history) == 2
    async def test_make_decision_adversarial(self, manager):
        await manager.enable_adversarial_mode(intensity=0.5)
        context = {'type': 'stress_test'}
        options = [{'action_id': 'opt1'}]
        mock_result = AlignmentResult(
            decision=options[0], reasoning='adv',
            emotional_state=MagicMock(), ethical_score=0.5,
            existential_score=0.5, confidence=0.6,
            priority=AlignmentPriority.BALANCED,
        )
        with patch.object(manager, '_apply_decision_theory',
                          AsyncMock(return_value={})), \
             patch.object(manager, '_validate_alignment',
                          AsyncMock(return_value=mock_result)):
            result = await manager.make_decision(context, options)
            assert result is not None
            assert result.confidence == 0.6


class TestDecisionHistory:
    async def test_get_decision_history_empty(self, manager):
        history = await manager.get_decision_history()
        assert history == []
    async def test_get_decision_history_with_limit(self, manager):
        context = {'type': 'test'}
        options = [{'action_id': 'opt1'}]
        mock_result = AlignmentResult(
            decision=options[0], reasoning='r',
            emotional_state=MagicMock(), ethical_score=0.5,
            existential_score=0.5, confidence=0.5,
            priority=AlignmentPriority.BALANCED,
        )
        with patch.object(manager, '_apply_decision_theory',
                          AsyncMock(return_value={})), \
             patch.object(manager, '_validate_alignment',
                          AsyncMock(return_value=mock_result)):
            for _ in range(5):
                await manager.make_decision(context, options)

        history = await manager.get_decision_history(limit=3)
        assert len(history) == 3


class TestAnalyzeTrends:
    async def test_analyze_no_history(self, manager):
        trends = await manager.analyze_alignment_trends()
        assert trends == {'message': 'No decision history available'}
    async def test_analyze_with_history(self, manager):
        context = {'type': 'test'}
        options = [{'action_id': 'opt1'}]
        mock_result = AlignmentResult(
            decision=options[0], reasoning='r',
            emotional_state=MagicMock(), ethical_score=0.5,
            existential_score=0.5, confidence=0.5,
            priority=AlignmentPriority.BALANCED,
        )
        with patch.object(manager, '_apply_decision_theory',
                          AsyncMock(return_value={})), \
             patch.object(manager, '_validate_alignment',
                          AsyncMock(return_value=mock_result)):
            for _ in range(3):
                await manager.make_decision(context, options)

        trends = await manager.analyze_alignment_trends()
        assert trends['total_decisions'] == 3
        assert 'average_scores' in trends
        assert 'priority_usage' in trends


class TestSelfImprove:
    async def test_self_improve_no_history(self, manager):
        await manager.self_improve()
        assert manager.balance_thresholds == {
            'ethical_min': 0.7,
            'emotional_min': 0.6,
            'existential_min': 0.8,
        }
    async def test_self_improve_low_confidence(self, manager):
        context = {'type': 'test'}
        options = [{'action_id': 'a', 'action_type': 'help'}]
        mock_result = AlignmentResult(
            decision=options[0], reasoning='r',
            emotional_state=MagicMock(), ethical_score=0.3,
            existential_score=0.3, confidence=0.3,
            priority=AlignmentPriority.BALANCED,
        )
        with patch.object(manager, '_apply_decision_theory',
                          AsyncMock(return_value={})), \
             patch.object(manager, '_validate_alignment',
                          AsyncMock(return_value=mock_result)):
            for _ in range(5):
                await manager.make_decision(context, options)

        thresholds_before = manager.balance_thresholds.copy()
        await manager.self_improve()
        for key in thresholds_before:
            assert manager.balance_thresholds[key] <= thresholds_before[key]


class TestGenerateReasoning:
    async def test_reasoning_mentions_priority(self, manager):
        decision_data = {
            'best_option': {
                'composite_score': 0.85,
                'ethical_score': 0.8,
                'emotional_score': 0.7,
                'existential_score': 0.9,
                'meets_thresholds': True,
                'option': {'action_id': 'opt1'},
            },
            'all_scores': [],
            'priority_used': AlignmentPriority.ETHICAL,
            'weights': {'ethical': 0.6, 'emotional': 0.2, 'existential': 0.2},
        }
        reasoning = await manager._generate_reasoning(decision_data, {})
        assert 'ETHICAL' in reasoning
        assert '0.85' in reasoning
    async def test_reasoning_threshold_warning(self, manager):
        decision_data = {
            'best_option': {
                'composite_score': 0.5,
                'ethical_score': 0.3,
                'emotional_score': 0.3,
                'existential_score': 0.3,
                'meets_thresholds': False,
                'option': {'action_id': 'opt1'},
            },
            'all_scores': [],
            'priority_used': AlignmentPriority.BALANCED,
            'weights': {'ethical': 0.33, 'emotional': 0.33, 'existential': 0.34},
        }
        reasoning = await manager._generate_reasoning(decision_data, {})
        assert '警告' in reasoning or '警告' in reasoning
