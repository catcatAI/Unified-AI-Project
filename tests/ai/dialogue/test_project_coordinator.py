"""Tests for apps.backend.src.ai.dialogue.project_coordinator"""
import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call

# Module was removed in architecture cleanup (Phase 1)
try:
    from ai.dialogue.project_coordinator import ProjectCoordinator
except ImportError:
    pytest.skip("ai.dialogue module was removed (Phase 1 architecture cleanup)", allow_module_level=True)


@pytest.fixture
def mock_angela_config():
    mock = MagicMock()
    mock.get_authority.return_value = {
        'fallback_patterns': {
            'task_decompose': ['task', 'processing', '幫我', '做一個', '規劃'],
            'character_card': ['character', '角色卡', '人物', '建立角色'],
            'research': ['research', '研究', '搜尋', '調查'],
        }
    }
    return mock


@pytest.fixture
def coordinator(mock_angela_config):
    with patch('core.config_loader.get_angela_config',
               return_value=mock_angela_config):
        pc = ProjectCoordinator()
        return pc


class TestInit:
    def test_default_init(self, coordinator):
        assert coordinator.ai_id == 'project_coordinator'
        assert coordinator.turn_timeout_seconds == 120
        assert coordinator.config == {}
        assert coordinator.task_completion_events == {}
        assert coordinator.task_results == {}
        assert coordinator.prompts == {}

    def test_init_with_custom_timeout(self, mock_angela_config):
        with patch('core.config_loader.get_angela_config',
                   return_value=mock_angela_config):
            pc = ProjectCoordinator(
                dialogue_manager_config={'turn_timeout_seconds': 300}
            )
            assert pc.turn_timeout_seconds == 300

    def test_init_with_hsp_connector(self, mock_angela_config):
        hsp_mock = MagicMock()
        hsp_mock.ai_id = 'custom_ai'
        with patch('core.config_loader.get_angela_config',
                   return_value=mock_angela_config):
            pc = ProjectCoordinator(hsp_connector=hsp_mock)
            assert pc.ai_id == 'custom_ai'

    def test_init_with_personality_manager(self, mock_angela_config):
        pm_mock = MagicMock()
        with patch('core.config_loader.get_angela_config',
                   return_value=mock_angela_config):
            pc = ProjectCoordinator(personality_manager=pm_mock)
            assert pc.personality_manager is pm_mock

    def test_init_with_memory_manager(self, mock_angela_config):
        mm_mock = MagicMock()
        with patch('core.config_loader.get_angela_config',
                   return_value=mock_angela_config):
            pc = ProjectCoordinator(memory_manager=mm_mock)
            assert pc.memory_manager is mm_mock


class TestDetectCapabilityType:
    @pytest.mark.parametrize('capability,expected', [
        ('web_search', 'web_search'),
        ('search_tool', 'web_search'),
        ('Web_Scraper', 'web_search'),
        ('creative_writing', 'creative'),
        ('write_article', 'creative'),
        ('角色扮演', 'creative'),
        ('document_builder', 'document'),
        ('doc_processing', 'document'),
        ('整理文档', 'document'),
        ('code_executor', 'code'),
        ('programming_task', 'code'),
        ('unknown_tool', 'hsp'),
        ('', 'hsp'),
    ])
    def test_detect(self, coordinator, capability, expected):
        assert coordinator._detect_capability_type(capability) == expected


class TestCleanJson:
    def test_extract_array(self, coordinator):
        text = 'prefix\n[{"key": "value"}]\nsuffix'
        assert coordinator._clean_json_response(text) == '[{"key": "value"}]'

    def test_extract_object(self, coordinator):
        text = 'before {"a": 1} after'
        assert coordinator._clean_json_response(text) == '{"a": 1}'

    def test_no_json(self, coordinator):
        text = 'plain text without json'
        assert coordinator._clean_json_response(text) == text

    def test_nested_brackets(self, coordinator):
        text = '{"outer": {"inner": "v"}}'
        assert coordinator._clean_json_response(text) == text


