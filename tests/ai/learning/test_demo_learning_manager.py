import sys
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

_MODULE_MOCKS = {
    'ai.memory.ham_memory.ham_manager': MagicMock(),
    'ai.hsp.connector': MagicMock(),
    'shared.utils.cleanup_utils': MagicMock(),
    'yaml': MagicMock(),
}
for mod_name, mock in _MODULE_MOCKS.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mock


@pytest.fixture
def demo_manager(tmp_path):
    from apps.backend.src.ai.learning.demo_learning_manager import DemoLearningManager
    config_data = {
        'demo_credentials': {
            'auto_learning': {'enabled': True, 'storage': {'path': str(tmp_path)}},
            'auto_cleanup': {
                'enabled': True, 'triggers': ['session_end'],
                'cleanup_targets': ['temporary_files'],
                'retention': {'cache_data': 1, 'important_logs': 7, 'demo_data': 30},
            },
        },
        'key_detection': {
            'demo_patterns': ['^demo_'],
            'on_demo_key_detected': [{'action': 'enable_demo_mode', 'priority': 1}],
        },
        'mock_services': {'enabled': True},
    }
    with patch.object(DemoLearningManager, '_load_config', return_value=config_data):
        manager = DemoLearningManager(config_path=str(tmp_path / 'nonexistent.yaml'))
    manager.storage_path = tmp_path
    return manager


class TestDemoLearningManagerInit:
    def test_init_default_config(self):
        from apps.backend.src.ai.learning.demo_learning_manager import DemoLearningManager
        config_data = {
            'demo_credentials': {
                'auto_learning': {'enabled': True, 'storage': {'path': 'data/test_demo'}},
            },
            'key_detection': {'demo_patterns': ['^test_']},
            'mock_services': {'enabled': False},
        }
        with patch.object(DemoLearningManager, '_load_config', return_value=config_data), \
             patch('pathlib.Path.mkdir', return_value=None):
            manager = DemoLearningManager(config_path='test_config.yaml')
        assert manager.demo_mode is False
        assert manager.initialized is False
        assert manager.training_configs == {}
        assert manager.model_registry == {}


class TestDemoLearningManagerModelManagement:
    async def test_start_learning(self, demo_manager):
        result = await demo_manager.start_learning('model_1', {'lr': 0.01})
        assert result == {'status': 'completed'}
        assert 'model_1' in demo_manager.model_registry
        assert demo_manager.model_registry['model_1']['status'] == 'trained'
    async def test_stop_learning_existing_model(self, demo_manager):
        demo_manager.model_registry['model_1'] = {'status': 'trained'}
        result = await demo_manager.stop_learning('model_1')
        assert result is True
        assert demo_manager.model_registry['model_1']['status'] == 'stopped'
    async def test_stop_learning_nonexistent_model(self, demo_manager):
        result = await demo_manager.stop_learning('nonexistent')
        assert result is False

    def test_get_model_status(self, demo_manager):
        demo_manager.model_registry['model_x'] = {'status': 'trained', 'accuracy': 0.95}
        status = demo_manager.get_model_status('model_x')
        assert status == {'status': 'trained', 'accuracy': 0.95}

    def test_get_model_status_nonexistent(self, demo_manager):
        assert demo_manager.get_model_status('ghost') is None

    def test_list_models(self, demo_manager):
        demo_manager.model_registry['a'] = {}
        demo_manager.model_registry['b'] = {}
        models = demo_manager.list_models()
        assert sorted(models) == ['a', 'b']


class TestDemoLearningManagerCredentials:
    def test_detect_demo_credentials_match(self, demo_manager):
        assert demo_manager.detect_demo_credentials({'key': 'demo_12345'}) is True

    def test_detect_demo_credentials_no_match(self, demo_manager):
        assert demo_manager.detect_demo_credentials({'key': 'production_key'}) is False

    def test_detect_demo_credentials_non_string(self, demo_manager):
        assert demo_manager.detect_demo_credentials({'key': 12345}) is False

    def test_detect_demo_credentials_empty(self, demo_manager):
        assert demo_manager.detect_demo_credentials({}) is False


class TestDemoLearningManagerActivation:
    async def test_activate_demo_mode_with_demo_credentials(self, demo_manager):
        assert demo_manager.demo_mode is False
        await demo_manager.activate_demo_mode({'key': 'demo_abcdef'})
        assert demo_manager.demo_mode is True
    async def test_activate_demo_mode_without_demo_credentials(self, demo_manager):
        await demo_manager.activate_demo_mode({'key': 'real_key'})
        assert demo_manager.demo_mode is False
    async def test_activate_demo_mode_creates_flag_file(self, demo_manager, tmp_path):
        await demo_manager.activate_demo_mode({'key': 'demo_xyz'})
        flag_file = demo_manager.storage_path / 'demo_mode.flag'
        assert flag_file.exists()


