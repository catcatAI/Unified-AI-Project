from datetime import datetime

import pytest

from apps.backend.src.ai.memory.memory_template import (
    AngelaState,
    MemoryTemplate,
    ResponseCategory,
    UserImpression,
    create_template,
    generate_template_id,
)


class TestResponseCategory:

    def test_basic_categories(self):
        assert ResponseCategory.GREETING.value == 'greeting'
        assert ResponseCategory.FAREWELL.value == 'farewell'
        assert ResponseCategory.SMALL_TALK.value == 'small_talk'
        assert ResponseCategory.QUESTION.value == 'question'
        assert ResponseCategory.COMMAND.value == 'command'

    def test_emotional_categories(self):
        assert ResponseCategory.EMOTIONAL.value == 'emotional'
        assert ResponseCategory.CASUAL.value == 'casual'

    def test_advanced_categories(self):
        assert ResponseCategory.AFFIRMATION.value == 'affirmation'
        assert ResponseCategory.NEGATION.value == 'negation'
        assert ResponseCategory.CURIOSITY.value == 'curiosity'
        assert ResponseCategory.INTIMACY.value == 'intimacy'
        assert ResponseCategory.SUPPORT.value == 'support'
        assert ResponseCategory.APOLOGY.value == 'apology'
        assert ResponseCategory.GRATITUDE.value == 'gratitude'
        assert ResponseCategory.HELP.value == 'help'
        assert ResponseCategory.CHARACTER_CARD.value == 'character_card'
        assert ResponseCategory.DOCUMENT.value == 'document'
        assert ResponseCategory.RESEARCH.value == 'research'
        assert ResponseCategory.PLAN.value == 'plan'
        assert ResponseCategory.UNKNOWN.value == 'unknown'

    def test_from_value(self):
        assert ResponseCategory('greeting') == ResponseCategory.GREETING
        assert ResponseCategory('unknown') == ResponseCategory.UNKNOWN


class TestAngelaState:

    def test_default_creation(self):
        state = AngelaState()
        assert state.alpha == {}
        assert state.beta == {}
        assert state.gamma == {}
        assert state.delta == {}

    def test_custom_creation(self):
        state = AngelaState(
            alpha={'energy': 0.8},
            beta={'mood': 0.6},
            gamma={'load': 0.3},
            delta={'fatigue': 0.2},
        )
        assert state.alpha['energy'] == 0.8
        assert state.beta['mood'] == 0.6
        assert state.gamma['load'] == 0.3
        assert state.delta['fatigue'] == 0.2

    def test_to_dict(self):
        state = AngelaState(alpha={'energy': 0.9})
        d = state.to_dict()
        assert d == {'alpha': {'energy': 0.9}, 'beta': {}, 'gamma': {}, 'delta': {}}

    def test_from_dict(self):
        data = {'alpha': {'a': 1.0}, 'beta': {'b': 0.5}, 'gamma': {}, 'delta': {}}
        state = AngelaState.from_dict(data)
        assert state.alpha == {'a': 1.0}
        assert state.beta == {'b': 0.5}

    def test_from_dict_empty(self):
        state = AngelaState.from_dict({})
        assert state.alpha == {}
        assert state.beta == {}


class TestUserImpression:

    def test_default_creation(self):
        imp = UserImpression()
        assert imp.relationship_level == 0.3
        assert imp.preferred_style == 'casual'
        assert imp.interaction_count == 0
        assert imp.tags == []

    def test_custom_creation(self):
        imp = UserImpression(
            relationship_level=0.9,
            preferred_style='formal',
            interaction_count=42,
            tags=['friendly', 'tech'],
        )
        assert imp.relationship_level == 0.9
        assert imp.preferred_style == 'formal'
        assert imp.interaction_count == 42
        assert imp.tags == ['friendly', 'tech']

    def test_to_dict(self):
        imp = UserImpression(relationship_level=0.5, tags=['a'])
        d = imp.to_dict()
        assert d['relationship_level'] == 0.5
        assert d['preferred_style'] == 'casual'
        assert d['tags'] == ['a']

    def test_from_dict(self):
        data = {'relationship_level': 0.8, 'preferred_style': 'playful', 'tags': ['x']}
        imp = UserImpression.from_dict(data)
        assert imp.relationship_level == 0.8
        assert imp.preferred_style == 'playful'
        assert imp.tags == ['x']

    def test_from_dict_defaults(self):
        imp = UserImpression.from_dict({})
        assert imp.relationship_level == 0.3
        assert imp.preferred_style == 'casual'


