"""Tests for apps.backend.src.ai.crisis.crisis_system"""
import sys
from unittest.mock import MagicMock, patch

import pytest

from apps.backend.src.ai.crisis.crisis_system import CrisisSystem


class TestCrisisSystemInit:
    def test_default_config(self):
        system = CrisisSystem()
        assert system.config == {}
        assert system.crisis_level == 0
        assert system.crisis_keywords == []
        assert system.negative_words == []
        assert system.default_crisis_level == 1
        assert system.crisis_protocols == {}
        assert system.emotion_system is None
        assert system.memory_system is None

    def test_custom_config(self):
        config = {
            'crisis_keywords': ['help', 'emergency'],
            'negative_words': ['sad', 'angry'],
            'default_crisis_level_on_keyword': 2,
            'crisis_protocols': {'1': 'monitor'},
        }
        system = CrisisSystem(config=config)
        assert system.crisis_keywords == ['help', 'emergency']
        assert system.negative_words == ['sad', 'angry']
        assert system.default_crisis_level == 2
        assert system.crisis_protocols == {'1': 'monitor'}

    def test_with_references(self):
        emotion = MagicMock()
        memory = MagicMock()
        system = CrisisSystem(emotion_system_ref=emotion, memory_system_ref=memory)
        assert system.emotion_system is emotion
        assert system.memory_system is memory

    @patch.object(CrisisSystem, '_load_config_from_file')
    def test_empty_config_loads_from_file(self, mock_load):
        system = CrisisSystem()
        mock_load.assert_called_once()


class TestCrisisSystemAssessInput:
    def test_no_crisis_normal_input(self):
        config = {
            'crisis_keywords': ['help', 'emergency'],
            'negative_words': ['sad', 'angry', 'hate'],
            'default_crisis_level_on_keyword': 2,
        }
        system = CrisisSystem(config=config)
        level = system.assess_input_for_crisis({'text': 'Tell me a joke'})
        assert level == 0
        assert system.crisis_level == 0

    def test_crisis_keyword_detected(self):
        config = {
            'crisis_keywords': ['help', 'emergency'],
            'negative_words': [],
            'default_crisis_level_on_keyword': 2,
        }
        system = CrisisSystem(config=config)
        level = system.assess_input_for_crisis({'text': 'I need help right now'})
        assert level == 2
        assert system.crisis_level == 2

    def test_negative_words_trigger_level_1(self):
        config = {
            'crisis_keywords': [],
            'negative_words': ['sad', 'angry', 'hate', 'depressed'],
            'default_crisis_level_on_keyword': 1,
        }
        system = CrisisSystem(config=config)
        level = system.assess_input_for_crisis({'text': 'I feel sad and depressed'})
        assert level == 1
        assert system.crisis_level == 1

    def test_single_negative_word_no_crisis(self):
        config = {
            'crisis_keywords': [],
            'negative_words': ['sad', 'angry'],
            'default_crisis_level_on_keyword': 1,
        }
        system = CrisisSystem(config=config)
        level = system.assess_input_for_crisis({'text': 'I feel sad'})
        assert level == 0
        assert system.crisis_level == 0

    def test_maintains_crisis_level_on_non_crisis_input(self):
        config = {
            'crisis_keywords': ['help'],
            'negative_words': [],
            'default_crisis_level_on_keyword': 2,
        }
        system = CrisisSystem(config=config)
        system.crisis_level = 2
        level = system.assess_input_for_crisis({'text': 'Tell me a joke'})
        assert level == 2
        assert system.crisis_level == 2

    def test_crisis_level_escalation(self):
        config = {
            'crisis_keywords': ['help', 'emergency'],
            'negative_words': [],
            'default_crisis_level_on_keyword': 1,
        }
        system = CrisisSystem(config=config)
        system.crisis_level = 0
        level = system.assess_input_for_crisis({'text': 'I need help'})
        assert level == 1
        assert system.crisis_level == 1

    def test_input_with_context(self):
        config = {
            'crisis_keywords': ['help'],
            'negative_words': [],
            'default_crisis_level_on_keyword': 2,
        }
        system = CrisisSystem(config=config)
        level = system.assess_input_for_crisis({'text': 'help'}, context={'user_history': 'previous'})
        assert level == 2

    def test_empty_text(self):
        system = CrisisSystem()
        level = system.assess_input_for_crisis({'text': ''})
        assert level == 0


class TestCrisisSystemResolve:
    def test_resolve_crisis(self):
        system = CrisisSystem()
        system.crisis_level = 3
        system.resolve_crisis('User is safe')
        assert system.crisis_level == 0

    def test_get_current_crisis_level(self):
        system = CrisisSystem()
        assert system.get_current_crisis_level() == 0
        system.crisis_level = 2
        assert system.get_current_crisis_level() == 2


class TestCrisisSystemProtocol:
    @patch('apps.backend.src.ai.crisis.crisis_system.logging')
    def test_trigger_protocol_log_only(self, mock_logging):
        config = {
            'crisis_keywords': ['help'],
            'negative_words': [],
            'default_crisis_level_on_keyword': 1,
            'crisis_protocols': {'1': 'log_only'},
        }
        system = CrisisSystem(config=config)
        system._trigger_protocol(1, {'input_text': 'help', 'context': {}})
        mock_logging.info.assert_any_call(
            'CRISIS_INFO: Level 1 event logged. Details: {\'input_text\': \'help\', \'context\': {}}'
        )

    @patch('apps.backend.src.ai.crisis.crisis_system.logging')
    def test_trigger_protocol_notify_human(self, mock_logging):
        config = {
            'crisis_keywords': ['help'],
            'negative_words': [],
            'default_crisis_level_on_keyword': 1,
            'crisis_protocols': {'1': 'notify_human_moderator'},
        }
        system = CrisisSystem(config=config)
        system._trigger_protocol(1, {'input_text': 'help', 'context': {}})
        mock_logging.critical.assert_called_once()

    @patch('apps.backend.src.ai.crisis.crisis_system.logging')
    def test_trigger_protocol_unknown_still_logs(self, mock_logging):
        config = {
            'crisis_keywords': ['help'],
            'negative_words': [],
            'default_crisis_level_on_keyword': 1,
            'crisis_protocols': {'1': 'unknown_protocol'},
        }
        system = CrisisSystem(config=config)
        system._trigger_protocol(1, {'input_text': 'help', 'context': {}})
        mock_logging.info.assert_called()


class TestCrisisSystemLoadConfig:
    @patch('builtins.open', side_effect=FileNotFoundError)
    @patch('apps.backend.src.ai.crisis.crisis_system.logging')
    def test_load_config_file_not_found(self, mock_logging, mock_open):
        system = CrisisSystem.__new__(CrisisSystem)
        system._load_config_from_file()
        assert system.config == {}

    @patch('builtins.open')
    @patch('json.load')
    @patch('apps.backend.src.ai.crisis.crisis_system.logging')
    def test_load_config_success(self, mock_logging, mock_json_load, mock_open):
        mock_json_load.return_value = {'crisis_keywords': ['help']}
        system = CrisisSystem.__new__(CrisisSystem)
        system._load_config_from_file()
        assert system.config == {'crisis_keywords': ['help']}
