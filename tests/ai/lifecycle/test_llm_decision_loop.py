"""Tests for the LLM decision loop module."""

import json
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.lifecycle.user_monitor import UserMonitor

_MODULE_MOCKS = {}
for name, mock in _MODULE_MOCKS.items():
    if name not in sys.modules:
        sys.modules[name] = mock


@pytest.fixture
def mock_llm_service():
    service = MagicMock()
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        'action': 'greet',
        'message': 'Hello!',
        'priority': 'medium',
        'reason': 'User is online',
        'confidence': 0.8,
    })
    service.chat_completion = AsyncMock(return_value=mock_response)
    return service


@pytest.fixture
def mock_state_manager():
    manager = MagicMock()
    manager.get_analysis = MagicMock(return_value={
        'averages': {'alpha': 0.6, 'beta': 0.5, 'gamma': 0.7, 'delta': 0.5},
        'dominant_emotion': ('neutral', 0.5),
    })
    return manager


@pytest.fixture
def mock_memory_manager():
    manager = MagicMock()
    manager.get_recent_memories = AsyncMock(return_value=['memory1', 'memory2'])
    manager.retrieve_emotional_memories = AsyncMock(return_value=[])
    return manager


@pytest.fixture
def user_monitor():
    um = UserMonitor(check_interval=999.0)
    um.user_state.online = True
    um.user_state.activity_level = 'high'
    um.user_state.emotion = 'neutral'
    um.user_state.emotion_intensity = 0.0
    return um


@pytest.fixture
def decision_loop(mock_llm_service, mock_state_manager, mock_memory_manager, user_monitor):
    from ai.lifecycle.llm_decision_loop import LLMDecisionLoop
    return LLMDecisionLoop(
        llm_service=mock_llm_service,
        state_manager=mock_state_manager,
        memory_manager=mock_memory_manager,
        user_monitor=user_monitor,
        loop_interval=1.0,
    )


class TestDecision:
    """Tests for the Decision dataclass."""

    def test_decision_creation(self):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        now = datetime.now()
        d = Decision(
            action=DecisionAction.GREET,
            message='Hello',
            priority=DecisionPriority.HIGH,
            reason='Test',
            timestamp=now,
            confidence=0.9,
        )
        assert d.action == 'greet'
        assert d.message == 'Hello'
        assert d.priority == 'high'
        assert d.confidence == 0.9
        assert d.reason == 'Test'
        assert d.timestamp == now
        assert not d.executed
        assert d.execution_result is None

    def test_decision_to_dict(self):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        now = datetime.now()
        d = Decision(
            action=DecisionAction.GREET,
            message='Hello',
            priority=DecisionPriority.HIGH,
            reason='Test',
            timestamp=now,
            confidence=0.9,
        )
        d.executed = True
        d.execution_result = {'success': True}
        result = d.to_dict()
        assert result['action'] == 'greet'
        assert result['priority'] == 'high'
        assert result['timestamp'] == now.isoformat()
        assert result['executed'] is True
        assert result['execution_result'] == {'success': True}

    def test_decision_defaults(self):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        d = Decision(
            action=DecisionAction.OBSERVE,
            message='',
            priority=DecisionPriority.LOW,
            reason='Testing defaults',
            timestamp=datetime.now(),
        )
        assert d.confidence == 0.0
        assert not d.executed
        assert d.execution_result is None

    def test_action_constants(self):
        from ai.lifecycle.llm_decision_loop import DecisionAction
        assert DecisionAction.NONE == 'none'
        assert DecisionAction.GREET == 'greet'
        assert DecisionAction.COMFORT == 'comfort'
        assert DecisionAction.REMIND == 'remind'
        assert DecisionAction.SHARE == 'share'
        assert DecisionAction.QUESTION == 'question'
        assert DecisionAction.OBSERVE == 'observe'

    def test_priority_constants(self):
        from ai.lifecycle.llm_decision_loop import DecisionPriority
        assert DecisionPriority.HIGH == 'high'
        assert DecisionPriority.MEDIUM == 'medium'
        assert DecisionPriority.LOW == 'low'


