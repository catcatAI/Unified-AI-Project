import pytest
from unittest.mock import MagicMock, patch, AsyncMock

try:
    from apps.backend.src.ai.memory.cognitive_pipeline import CognitivePipeline
except ImportError:
    pytest.skip("CognitivePipeline not available (stub module)", allow_module_level=True)


@pytest.fixture
def mock_state_matrix():
    sm = MagicMock()
    sm.alpha.values = {'energy': 0.7}
    sm.beta.values = {'focus': 0.6}
    sm.gamma.values = {'happiness': 0.5}
    sm.delta.values = {'bond': 0.4}
    sm.epsilon.values = {'certainty': 0.8}
    return sm


@pytest.fixture
def mock_attractor_field():
    af = MagicMock()
    af.navigate.return_value = ([0.5] * 5, MagicMock(
        blended_behavior='ok',
        blended_tone=MagicMock(value='warm'),
        navigation_steps=3,
        gradient_strength=0.7,
        certainty=0.9,
        nearest_attractors=[],
    ))
    af.compute_gradient.return_value = MagicMock(nearest_attractors=[])
    return af


@pytest.fixture
def mock_math_engine():
    me = MagicMock()
    me.analyze_expression.return_value = {
        'result': None,
        'ripples': [],
        'cognitive_summary': '',
    }
    return me


class TestCognitivePipelineInit:

    @patch('apps.backend.src.ai.memory.cognitive_pipeline.CognitivePipeline._init_subsystems')
    def test_init_minimal(self, mock_init):
        pipeline = CognitivePipeline()
        assert pipeline.state_matrix is None
        assert pipeline.attractor_field is None
        assert pipeline.math_engine is None
        assert pipeline.code_inspector is None

    def test_init_with_all_subsystems(self, mock_state_matrix, mock_attractor_field, mock_math_engine):
        pipeline = CognitivePipeline(
            state_matrix=mock_state_matrix,
            attractor_field=mock_attractor_field,
            math_ripple_engine=mock_math_engine,
        )
        assert pipeline.state_matrix == mock_state_matrix
        assert pipeline.attractor_field == mock_attractor_field
        assert pipeline.math_engine == mock_math_engine


class TestCognitivePipelineState:

    def test_get_current_state_with_matrix(self, mock_state_matrix):
        pipeline = CognitivePipeline(state_matrix=mock_state_matrix)
        state = pipeline.get_current_state()
        assert state == [0.7, 0.6, 0.5, 0.4, 0.8]

    @patch('apps.backend.src.ai.memory.cognitive_pipeline.CognitivePipeline._init_subsystems')
    def test_get_current_state_without_matrix(self, mock_init):
        pipeline = CognitivePipeline()
        state = pipeline.get_current_state()
        assert state == [0.5] * 5

    def test_get_current_state_partial(self):
        sm = MagicMock()
        sm.alpha.values = {'energy': 1.0}
        sm.beta.values = {}
        sm.gamma.values = {}
        sm.delta.values = {}
        sm.epsilon.values = {}
        pipeline = CognitivePipeline(state_matrix=sm)
        state = pipeline.get_current_state()
        assert state == [1.0, 0.5, 0.5, 0.5, 0.5]


class TestAllocateDecision:

    def test_fallback_allocate_decision(self):
        from apps.backend.src.ai.memory.cognitive_pipeline import AllocateDecision
        ad = AllocateDecision(action='assign', confidence=0.85, reasoning='high match')
        assert ad.action == 'assign'
        assert ad.confidence == 0.85
        assert ad.reasoning == 'high match'

    def test_to_dict_includes_action(self):
        from apps.backend.src.ai.memory.cognitive_pipeline import AllocateDecision
        ad = AllocateDecision('create')
        d = ad.to_dict()
        assert d['action'] == 'create'


class TestCognitivePipelineExtractLabel:

    @patch('apps.backend.src.ai.memory.cognitive_pipeline.CognitivePipeline._init_subsystems')
    def test_extract_label_normal(self, mock_init):
        pipeline = CognitivePipeline()
        label = pipeline._extract_label('Hello world this is a test')
        assert label == 'hello world this test'

    @patch('apps.backend.src.ai.memory.cognitive_pipeline.CognitivePipeline._init_subsystems')
    def test_extract_label_short_words_skipped(self, mock_init):
        pipeline = CognitivePipeline()
        # words with len <= 2 are skipped; 'the' (len 3) passes
        label = pipeline._extract_label('a an the hi')
        assert label == 'the'

    @patch('apps.backend.src.ai.memory.cognitive_pipeline.CognitivePipeline._init_subsystems')
    def test_extract_label_truncates(self, mock_init):
        pipeline = CognitivePipeline()
        label = pipeline._extract_label('a bb ccc ddd eee fff ggg hhh iii jjj kkk')
        words = label.split()
        assert len(words) <= 8


