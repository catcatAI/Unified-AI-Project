# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3+]
# =============================================================================

import sys
import unittest.mock as um
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


_MODULE_MOCKS = {
    'core.autonomous.state_matrix': MagicMock(),
    'core.engine.state_matrix_adapter': MagicMock(),
    'ai.security.ego_guard': MagicMock(),
    'services.angela_llm_service': MagicMock(),
}

for mod_name, mock in _MODULE_MOCKS.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mock


@pytest.fixture
def chat_service():
    from apps.backend.src.services.chat_service import ChatService
    service = ChatService()
    service.ego_guard = MagicMock()
    service.ego_guard.sanitize_prompt.return_value = ('hello', False)
    service.state_matrix = MagicMock()
    service.state_matrix.get_analysis.return_value = {'valence': 0.5}
    service.state_matrix.export_for_llm.return_value = {}
    return service


class TestChatServiceInit:

    def test_initialization(self):
        from apps.backend.src.services.chat_service import ChatService
        service = ChatService()
        assert service._initialized is True
        assert service._user_profiles == {}
        assert service._conversation_history == []
        assert service.pending_evolution_proposals == {}

    def test_initialized_flag(self):
        from apps.backend.src.services.chat_service import ChatService
        service = ChatService()
        assert service._initialized is True


class TestChatServiceGenerateResponse:

    async def test_generate_response_basic(self, chat_service):
        chat_service._call_llm = AsyncMock(return_value='Hello!')
        result = await chat_service.generate_response('hello', 'User')
        assert result == 'Hello!'

    async def test_generate_response_ego_violation(self, chat_service):
        chat_service.ego_guard.sanitize_prompt.return_value = ('bad content', True)
        result = await chat_service.generate_response('bad stuff', 'User')
        assert '安全' in result or '不當' in result

    async def test_generate_response_llm_error_fallback(self, chat_service):
        chat_service._call_llm = AsyncMock(return_value='fallback response')
        result = await chat_service.generate_response('hello', 'User')
        assert result == 'fallback response'

    async def test_generate_response_llm_manage_intent(self, chat_service):
        chat_service.ego_guard.sanitize_prompt.return_value = ('切換模型 gpt-4', False)
        chat_service._handle_llm_manage_intent = AsyncMock(return_value='演化提案已準備')
        result = await chat_service.generate_response('切換模型 gpt-4', 'User')
        assert '演化' in result


class TestChatServiceEvolution:

    async def test_evolution_proposal_confirm(self, chat_service):
        import types
        chat_service.pending_evolution_proposals['User'] = {
            'config_type': 'llm', 'proposed_updates': {'model': 'gpt-4'},
        }
        mock_mutator = MagicMock(apply_mutation=MagicMock(return_value=True))
        mock_bootstrap = MagicMock()
        mock_src = types.ModuleType('src')
        mock_core = types.ModuleType('src.core')
        mock_sys = types.ModuleType('src.core.system')
        mock_evo = types.ModuleType('src.core.system.evolution')
        mock_cfg = types.ModuleType('src.core.system.evolution.config_mutator')
        mock_cfg.ConfigMutator = MagicMock(return_value=mock_mutator)
        mock_evo.config_mutator = mock_cfg
        mock_bs = types.ModuleType('src.core.system.bootstrap')
        mock_bs.get_bootstrap_manager = MagicMock(return_value=mock_bootstrap)
        mock_sys.bootstrap = mock_bs
        mock_sys.evolution = mock_evo
        mock_core.system = mock_sys
        mock_src.core = mock_core
        with patch.dict('sys.modules', {
            'src': mock_src, 'src.core': mock_core, 'src.core.system': mock_sys,
            'src.core.system.evolution': mock_evo,
            'src.core.system.evolution.config_mutator': mock_cfg,
            'src.core.system.bootstrap': mock_bs,
        }):
            result = await chat_service._handle_evolution_proposal('User', '確認')
        assert '成功' in result
        assert 'User' not in chat_service.pending_evolution_proposals

    async def test_evolution_proposal_cancel(self, chat_service):
        chat_service.pending_evolution_proposals['User'] = {
            'config_type': 'llm', 'proposed_updates': {},
        }
        result = await chat_service._handle_evolution_proposal('User', '取消')
        assert '取消' in result
        assert 'User' not in chat_service.pending_evolution_proposals

    async def test_evolution_proposal_no_pending(self, chat_service):
        result = await chat_service._handle_evolution_proposal('User', '確認')
        assert result is None