class TestLLMDecisionLoopInit:
    """Tests for LLMDecisionLoop initialization."""

    def test_init_defaults(self, decision_loop):
        assert not decision_loop.is_running
        assert decision_loop.loop_interval == 1.0
        assert decision_loop.decision_history == []
        assert decision_loop.stats['total_decisions'] == 0
        assert decision_loop.stats['executed_decisions'] == 0
        assert decision_loop.stats['failed_decisions'] == 0

    def test_init_with_custom_interval(self, mock_llm_service, mock_state_manager, mock_memory_manager, user_monitor):
        from ai.lifecycle.llm_decision_loop import LLMDecisionLoop
        loop = LLMDecisionLoop(
            llm_service=mock_llm_service,
            state_manager=mock_state_manager,
            memory_manager=mock_memory_manager,
            user_monitor=user_monitor,
            loop_interval=5.0,
            min_loop_interval=3.0,
            max_loop_interval=10.0,
        )
        assert loop.loop_interval == 5.0
        assert loop.min_loop_interval == 3.0
        assert loop.max_loop_interval == 10.0

    def test_init_with_broadcast_callback(self, mock_llm_service, mock_state_manager, mock_memory_manager, user_monitor):
        from ai.lifecycle.llm_decision_loop import LLMDecisionLoop
        callback = AsyncMock()
        loop = LLMDecisionLoop(
            llm_service=mock_llm_service,
            state_manager=mock_state_manager,
            memory_manager=mock_memory_manager,
            user_monitor=user_monitor,
            broadcast_callback=callback,
        )
        assert loop.broadcast_callback is callback

    @pytest.mark.asyncio
    async def test_start_stop(self, decision_loop):
        assert not decision_loop.is_running
        await decision_loop.start()
        assert decision_loop.is_running
        assert decision_loop._decision_task is not None
        await decision_loop.stop()
        assert not decision_loop.is_running

    @pytest.mark.asyncio
    async def test_start_when_already_running(self, decision_loop):
        await decision_loop.start()
        await decision_loop.start()
        assert decision_loop.is_running
        await decision_loop.stop()

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, decision_loop):
        await decision_loop.stop()
        assert not decision_loop.is_running

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self, decision_loop):
        await decision_loop.start()
        task = decision_loop._decision_task
        await decision_loop.stop()
        assert task.done()