class TestCognitivePipelineProcess:
    @patch('apps.backend.src.ai.memory.cognitive_pipeline.CognitivePipeline._init_subsystems')
    async def test_process_without_subsystems(self, mock_init):
        pipeline = CognitivePipeline()
        result = await pipeline.process('hello')
        assert result['response'] == '我聽到了。'
        assert result['navigation_steps'] == 0
        assert result['state'] == [0.5, 0.5, 0.5, 0.5, 0.5]
        assert result['tone'] == 'warm'
    async def test_process_with_attractor_field(self, mock_attractor_field, mock_math_engine):
        pipeline = CognitivePipeline(
            attractor_field=mock_attractor_field,
            math_ripple_engine=mock_math_engine,
        )
        result = await pipeline.process('hello')
        assert result['response'] == 'ok'
        assert result['tone'] == 'warm'
        assert result['navigation_steps'] == 3
        assert result['certainty'] == 0.9
    async def test_process_with_all(self, mock_state_matrix, mock_attractor_field, mock_math_engine):
        pipeline = CognitivePipeline(
            state_matrix=mock_state_matrix,
            attractor_field=mock_attractor_field,
            math_ripple_engine=mock_math_engine,
        )
        result = await pipeline.process('hello', user_name='Test')
        assert result['tone'] == 'warm'
        assert result['state'] == [0.5, 0.5, 0.5, 0.5, 0.5]
    async def test_process_with_math_result(self, mock_state_matrix):
        math_engine = MagicMock()
        math_engine.analyze_expression.return_value = {
            'result': 42.0,
            'ripples': [{'alpha_arousal': 0.1}],
            'cognitive_summary': 'normal',
        }
        af = MagicMock()
        af.navigate.return_value = ([0.5] * 5, MagicMock(
            blended_behavior='ok',
            blended_tone=MagicMock(value='excited'),
            navigation_steps=2,
            gradient_strength=0.5,
            certainty=0.8,
            nearest_attractors=[],
        ))
        pipeline = CognitivePipeline(
            state_matrix=mock_state_matrix,
            attractor_field=af,
            math_ripple_engine=math_engine,
        )
        result = await pipeline.process('2+2', user_name='Test')
        assert result['math_result'] == 42.0
        assert result['response'] == '計算結果是 42.0。（我的狀態很穩定）'


class TestCognitivePipelineQueryAttractors:

    @patch('apps.backend.src.ai.memory.cognitive_pipeline.CognitivePipeline._init_subsystems')
    def test_query_without_field(self, mock_init):
        pipeline = CognitivePipeline()
        assert pipeline.query_attractors() == []

    def test_query_with_field(self, mock_attractor_field, mock_state_matrix):
        pipeline = CognitivePipeline(
            state_matrix=mock_state_matrix,
            attractor_field=mock_attractor_field,
        )
        result = pipeline.query_attractors()
        assert result == []

    def test_query_with_custom_state(self, mock_attractor_field):
        af = MagicMock()
        af.compute_gradient.return_value = MagicMock(nearest_attractors=[])
        pipeline = CognitivePipeline(attractor_field=af)
        result = pipeline.query_attractors([0.1, 0.2, 0.3, 0.4, 0.5])
        assert result == []


class TestCognitivePipelineRipple:

    def test_apply_ripple_to_state(self, mock_state_matrix):
        pipeline = CognitivePipeline(state_matrix=mock_state_matrix)
        ripple = {'alpha_arousal': 0.2, 'beta_focus': 0.1, 'gamma_excitement': 0.3}
        pipeline._apply_ripple_to_state(ripple)
        assert mock_state_matrix.alpha.values['arousal'] == 0.7
        assert mock_state_matrix.beta.values['focus'] == 0.7
        assert mock_state_matrix.gamma.values['happiness'] == 0.8

    def test_apply_cognitive_overload(self, mock_state_matrix):
        pipeline = CognitivePipeline(state_matrix=mock_state_matrix)
        pipeline._apply_cognitive_overload()
        assert mock_state_matrix.beta.values['confusion'] == 0.3

    def test_apply_division_fear(self, mock_state_matrix):
        pipeline = CognitivePipeline(state_matrix=mock_state_matrix)
        pipeline._apply_division_fear()
        assert mock_state_matrix.gamma.values['fear'] == 0.3
