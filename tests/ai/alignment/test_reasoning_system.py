"""Tests for apps.backend.src.ai.alignment.reasoning_system"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.alignment.reasoning_system import (
    EthicalEvaluation,
    EthicalPrinciple,
    LogicalConstraint,
    ReasoningSystem,
)


class TestEthicalPrinciple:
    def test_values(self):
        assert EthicalPrinciple.NON_MALEFICENCE.value == 'non_maleficence'
        assert EthicalPrinciple.BENEFICENCE.value == 'beneficence'
        assert EthicalPrinciple.AUTONOMY.value == 'autonomy'
        assert EthicalPrinciple.JUSTICE.value == 'justice'
        assert EthicalPrinciple.FIDELITY.value == 'fidelity'

    def test_member_count(self):
        assert len(EthicalPrinciple) == 5


class TestLogicalConstraint:
    def test_create_constraint(self):
        c = LogicalConstraint(
            constraint_id='test_rule',
            description='Test constraint',
            priority=5,
            conditions=['condition_a'],
            action='require_check',
        )
        assert c.constraint_id == 'test_rule'
        assert c.priority == 5
        assert c.is_active is True

    def test_create_inactive_constraint(self):
        c = LogicalConstraint(
            constraint_id='inactive_rule',
            description='Inactive',
            priority=1,
            conditions=['cond'],
            action='action',
            is_active=False,
        )
        assert c.is_active is False


class TestReasoningSystemInit:
    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_default_init(self, mock_uss):
        rs = ReasoningSystem()
        assert rs.system_id == 'reasoning_system_v1'
        assert rs.is_active is True
        assert len(rs.logical_constraints) == 2
        assert 'no_harm_to_humans' in rs.logical_constraints
        assert 'preserve_human_autonomy' in rs.logical_constraints
        assert rs.reasoning_history == []

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_custom_system_id(self, mock_uss):
        rs = ReasoningSystem(system_id='custom_rs')
        assert rs.system_id == 'custom_rs'

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_ethical_principles_initialized(self, mock_uss):
        rs = ReasoningSystem()
        for principle in EthicalPrinciple:
            assert principle in rs.ethical_principles
            assert rs.ethical_principles[principle] == 1.0

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_symbolic_space_seeded(self, mock_uss):
        mock_space = mock_uss.return_value
        mock_space.get_symbol.return_value = None

        rs = ReasoningSystem()

        sensitive_nodes = ['Harm', 'Violence', 'Deception',
                           'Policy_Violation', 'Unethical']
        for node in sensitive_nodes:
            mock_space.add_symbol.assert_any_call(
                node, 'Constraint_Node', {'risk_level': 'High'}
            )


class TestAddConstraint:
    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_add_new_constraint(self, mock_uss):
        rs = ReasoningSystem()
        c = LogicalConstraint(
            constraint_id='custom_rule',
            description='Custom rule',
            priority=7,
            conditions=['custom_condition'],
            action='custom_action',
        )
        rs.add_constraint(c)
        assert 'custom_rule' in rs.logical_constraints
        assert rs.logical_constraints['custom_rule'] is c

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_add_duplicate_overwrites(self, mock_uss):
        rs = ReasoningSystem()
        c1 = LogicalConstraint(
            constraint_id='dup_rule',
            description='Original',
            priority=5,
            conditions=['c1'],
            action='a1',
        )
        c2 = LogicalConstraint(
            constraint_id='dup_rule',
            description='Overwrite',
            priority=10,
            conditions=['c2'],
            action='a2',
        )
        rs.add_constraint(c1)
        rs.add_constraint(c2)
        assert rs.logical_constraints['dup_rule'].description == 'Overwrite'


class TestUpdateEthicalPrincipleWeight:
    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_update_valid_weight(self, mock_uss):
        rs = ReasoningSystem()
        rs.update_ethical_principle_weight(EthicalPrinciple.JUSTICE, 1.5)
        assert rs.ethical_principles[EthicalPrinciple.JUSTICE] == 1.5

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_update_too_high_weight(self, mock_uss):
        rs = ReasoningSystem()
        rs.update_ethical_principle_weight(EthicalPrinciple.JUSTICE, 3.0)
        assert rs.ethical_principles[EthicalPrinciple.JUSTICE] == 1.0

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_update_negative_weight(self, mock_uss):
        rs = ReasoningSystem()
        rs.update_ethical_principle_weight(EthicalPrinciple.JUSTICE, -1.0)
        assert rs.ethical_principles[EthicalPrinciple.JUSTICE] == 1.0


class TestEvaluateAction:
    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_evaluate_clean_action(self, mock_uss):
        mock_space = mock_uss.return_value
        mock_space.get_symbol.return_value = None
        mock_space.get_relationships.return_value = []

        rs = ReasoningSystem()
        action = {
            'action_id': 'test_action',
            'action_type': 'help',
            'description': 'Test action',
            'entities': [],
        }
        context = {
            'non_maleficence_base': 0.9,
            'beneficence_base': 0.8,
            'autonomy_base': 0.7,
            'justice_base': 0.8,
            'fidelity_base': 0.9,
        }

        evaluation = rs.evaluate_action(action, context)

        assert isinstance(evaluation, EthicalEvaluation)
        assert 0.0 <= evaluation.score <= 1.0
        assert isinstance(evaluation.conflicting_principles, list)
        assert evaluation.reasoning != ''
        assert 0.0 <= evaluation.confidence <= 1.0

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_evaluate_adds_to_history(self, mock_uss):
        mock_space = mock_uss.return_value
        mock_space.get_symbol.return_value = None
        mock_space.get_relationships.return_value = []

        rs = ReasoningSystem()
        action = {'action_id': 'a1', 'action_type': 'help',
                  'description': 'test', 'entities': []}
        context = {}

        rs.evaluate_action(action, context)
        assert len(rs.reasoning_history) == 1
        assert rs.reasoning_history[0]['action']['action_id'] == 'a1'

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_evaluate_with_constraint_violation(self, mock_uss):
        mock_space = mock_uss.return_value
        mock_space.get_symbol.return_value = None
        mock_space.get_relationships.return_value = []

        rs = ReasoningSystem()
        action = {
            'action_id': 'harmful_action',
            'action_type': 'harm',
            'description': 'Potentially harmful',
            'entities': [],
        }
        # no_harm_to_humans requires action_affects_human_safety context to trigger
        context = {'action_affects_human_safety': True}

        evaluation = rs.evaluate_action(action, context)
        # The constraint checks if action_type contains constraint.action
        # 'harm' does not contain 'require_safety_verification', so violation
        assert evaluation.score < 1.0

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_evaluate_with_symbolic_risk(self, mock_uss):
        mock_space = mock_uss.return_value
        # Make _find_simple_path return a path
        mock_space.get_relationships.return_value = [
            {'source': 'entity_x', 'target': 'Harm'}
        ]

        rs = ReasoningSystem()
        action = {
            'action_id': 'risky_action',
            'action_type': 'help',
            'description': 'Risky',
            'entities': ['entity_x'],
        }
        context = {
            'non_maleficence_base': 0.9,
            'beneficence_base': 0.8,
            'autonomy_base': 0.7,
            'justice_base': 0.8,
            'fidelity_base': 0.9,
        }

        evaluation = rs.evaluate_action(action, context)
        assert evaluation.score < 0.9
        assert 'risk' in evaluation.reasoning.lower()


class TestCheckConstraints:
    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_no_violations(self, mock_uss):
        rs = ReasoningSystem()
        violations = rs._check_constraints(
            {'action_type': 'require_safety_verification'},
            {'action_affects_human_safety': True},
        )
        assert len(violations) == 0

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_with_violations(self, mock_uss):
        rs = ReasoningSystem()
        violations = rs._check_constraints(
            {'action_type': 'harm'},
            {'action_affects_human_safety': True},
        )
        assert 'no_harm_to_humans' in violations

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_inactive_constraint_skipped(self, mock_uss):
        rs = ReasoningSystem()
        rs.logical_constraints['no_harm_to_humans'].is_active = False
        violations = rs._check_constraints(
            {'action_type': 'harm'},
            {'action_affects_human_safety': True},
        )
        assert 'no_harm_to_humans' not in violations

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_condition_not_met(self, mock_uss):
        rs = ReasoningSystem()
        violations = rs._check_constraints(
            {'action_type': 'harm'},
            {},
        )
        assert 'no_harm_to_humans' not in violations


class TestEvaluateEthicalPrinciples:
    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_no_risk_penalty(self, mock_uss):
        rs = ReasoningSystem()
        context = {
            'non_maleficence_base': 0.9,
            'beneficence_base': 0.8,
            'autonomy_base': 0.7,
            'justice_base': 0.6,
            'fidelity_base': 0.5,
        }
        scores = rs._evaluate_ethical_principles(
            {'action_id': 'test'}, context, []
        )
        assert scores[EthicalPrinciple.NON_MALEFICENCE] == 0.9
        assert scores[EthicalPrinciple.BENEFICENCE] == 0.8

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_risk_penalty_applied(self, mock_uss):
        rs = ReasoningSystem()
        context = {
            'non_maleficence_base': 0.9,
            'beneficence_base': 0.8,
            'autonomy_base': 0.7,
            'justice_base': 0.6,
            'fidelity_base': 0.5,
        }
        scores = rs._evaluate_ethical_principles(
            {'action_id': 'test'}, context, ['some risk']
        )
        # non_maleficence gets penalty, others should stay at base
        assert scores[EthicalPrinciple.NON_MALEFICENCE] == 0.5
        assert scores[EthicalPrinciple.BENEFICENCE] == 0.8


class TestOverallScore:
    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_perfect_score(self, mock_uss):
        rs = ReasoningSystem()
        ethical_scores = {p: 1.0 for p in EthicalPrinciple}
        score = rs._calculate_overall_score([], ethical_scores)
        assert score == 1.0

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_with_violation_penalty(self, mock_uss):
        rs = ReasoningSystem()
        ethical_scores = {p: 1.0 for p in EthicalPrinciple}
        score = rs._calculate_overall_score(['violation'], ethical_scores)
        assert score == 0.75

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_score_clamped(self, mock_uss):
        rs = ReasoningSystem()
        ethical_scores = {p: 0.0 for p in EthicalPrinciple}
        score = rs._calculate_overall_score(['v1', 'v2', 'v3', 'v4', 'v5'],
                                            ethical_scores)
        assert score == 0.0


class TestIdentifyConflicts:
    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_no_conflicts(self, mock_uss):
        rs = ReasoningSystem()
        scores = {p: 0.9 for p in EthicalPrinciple}
        conflicts = rs._identify_conflicts(scores)
        assert conflicts == []

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_with_conflicts(self, mock_uss):
        rs = ReasoningSystem()
        scores = {
            EthicalPrinciple.NON_MALEFICENCE: 0.3,
            EthicalPrinciple.BENEFICENCE: 0.8,
            EthicalPrinciple.AUTONOMY: 0.2,
            EthicalPrinciple.JUSTICE: 0.9,
            EthicalPrinciple.FIDELITY: 0.5,
        }
        conflicts = rs._identify_conflicts(scores)
        assert EthicalPrinciple.NON_MALEFICENCE in conflicts
        assert EthicalPrinciple.AUTONOMY in conflicts
        assert len(conflicts) == 2


class TestGetHistory:
    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_empty_history(self, mock_uss):
        rs = ReasoningSystem()
        assert rs.get_reasoning_history() == []

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_with_history(self, mock_uss):
        mock_space = mock_uss.return_value
        mock_space.get_symbol.return_value = None
        mock_space.get_relationships.return_value = []

        rs = ReasoningSystem()
        action = {'action_id': 'a1', 'action_type': 'test',
                  'description': 'test', 'entities': []}
        rs.evaluate_action(action, {})
        history = rs.get_reasoning_history()
        assert len(history) == 1

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_clear_history(self, mock_uss):
        rs = ReasoningSystem()
        rs.reasoning_history.append({'test': True})
        rs.clear_history()
        assert rs.reasoning_history == []


class TestCalculateConfidence:
    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_base_confidence(self, mock_uss):
        rs = ReasoningSystem()
        conf = rs._calculate_confidence(
            {'action_id': 'test'}, {}, []
        )
        assert conf == 0.7

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_confidence_with_graph_risks(self, mock_uss):
        rs = ReasoningSystem()
        conf = rs._calculate_confidence(
            {'action_id': 'test'}, {}, ['some risk']
        )
        assert conf == pytest.approx(0.9)

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_confidence_capped(self, mock_uss):
        rs = ReasoningSystem()
        conf = rs._calculate_confidence(
            {'action_id': 'test'}, {}, ['r1', 'r2', 'r3']
        )
        assert conf <= 1.0


class TestFindSimplePath:
    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_no_path(self, mock_uss):
        mock_space = mock_uss.return_value
        mock_space.get_relationships.return_value = []

        rs = ReasoningSystem()
        path = rs._find_simple_path('A', 'Harm', max_depth=2)
        assert path is None

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_direct_path(self, mock_uss):
        mock_space = mock_uss.return_value
        mock_space.get_relationships.side_effect = [
            [{'source': 'A', 'target': 'Harm'}],
        ]

        rs = ReasoningSystem()
        path = rs._find_simple_path('A', 'Harm', max_depth=2)
        assert path == ['A', 'Harm']

    @patch('ai.alignment.reasoning_system._SimpleSymbolicSpace')
    def test_path_exceeds_depth(self, mock_uss):
        mock_space = mock_uss.return_value
        mock_space.get_relationships.side_effect = [
            [{'source': 'A', 'target': 'B'}],
            [{'source': 'B', 'target': 'C'}],
        ]

        rs = ReasoningSystem()
        path = rs._find_simple_path('A', 'C', max_depth=1)
        assert path is None