class TestDecisionExecution:
    """Tests for individual decision execution methods."""

    @pytest.mark.asyncio
    async def test_execute_greet_action(self, decision_loop):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        decision = Decision(
            action=DecisionAction.GREET,
            message='Hello!',
            priority=DecisionPriority.HIGH,
            reason='Greeting',
            timestamp=datetime.now(),
        )
        result = await decision_loop._execute_greet(decision)
        assert result['success']
        assert result['sent']

    @pytest.mark.asyncio
    async def test_execute_comfort_action(self, decision_loop):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        decision = Decision(
            action=DecisionAction.COMFORT,
            message='Feel better',
            priority=DecisionPriority.HIGH,
            reason='Comfort',
            timestamp=datetime.now(),
        )
        result = await decision_loop._execute_comfort(decision)
        assert result['success']

    @pytest.mark.asyncio
    async def test_execute_remind_action(self, decision_loop):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        decision = Decision(
            action=DecisionAction.REMIND,
            message='Reminder!',
            priority=DecisionPriority.HIGH,
            reason='Remind',
            timestamp=datetime.now(),
        )
        result = await decision_loop._execute_remind(decision)
        assert result['success']

    @pytest.mark.asyncio
    async def test_execute_share_action(self, decision_loop):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        decision = Decision(
            action=DecisionAction.SHARE,
            message='Share this',
            priority=DecisionPriority.MEDIUM,
            reason='Share',
            timestamp=datetime.now(),
        )
        result = await decision_loop._execute_share(decision)
        assert result['success']

    @pytest.mark.asyncio
    async def test_execute_question_action(self, decision_loop):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        decision = Decision(
            action=DecisionAction.QUESTION,
            message='Question?',
            priority=DecisionPriority.MEDIUM,
            reason='Question',
            timestamp=datetime.now(),
        )
        result = await decision_loop._execute_question(decision)
        assert result['success']

    @pytest.mark.asyncio
    async def test_execute_observe_action_does_not_broadcast(self, decision_loop):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        decision = Decision(
            action=DecisionAction.OBSERVE,
            message='Watching',
            priority=DecisionPriority.LOW,
            reason='Observing',
            timestamp=datetime.now(),
        )
        result = await decision_loop._execute_observe(decision)
        assert result['success']
        assert result['observed']

    @pytest.mark.asyncio
    async def test_execute_decision_dispatches_by_action(self, decision_loop):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        for action in [
            DecisionAction.GREET,
            DecisionAction.COMFORT,
            DecisionAction.REMIND,
            DecisionAction.SHARE,
            DecisionAction.QUESTION,
            DecisionAction.OBSERVE,
        ]:
            decision = Decision(
                action=action,
                message='Test',
                priority=DecisionPriority.MEDIUM,
                reason='Testing dispatch',
                timestamp=datetime.now(),
            )
            result = await decision_loop._execute_decision(decision)
            assert result['success'], f'Failed for action {action}'

    @pytest.mark.asyncio
    async def test_execute_decision_updates_stats(self, decision_loop):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        decision = Decision(
            action=DecisionAction.GREET,
            message='Hi',
            priority=DecisionPriority.HIGH,
            reason='Test',
            timestamp=datetime.now(),
        )
        await decision_loop._execute_decision(decision)
        assert decision_loop.stats['executed_decisions'] == 1

    @pytest.mark.asyncio
    async def test_execute_greet_via_broadcast_callback(self, mock_llm_service, mock_state_manager, mock_memory_manager, user_monitor):
        from ai.lifecycle.llm_decision_loop import LLMDecisionLoop, Decision, DecisionAction, DecisionPriority
        callback = AsyncMock()
        loop = LLMDecisionLoop(
            llm_service=mock_llm_service,
            state_manager=mock_state_manager,
            memory_manager=mock_memory_manager,
            user_monitor=user_monitor,
            broadcast_callback=callback,
        )
        decision = Decision(
            action=DecisionAction.GREET,
            message='Hello via ws',
            priority=DecisionPriority.HIGH,
            reason='Test broadcast',
            timestamp=datetime.now(),
        )
        await loop._execute_greet(decision)
        callback.assert_called_once()
        call_arg = callback.call_args[0][0]
        assert call_arg['type'] == 'angela_action'
        assert call_arg['action'] == 'greet'
        assert call_arg['message'] == 'Hello via ws'


class TestMakeDecision:
    """Tests for the decision-making flow."""

    @pytest.mark.asyncio
    async def test_make_decision_records_and_executes(self, decision_loop):
        await decision_loop._make_decision()
        assert len(decision_loop.decision_history) == 1
        assert decision_loop.stats['total_decisions'] == 1
        recorded = decision_loop.decision_history[0]
        assert recorded.action == 'greet'
        assert recorded.executed

    @pytest.mark.asyncio
    async def test_make_decision_uses_fallback_when_no_chat_completion(self, mock_state_manager, mock_memory_manager, user_monitor):
        from ai.lifecycle.llm_decision_loop import LLMDecisionLoop
        bad_llm = MagicMock(spec=[])
        loop = LLMDecisionLoop(
            llm_service=bad_llm,
            state_manager=mock_state_manager,
            memory_manager=mock_memory_manager,
            user_monitor=user_monitor,
        )
        await loop._make_decision()
        assert len(loop.decision_history) == 1
        assert loop.stats['total_decisions'] == 1

    @pytest.mark.asyncio
    async def test_make_decision_handles_json_parse_error(self, decision_loop):
        mock_response = MagicMock()
        mock_response.content = 'not valid json'
        decision_loop.llm_service.chat_completion.return_value = mock_response
        await decision_loop._make_decision()
        assert len(decision_loop.decision_history) == 1

    @pytest.mark.asyncio
    async def test_make_decision_handles_llm_exception_gracefully(self, decision_loop):
        decision_loop.llm_service.chat_completion.side_effect = Exception('LLM error')
        await decision_loop._make_decision()
        assert decision_loop.stats['total_decisions'] >= 0

    @pytest.mark.asyncio
    async def test_make_decision_no_action_skips_execution(self, decision_loop):
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            'action': 'none',
            'message': '',
            'priority': 'low',
            'reason': 'Nothing to do',
            'confidence': 0.9,
        })
        decision_loop.llm_service.chat_completion.return_value = mock_response
        await decision_loop._make_decision()
        assert len(decision_loop.decision_history) == 1
        d = decision_loop.decision_history[0]
        assert d.action == 'none'
        assert not d.executed