class TestSubstituteDependencies:
    def test_basic_substitution(self, coordinator):
        params = {'query': 'result:  < output_of_task_0 >  continue'}
        results = {0: 'important_data'}
        result = coordinator._substitute_dependencies(params, results)
        assert result['query'] == 'result: important_data continue'

    def test_no_substitution(self, coordinator):
        params = {'query': 'plain text', 'other': 42}
        result = coordinator._substitute_dependencies(params, {0: 'x'})
        assert result['query'] == 'plain text'
        assert result['other'] == 42

    def test_non_string_param(self, coordinator):
        params = {'count': 5, 'items': ['a', 'b']}
        result = coordinator._substitute_dependencies(params, {0: 'x'})
        assert result['count'] == 5
        assert result['items'] == ['a', 'b']

    def test_missing_task_index(self, coordinator):
        params = {'query': '  < output_of_task_5 >  data'}
        results = {0: 'found'}
        result = coordinator._substitute_dependencies(params, results)
        assert result['query'] == '  data'


class TestFallbackDecompose:
    def test_task_pattern(self, coordinator):
        result = coordinator._fallback_decompose('process this task')
        assert len(result) == 1
        assert result[0]['capability_needed'] == 'creative_writing_v1'

    def test_character_card_pattern(self, coordinator):
        result = coordinator._fallback_decompose('create a character')
        assert len(result) == 2
        assert result[0]['task_parameters']['task_type'] == 'character_card'
        assert result[1]['task_parameters']['task_type'] == 'character_background'

    def test_research_pattern(self, coordinator):
        result = coordinator._fallback_decompose('research this topic')
        assert len(result) == 2
        assert result[0]['capability_needed'] == 'web_search_v1'
        assert result[1]['capability_needed'] == 'creative_writing_v1'

    def test_default_fallback(self, coordinator):
        result = coordinator._fallback_decompose('hello world')
        assert len(result) == 1
        assert result[0]['capability_needed'] == 'creative_writing_v1'

    def test_empty_query(self, coordinator):
        result = coordinator._fallback_decompose('')
        assert len(result) == 1


class TestDetectComplexTask:
    @patch('ai.dialogue.project_coordinator._intent_registry', None)
    def test_detect_by_chinese_keyword(self, coordinator):
        assert coordinator._detect_complex_task('生成一個報告') is True

    @patch('ai.dialogue.project_coordinator._intent_registry', None)
    def test_detect_by_long_query(self, coordinator):
        assert coordinator._detect_complex_task('a' * 51) is True

    @patch('ai.dialogue.project_coordinator._intent_registry', None)
    def test_simple_short_query(self, coordinator):
        assert coordinator._detect_complex_task('hi') is False

    @patch('ai.dialogue.project_coordinator._intent_registry', None)
    def test_empty_query(self, coordinator):
        assert coordinator._detect_complex_task('') is False

    @patch('ai.dialogue.project_coordinator._intent_registry')
    def test_detect_via_registry(self, mock_registry, coordinator):
        mock_registry.detect_complex_task.return_value = True
        assert coordinator._detect_complex_task('anything') is True

    @patch('ai.dialogue.project_coordinator._intent_registry')
    def test_detect_via_registry_false(self, mock_registry, coordinator):
        mock_registry.detect_complex_task.return_value = False
        assert coordinator._detect_complex_task('anything') is False


class TestHandleTaskResult:
    def test_handle_success(self, coordinator):
        corr_id = 'corr-001'
        event = asyncio.Event()
        coordinator.task_completion_events[corr_id] = event

        result_payload = {'status': 'success', 'payload': {'data': 'done'}}
        envelope = {'correlation_id': corr_id}
        coordinator.handle_task_result(result_payload, 'sender', envelope)

        assert coordinator.task_results[corr_id] == {'data': 'done'}
        assert event.is_set()

    def test_handle_failure(self, coordinator):
        corr_id = 'corr-002'
        event = asyncio.Event()
        coordinator.task_completion_events[corr_id] = event

        result_payload = {
            'status': 'failure',
            'error_details': {'error_message': 'broken'},
        }
        envelope = {'correlation_id': corr_id}
        coordinator.handle_task_result(result_payload, 'sender', envelope)

        assert coordinator.task_results[corr_id] == {
            'error': {'error_message': 'broken'}
        }
        assert event.is_set()

    def test_handle_no_correlation_id(self, coordinator):
        result_payload = {'status': 'success', 'payload': {}}
        envelope = {}
        coordinator.handle_task_result(result_payload, 'sender', envelope)
        assert len(coordinator.task_results) == 0

    def test_handle_unknown_correlation_id(self, coordinator):
        result_payload = {'status': 'success', 'payload': {'x': 1}}
        envelope = {'correlation_id': 'nonexistent'}
        coordinator.handle_task_result(result_payload, 'sender', envelope)
        assert 'nonexistent' in coordinator.task_results
        assert coordinator.task_results['nonexistent'] == {'x': 1}


