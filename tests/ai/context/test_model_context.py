import sys
from unittest.mock import MagicMock

_MODULE_MOCKS = {}
for name, mock in _MODULE_MOCKS.items():
    if name not in sys.modules:
        sys.modules[name] = mock

from datetime import datetime

import pytest

from apps.backend.src.ai.context.model_context import (
    AgentCollaboration,
    AgentContextManager,
    CollaborationStep,
    ModelCallRecord,
    ModelContextManager,
    ModelPerformanceMetrics,
)


class TestModelCallRecord:
    def test_creation(self):
        record = ModelCallRecord('model_a', 'model_b', {'param': 1}, 'result', 0.5, True)
        assert record.caller_model_id == 'model_a'
        assert record.callee_model_id == 'model_b'
        assert record.parameters == {'param': 1}
        assert record.result == 'result'
        assert record.duration == 0.5
        assert record.success is True
        assert isinstance(record.timestamp, datetime)
        assert record.record_id.startswith('call_')


class TestModelPerformanceMetrics:
    def test_initial_state(self):
        metrics = ModelPerformanceMetrics()
        assert metrics.total_calls == 0
        assert metrics.success_rate == 0.0
        assert metrics.average_duration == 0.0
        assert metrics.last_called is None

    def test_update_from_call(self):
        metrics = ModelPerformanceMetrics()
        record = ModelCallRecord('a', 'b', {}, 'ok', 1.0, True)
        metrics.update_from_call(record)
        assert metrics.total_calls == 1
        assert metrics.success_rate == 1.0
        assert metrics.average_duration == 1.0

    def test_update_from_failed_call(self):
        metrics = ModelPerformanceMetrics()
        record = ModelCallRecord('a', 'b', {}, None, 2.0, False)
        metrics.update_from_call(record)
        assert metrics.success_rate == 0.0


class TestAgentCollaboration:
    def test_creation(self):
        collab = AgentCollaboration('task1', ['agent_a', 'agent_b'])
        assert collab.task_id == 'task1'
        assert collab.participating_agents == ['agent_a', 'agent_b']
        assert collab.collaboration_steps == []
        assert collab.status == 'active'
        assert collab.start_time is not None
        assert collab.end_time is None
        assert collab.collaboration_id.startswith('collab_')

    def test_add_step(self):
        collab = AgentCollaboration('task1', ['agent_a'])
        step = CollaborationStep('agent_a', 'process', 'input', 'output')
        collab.add_step(step)
        assert len(collab.collaboration_steps) == 1

    def test_complete(self):
        collab = AgentCollaboration('task1', ['agent_a'])
        collab.complete()
        assert collab.status == 'completed'
        assert collab.end_time is not None

    def test_fail(self):
        collab = AgentCollaboration('task1', ['agent_a'])
        collab.fail()
        assert collab.status == 'failed'
        assert collab.end_time is not None


class TestCollaborationStep:
    def test_creation(self):
        step = CollaborationStep('agent_a', 'analyze', {'data': 'test'}, {'result': 'done'})
        assert step.agent_id == 'agent_a'
        assert step.action == 'analyze'
        assert step.input_data == {'data': 'test'}
        assert step.output_data == {'result': 'done'}
        assert step.duration is None
        assert step.step_id.startswith('step_')


class TestModelContextManager:
    def test_init(self):
        mock_cm = MagicMock()
        mgr = ModelContextManager(mock_cm)
        assert mgr.context_manager is mock_cm
        assert mgr.model_metrics == {}
        assert mgr.call_records == []

    def test_record_model_call(self):
        mock_cm = MagicMock()
        mgr = ModelContextManager(mock_cm)
        result = mgr.record_model_call('model_a', 'model_b', {'x': 1}, 'ok', 0.5, True)
        assert result is True
        assert len(mgr.call_records) == 1
        assert 'model_a' in mgr.model_metrics
        assert 'model_b' in mgr.model_metrics
        assert mgr.model_metrics['model_a'].total_calls == 1
        assert mgr.model_metrics['model_b'].total_calls == 1

    def test_get_model_context(self):
        mock_cm = MagicMock()
        mgr = ModelContextManager(mock_cm)
        assert mgr.get_model_context('model_a') is None

    def test_get_model_call_history(self):
        mock_cm = MagicMock()
        mgr = ModelContextManager(mock_cm)
        mgr.record_model_call('model_a', 'model_b', {}, 'ok', 0.5, True)
        mgr.record_model_call('model_b', 'model_c', {}, 'ok', 1.0, True)
        history = mgr.get_model_call_history('model_a')
        assert len(history) == 1
        history = mgr.get_model_call_history('model_b')
        assert len(history) == 2


class TestAgentContextManager:
    def test_init(self):
        mock_cm = MagicMock()
        mgr = AgentContextManager(mock_cm)
        assert mgr.context_manager is mock_cm
        assert mgr.collaborations == {}

    def test_start_collaboration(self):
        mock_cm = MagicMock()
        mgr = AgentContextManager(mock_cm)
        collab_id = mgr.start_collaboration('task1', ['agent_a', 'agent_b'])
        assert collab_id in mgr.collaborations
        assert mgr.collaborations[collab_id].task_id == 'task1'

    def test_record_collaboration_step(self):
        mock_cm = MagicMock()
        mgr = AgentContextManager(mock_cm)
        collab_id = mgr.start_collaboration('task1', ['agent_a'])
        result = mgr.record_collaboration_step(collab_id, 'agent_a', 'process', 'in', 'out', 1.5)
        assert result is True
        assert len(mgr.collaborations[collab_id].collaboration_steps) == 1

    def test_record_collaboration_step_not_found(self):
        mock_cm = MagicMock()
        mgr = AgentContextManager(mock_cm)
        assert mgr.record_collaboration_step('nonexistent', 'agent_a', 'process', 'in', 'out', 1.0) is False

    def test_complete_collaboration(self):
        mock_cm = MagicMock()
        mgr = AgentContextManager(mock_cm)
        collab_id = mgr.start_collaboration('task1', ['agent_a'])
        result = mgr.complete_collaboration(collab_id)
        assert result is True
        assert mgr.collaborations[collab_id].status == 'completed'

    def test_complete_collaboration_not_found(self):
        mock_cm = MagicMock()
        mgr = AgentContextManager(mock_cm)
        assert mgr.complete_collaboration('nonexistent') is False

    def test_get_collaboration_context(self):
        mock_cm = MagicMock()
        mgr = AgentContextManager(mock_cm)
        assert mgr.get_collaboration_context('nonexistent') is None

    def test_get_collaboration_context_found(self):
        mock_cm = MagicMock()
        mgr = AgentContextManager(mock_cm)
        collab_id = mgr.start_collaboration('task1', ['agent_a'])
        assert mgr.get_collaboration_context(collab_id) is None
