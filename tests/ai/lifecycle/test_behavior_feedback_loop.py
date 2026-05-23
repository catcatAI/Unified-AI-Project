"""Tests for the behavior feedback loop module."""

import sys
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

_MODULE_MOCKS = {}
for name, mock in _MODULE_MOCKS.items():
    if name not in sys.modules:
        sys.modules[name] = mock


@pytest.fixture
def mock_llm_service():
    return MagicMock()


@pytest.fixture
def mock_memory_manager():
    manager = MagicMock()
    manager.store_experience = AsyncMock()
    return manager


@pytest.fixture
def mock_learning_engine():
    return MagicMock()


@pytest.fixture
def feedback_loop(mock_llm_service, mock_memory_manager, mock_learning_engine):
    from ai.lifecycle.behavior_feedback_loop import BehaviorFeedbackLoop
    return BehaviorFeedbackLoop(
        llm_service=mock_llm_service,
        memory_manager=mock_memory_manager,
        learning_engine=mock_learning_engine,
        loop_interval=30.0,
    )


class TestBehaviorRecord:
    """Tests for BehaviorRecord dataclass."""

    def test_record_creation(self):
        from ai.lifecycle.behavior_feedback_loop import BehaviorRecord
        now = datetime.now()
        record = BehaviorRecord(
            action='greet',
            message='Hello!',
            priority='high',
            timestamp=now,
            user_response='Hi there',
            user_emotion='happy',
        )
        assert record.action == 'greet'
        assert record.message == 'Hello!'
        assert record.priority == 'high'
        assert record.user_response == 'Hi there'
        assert record.user_emotion == 'happy'
        assert record.effectiveness_score == 0.0
        assert record.outcome == 'unknown'

    def test_record_to_dict(self):
        from ai.lifecycle.behavior_feedback_loop import BehaviorRecord
        now = datetime.now()
        record = BehaviorRecord(
            action='comfort',
            message='Feel better',
            priority='high',
            timestamp=now,
            user_response='Thanks',
            user_emotion='neutral',
            effectiveness_score=0.7,
            outcome='success',
        )
        result = record.to_dict()
        assert result['action'] == 'comfort'
        assert result['effectiveness_score'] == 0.7
        assert result['outcome'] == 'success'
        assert result['user_response'] == 'Thanks'

    def test_record_defaults(self):
        from ai.lifecycle.behavior_feedback_loop import BehaviorRecord
        record = BehaviorRecord(
            action='greet',
            message='Hi',
            priority='low',
            timestamp=datetime.now(),
        )
        assert record.user_response is None
        assert record.user_emotion is None
        assert record.effectiveness_score == 0.0
        assert record.outcome == 'unknown'


class TestBehaviorPattern:
    """Tests for BehaviorPattern dataclass."""

    def test_pattern_creation(self):
        from ai.lifecycle.behavior_feedback_loop import BehaviorPattern
        now = datetime.now()
        pattern = BehaviorPattern(
            action='greet',
            context='default',
            success_rate=0.8,
            avg_effectiveness=0.75,
            count=10,
            last_updated=now,
        )
        assert pattern.action == 'greet'
        assert pattern.success_rate == 0.8
        assert pattern.avg_effectiveness == 0.75
        assert pattern.count == 10

    def test_pattern_to_dict(self):
        from ai.lifecycle.behavior_feedback_loop import BehaviorPattern
        now = datetime.now()
        pattern = BehaviorPattern(
            action='comfort',
            context='default',
            success_rate=0.5,
            avg_effectiveness=0.6,
            count=5,
            last_updated=now,
        )
        result = pattern.to_dict()
        assert result['action'] == 'comfort'
        assert result['success_rate'] == 0.5
        assert result['count'] == 5