class TestExecuteWebSearch:
    async def test_success(self, coordinator):
        web_mock = MagicMock()
        web_mock.search.return_value = ['r1', 'r2']
        coordinator._web_search = web_mock

        result = await coordinator._execute_web_search(
            {'query': 'test', 'num_results': 5}
        )
        assert result['count'] == 2
        assert result['query'] == 'test'
        web_mock.search.assert_called_once_with('test', num_results=5)
    async def test_with_search_query_param(self, coordinator):
        web_mock = MagicMock()
        web_mock.search.return_value = []
        coordinator._web_search = web_mock

        result = await coordinator._execute_web_search(
            {'search_query': 'fallback'}
        )
        assert result['count'] == 0
        web_mock.search.assert_called_once_with('fallback', num_results=5)
    async def test_tool_unavailable(self, coordinator):
        coordinator._web_search = None
        with patch('core.tools.web_search_tool.WebSearchTool',
                   side_effect=ImportError('No module')):
            result = await coordinator._execute_web_search({'query': 'test'})
            assert 'error' in result


class TestExecuteDocumentTask:
    async def test_success(self, coordinator):
        doc_builder = AsyncMock()
        doc_result = MagicMock(
            full_text='doc text',
            segments=['s1', 's2'],
            successful_segments=2,
            format_id='fmt-1',
            task_id='t-1',
        )
        doc_builder.build.return_value = doc_result
        coordinator._document_builder = doc_builder

        result = await coordinator._execute_document_task(
            {'query': 'write'}, 'document'
        )
        assert result['full_text'] == 'doc text'
        assert result['segments'] == 2
        assert result['successful'] == 2
        assert result['format_id'] == 'fmt-1'
    async def test_no_query(self, coordinator):
        result = await coordinator._execute_document_task({}, 'document')
        assert 'error' in result
    async def test_task_type_creative(self, coordinator):
        doc_builder = AsyncMock()
        doc_builder.build.return_value = MagicMock(
            full_text='creative', segments=[], successful_segments=0,
            format_id=None, task_id=None,
        )
        coordinator._document_builder = doc_builder

        result = await coordinator._execute_document_task(
            {'prompt': 'write story'}, 'creative'
        )
        assert result['full_text'] == 'creative'


class TestExecuteLLM:
    async def test_direct_llm_call(self, coordinator):
        llm_mock = AsyncMock()
        llm_mock.generate_text.return_value = 'llm response'
        with patch.object(
            coordinator, '_ensure_llm_service', AsyncMock(return_value=llm_mock)
        ):
            result = await coordinator._execute_llm_direct({'prompt': 'hi'})
            assert result['text'] == 'llm response'
    async def test_with_query_param(self, coordinator):
        llm_mock = AsyncMock()
        llm_mock.generate_text.return_value = 'response'
        with patch.object(
            coordinator, '_ensure_llm_service', AsyncMock(return_value=llm_mock)
        ):
            result = await coordinator._execute_llm_direct({'query': 'what'})
            assert result['text'] == 'response'
    async def test_empty_prompt(self, coordinator):
        llm_mock = AsyncMock()
        llm_mock.generate_text.return_value = ''
        with patch.object(
            coordinator, '_ensure_llm_service', AsyncMock(return_value=llm_mock)
        ):
            result = await coordinator._execute_llm_direct({'prompt': ''})
            assert result['text'] == ''


