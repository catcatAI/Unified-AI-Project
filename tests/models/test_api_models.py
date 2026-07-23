"""Tests for apps.backend.src.models.api_models"""
import pytest
from pydantic import ValidationError

from apps.backend.src.models.api_models import (
    AIOutput,
    AtlassianConfigModel,
    ConfluencePageModel,
    HealthStatusModel,
    HotStatusModel,
    HSPCapabilityModel,
    HSPTaskRequestInput,
    HSPTaskRequestOutput,
    JiraIssueModel,
    JQLSearchModel,
    ReadinessStatusModel,
    RovoDevTaskModel,
    SessionStartRequest,
    SessionStartResponse,
    UserInput,
)


class TestUserInput:
    def test_create_valid_user_input(self):
        m = UserInput(user_id='u1', session_id='s1', text='hello')
        assert m.user_id == 'u1'
        assert m.session_id == 's1'
        assert m.text == 'hello'

    def test_missing_field(self):
        with pytest.raises(ValidationError):
            UserInput(user_id='u1')

    def test_roundtrip_json_user_input(self):
        m1 = UserInput(user_id='u1', session_id='s1', text='hi')
        data = m1.model_dump_json()
        m2 = UserInput.model_validate_json(data)
        assert m1.model_dump() == m2.model_dump()


class TestAIOutput:
    def test_create_valid_ai_output(self):
        m = AIOutput(response_text='resp', user_id='u1', session_id='s1', timestamp='2024-01-01')
        assert m.response_text == 'resp'

    def test_roundtrip_dict(self):
        m1 = AIOutput(response_text='a', user_id='b', session_id='c', timestamp='t')
        d = m1.model_dump()
        m2 = AIOutput(**d)
        assert m1 == m2

    def test_missing_fields(self):
        with pytest.raises(ValidationError):
            AIOutput(response_text='a')


class TestSessionStartRequest:
    def test_create_with_user_id(self):
        m = SessionStartRequest(user_id='u1')
        assert m.user_id == 'u1'

    def test_missing(self):
        with pytest.raises(ValidationError):
            SessionStartRequest()


class TestSessionStartResponse:
    def test_create_with_greeting(self):
        m = SessionStartResponse(greeting='hi', session_id='s1', timestamp='t1')
        assert m.greeting == 'hi'

    def test_roundtrip_json_session_response(self):
        m1 = SessionStartResponse(greeting='g', session_id='s', timestamp='t')
        d = m1.model_dump_json()
        m2 = SessionStartResponse.model_validate_json(d)
        assert m1 == m2


class TestHSPTaskRequestInput:
    def test_create_valid(self):
        m = HSPTaskRequestInput(target_capability_id='c1', parameters={'key': 'val'})
        assert m.target_capability_id == 'c1'
        assert m.parameters == {'key': 'val'}

    def test_missing_target(self):
        with pytest.raises(ValidationError):
            HSPTaskRequestInput(parameters={})


class TestHSPTaskRequestOutput:
    def test_create_minimal_defaults(self):
        m = HSPTaskRequestOutput(status_message='ok', target_capability_id='c1')
        assert m.status_message == 'ok'
        assert m.correlation_id is None
        assert m.error is None

    def test_create_full(self):
        m = HSPTaskRequestOutput(
            status_message='done', correlation_id='corr1', target_capability_id='c1', error='err'
        )
        assert m.correlation_id == 'corr1'
        assert m.error == 'err'

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            HSPTaskRequestOutput(status_message='ok')


class TestAtlassianConfigModel:
    def test_create_with_config_fields(self):
        m = AtlassianConfigModel(base_url='https://x.atlassian.net', username='user', api_token='tok')
        assert m.base_url == 'https://x.atlassian.net'


class TestConfluencePageModel:
    def test_create_with_page_fields(self):
        m = ConfluencePageModel(space_key='SP', title='T', content='C')
        assert m.title == 'T'

    def test_missing(self):
        with pytest.raises(ValidationError):
            ConfluencePageModel(space_key='SP')


