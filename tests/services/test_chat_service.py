# =============================================================================
# ANGELA-MATRIX: [L2] [αβγδ] [A] [L3+]
# =============================================================================

import sys
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

    async def test_analyze_intent_general(self, chat_service):
        result = await chat_service._analyze_intent('how are you')
        assert result == {'primary_intent': 'general'}

    async def test_analyze_intent_llm(self, chat_service):
        result = await chat_service._analyze_intent('切換模型 to gpt-4')
        assert result == {'primary_intent': 'llm_manage'}

    async def test_analyze_intent_file(self, chat_service):
        result = await chat_service._analyze_intent('讀取檔案 myfile.txt')
        assert result == {'primary_intent': 'file_op'}

    async def test_analyze_intent_learning(self, chat_service):
        result = await chat_service._analyze_intent('教你 something new')
        assert result == {'primary_intent': 'learning'}


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