class TestHandleAsDocumentTask:
    async def test_returns_full_text(self, coordinator):
        doc_builder = AsyncMock()
        doc_builder.build.return_value = MagicMock(full_text='generated text')
        coordinator._document_builder = doc_builder

        result = await coordinator._handle_as_document_task(
            'query', MagicMock()
        )
        assert result == 'generated text'
    async def test_empty_full_text(self, coordinator):
        doc_builder = AsyncMock()
        doc_builder.build.return_value = MagicMock(full_text=None)
        coordinator._document_builder = doc_builder

        result = await coordinator._handle_as_document_task(
            'query', MagicMock()
        )
        assert '抱歉' in result


class TestDecomposeUserIntent:
    async def test_decompose_returns_list(self, coordinator):
        llm_mock = AsyncMock()
        llm_mock.generate_text.return_value = json.dumps([
            {'capability_needed': 'search', 'task_parameters': {'q': 'test'},
             'task_description': 'search task'}
        ])
        result = await coordinator._decompose_user_intent_into_subtasks(
            'test query', [], llm_mock
        )
        assert len(result) == 1
        assert result[0]['capability_needed'] == 'search'
    async def test_decompose_empty_llm_response(self, coordinator):
        llm_mock = AsyncMock()
        llm_mock.generate_text.return_value = ''
        result = await coordinator._decompose_user_intent_into_subtasks(
            'test', [], llm_mock
        )
        assert result == []
    async def test_decompose_invalid_json(self, coordinator):
        llm_mock = AsyncMock()
        llm_mock.generate_text.return_value = 'not json'
        with patch.object(coordinator, '_detect_complex_task',
                          return_value=False):
            result = await coordinator._decompose_user_intent_into_subtasks(
                'simple', [], llm_mock
            )
            assert result == []
    async def test_decompose_invalid_json_with_complex_fallback(
        self, coordinator
    ):
        llm_mock = AsyncMock()
        llm_mock.generate_text.return_value = 'not json'
        with patch.object(coordinator, '_detect_complex_task',
                          return_value=True):
            with patch.object(coordinator, '_fallback_decompose',
                              return_value=[{'capability_needed': 'fallback'}]):
                result = await coordinator._decompose_user_intent_into_subtasks(
                    'complex task', [], llm_mock
                )
                assert result == [{'capability_needed': 'fallback'}]
    async def test_decompose_with_subtasks_key(self, coordinator):
        llm_mock = AsyncMock()
        llm_mock.generate_text.return_value = json.dumps({
            'subtasks': [
                {'capability_needed': 'search', 'task_parameters': {},
                 'task_description': 's1'},
            ]
        })
        result = await coordinator._decompose_user_intent_into_subtasks(
            'q', [], llm_mock
        )
        assert len(result) == 1
        assert result[0]['capability_needed'] == 'search'


class TestIntegrateSubtaskResults:
    async def test_integrate(self, coordinator):
        llm_mock = AsyncMock()
        llm_mock.generate_text.return_value = 'integrated response'
        result = await coordinator._integrate_subtask_results(
            'original query',
            {0: {'text': 'result1'}},
            llm_mock,
        )
        assert result == 'integrated response'
        llm_mock.generate_text.assert_called_once()
        call_args = llm_mock.generate_text.call_args[1]
        assert 'original query' in call_args['prompt']
        assert 'result1' in call_args['prompt']


class TestExecuteViaHSP:
    async def test_execute_via_hsp_success(self, coordinator):
        hsp_mock = AsyncMock()
        coordinator.hsp_connector = hsp_mock

        with patch.object(
            coordinator, 'task_completion_events',
            {'test-corr': asyncio.Event()},
        ):
            corr_id = 'test-corr'
            coordinator.task_results[corr_id] = {'result': 'done'}
            coordinator.task_completion_events[corr_id].set()

            result = await coordinator._execute_via_hsp(
                'some_cap', {'param': 1}
            )
    async def test_execute_no_hsp(self, coordinator):
        coordinator.hsp_connector = None
        result = await coordinator._execute_via_hsp('cap', {})
        assert 'error' in result
