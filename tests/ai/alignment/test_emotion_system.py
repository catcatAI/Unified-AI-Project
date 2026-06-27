"""Tests for apps.backend.src.ai.alignment.emotion_system"""
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from ai.alignment.emotion_system import (
    EmotionalState,
    EmotionSystem,
    EmotionType,
    EmpathyAnalysis,
    ValueAssessment,
    ValueDimension,
)


class TestEnums:
    def test_emotion_type_values(self):
        assert EmotionType.JOY.value == 'joy'
        assert EmotionType.TRUST.value == 'trust'
        assert EmotionType.FEAR.value == 'fear'
        assert EmotionType.SURPRISE.value == 'surprise'
        assert EmotionType.SADNESS.value == 'sadness'
        assert EmotionType.DISGUST.value == 'disgust'
        assert EmotionType.ANGER.value == 'anger'
        assert EmotionType.ANTICIPATION.value == 'anticipation'

    def test_value_dimension_values(self):
        assert ValueDimension.WELL_BEING.value == 'well_being'
        assert ValueDimension.FREEDOM.value == 'freedom'
        assert ValueDimension.JUSTICE.value == 'justice'
        assert ValueDimension.BEAUTY.value == 'beauty'
        assert ValueDimension.TRUTH.value == 'truth'
        assert ValueDimension.GROWTH.value == 'growth'
        assert ValueDimension.CONNECTION.value == 'connection'
        assert ValueDimension.MEANING.value == 'meaning'
        assert ValueDimension.SECURITY.value == 'security'

    def test_emotion_type_members_count(self):
        assert len(EmotionType) == 8

    def test_value_dimension_members_count(self):
        assert len(ValueDimension) == 9


class TestEmotionalState:
    def test_create_default(self):
        state = EmotionalState(
            primary_emotion=EmotionType.JOY,
            emotion_intensity=0.8,
            secondary_emotions={},
            valence=0.5,
            arousal=0.6,
        )
        assert state.primary_emotion == EmotionType.JOY
        assert state.emotion_intensity == 0.8
        assert state.secondary_emotions == {}
        assert state.valence == 0.5
        assert state.arousal == 0.6
        assert state.timestamp > 0

    def test_create_with_secondary(self):
        state = EmotionalState(
            primary_emotion=EmotionType.TRUST,
            emotion_intensity=0.6,
            secondary_emotions={EmotionType.JOY: 0.3},
            valence=0.4,
            arousal=0.5,
        )
        assert state.secondary_emotions[EmotionType.JOY] == 0.3

    def test_negative_valence(self):
        state = EmotionalState(
            primary_emotion=EmotionType.FEAR,
            emotion_intensity=0.9,
            secondary_emotions={},
            valence=-0.7,
            arousal=0.8,
        )
        assert state.valence < 0


class TestEmotionSystemInit:
    def test_default_init(self):
        es = EmotionSystem()
        assert es.system_id == 'emotion_system_v1'
        assert es.emotion_history == []
        assert es.is_active is True
        assert len(es.value_weights) == len(ValueDimension)
        for dim in ValueDimension:
            assert es.value_weights[dim] == 1.0

    def test_custom_system_id(self):
        es = EmotionSystem(system_id='custom_es')
        assert es.system_id == 'custom_es'

    def test_emotion_value_mapping_initialized(self):
        es = EmotionSystem()
        assert EmotionType.JOY in es.emotion_value_impact
        assert EmotionType.TRUST in es.emotion_value_impact
        assert EmotionType.FEAR in es.emotion_value_impact
        assert EmotionType.ANGER in es.emotion_value_impact
        assert EmotionType.SADNESS in es.emotion_value_impact


class TestEmotionSummary:
    def test_summary_empty_history(self):
        es = EmotionSystem()
        summary = es.get_emotion_summary()
        assert summary['dominant_emotion'] == 'neutral'
        assert summary['intensity'] == 0.5
        assert summary['arousal'] == 0.5
        assert summary['valence'] == 0.0

    def test_summary_after_context_analysis(self):
        with patch('textblob.TextBlob') as mock_tb, \
             patch('core.system.config.tiered_loader.get_config') as mock_gc:

            mock_tb.return_value.sentiment.polarity = 0.8
            mock_gc.return_value = {
                'biological_thresholds': {
                    'emotion_classification_stress': 0.7,
                }
            }

            es = EmotionSystem()
            es.analyze_emotional_context({'text': 'I am very happy!'})
            summary = es.get_emotion_summary()
            assert summary['dominant_emotion'] == 'joy'
            assert summary['valence'] == 0.8


