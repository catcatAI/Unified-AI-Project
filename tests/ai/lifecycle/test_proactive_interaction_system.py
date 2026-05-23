"""Tests for the proactive interaction system module."""

import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai.lifecycle.user_monitor import UserMonitor

_MODULE_MOCKS = {}
for name, mock in _MODULE_MOCKS.items():
    if name not in sys.modules:
        sys.modules[name] = mock


@pytest.fixture
def mock_llm_service():
    return MagicMock()


@pytest.fixture
def mock_state_manager():
    return MagicMock()


@pytest.fixture
def mock_memory_manager():
    manager = MagicMock()
    manager.get_important_events = AsyncMock(return_value=['event1', 'event2'])
    return manager


@pytest.fixture
def user_monitor():
    um = UserMonitor(check_interval=999.0)
    um.user_state.online = True
    um.user_state.activity_level = 'medium'
    um.user_state.emotion = 'neutral'
    um.user_state.emotion_intensity = 0.0
    return um


@pytest.fixture
def proactive_system(mock_llm_service, mock_state_manager, mock_memory_manager, user_monitor):
    from ai.lifecycle.proactive_interaction_system import ProactiveInteractionSystem
    return ProactiveInteractionSystem(
        llm_service=mock_llm_service,
        state_manager=mock_state_manager,
        memory_manager=mock_memory_manager,
        user_monitor=user_monitor,
        check_interval=10.0,
    )


class TestInteractionOpportunity:
    """Tests for InteractionOpportunity enum."""

    def test_opportunity_values(self):
        from ai.lifecycle.proactive_interaction_system import InteractionOpportunity
        assert InteractionOpportunity.USER_RETURN.value == 'user_return'
        assert InteractionOpportunity.LONG_IDLE.value == 'long_idle'
        assert InteractionOpportunity.EMOTIONAL_CHANGE.value == 'emotional_change'
        assert InteractionOpportunity.TIME_BASED.value == 'time_based'
        assert InteractionOpportunity.MEMORY_TRIGGER.value == 'memory_trigger'
        assert InteractionOpportunity.LEARNING_SHARE.value == 'learning_share'
        assert InteractionOpportunity.WEATHER_CHANGE.value == 'weather_change'
        assert InteractionOpportunity.EVENT_REMINDER.value == 'event_reminder'


class TestInteractionPlan:
    """Tests for InteractionPlan dataclass."""

    def test_plan_creation(self):
        from ai.lifecycle.proactive_interaction_system import InteractionPlan
        now = datetime.now()
        plan = InteractionPlan(
            opportunity='user_return',
            action='proactive_message',
            message='Welcome back!',
            priority='high',
            scheduled_time=now,
        )
        assert plan.opportunity == 'user_return'
        assert plan.action == 'proactive_message'
        assert plan.message == 'Welcome back!'
        assert plan.priority == 'high'
        assert not plan.executed
        assert plan.execution_result is None

    def test_plan_to_dict(self):
        from ai.lifecycle.proactive_interaction_system import InteractionPlan
        now = datetime.now()
        plan = InteractionPlan(
            opportunity='long_idle',
            action='proactive_message',
            message='Hey there!',
            priority='medium',
            scheduled_time=now,
        )
        plan.executed = True
        plan.execution_result = {'success': True}
        result = plan.to_dict()
        assert result['opportunity'] == 'long_idle'
        assert result['executed'] is True
        assert result['execution_result'] == {'success': True}


class TestProactiveInteractionSystemInit:
    """Tests for ProactiveInteractionSystem initialization."""

    def test_init_defaults(self, proactive_system):
        assert not proactive_system.is_running
        assert proactive_system.check_interval == 10.0
        assert proactive_system.interaction_queue == []
        assert proactive_system.stats['total_opportunities'] == 0
        assert proactive_system.stats['planned_actions'] == 0

    def test_init_with_custom_values(self, mock_llm_service, mock_state_manager, mock_memory_manager, user_monitor):
        from ai.lifecycle.proactive_interaction_system import ProactiveInteractionSystem
        system = ProactiveInteractionSystem(
            llm_service=mock_llm_service,
            state_manager=mock_state_manager,
            memory_manager=mock_memory_manager,
            user_monitor=user_monitor,
            check_interval=30.0,
            min_check_interval=15.0,
            max_check_interval=60.0,
        )
        assert system.check_interval == 30.0
        assert system.min_check_interval == 15.0
        assert system.max_check_interval == 60.0

    @pytest.mark.asyncio
    async def test_start_stop(self, proactive_system):
        await proactive_system.start()
        assert proactive_system.is_running
        assert proactive_system._proactive_task is not None
        await proactive_system.stop()
        assert not proactive_system.is_running

    @pytest.mark.asyncio
    async def test_start_when_already_running(self, proactive_system):
        await proactive_system.start()
        await proactive_system.start()
        assert proactive_system.is_running
        await proactive_system.stop()

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, proactive_system):
        await proactive_system.stop()
        assert not proactive_system.is_running


