import sys
import pytest
from unittest.mock import MagicMock, AsyncMock

_MODULE_MOCKS = {
    'ai.memory.ham_memory.ham_manager': MagicMock(),
    'ai.trust.trust_manager_module': MagicMock(),
    'ai.personality.personality_manager': MagicMock(),
    'core.interfaces.protocols': MagicMock(),
    'ai.knowledge_graph.types': MagicMock(),
    'core.hsp.types': MagicMock(),
    'networkx': MagicMock(),
}
for mod_name, mock in _MODULE_MOCKS.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mock


@pytest.fixture
def learning_manager():
    from apps.backend.src.ai.learning.learning_manager import LearningManager
    hsp_connector = MagicMock()
    hsp_connector.publish_fact = AsyncMock()
    lm = LearningManager(
        ai_id='test_ai',
        ham_manager=MagicMock(),
        fact_extractor=MagicMock(),
        personality_manager=MagicMock(),
        content_analyzer=MagicMock(),
        hsp_connector=hsp_connector,
        trust_manager=MagicMock(),
    )
    return lm


class TestLearningManagerInit:
    def test_init_default_config(self, learning_manager):
        assert learning_manager.ai_id == 'test_ai'
        assert learning_manager.min_fact_confidence_to_store == 0.7
        assert learning_manager.min_fact_confidence_to_share_via_hsp == 0.8

    def test_init_custom_config(self):
        from apps.backend.src.ai.learning.learning_manager import LearningManager
        config = {
            'learning_thresholds': {
                'min_fact_confidence_to_store': 0.5,
                'min_fact_confidence_to_share_via_hsp': 0.9,
            },
        }
        lm = LearningManager(
            ai_id='custom_ai',
            ham_manager=MagicMock(),
            fact_extractor=MagicMock(),
            personality_manager=MagicMock(),
            operational_config=config,
        )
        assert lm.min_fact_confidence_to_store == 0.5
        assert lm.min_fact_confidence_to_share_via_hsp == 0.9
        assert lm.operational_config == config


class TestLearningManagerAnalyze:
    @pytest.mark.asyncio
    async def test_analyze_positive_keywords(self, learning_manager):
        result = await learning_manager.analyze_for_personality_adjustment('This is great and amazing')
        assert result == {'friendliness': 0.05}

    @pytest.mark.asyncio
    async def test_analyze_negative_keywords(self, learning_manager):
        result = await learning_manager.analyze_for_personality_adjustment('This is terrible and awful')
        assert result == {'empathy': 0.05}

    @pytest.mark.asyncio
    async def test_analyze_technical_keywords(self, learning_manager):
        result = await learning_manager.analyze_for_personality_adjustment('Need help with code and programming')
        assert result == {'technical_focus': 0.05}

    @pytest.mark.asyncio
    async def test_analyze_empty_string(self, learning_manager):
        result = await learning_manager.analyze_for_personality_adjustment('')
        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_no_keywords(self, learning_manager):
        result = await learning_manager.analyze_for_personality_adjustment('just a normal sentence')
        assert result is None


class TestLearningManagerProcessAndStore:
    @pytest.mark.asyncio
    async def test_empty_text_returns_empty(self, learning_manager):
        result = await learning_manager.process_and_store_learnables('', 'user1')
        assert result == []

    @pytest.mark.asyncio
    async def test_below_threshold_not_stored(self, learning_manager):
        learning_manager.fact_extractor.extract_facts = AsyncMock(
            return_value=[{'confidence': 0.3, 'content': 'test', 'fact_type': 'statement'}]
        )
        result = await learning_manager.process_and_store_learnables('test text', 'user1')
        assert result == []

    @pytest.mark.asyncio
    async def test_above_threshold_stored(self, learning_manager):
        learning_manager.fact_extractor.extract_facts = AsyncMock(
            return_value=[{'confidence': 0.9, 'content': 'important fact', 'fact_type': 'knowledge'}]
        )
        learning_manager.ham_memory.store_experience.return_value = 'stored_id_123'
        result = await learning_manager.process_and_store_learnables('important text', 'user1')
        assert result == ['stored_id_123']
        learning_manager.ham_memory.store_experience.assert_called_once()

    @pytest.mark.asyncio
    async def test_above_share_threshold_shares_via_hsp(self, learning_manager):
        learning_manager.fact_extractor.extract_facts = AsyncMock(
            return_value=[{
                'confidence': 0.95, 'content': 'shareable fact', 'fact_type': 'user_preference',
            }]
        )
        learning_manager.ham_memory.store_experience.return_value = 'stored_id_456'
        learning_manager.hsp_connector.publish_fact = AsyncMock()
        result = await learning_manager.process_and_store_learnables('shareable text', 'user1')
        assert result == ['stored_id_456']
        learning_manager.hsp_connector.publish_fact.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_hsp_connector_does_not_share(self, learning_manager):
        learning_manager.hsp_connector = None
        learning_manager.fact_extractor.extract_facts = AsyncMock(
            return_value=[{'confidence': 0.95, 'content': 'fact', 'fact_type': 'statement'}]
        )
        learning_manager.ham_memory.store_experience.return_value = 'stored_id'
        result = await learning_manager.process_and_store_learnables('text', 'user1')
        assert result == ['stored_id']

    @pytest.mark.asyncio
    async def test_multiple_facts_some_filtered(self, learning_manager):
        learning_manager.fact_extractor.extract_facts = AsyncMock(return_value=[
            {'confidence': 0.9, 'content': 'high confidence', 'fact_type': 'statement'},
            {'confidence': 0.3, 'content': 'low confidence', 'fact_type': 'statement'},
            {'confidence': 0.8, 'content': 'medium confidence', 'fact_type': 'preference'},
        ])
        learning_manager.ham_memory.store_experience.side_effect = ['id1', 'id2']
        result = await learning_manager.process_and_store_learnables('multi text', 'user1')
        assert result == ['id1', 'id2']
        assert learning_manager.ham_memory.store_experience.call_count == 2