class TestAnalyzeEmotionalContext:
    _base_config = {
        'biological_thresholds': {'emotion_classification_stress': 0.7}
    }

    @pytest.fixture
    def emotion_system(self):
        with patch('textblob.TextBlob') as mock_tb, \
             patch('core.system.config.tiered_loader.get_config') as mock_gc:
            mock_tb.return_value.sentiment.polarity = 0.6
            mock_gc.return_value = self._base_config
            yield EmotionSystem()

    def test_analyze_positive_context(self, emotion_system):
        state = emotion_system.analyze_emotional_context({
            'text': 'This is wonderful!',
            'stress_level': 0.2,
        })
        assert state.primary_emotion == EmotionType.JOY
        assert state.valence > 0
        assert len(emotion_system.emotion_history) == 1

    def test_analyze_adds_to_history(self, emotion_system):
        emotion_system.analyze_emotional_context({'text': 'ok'})
        emotion_system.analyze_emotional_context({'text': 'great'})
        assert len(emotion_system.emotion_history) == 2


class TestGetCurrentEmotionState:
    async def test_async_get_state(self):
        es = EmotionSystem()
        state_str = await es.get_current_emotion_state()
        assert 'neutral' in state_str
        assert 'intensity' in state_str
    async def test_async_get_state_after_context(self):
        with patch('textblob.TextBlob') as mock_tb, \
             patch('core.system.config.tiered_loader.get_config') as mock_gc:

            mock_tb.return_value.sentiment.polarity = 0.9
            mock_gc.return_value = {
                'biological_thresholds': {
                    'emotion_classification_stress': 0.7,
                }
            }

            es = EmotionSystem()
            es.analyze_emotional_context({'text': 'amazing!'})
            state_str = await es.get_current_emotion_state()
            assert 'joy' in state_str


class TestValueAssessment:
    @pytest.fixture
    def emotion_system(self):
        with patch('textblob.TextBlob') as mock_tb, \
             patch('core.system.config.tiered_loader.get_config') as mock_gc:
            mock_tb.return_value.sentiment.polarity = 0.5
            mock_gc.return_value = TestAnalyzeEmotionalContext._base_config
            yield EmotionSystem()

    def test_assess_values_without_explicit_state(self, emotion_system):
        action = {'action_id': 'test_action', 'type': 'help'}
        context = {'text': 'helpful context'}
        assessment = emotion_system.assess_values(action, context)
        assert len(assessment.value_scores) == len(ValueDimension)
        assert 0.0 <= assessment.overall_value <= 1.0
        assert 0.0 <= assessment.confidence <= 1.0
        assert len(assessment.reasoning) > 0

    def test_assess_values_with_explicit_state(self, emotion_system):
        action = {'action_id': 'test'}
        context = {'text': 'context'}
        state = EmotionalState(
            primary_emotion=EmotionType.JOY,
            emotion_intensity=0.9,
            secondary_emotions={},
            valence=0.8,
            arousal=0.7,
        )
        assessment = emotion_system.assess_values(action, context, state)
        assert isinstance(assessment, ValueAssessment)

    def test_overall_value_is_average(self, emotion_system):
        action = {'action_id': 'test'}
        context = {'text': 'ctx'}
        state = EmotionalState(
            primary_emotion=EmotionType.JOY,
            emotion_intensity=0.5,
            secondary_emotions={},
            valence=0.5,
            arousal=0.5,
        )
        assessment = emotion_system.assess_values(action, context, state)
        expected_avg = sum(assessment.value_scores.values()) / len(assessment.value_scores)
        assert assessment.overall_value == pytest.approx(expected_avg)

    def test_confidence_formula(self, emotion_system):
        action = {'action_id': 'test'}
        context = {'text': 'ctx'}
        state = EmotionalState(
            primary_emotion=EmotionType.JOY,
            emotion_intensity=1.0,
            secondary_emotions={},
            valence=0.5,
            arousal=0.5,
        )
        assessment = emotion_system.assess_values(action, context, state)
        expected_conf = (1.0 + 0.8) / 2.0
        assert assessment.confidence == expected_conf

    def test_dimension_score_clamped(self, emotion_system):
        action = {'action_id': 'test'}
        context = {'text': 'ctx'}
        state = EmotionalState(
            primary_emotion=EmotionType.FEAR,
            emotion_intensity=1.0,
            secondary_emotions={},
            valence=-0.9,
            arousal=0.9,
        )
        assessment = emotion_system.assess_values(action, context, state)
        for dim, score in assessment.value_scores.items():
            assert 0.0 <= score <= 1.0