class TestDetectUserState:
    """Tests for user state detection."""

    @pytest.mark.asyncio
    async def test_detect_user_state_returns_dict(self, proactive_system, user_monitor):
        user_monitor.user_state.online = True
        state = await proactive_system._detect_user_state()
        assert state['online'] is True
        assert 'activity_level' in state
        assert 'emotion' in state
        assert 'idle_time' in state
        assert 'user_return' in state


class TestIdentifyOpportunities:
    """Tests for opportunity identification."""

    @pytest.mark.asyncio
    async def test_identify_user_return_opportunity(self, proactive_system):
        user_state = {
            'online': True,
            'activity_level': 'medium',
            'emotion': 'neutral',
            'user_return': True,
            'session_duration': 0,
            'idle_time': 0,
        }
        opportunities = await proactive_system._identify_opportunities(user_state)
        types = [o['type'] for o in opportunities]
        assert 'user_return' in types

    @pytest.mark.asyncio
    async def test_identify_long_idle_opportunity(self, proactive_system):
        user_state = {
            'online': True,
            'activity_level': 'medium',
            'emotion': 'neutral',
            'user_return': False,
            'idle_time': 200,
        }
        opportunities = await proactive_system._identify_opportunities(user_state)
        types = [o['type'] for o in opportunities]
        assert 'long_idle' in types

    @pytest.mark.asyncio
    async def test_identify_emotional_change_opportunity(self, proactive_system):
        user_state = {
            'online': True,
            'activity_level': 'medium',
            'emotion': 'sad',
            'user_return': False,
            'idle_time': 0,
            'emotion_intensity': 0.8,
        }
        opportunities = await proactive_system._identify_opportunities(user_state)
        types = [o['type'] for o in opportunities]
        assert 'emotional_change' in types

    @pytest.mark.asyncio
    async def test_identify_no_opportunities(self, proactive_system):
        user_state = {
            'online': True,
            'activity_level': 'medium',
            'emotion': 'neutral',
            'user_return': False,
            'idle_time': 10,
        }
        with patch.object(proactive_system, '_check_time_based_opportunities', AsyncMock()):
            with patch.object(proactive_system, '_check_memory_triggers', AsyncMock()):
                opportunities = await proactive_system._identify_opportunities(user_state)
        assert len(opportunities) == 0

    @pytest.mark.asyncio
    async def test_identify_memory_trigger_opportunity(self, proactive_system, mock_memory_manager):
        mock_memory_manager.get_important_events = AsyncMock(return_value=['Important event'])
        user_state = {
            'online': True,
            'activity_level': 'medium',
            'emotion': 'neutral',
            'user_return': False,
            'idle_time': 0,
        }
        opportunities = await proactive_system._identify_opportunities(user_state)
        types = [o['type'] for o in opportunities]
        assert 'memory_trigger' in types

    @pytest.mark.asyncio
    async def test_opportunity_counts_tracked(self, proactive_system):
        user_state = {
            'online': True,
            'activity_level': 'medium',
            'emotion': 'sad',
            'user_return': True,
            'idle_time': 200,
            'emotion_intensity': 0.8,
            'session_duration': 0,
        }
        with patch.object(proactive_system, '_check_time_based_opportunities', AsyncMock()):
            with patch.object(proactive_system, '_check_memory_triggers', AsyncMock()):
                await proactive_system._identify_opportunities(user_state)
        assert proactive_system.stats['total_opportunities'] >= 3  # return + idle + emotional