class TestBehaviorFeedbackLoopInit:
    """Tests for BehaviorFeedbackLoop initialization."""

    def test_init_defaults(self, feedback_loop):
        assert not feedback_loop.is_running
        assert feedback_loop.loop_interval == 30.0
        assert feedback_loop.behavior_records == []
        assert feedback_loop.behavior_patterns == {}
        assert feedback_loop.stats['total_behaviors'] == 0
        assert feedback_loop.stats['evaluated_behaviors'] == 0

    def test_init_with_custom_values(self, mock_llm_service, mock_memory_manager, mock_learning_engine):
        from ai.lifecycle.behavior_feedback_loop import BehaviorFeedbackLoop
        loop = BehaviorFeedbackLoop(
            llm_service=mock_llm_service,
            memory_manager=mock_memory_manager,
            learning_engine=mock_learning_engine,
            loop_interval=60.0,
            min_loop_interval=45.0,
            max_loop_interval=120.0,
        )
        assert loop.loop_interval == 60.0
        assert loop.min_loop_interval == 45.0
        assert loop.max_loop_interval == 120.0

    def test_strategy_parameters_defaults(self, feedback_loop):
        params = feedback_loop.strategy_parameters
        assert params['greet_threshold'] == 60.0
        assert params['comfort_sensitivity'] == 0.7
        assert params['interaction_frequency'] == 0.5
        assert params['priority_weight']['high'] == 1.0
        assert params['priority_weight']['medium'] == 0.7
        assert params['priority_weight']['low'] == 0.4

    @pytest.mark.asyncio
    async def test_start_stop(self, feedback_loop):
        await feedback_loop.start()
        assert feedback_loop.is_running
        assert feedback_loop._feedback_task is not None
        await feedback_loop.stop()
        assert not feedback_loop.is_running

    @pytest.mark.asyncio
    async def test_start_when_already_running(self, feedback_loop):
        await feedback_loop.start()
        await feedback_loop.start()
        assert feedback_loop.is_running
        await feedback_loop.stop()

    @pytest.mark.asyncio
    async def test_stop_when_not_running(self, feedback_loop):
        await feedback_loop.stop()
        assert not feedback_loop.is_running


class TestRecordBehavior:
    """Tests for recording behaviors."""

    def test_record_behavior(self, feedback_loop):
        feedback_loop.record_behavior(
            action='greet',
            message='Hello!',
            priority='high',
            user_response='Hi!',
            user_emotion='happy',
        )
        assert len(feedback_loop.behavior_records) == 1
        assert feedback_loop.stats['total_behaviors'] == 1
        record = feedback_loop.behavior_records[0]
        assert record.action == 'greet'
        assert record.user_response == 'Hi!'
        assert record.user_emotion == 'happy'

    def test_record_behavior_without_optional_fields(self, feedback_loop):
        feedback_loop.record_behavior(
            action='observe',
            message='Watching',
            priority='low',
        )
        assert len(feedback_loop.behavior_records) == 1
        record = feedback_loop.behavior_records[0]
        assert record.user_response is None
        assert record.user_emotion is None

    def test_record_behavior_limits_max_records(self, feedback_loop):
        feedback_loop.max_records = 3
        for i in range(5):
            feedback_loop.record_behavior(
                action='greet',
                message=f'Hi {i}',
                priority='low',
            )
        assert len(feedback_loop.behavior_records) == 3

    def test_get_behavior_history(self, feedback_loop):
        for i in range(5):
            feedback_loop.record_behavior(
                action='greet', message=f'Hi {i}', priority='low',
            )
        history = feedback_loop.get_behavior_history(limit=3)
        assert len(history) == 3
        for entry in history:
            assert 'action' in entry
            assert 'message' in entry
            assert 'timestamp' in entry


class TestEvaluateBehavior:
    """Tests for behavior evaluation."""

    @pytest.mark.asyncio
    async def test_evaluate_behavior_with_positive_response(self, feedback_loop):
        from ai.lifecycle.behavior_feedback_loop import BehaviorRecord
        now = datetime.now()
        record = BehaviorRecord(
            action='greet',
            message='Hello!',
            priority='high',
            timestamp=now,
            user_response='A long and thoughtful response',
            user_emotion='happy',
        )
        score = await feedback_loop.evaluate_behavior(record)
        assert score > 0.5
        assert score <= 1.0

    @pytest.mark.asyncio
    async def test_evaluate_behavior_no_response(self, feedback_loop):
        from ai.lifecycle.behavior_feedback_loop import BehaviorRecord
        record = BehaviorRecord(
            action='greet',
            message='Hello!',
            priority='low',
            timestamp=datetime.now(),
        )
        score = await feedback_loop.evaluate_behavior(record)
        assert score == 0.6  # 0.5 base + 0.1 time bonus

    @pytest.mark.asyncio
    async def test_evaluate_behavior_negative_emotion(self, feedback_loop):
        from ai.lifecycle.behavior_feedback_loop import BehaviorRecord
        record = BehaviorRecord(
            action='comfort',
            message='Feel better',
            priority='high',
            timestamp=datetime.now(),
            user_response='Still sad',
            user_emotion='sad',
        )
        score = await feedback_loop.evaluate_behavior(record)
        assert score == 0.5  # 0.5 base + 0.1 response - 0.2 emotion + 0.1 time

    @pytest.mark.asyncio
    async def test_evaluate_behavior_old_record(self, feedback_loop):
        from ai.lifecycle.behavior_feedback_loop import BehaviorRecord
        old_time = datetime.now() - timedelta(hours=2)
        record = BehaviorRecord(
            action='greet',
            message='Hello!',
            priority='low',
            timestamp=old_time,
            user_response='Hi!',
            user_emotion='neutral',
            effectiveness_score=0.0,
        )
        score = await feedback_loop.evaluate_behavior(record)
        assert score >= 0.0

    @pytest.mark.asyncio
    async def test_evaluate_behaviors_catches_evaluation_errors(self, feedback_loop):
        from ai.lifecycle.behavior_feedback_loop import BehaviorRecord
        record = BehaviorRecord(
            action='greet', message='Hi', priority='low',
            timestamp=datetime.now(), user_response='Hi!',
        )
        feedback_loop.behavior_records.append(record)
        with patch.object(feedback_loop, 'evaluate_behavior', AsyncMock(side_effect=Exception('Eval error'))):
            await feedback_loop._process_feedback()  # should not raise
        assert feedback_loop.stats['evaluated_behaviors'] == 0

    @pytest.mark.asyncio
    async def test_evaluate_behaviors_skips_already_evaluated(self, feedback_loop):
        from ai.lifecycle.behavior_feedback_loop import BehaviorRecord
        evaluated = BehaviorRecord(
            action='greet', message='Hi', priority='low',
            timestamp=datetime.now(),
            effectiveness_score=0.8, outcome='success',
        )
        unevaluated = BehaviorRecord(
            action='comfort', message='There', priority='high',
            timestamp=datetime.now(),
            effectiveness_score=0.0, outcome='unknown',
        )
        feedback_loop.behavior_records = [evaluated, unevaluated]
        await feedback_loop._evaluate_behaviors()
        assert evaluated.effectiveness_score == 0.8  # unchanged
        assert unevaluated.effectiveness_score != 0.0  # now evaluated