class TestLearningManagerProcessHspFact:
    @pytest.mark.asyncio
    async def test_duplicate_fact_returns_none(self, learning_manager):
        hsp_payload = {
            'id': 'fact_1', 'source_ai_id': 'ai_1',
            'confidence_score': 0.9, 'tags': ['knowledge'],
            'statement_structured': 'data', 'statement_nl': 'text',
        }
        learning_manager.ham_memory.query_core_memory.return_value = [{'id': 'existing'}]
        result = await learning_manager.process_and_store_hsp_fact(hsp_payload, 'sender_ai', None)
        assert result is None

    @pytest.mark.asyncio
    async def test_below_threshold_discards(self, learning_manager):
        hsp_payload = {
            'id': 'fact_2', 'source_ai_id': 'ai_1',
            'confidence_score': 0.1, 'tags': ['knowledge'],
            'statement_structured': 'data', 'statement_nl': 'text',
        }
        learning_manager.ham_memory.query_core_memory.return_value = []
        learning_manager.trust_manager.get_trust_score.return_value = 0.5
        result = await learning_manager.process_and_store_hsp_fact(hsp_payload, 'sender_ai', None)
        assert result is None

    @pytest.mark.asyncio
    async def test_above_threshold_stores(self, learning_manager):
        hsp_payload = {
            'id': 'fact_3', 'source_ai_id': 'ai_1',
            'confidence_score': 0.9, 'tags': ['knowledge'],
            'statement_structured': 'important data', 'statement_nl': 'text',
        }
        learning_manager.ham_memory.query_core_memory.return_value = []
        learning_manager.trust_manager.get_trust_score.return_value = 0.9
        learning_manager.ham_memory.store_experience.return_value = 'stored_hsp_fact'
        result = await learning_manager.process_and_store_hsp_fact(hsp_payload, 'sender_ai', None)
        assert result == 'stored_hsp_fact'

    @pytest.mark.asyncio
    async def test_with_content_analyzer_boosts_novelty(self, learning_manager):
        learning_manager.min_hsp_fact_confidence_to_store = 0.3
        hsp_payload = {
            'id': 'fact_4', 'source_ai_id': 'ai_1',
            'confidence_score': 0.6, 'tags': ['knowledge'],
            'statement_structured': 'data', 'statement_nl': 'text',
        }
        learning_manager.ham_memory.query_core_memory.return_value = []
        learning_manager.trust_manager.get_trust_score.return_value = 0.9
        learning_manager.content_analyzer.process_hsp_fact_content.return_value = {
            'updated_graph': True,
        }
        learning_manager.ham_memory.store_experience.return_value = 'stored_id'
        result = await learning_manager.process_and_store_hsp_fact(hsp_payload, 'sender_ai', None)
        assert result == 'stored_id'

    @pytest.mark.asyncio
    async def test_without_trust_uses_default(self, learning_manager):
        learning_manager.min_hsp_fact_confidence_to_store = 0.3
        learning_manager.trust_manager = None
        hsp_payload = {
            'id': 'fact_5', 'source_ai_id': 'ai_1',
            'confidence_score': 0.9, 'tags': ['knowledge'],
            'statement_structured': 'data', 'statement_nl': 'text',
        }
        learning_manager.ham_memory.query_core_memory.return_value = []
        learning_manager.ham_memory.store_experience.return_value = 'stored_id'
        result = await learning_manager.process_and_store_hsp_fact(hsp_payload, 'sender_ai', None)
        assert result == 'stored_id'


class TestLearningManagerLearnFromCase:
    @pytest.mark.asyncio
    async def test_learn_from_project_case(self, learning_manager):
        project_case = {'user_query': 'build a web app', 'user_id': 'user1'}
        learning_manager.ham_memory.store_experience.return_value = 'case_id'
        await learning_manager.learn_from_project_case(project_case)
        learning_manager.ham_memory.store_experience.assert_called_once()