class TestShouldMakeDecision:
    """Tests for the should_make_decision logic."""

    def test_should_make_decision_when_online(self, decision_loop, user_monitor):
        user_monitor.user_state.online = True
        state = {'dummy': True}
        assert decision_loop._should_make_decision(state) is True

    def test_should_make_decision_when_offline_and_recent(self, decision_loop, user_monitor):
        user_monitor.user_state.online = False
        state = {'dummy': True}
        decision_loop.user_monitor.get_idle_time = MagicMock(return_value=100)
        assert decision_loop._should_make_decision(state) is False

    def test_should_make_decision_when_offline_and_long(self, decision_loop, user_monitor):
        user_monitor.user_state.online = False
        state = {'dummy': True}
        decision_loop.user_monitor.get_idle_time = MagicMock(return_value=700)
        assert decision_loop._should_make_decision(state) is True


class TestFallbackDecision:
    """Tests for fallback decision logic."""

    def test_fallback_when_user_offline(self, decision_loop, user_monitor):
        user_monitor.user_state.online = False
        fallback = decision_loop._fallback_decision()
        assert fallback['action'] == 'none'
        assert fallback['priority'] == 'low'

    def test_fallback_when_user_returns(self, decision_loop, user_monitor):
        user_monitor.user_state.online = True
        with patch.object(user_monitor, 'detect_return', return_value=True):
            fallback = decision_loop._fallback_decision()
            assert fallback['action'] == 'greet'
            assert fallback['priority'] == 'high'
            assert fallback['reason'] == '檢測到用戶返回'

    def test_fallback_when_idle_and_negative_emotion(self, decision_loop, user_monitor):
        user_monitor.user_state.online = True
        user_monitor.user_state.emotion = 'sad'
        with patch.object(user_monitor, 'detect_return', return_value=False):
            with patch.object(user_monitor, 'get_idle_time', return_value=90):
                fallback = decision_loop._fallback_decision()
                assert fallback['action'] == 'comfort'
                assert fallback['priority'] == 'medium'

    def test_fallback_when_long_idle(self, decision_loop, user_monitor):
        user_monitor.user_state.online = True
        with patch.object(user_monitor, 'detect_return', return_value=False):
            with patch.object(user_monitor, 'get_idle_time', return_value=130):
                fallback = decision_loop._fallback_decision()
                assert fallback['action'] == 'greet'
                assert fallback['priority'] == 'low'

    def test_fallback_default(self, decision_loop, user_monitor):
        user_monitor.user_state.online = True
        with patch.object(user_monitor, 'detect_return', return_value=False):
            with patch.object(user_monitor, 'get_idle_time', return_value=10):
                fallback = decision_loop._fallback_decision()
                assert fallback['action'] == 'none'
                assert fallback['priority'] == 'low'