class TestPlanProactiveAction:
    """Tests for planning proactive actions."""

    @pytest.mark.asyncio
    async def test_plan_user_return_action(self, proactive_system):
        opportunity = {
            'type': 'user_return',
            'priority': 'high',
            'data': {'offline_duration': 100},
        }
        user_state = {'online': True}
        plan = await proactive_system._plan_proactive_action(opportunity, user_state)
        assert plan is not None
        assert plan.opportunity == 'user_return'
        assert plan.priority == 'high'

    @pytest.mark.asyncio
    async def test_plan_respects_cooldown(self, proactive_system):
        proactive_system.last_interaction_time = datetime.now()
        opportunity = {
            'type': 'long_idle',
            'priority': 'medium',
            'data': {'idle_time': 200},
        }
        user_state = {'online': True}
        plan = await proactive_system._plan_proactive_action(opportunity, user_state)
        assert plan is None  # cooldown active, not high priority

    @pytest.mark.asyncio
    async def test_plan_bypasses_cooldown_for_high_priority(self, proactive_system):
        proactive_system.last_interaction_time = datetime.now()
        opportunity = {
            'type': 'user_return',
            'priority': 'high',
            'data': {'offline_duration': 100},
        }
        user_state = {'online': True}
        plan = await proactive_system._plan_proactive_action(opportunity, user_state)
        assert plan is not None  # high priority bypasses cooldown

    @pytest.mark.asyncio
    async def test_plan_cooldown_expired(self, proactive_system):
        proactive_system.last_interaction_time = datetime.now() - timedelta(seconds=120)
        opportunity = {
            'type': 'long_idle',
            'priority': 'medium',
            'data': {'idle_time': 200},
        }
        user_state = {'online': True}
        plan = await proactive_system._plan_proactive_action(opportunity, user_state)
        assert plan is not None  # cooldown expired


class TestExecutePlannedActions:
    """Tests for executing planned actions."""

    @pytest.mark.asyncio
    async def test_execute_empty_queue(self, proactive_system):
        await proactive_system._execute_planned_actions()
        assert proactive_system.stats['executed_actions'] == 0

    @pytest.mark.asyncio
    async def test_execute_single_plan(self, proactive_system):
        from ai.lifecycle.proactive_interaction_system import InteractionPlan
        now = datetime.now()
        plan = InteractionPlan(
            opportunity='user_return',
            action='proactive_message',
            message='Welcome!',
            priority='high',
            scheduled_time=now,
        )
        proactive_system.interaction_queue.append(plan)
        await proactive_system._execute_planned_actions()
        assert plan.executed is True
        assert proactive_system.stats['executed_actions'] == 1

    @pytest.mark.asyncio
    async def test_execute_prioritizes_high(self, proactive_system):
        from ai.lifecycle.proactive_interaction_system import InteractionPlan
        now = datetime.now()
        low_plan = InteractionPlan(
            opportunity='long_idle',
            action='proactive_message',
            message='Hey',
            priority='low',
            scheduled_time=now,
        )
        high_plan = InteractionPlan(
            opportunity='user_return',
            action='proactive_message',
            message='Welcome!',
            priority='high',
            scheduled_time=now,
        )
        proactive_system.interaction_queue.extend([low_plan, high_plan])
        await proactive_system._execute_planned_actions()
        assert high_plan.executed is True
        assert low_plan.executed is True  # both in first 3 after sort

    @pytest.mark.asyncio
    async def test_execute_limits_to_three(self, proactive_system):
        from ai.lifecycle.proactive_interaction_system import InteractionPlan
        now = datetime.now()
        for i in range(5):
            plan = InteractionPlan(
                opportunity='user_return',
                action='proactive_message',
                message=f'Plan {i}',
                priority='medium',
                scheduled_time=now,
            )
            proactive_system.interaction_queue.append(plan)
        await proactive_system._execute_planned_actions()
        executed = sum(1 for p in proactive_system.interaction_queue if p.executed)
        assert executed <= 3