class TestMemoryTemplate:

    @pytest.fixture
    def sample_template(self):
        return MemoryTemplate(
            id='tpl_001',
            category=ResponseCategory.GREETING,
            content='Hello!',
            keywords=['hi', 'hello'],
            metadata={'version': 1},
        )

    def test_create_minimal(self):
        tpl = MemoryTemplate(id='min', category=ResponseCategory.UNKNOWN, content='test')
        assert tpl.id == 'min'
        assert tpl.category == ResponseCategory.UNKNOWN
        assert tpl.content == 'test'
        assert tpl.keywords == []
        assert tpl.usage_count == 0
        assert tpl.success_rate == 1.0
        assert tpl.last_used is None
        assert isinstance(tpl.created_at, datetime)

    def test_create_full(self, sample_template):
        assert sample_template.id == 'tpl_001'
        assert sample_template.category == ResponseCategory.GREETING
        assert sample_template.content == 'Hello!'
        assert sample_template.keywords == ['hi', 'hello']
        assert sample_template.usage_count == 0
        assert sample_template.angela_state.to_dict() == AngelaState().to_dict()
        assert sample_template.user_impression.to_dict() == UserImpression().to_dict()

    def test_to_dict(self, sample_template):
        d = sample_template.to_dict()
        assert d['id'] == 'tpl_001'
        assert d['category'] == 'greeting'
        assert d['content'] == 'Hello!'
        assert d['keywords'] == ['hi', 'hello']
        assert d['usage_count'] == 0
        assert d['success_rate'] == 1.0
        assert d['created_at'] == sample_template.created_at.isoformat()
        assert d['updated_at'] == sample_template.updated_at.isoformat()
        assert d['angela_state'] == sample_template.angela_state.to_dict()
        assert d['user_impression'] == sample_template.user_impression.to_dict()

    def test_from_dict_roundtrip(self, sample_template):
        d = sample_template.to_dict()
        restored = MemoryTemplate.from_dict(d)
        assert restored.id == sample_template.id
        assert restored.category == sample_template.category
        assert restored.content == sample_template.content
        assert restored.keywords == sample_template.keywords
        assert restored.usage_count == sample_template.usage_count

    def test_record_usage_success(self, sample_template):
        sample_template.record_usage(success=True)
        assert sample_template.usage_count == 1
        assert sample_template.success_rate == 1.0
        assert isinstance(sample_template.last_used, datetime)
        assert (datetime.utcnow() - sample_template.last_used).total_seconds() < 5

    def test_record_usage_failure(self, sample_template):
        sample_template.record_usage(success=False)
        assert sample_template.usage_count == 1
        assert sample_template.success_rate == 0.8

    def test_record_usage_multiple(self, sample_template):
        sample_template.record_usage(success=True)
        sample_template.record_usage(success=True)
        sample_template.record_usage(success=False)
        assert sample_template.usage_count == 3
        assert sample_template.success_rate == 0.8

    def test_is_suitable_for_high_score(self, sample_template):
        state = AngelaState()
        imp = UserImpression()
        assert sample_template.is_suitable_for(state, imp) is True

    def test_calculate_match_score_no_keywords(self, sample_template):
        tpl = MemoryTemplate(id='t', category=ResponseCategory.UNKNOWN, content='x')
        score = tpl.calculate_match_score('anything', AngelaState(), UserImpression())
        assert score == pytest.approx(0.65, abs=1e-6)

    def test_calculate_keyword_match_all(self, sample_template):
        score = sample_template._calculate_keyword_match('hello world hi')
        assert score == 1.0

    def test_calculate_keyword_match_partial(self, sample_template):
        score = sample_template._calculate_keyword_match('hello only')
        assert score == 0.5

    def test_calculate_keyword_match_none(self, sample_template):
        score = sample_template._calculate_keyword_match('goodbye')
        assert score == 0.0

    def test_calculate_state_similarity_identical(self, sample_template):
        state = AngelaState(alpha={'energy': 0.5, 'focus': 0.5})
        sample_template.angela_state = AngelaState(alpha={'energy': 0.5, 'focus': 0.5})
        score = sample_template._calculate_state_similarity(state)
        assert score == 0.5

    def test_calculate_state_similarity_different(self, sample_template):
        state = AngelaState(alpha={'energy': 1.0})
        sample_template.angela_state = AngelaState(alpha={'energy': 0.0})
        score = sample_template._calculate_state_similarity(state)
        assert score == 0.5

    def test_calculate_state_similarity_no_common(self, sample_template):
        state = AngelaState(alpha={'a': 0.5})
        sample_template.angela_state = AngelaState(beta={'b': 0.5})
        score = sample_template._calculate_state_similarity(state)
        assert score == 0.5


class TestHelpers:

    def test_generate_template_id_format(self):
        tid = generate_template_id('hello')
        assert tid.startswith('tpl_')
        # tpl_YYYYMMDDHHMMSS_8charhex
        assert tid.count('_') == 2

    def test_create_template_defaults(self):
        tpl = create_template('content', ResponseCategory.GREETING)
        assert tpl.content == 'content'
        assert tpl.category == ResponseCategory.GREETING
        assert tpl.keywords == []
        assert tpl.angela_state.to_dict() == AngelaState().to_dict()
        assert tpl.user_impression.to_dict() == UserImpression().to_dict()

    def test_create_template_custom(self):
        state = AngelaState(alpha={'energy': 0.9})
        imp = UserImpression(relationship_level=0.8)
        tpl = create_template(
            'custom', ResponseCategory.QUESTION,
            keywords=['how', 'why'],
            angela_state=state,
            user_impression=imp,
            metadata={'source': 'test'},
        )
        assert tpl.keywords == ['how', 'why']
        assert tpl.angela_state.alpha['energy'] == 0.9
        assert tpl.user_impression.relationship_level == 0.8
        assert tpl.metadata == {'source': 'test'}