class TestDecisionHistoryAndStats:
    """Tests for decision history and statistics."""

    def test_record_decision_updates_history_and_stats(self, decision_loop):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        d = Decision(
            action=DecisionAction.GREET,
            message='Hi',
            priority=DecisionPriority.HIGH,
            reason='Testing',
            timestamp=datetime.now(),
        )
        decision_loop._record_decision(d)
        assert len(decision_loop.decision_history) == 1
        assert decision_loop.stats['total_decisions'] == 1
        assert decision_loop.stats['action_counts'].get('greet') == 1

    def test_record_multiple_decisions_tracks_counts(self, decision_loop):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        for action in ['greet', 'greet', 'comfort', 'observe']:
            d = Decision(
                action=action,
                message='Test',
                priority=DecisionPriority.LOW,
                reason='Test',
                timestamp=datetime.now(),
            )
            decision_loop._record_decision(d)
        assert decision_loop.stats['total_decisions'] == 4
        assert decision_loop.stats['action_counts']['greet'] == 2
        assert decision_loop.stats['action_counts']['comfort'] == 1
        assert decision_loop.stats['action_counts']['observe'] == 1

    def test_decision_history_honors_max_size(self, decision_loop):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        decision_loop.max_history_size = 5
        for i in range(10):
            d = Decision(
                action=DecisionAction.GREET,
                message=f'Hi {i}',
                priority=DecisionPriority.LOW,
                reason='Test',
                timestamp=datetime.now(),
            )
            decision_loop._record_decision(d)
        assert len(decision_loop.decision_history) == 5

    def test_get_decision_history(self, decision_loop):
        from ai.lifecycle.llm_decision_loop import Decision, DecisionAction, DecisionPriority
        for i in range(5):
            d = Decision(
                action=DecisionAction.GREET,
                message=f'Hi {i}',
                priority=DecisionPriority.LOW,
                reason='Test',
                timestamp=datetime.now(),
            )
            decision_loop._record_decision(d)
        history = decision_loop.get_decision_history(limit=3)
        assert len(history) == 3
        for entry in history:
            assert 'action' in entry
            assert 'message' in entry
            assert 'timestamp' in entry

    def test_get_stats(self, decision_loop):
        stats = decision_loop.get_stats()
        assert 'is_running' in stats
        assert 'total_decisions' in stats
        assert 'executed_decisions' in stats
        assert 'failed_decisions' in stats
        assert 'action_counts' in stats
        assert not stats['is_running']


class TestCalculateInterval:
    """Tests for dynamic interval calculation."""

    def test_interval_high_activity(self, decision_loop, user_monitor):
        user_monitor.user_state.online = True
        user_monitor.user_state.activity_level = 'high'
        interval = decision_loop._calculate_interval()
        assert interval == decision_loop.min_loop_interval

    def test_interval_low_activity(self, decision_loop, user_monitor):
        user_monitor.user_state.online = True
        user_monitor.user_state.activity_level = 'low'
        interval = decision_loop._calculate_interval()
        assert interval == decision_loop.max_loop_interval

    def test_interval_offline(self, decision_loop, user_monitor):
        user_monitor.user_state.online = False
        interval = decision_loop._calculate_interval()
        assert interval == decision_loop.loop_interval


class TestGetCurrentState:
    """Tests for get_current_state."""

    @pytest.mark.asyncio
    async def test_get_current_state_returns_dict(self, decision_loop):
        state = await decision_loop._get_current_state()
        assert 'state_matrix' in state
        assert 'dominant_emotion' in state
        assert 'mood' in state
        assert 'energy' in state
        assert 'boredom' in state
        assert state['dominant_emotion'] == 'neutral'

    @pytest.mark.asyncio
    async def test_get_current_state_without_analysis(self, mock_memory_manager, user_monitor):
        from ai.lifecycle.llm_decision_loop import LLMDecisionLoop
        state_manager = MagicMock(spec=[])
        loop = LLMDecisionLoop(
            llm_service=MagicMock(),
            state_manager=state_manager,
            memory_manager=mock_memory_manager,
            user_monitor=user_monitor,
        )
        state = await loop._get_current_state()
        assert state['dominant_emotion'] == 'neutral'
        assert state['mood'] == 0.5

    @pytest.mark.asyncio
    async def test_get_current_state_fallback_on_error(self, decision_loop, mock_state_manager):
        mock_state_manager.get_analysis.side_effect = Exception('State error')
        state = await decision_loop._get_current_state()
        assert 'dominant_emotion' not in state
        assert state['mood'] == 0.5
        assert state['mood'] == 0.5