class TestChatServiceIntent:

    async def _assert_intent(self, chat_service, text, expected_intent):
        result = await chat_service._analyze_intent(text)
        assert result['primary_intent'] == expected_intent, f"Expected {expected_intent}, got {result} for '{text}'"
        assert 'confidence' in result

    async def test_analyze_intent_general(self, chat_service):
        await self._assert_intent(chat_service, 'how are you', 'general')

    async def test_analyze_intent_llm(self, chat_service):
        await self._assert_intent(chat_service, '切換模型 to gpt-4', 'llm_manage')

    async def test_analyze_intent_file(self, chat_service):
        await self._assert_intent(chat_service, '讀取檔案 myfile.txt', 'file_op')

    async def test_analyze_intent_learning(self, chat_service):
        await self._assert_intent(chat_service, '教你 something new', 'learning')

    async def test_analyze_intent_via_registry(self, chat_service):
        mock_mm = MagicMock()
        mock_ireg = MagicMock()
        mock_ireg.instance.detect.return_value = ('task', 0.8)
        mock_mm.has.return_value = True
        mock_mm.get_module.return_value = mock_ireg
        patcher = um.patch.object(type(chat_service), '_module_manager',
                                   new_callable=um.PropertyMock(return_value=mock_mm))
        patcher.start()
        result = await chat_service._analyze_intent('生成一份報告')
        patcher.stop()
        assert result['primary_intent'] == 'task'
        assert result['confidence'] == 0.8

    async def test_analyze_intent_character_card_via_registry(self, chat_service):
        mock_mm = MagicMock()
        mock_ireg = MagicMock()
        mock_ireg.instance.detect.return_value = ('character_card', 0.9)
        mock_mm.has.return_value = True
        mock_mm.get_module.return_value = mock_ireg
        patcher = um.patch.object(type(chat_service), '_module_manager',
                                   new_callable=um.PropertyMock(return_value=mock_mm))
        patcher.start()
        result = await chat_service._analyze_intent('生成一個角色卡')
        patcher.stop()
        assert result['primary_intent'] == 'character_card'

    async def test_analyze_intent_registry_exception_falls_back(self, chat_service):
        mock_mm = MagicMock()
        mock_mm.has.side_effect = Exception("registry fail")
        patcher = um.patch.object(type(chat_service), '_module_manager',
                                   new_callable=um.PropertyMock(return_value=mock_mm))
        patcher.start()
        result = await chat_service._analyze_intent('how are you')
        patcher.stop()
        assert result['primary_intent'] == 'general'

    async def test_analyze_intent_no_module_manager_falls_back(self, chat_service):
        patcher = um.patch.object(type(chat_service), '_module_manager',
                                   new_callable=um.PropertyMock(return_value=None))
        patcher.start()
        result = await chat_service._analyze_intent('切換模型 to gpt-4')
        assert result['primary_intent'] == 'llm_manage'


class TestChatServiceCharacterCard:

    def _start_mm_mock(self, chat_service, mock_mm):
        patcher = um.patch.object(type(chat_service), '_module_manager',
                                   new_callable=um.PropertyMock(return_value=mock_mm))
        patcher.start()
        return patcher

    async def test_character_card_with_pipeline(self, chat_service):
        mock_card = MagicMock(card_id="CC-99")
        mock_result = MagicMock(card=mock_card, confidence=0.85, stage="auto")
        mock_mm = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.instance.process.return_value = mock_result
        mock_mm.has.return_value = True
        mock_mm.get_module.return_value = mock_pipeline
        patcher = self._start_mm_mock(chat_service, mock_mm)
        result = await chat_service._handle_character_card_intent("CC-99: Test")
        patcher.stop()
        assert "CC-99" in result
        assert "85%" in result
        assert "auto" in result

    async def test_character_card_no_pipeline(self, chat_service):
        mock_mm = MagicMock()
        mock_mm.has.return_value = False
        patcher = self._start_mm_mock(chat_service, mock_mm)
        result = await chat_service._handle_character_card_intent("CC-99: Test")
        patcher.stop()
        assert "尚未就緒" in result

    async def test_character_card_pipeline_error(self, chat_service):
        mock_mm = MagicMock()
        mock_pipeline = MagicMock()
        mock_pipeline.instance.process.side_effect = Exception("parse error")
        mock_mm.has.return_value = True
        mock_mm.get_module.return_value = mock_pipeline
        patcher = self._start_mm_mock(chat_service, mock_mm)
        result = await chat_service._handle_character_card_intent("bad text")
        patcher.stop()
        assert "錯誤" in result

    async def test_character_card_in_generate_response(self, chat_service):
        chat_service._handle_character_card_intent = AsyncMock(return_value="card result")
        mock_mm = MagicMock()
        mock_ireg = MagicMock()
        mock_ireg.instance.detect.return_value = ('character_card', 0.9)
        mock_mm.has.return_value = True
        mock_mm.get_module.return_value = mock_ireg
        patcher = self._start_mm_mock(chat_service, mock_mm)
        result = await chat_service.generate_response("生成一個角色卡", "User")
        assert result == "card result"


class TestChatServiceHelpers:

    def test_get_anchor_keywords_default(self, chat_service):
        result = chat_service._get_anchor_keywords()
        assert 'alpha' in result
        assert 'beta' in result

    def test_get_state_constants_default(self, chat_service):
        result = chat_service._get_state_constants('nonexistent', 'default_val')
        assert result == 'default_val'

    def test_conversation_history_limit(self, chat_service):
        for i in range(25):
            chat_service._conversation_history.append({'role': 'user', 'content': f'msg {i}'})
            chat_service._conversation_history.append({'role': 'assistant', 'content': f'resp {i}'})
        assert len(chat_service._conversation_history) == 50