class TestDemoLearningManagerRecording:
    async def test_record_user_interaction_only_in_demo_mode(self, demo_manager):
        await demo_manager.record_user_interaction('test_action', {}, 'success')
        assert len(demo_manager.learning_data['user_interactions']) == 0
    async def test_record_user_interaction_in_demo_mode(self, demo_manager):
        demo_manager.demo_mode = True
        await demo_manager.record_user_interaction('test_action', {'key': 'val'}, 'success')
        assert len(demo_manager.learning_data['user_interactions']) == 1
        entry = demo_manager.learning_data['user_interactions'][0]
        assert entry['action'] == 'test_action'
        assert entry['result'] == 'success'
    async def test_record_error_pattern_only_in_demo_mode(self, demo_manager):
        await demo_manager.record_error_pattern('type_a', 'msg', {}, 'fix')
        assert len(demo_manager.learning_data['error_patterns']) == 0
    async def test_record_error_pattern_in_demo_mode(self, demo_manager):
        demo_manager.demo_mode = True
        await demo_manager.record_error_pattern('type_a', 'error msg', {'ctx': 1}, 'restart')
        assert len(demo_manager.learning_data['error_patterns']) == 1
        key = 'type_a-error msg'
        assert demo_manager.learning_data['error_patterns'][key]['frequency'] == 1
    async def test_record_error_pattern_increments_frequency(self, demo_manager):
        demo_manager.demo_mode = True
        await demo_manager.record_error_pattern('type_a', 'msg', {}, 'fix')
        await demo_manager.record_error_pattern('type_a', 'msg', {}, 'fix')
        key = 'type_a-msg'
        assert demo_manager.learning_data['error_patterns'][key]['frequency'] == 2
    async def test_learning_data_capacity_limit(self, demo_manager):
        demo_manager.demo_mode = True
        for i in range(1200):
            await demo_manager.record_user_interaction(f'action_{i}', {}, 'success')
        assert len(demo_manager.learning_data['user_interactions']) <= 1000


class TestDemoLearningManagerInsights:
    async def test_get_learning_insights_not_in_demo_mode(self, demo_manager):
        insights = await demo_manager.get_learning_insights()
        assert insights == {}
    async def test_get_learning_insights_in_demo_mode(self, demo_manager):
        demo_manager.demo_mode = True
        demo_manager.learning_data['user_interactions'] = [
            {'action': 'click', 'result': 'success', 'timestamp': '2026-01-01T00:00:00'},
        ]
        demo_manager.learning_data['performance_metrics'] = [
            {'memory_usage': {'percent': 50}, 'storage_usage': {'total_mb': 100}},
        ]
        insights = await demo_manager.get_learning_insights()
        assert insights['demo_mode'] is True
        assert insights['interactions']['total'] == 1
        assert insights['performance']['samples'] == 1
    async def test_get_learning_insights_recommendations_high_memory(self, demo_manager):
        demo_manager.demo_mode = True
        demo_manager.learning_data['performance_metrics'] = [
            {'memory_usage': {'percent': 95}, 'storage_usage': {'total_mb': 200}},
        ]
        insights = await demo_manager.get_learning_insights()
        assert len(insights['recommendations']) > 0
    async def test_get_learning_insights_recommendations_low_success(self, demo_manager):
        demo_manager.demo_mode = True
        for i in range(10):
            result = 'success' if i < 3 else 'failure'
            demo_manager.learning_data['user_interactions'].append(
                {'action': 'op', 'result': result, 'timestamp': f'2026-01-01T00:00:{i:02d}'}
            )
        insights = await demo_manager.get_learning_insights()
        assert any('成功' in r or '成功率' in r for r in insights['recommendations'])


class TestDemoLearningManagerShutdown:
    async def test_shutdown_not_in_demo_mode(self, demo_manager):
        await demo_manager.shutdown()
        assert demo_manager.demo_mode is False
    async def test_shutdown_in_demo_mode_saves_data(self, demo_manager, tmp_path):
        demo_manager.demo_mode = True
        await demo_manager.shutdown()
        assert demo_manager.demo_mode is False


class TestDemoLearningManagerInternal:
    def test_get_memory_usage(self, demo_manager):
        result = demo_manager._get_memory_usage()
        assert isinstance(result, dict)

    def test_get_storage_usage(self, demo_manager, tmp_path):
        (tmp_path / 'test_file.txt').write_text('hello')
        result = demo_manager._get_storage_usage()
        assert result['file_count'] >= 1
        assert result['total_bytes'] >= 5

    def test_get_active_connections(self, demo_manager):
        assert demo_manager._get_active_connections() == 0
    async def test_collect_learning_data(self, demo_manager):
        demo_manager.demo_mode = True
        await demo_manager._collect_learning_data()
        assert len(demo_manager.learning_data['performance_metrics']) == 1
