import sys
import pytest
from unittest.mock import patch

_MODULE_MOCKS = {
    'numpy': None,
}
for mod_name, mock in _MODULE_MOCKS.items():
    if mod_name not in sys.modules:
        sys.modules[mod_name] = mock


class TestExperienceReplayBufferInit:
    def test_init_default(self):
        from apps.backend.src.ai.learning.experience_replay import ExperienceReplayBuffer
        buffer = ExperienceReplayBuffer()
        assert buffer.capacity == 10000
        assert buffer.priority_alpha == 0.6
        assert buffer.buffer == []
        assert buffer.priorities == []
        assert buffer.position == 0

    def test_init_custom(self):
        from apps.backend.src.ai.learning.experience_replay import ExperienceReplayBuffer
        buffer = ExperienceReplayBuffer(capacity=100, priority_alpha=0.8)
        assert buffer.capacity == 100
        assert buffer.priority_alpha == 0.8


class TestExperienceReplayBufferAdd:
    def test_add_experience(self):
        from apps.backend.src.ai.learning.experience_replay import ExperienceReplayBuffer
        buffer = ExperienceReplayBuffer(capacity=10)
        buffer.add_experience(state='s1', action='a1', reward=1.0, next_state='s2', done=False)
        assert len(buffer.buffer) == 1
        exp = buffer.buffer[0]
        assert exp['state'] == 's1'
        assert exp['action'] == 'a1'
        assert exp['reward'] == 1.0
        assert exp['next_state'] == 's2'
        assert exp['done'] is False
        assert 'timestamp' in exp

    def test_add_experience_with_error_high_priority(self):
        from apps.backend.src.ai.learning.experience_replay import ExperienceReplayBuffer
        buffer = ExperienceReplayBuffer(capacity=10)
        buffer.add_experience(state='s1', action='a1', reward=0.0, next_state='s2', done=True, error='timeout')
        assert buffer.priorities[0] == 1.0

    def test_add_experience_without_error_default_priority(self):
        from apps.backend.src.ai.learning.experience_replay import ExperienceReplayBuffer
        buffer = ExperienceReplayBuffer(capacity=10)
        buffer.add_experience(state='s1', action='a1', reward=1.0, next_state='s2', done=False)
        assert buffer.priorities[0] == 0.5

    def test_add_experience_overwrites_when_full(self):
        from apps.backend.src.ai.learning.experience_replay import ExperienceReplayBuffer
        buffer = ExperienceReplayBuffer(capacity=3)
        for i in range(5):
            buffer.add_experience(state=f's{i}', action='a', reward=1.0, next_state='s2', done=False)
        assert len(buffer.buffer) == 3

    def test_add_experience_cycles_position(self):
        from apps.backend.src.ai.learning.experience_replay import ExperienceReplayBuffer
        buffer = ExperienceReplayBuffer(capacity=3)
        for i in range(6):
            buffer.add_experience(state=f's{i}', action='a', reward=1.0, next_state='s2', done=False)
        assert len(buffer.buffer) == 3
        assert buffer.buffer[0]['state'] == 's3'


class TestExperienceReplayBufferSample:
    def test_sample_returns_all_when_under_batch_size(self):
        from apps.backend.src.ai.learning.experience_replay import ExperienceReplayBuffer
        buffer = ExperienceReplayBuffer(capacity=10)
        for i in range(3):
            buffer.add_experience(state=f's{i}', action='a', reward=1.0, next_state='s2', done=False)
        sampled = buffer.sample_batch(batch_size=5)
        assert len(sampled) == 3

    def test_sample_with_random_fallback(self):
        from apps.backend.src.ai.learning.experience_replay import ExperienceReplayBuffer
        from apps.backend.src.ai.learning import experience_replay
        with patch.object(experience_replay, 'np', None):
            buffer = ExperienceReplayBuffer(capacity=100)
            for i in range(20):
                buffer.add_experience(state=f's{i}', action='a', reward=1.0, next_state=f's{i+1}', done=False)
            sampled = buffer.sample_batch(batch_size=5)
            assert len(sampled) == 5

    def test_sample_empty_buffer(self):
        from apps.backend.src.ai.learning.experience_replay import ExperienceReplayBuffer
        buffer = ExperienceReplayBuffer(capacity=10)
        sampled = buffer.sample_batch(batch_size=5)
        assert sampled == []


class TestExperienceReplayBufferPriority:
    def test_priority_list_matches_buffer_length(self):
        from apps.backend.src.ai.learning.experience_replay import ExperienceReplayBuffer
        buffer = ExperienceReplayBuffer(capacity=10)
        for i in range(5):
            buffer.add_experience(state=f's{i}', action='a', reward=1.0, next_state='s2', done=False)
        assert len(buffer.priorities) == len(buffer.buffer)
