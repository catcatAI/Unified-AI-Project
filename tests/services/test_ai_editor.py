# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3+]
# =============================================================================

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def editor():
    from apps.backend.src.services.ai_editor import AIEditorService
    return AIEditorService()


@pytest.fixture
def data_processor():
    from apps.backend.src.services.ai_editor import DataProcessor
    return DataProcessor()


class TestAIEditorServiceInit:

    def test_initialization(self, editor):
        assert editor.virtual_input_service is not None
        assert editor.sandbox_executor is not None
        assert editor.data_processor is not None
        assert editor.memory_manager is None

    def test_set_memory_manager(self, editor):
        mock_memory = MagicMock()
        editor.set_memory_manager(mock_memory)
        assert editor.memory_manager is mock_memory


class TestAIEditorServiceProcessText:

    def test_process_text_content(self, editor):
        result = editor.process_text_content('Hello world this is a test')
        assert result['data_type'] == 'text'
        assert result['processed_data']['word_count'] == 6
        assert result['processed_data']['raw_text'] == 'Hello world this is a test'

    def test_process_text_content_with_rules(self, editor):
        result = editor.process_text_content('Hello', transformation_rules={'uppercase': True})
        assert result['transformation_rules_applied'] == {'uppercase': True}


class TestAIEditorServiceProcessCode:

    def test_process_code_content(self, editor):
        code = 'def foo():\n    pass\n'
        result = editor.process_code_content(code)
        assert result['data_type'] == 'code'
        assert result['processed_data']['line_count'] == 2

    def test_process_code_content_empty(self, editor):
        result = editor.process_code_content('')
        assert result['processed_data']['line_count'] == 0


class TestAIEditorServiceProcessStructured:

    def test_process_structured_data_dict(self, editor):
        data = {'key': 'value', 'nested': {'a': 1}}
        result = editor.process_structured_data(data)
        assert result['data_type'] == 'structured'
        assert result['processed_data']['raw_structure'] == data

    def test_process_structured_data_list(self, editor):
        data = [1, 2, 3]
        result = editor.process_structured_data(data)
        assert result['data_type'] == 'structured'


class TestAIEditorServiceProcessApplication:

    def test_process_application_data(self, editor):
        data = {'ui_elements': [{'id': 'btn1', 'type': 'button'}]}
        result = editor.process_application_data(data)
        assert result['data_type'] == 'application'
        assert len(result['processed_data']['ui_elements']) == 1

    def test_process_application_data_empty(self, editor):
        result = editor.process_application_data({})
        assert result['processed_data']['ui_elements'] == []


class TestAIEditorServiceSandbox:

    def test_execute_transformation_script(self, editor):
        mock_result = MagicMock()
        editor.sandbox_executor.run = MagicMock(return_value=(mock_result, None))
        result = editor.execute_data_transformation_script('script', {'param': 1})
        assert 'execution_result' in result
        assert result['execution_result'] is mock_result

    def test_execute_transformation_script_error(self, editor):
        editor.sandbox_executor.run = MagicMock(return_value=(None, 'error'))
        with pytest.raises(Exception, match='Sandbox execution failed'):
            editor.execute_data_transformation_script('bad_script', {})


class TestAIEditorServiceMemory:

    def test_get_processed_data_from_memory_no_manager(self, editor):
        result = editor.get_processed_data_from_memory('mem_id')
        assert result is None

    def test_get_processed_data_from_memory_with_manager(self, editor):
        mock_memory = MagicMock()
        mock_memory.recall_gist.return_value = {'data': 'test'}
        editor.set_memory_manager(mock_memory)
        result = editor.get_processed_data_from_memory('mem_id')
        assert result == {'data': 'test'}


class TestDataProcessor:

    def test_unsupported_data_type(self, data_processor):
        with pytest.raises(ValueError, match='Unsupported data type'):
            data_processor.process_data('data', 'unsupported_type')

    def test_process_text(self, data_processor):
        result = data_processor.process_data('hello world', 'text')
        assert result['processed_data']['word_count'] == 2

    def test_process_code(self, data_processor):
        result = data_processor.process_data('a\nb\nc', 'code')
        assert result['processed_data']['line_count'] == 3

    def test_process_structured(self, data_processor):
        result = data_processor.process_data({'a': 1}, 'structured')
        assert result['processed_data']['raw_structure'] == {'a': 1}

    def test_process_application(self, data_processor):
        result = data_processor.process_data({'ui_elements': ['btn1']}, 'application')
        assert result['processed_data']['ui_elements'] == ['btn1']

    def test_generate_summary(self, data_processor):
        result = data_processor._generate_summary('Hello world this is a test')
        assert result == 'Hello world this is a test'[:50]

    def test_extract_keywords(self, data_processor):
        result = data_processor._extract_keywords('one two three four five six')
        assert result == ['one', 'two', 'three', 'four', 'five']