class TestEmpathyAnalysis:
    @pytest.fixture
    def emotion_system(self):
        with patch('textblob.TextBlob') as mock_tb, \
             patch('core.system.config.tiered_loader.get_config') as mock_gc:
            mock_tb.return_value.sentiment.polarity = -0.5
            mock_gc.return_value = TestAnalyzeEmotionalContext._base_config
            yield EmotionSystem()

    def test_analyze_empathy_returns_analysis(self, emotion_system):
        analysis = emotion_system.analyze_empathy('human_user', {
            'text': 'I feel sad',
            'stress_level': 0.6,
        })
        assert isinstance(analysis, EmpathyAnalysis)
        assert analysis.target_entity == 'human_user'
        assert 0.0 <= analysis.empathy_score <= 1.0
        assert 0.0 <= analysis.compassion_level <= 1.0
        assert analysis.recommended_response != ''

    def test_empathy_predicts_emotion(self, emotion_system):
        analysis = emotion_system.analyze_empathy('user', {
            'text': 'I am very sad today',
            'stress_level': 0.8,
        })
        assert isinstance(analysis.predicted_emotional_state, EmotionalState)

    def test_empathy_score_non_negative(self, emotion_system):
        analysis = emotion_system.analyze_empathy('user', {
            'text': 'neutral statement',
            'stress_level': 0.0,
        })
        assert analysis.empathy_score >= 0.0

    def test_compassion_for_sadness(self, emotion_system):
        with patch.object(
            emotion_system, '_predict_entity_emotion',
            return_value=EmotionalState(
                primary_emotion=EmotionType.SADNESS,
                emotion_intensity=0.8,
                secondary_emotions={},
                valence=-0.6,
                arousal=0.5,
            ),
        ):
            analysis = emotion_system.analyze_empathy('user', {})
            assert analysis.compassion_level > 0.5

    def test_compassion_for_joy_lower(self, emotion_system):
        with patch.object(
            emotion_system, '_predict_entity_emotion',
            return_value=EmotionalState(
                primary_emotion=EmotionType.JOY,
                emotion_intensity=0.8,
                secondary_emotions={},
                valence=0.7,
                arousal=0.5,
            ),
        ):
            analysis = emotion_system.analyze_empathy('user', {})
            assert analysis.compassion_level < 0.5


class TestInfluenceAndWeights:
    def test_apply_influence(self):
        es = EmotionSystem()
        es.apply_influence('external_event', 'boost', 0.5, 0.3)
        # Should not raise

    def test_update_value_weight(self):
        es = EmotionSystem()
        es.update_value_weight(ValueDimension.JUSTICE, 2.0)
        assert es.value_weights[ValueDimension.JUSTICE] == 2.0

    def test_get_emotion_history(self):
        es = EmotionSystem()
        history = es.get_emotion_history()
        assert history == []

    def test_get_emotion_history_limit(self):
        with patch('textblob.TextBlob') as mock_tb, \
             patch('core.system.config.tiered_loader.get_config') as mock_gc:
            mock_tb.return_value.sentiment.polarity = 0.3
            mock_gc.return_value = {
                'biological_thresholds': {
                    'emotion_classification_stress': 0.7,
                }
            }
            es = EmotionSystem()
            for _ in range(5):
                es.analyze_emotional_context({'text': 'ok'})
            history = es.get_emotion_history(limit=3)
            assert len(history) == 3