class TestJiraIssueModel:
    def test_create_with_issue_fields(self):
        m = JiraIssueModel(project_key='PROJ', summary='Sum', description='Desc')
        assert m.summary == 'Sum'


class TestRovoDevTaskModel:
    def test_create_with_capability(self):
        m = RovoDevTaskModel(capability='cap', parameters={'a': 1})
        assert m.capability == 'cap'


class TestJQLSearchModel:
    def test_create_with_jql(self):
        m = JQLSearchModel(jql='project = PROJ')
        assert m.jql == 'project = PROJ'

    def test_missing(self):
        with pytest.raises(ValidationError):
            JQLSearchModel()


class TestHotStatusModel:
    def test_create(self):
        m = HotStatusModel(
            draining=False,
            services_initialized={'svc': True},
            hsp={'key': 'val'},
            mcp={'key2': 'val2'},
            metrics={'cpu': 0.5},
        )
        assert m.draining is False
        assert m.services_initialized == {'svc': True}


class TestHealthStatusModel:
    def test_create_minimal_health(self):
        m = HealthStatusModel(status='healthy', timestamp='t', services_initialized={'s': True})
        assert m.status == 'healthy'
        assert m.components == {}

    def test_create_with_components(self):
        m = HealthStatusModel(
            status='degraded', timestamp='t', services_initialized={'s': True}, components={'db': 'ok'}
        )
        assert m.components == {'db': 'ok'}


class TestReadinessStatusModel:
    def test_create_minimal_readiness(self):
        m = ReadinessStatusModel(ready=True, timestamp='t', services_initialized={'s': True})
        assert m.ready is True
        assert m.reason is None

    def test_create_with_reason(self):
        m = ReadinessStatusModel(
            ready=False, timestamp='t', services_initialized={'s': False}, reason='not ready'
        )
        assert m.reason == 'not ready'
        assert m.signals == {}

    def test_roundtrip_json(self):
        m1 = ReadinessStatusModel(
            ready=True, timestamp='t', services_initialized={'s': True}, signals={'cpu': 1.0}
        )
        d = m1.model_dump_json()
        m2 = ReadinessStatusModel.model_validate_json(d)
        assert m1 == m2


class TestHSPCapabilityModel:
    def test_create_minimal(self):
        m = HSPCapabilityModel(
            capability_id='c1',
            name='n',
            description='d',
            version='1.0',
            ai_id='ai1',
            availability_status='available',
        )
        assert m.tags == []
        assert m.supported_interfaces == []
        assert m.metadata == {}

    def test_create_full(self):
        m = HSPCapabilityModel(
            capability_id='c1',
            name='n',
            description='d',
            version='1.0',
            ai_id='ai1',
            availability_status='available',
            tags=['tag1'],
            supported_interfaces=['rest'],
            metadata={'key': 'val'},
        )
        assert len(m.tags) == 1
        assert 'rest' in m.supported_interfaces

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            HSPCapabilityModel(capability_id='c1', name='n')


class TestAllModelsRoundtrip:
    @pytest.mark.parametrize('model_cls,kwargs', [
        (UserInput, {'user_id': 'u', 'session_id': 's', 'text': 't'}),
        (AIOutput, {'response_text': 'r', 'user_id': 'u', 'session_id': 's', 'timestamp': 't'}),
        (HSPTaskRequestInput, {'target_capability_id': 'c', 'parameters': {'k': 'v'}}),
        (AtlassianConfigModel, {'base_url': 'u', 'username': 'n', 'api_token': 't'}),
    ])
    def test_json_roundtrip(self, model_cls, kwargs):
        m1 = model_cls(**kwargs)
        data = m1.model_dump_json()
        m2 = model_cls.model_validate_json(data)
        assert m1 == m2