class TestAnalyzePatterns:
    """Tests for behavior pattern analysis."""

    @pytest.mark.asyncio
    async def test_analyze_patterns_creates_patterns(self, feedback_loop):
        from ai.lifecycle.behavior_feedback_loop import BehaviorRecord
        now = datetime.now()
        for i in range(3):
            feedback_loop.behavior_records.append(BehaviorRecord(
                action='greet', message=f'Hi {i}', priority='medium',
                timestamp=now, effectiveness_score=0.8, outcome='success',
            ))
        feedback_loop.stats['evaluated_behaviors'] = 3
        feedback_loop.stats['successful_behaviors'] = 3
        await feedback_loop._analyze_patterns()
        assert 'greet_default' in feedback_loop.behavior_patterns
        pattern = feedback_loop.behavior_patterns['greet_default']
        assert pattern.success_rate == 1.0
        assert pattern.avg_effectiveness == pytest.approx(0.8)

    @pytest.mark.asyncio
    async def test_analyze_patterns_skips_insufficient_data(self, feedback_loop):
        from ai.lifecycle.behavior_feedback_loop import BehaviorRecord
        feedback_loop.behavior_records.append(BehaviorRecord(
            action='comfort', message='There', priority='high',
            timestamp=datetime.now(), effectiveness_score=0.5, outcome='neutral',
        ))
        await feedback_loop._analyze_patterns()
        assert 'comfort_default' not in feedback_loop.behavior_patterns

    @pytest.mark.asyncio
    async def test_analyze_patterns_updates_existing(self, feedback_loop):
        from ai.lifecycle.behavior_feedback_loop import BehaviorRecord, BehaviorPattern
        now = datetime.now()
        feedback_loop.behavior_patterns['greet_default'] = BehaviorPattern(
            action='greet', context='default',
            success_rate=0.5, avg_effectiveness=0.5, count=3,
            last_updated=now - timedelta(hours=1),
        )
        for i in range(5):
            feedback_loop.behavior_records.append(BehaviorRecord(
                action='greet', message=f'Hi {i}', priority='medium',
                timestamp=now, effectiveness_score=0.9, outcome='success',
            ))
        feedback_loop.stats['evaluated_behaviors'] = 5
        feedback_loop.stats['successful_behaviors'] = 5
        await feedback_loop._analyze_patterns()
        pattern = feedback_loop.behavior_patterns['greet_default']
        assert pattern.success_rate == 1.0
        assert pattern.count == 5