class TestCleanupQueue:
    """Tests for queue cleanup."""

    def test_cleanup_removes_executed(self, proactive_system):
        from ai.lifecycle.proactive_interaction_system import InteractionPlan
        now = datetime.now()
        executed = InteractionPlan(
            opportunity='user_return', action='proactive_message',
            message='Done', priority='high', scheduled_time=now,
        )
        executed.executed = True
        pending = InteractionPlan(
            opportunity='long_idle', action='proactive_message',
            message='Pending', priority='medium', scheduled_time=now,
        )
        proactive_system.interaction_queue = [executed, pending]
        proactive_system._cleanup_queue()
        assert len(proactive_system.interaction_queue) == 1
        assert proactive_system.interaction_queue[0] is pending

    def test_cleanup_limits_queue_size(self, proactive_system):
        from ai.lifecycle.proactive_interaction_system import InteractionPlan
        now = datetime.now()
        proactive_system.max_queue_size = 3
        for _ in range(10):
            plan = InteractionPlan(
                opportunity='long_idle', action='proactive_message',
                message='Test', priority='low', scheduled_time=now,
            )
            proactive_system.interaction_queue.append(plan)
        proactive_system._cleanup_queue()
        assert len(proactive_system.interaction_queue) <= 3


class TestStatsAndQueue:
    """Tests for statistics and queue inspection."""

    def test_get_stats(self, proactive_system):
        stats = proactive_system.get_stats()
        assert 'is_running' in stats
        assert 'total_opportunities' in stats
        assert 'planned_actions' in stats
        assert 'executed_actions' in stats
        assert 'queue_size' in stats

    def test_get_queue(self, proactive_system):
        from ai.lifecycle.proactive_interaction_system import InteractionPlan
        now = datetime.now()
        for _ in range(3):
            plan = InteractionPlan(
                opportunity='user_return', action='proactive_message',
                message='Test', priority='high', scheduled_time=now,
            )
            proactive_system.interaction_queue.append(plan)
        queue = proactive_system.get_queue(limit=2)
        assert len(queue) == 2
        for entry in queue:
            assert 'opportunity' in entry


class TestCalculateInterval:
    """Tests for interval calculation."""

    def test_interval_high_activity(self, proactive_system, user_monitor):
        user_monitor.user_state.online = True
        user_monitor.user_state.activity_level = 'high'
        interval = proactive_system._calculate_interval()
        assert interval == proactive_system.max_check_interval

    def test_interval_low_activity(self, proactive_system, user_monitor):
        user_monitor.user_state.online = True
        user_monitor.user_state.activity_level = 'low'
        interval = proactive_system._calculate_interval()
        assert interval == proactive_system.min_check_interval

    def test_interval_offline(self, proactive_system, user_monitor):
        user_monitor.user_state.online = False
        interval = proactive_system._calculate_interval()
        assert interval == proactive_system.check_interval


class TestMessageGeneration:
    """Tests for message generation methods."""

    @pytest.mark.asyncio
    async def test_generate_return_message(self, proactive_system):
        msg = await proactive_system._generate_return_message({})
        assert isinstance(msg, str)
        assert len(msg) > 0

    @pytest.mark.asyncio
    async def test_generate_idle_message_long(self, proactive_system):
        msg = await proactive_system._generate_idle_message({'data': {'idle_time': 400}})
        assert '忙' in msg or '帮忙' in msg

    @pytest.mark.asyncio
    async def test_generate_idle_message_short(self, proactive_system):
        msg = await proactive_system._generate_idle_message({'data': {'idle_time': 100}})
        assert '做' in msg

    @pytest.mark.asyncio
    async def test_generate_emotional_message_sad(self, proactive_system):
        msg = await proactive_system._generate_emotional_message({'data': {'emotion': 'sad'}})
        assert '難過' in msg

    @pytest.mark.asyncio
    async def test_generate_emotional_message_frustrated(self, proactive_system):
        msg = await proactive_system._generate_emotional_message({'data': {'emotion': 'frustrated'}})
        assert '煩惱' in msg

    @pytest.mark.asyncio
    async def test_generate_time_based_morning(self, proactive_system):
        msg = await proactive_system._generate_time_based_message({'data': {'time_type': 'morning_greeting'}})
        assert '早上' in msg

    @pytest.mark.asyncio
    async def test_generate_time_based_evening(self, proactive_system):
        msg = await proactive_system._generate_time_based_message({'data': {'time_type': 'evening_greeting'}})
        assert '晚上' in msg

    @pytest.mark.asyncio
    async def test_generate_memory_message(self, proactive_system):
        msg = await proactive_system._generate_memory_message({'data': {'events': ['We talked about AI yesterday']}})
        assert '記得' in msg

    @pytest.mark.asyncio
    async def test_generate_memory_message_no_events(self, proactive_system):
        msg = await proactive_system._generate_memory_message({'data': {'events': []}})
        assert '想起' in msg