class TestUpdateStrategy:
    """Tests for strategy parameter updates."""

    @pytest.mark.asyncio
    async def test_update_strategy_low_success_rate(self, feedback_loop):
        from ai.lifecycle.behavior_feedback_loop import BehaviorPattern
        now = datetime.now()
        feedback_loop.behavior_patterns['greet_default'] = BehaviorPattern(
            action='greet', context='default',
            success_rate=0.3, avg_effectiveness=0.3, count=10,
            last_updated=now,
        )
        initial_threshold = feedback_loop.strategy_parameters['greet_threshold']
        await feedback_loop._update_strategy()
        assert feedback_loop.strategy_parameters['greet_threshold'] > initial_threshold
        assert feedback_loop.stats['strategy_updates'] == 1

    @pytest.mark.asyncio
    async def test_update_strategy_high_success_rate(self, feedback_loop):
        from ai.lifecycle.behavior_feedback_loop import BehaviorPattern
        now = datetime.now()
        feedback_loop.behavior_patterns['greet_default'] = BehaviorPattern(
            action='greet', context='default',
            success_rate=0.9, avg_effectiveness=0.9, count=10,
            last_updated=now,
        )
        initial_threshold = feedback_loop.strategy_parameters['greet_threshold']
        await feedback_loop._update_strategy()
        assert feedback_loop.strategy_parameters['greet_threshold'] < initial_threshold
        assert feedback_loop.stats['strategy_updates'] == 1

    @pytest.mark.asyncio
    async def test_update_strategy_comfort_low_success(self, feedback_loop):
        from ai.lifecycle.behavior_feedback_loop import BehaviorPattern
        now = datetime.now()
        feedback_loop.behavior_patterns['comfort_default'] = BehaviorPattern(
            action='comfort', context='default',
            success_rate=0.2, avg_effectiveness=0.2, count=10,
            last_updated=now,
        )
        await feedback_loop._update_strategy()
        assert feedback_loop.strategy_parameters['comfort_sensitivity'] <= 1.0

    @pytest.mark.asyncio
    async def test_update_strategy_insufficient_data(self, feedback_loop):
        from ai.lifecycle.behavior_feedback_loop import BehaviorPattern
        now = datetime.now()
        feedback_loop.behavior_patterns['greet_default'] = BehaviorPattern(
            action='greet', context='default',
            success_rate=0.3, avg_effectiveness=0.3, count=3,
            last_updated=now,
        )
        await feedback_loop._update_strategy()
        assert feedback_loop.stats['strategy_updates'] == 0  # count <= 5


class TestStoreLearningResults:
    """Tests for storing learning results."""

    @pytest.mark.asyncio
    async def test_store_learning_results_calls_memory_manager(self, feedback_loop, mock_memory_manager):
        await feedback_loop._store_learning_results()
        mock_memory_manager.store_experience.assert_called_once()

    @pytest.mark.asyncio
    async def test_store_learning_results_without_memory_method(self, feedback_loop, mock_memory_manager):
        del mock_memory_manager.store_experience
        await feedback_loop._store_learning_results()  # should not raise

    @pytest.mark.asyncio
    async def test_store_learning_results_handles_exception(self, feedback_loop, mock_memory_manager):
        mock_memory_manager.store_experience.side_effect = Exception('Storage error')
        await feedback_loop._store_learning_results()  # should not raise


class TestCalculateInterval:
    """Tests for interval calculation."""

    def test_interval_many_records(self, feedback_loop):
        feedback_loop.behavior_records = list(range(101))
        interval = feedback_loop._calculate_interval()
        assert interval == feedback_loop.min_loop_interval

    def test_interval_moderate_records(self, feedback_loop):
        feedback_loop.behavior_records = list(range(60))
        interval = feedback_loop._calculate_interval()
        assert interval == feedback_loop.loop_interval

    def test_interval_few_records(self, feedback_loop):
        feedback_loop.behavior_records = list(range(10))
        interval = feedback_loop._calculate_interval()
        assert interval == feedback_loop.max_loop_interval


class TestStatsAndGetters:
    """Tests for statistics and getter methods."""

    def test_get_patterns(self, feedback_loop):
        patterns = feedback_loop.get_patterns()
        assert isinstance(patterns, dict)

    def test_get_strategy_parameters(self, feedback_loop):
        params = feedback_loop.get_strategy_parameters()
        assert 'greet_threshold' in params
        assert 'comfort_sensitivity' in params

    def test_get_stats(self, feedback_loop):
        stats = feedback_loop.get_stats()
        assert 'is_running' in stats
        assert 'total_behaviors' in stats
        assert 'evaluated_behaviors' in stats
        assert 'success_rate' in stats
        assert 'patterns_count' in stats

    def test_get_stats_success_rate_calculation(self, feedback_loop):
        feedback_loop.stats['evaluated_behaviors'] = 10
        feedback_loop.stats['successful_behaviors'] = 7
        stats = feedback_loop.get_stats()
        assert stats['success_rate'] == 0.7

    def test_get_stats_success_rate_zero_division(self, feedback_loop):
        stats = feedback_loop.get_stats()
        assert stats['success_rate'] == 0.0
