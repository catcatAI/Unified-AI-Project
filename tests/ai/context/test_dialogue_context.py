import sys
from unittest.mock import MagicMock

_MODULE_MOCKS = {}
for name, mock in _MODULE_MOCKS.items():
    if name not in sys.modules:
        sys.modules[name] = mock

from datetime import datetime

import pytest

from apps.backend.src.ai.context.dialogue_context import (
    ContextSummary,
    Conversation,
    DialogueContextManager,
    Message,
)


class TestMessage:
    def test_creation(self):
        msg = Message('alice', 'Hello!', 'text')
        assert msg.sender == 'alice'
        assert msg.content == 'Hello!'
        assert msg.message_type == 'text'
        assert isinstance(msg.timestamp, datetime)
        assert msg.metadata == {}
        assert msg.message_id.startswith('msg_')

    def test_default_message_type(self):
        msg = Message('bob', 'Hi')
        assert msg.message_type == 'text'


class TestConversation:
    def test_creation(self):
        conv = Conversation('conv1', ['alice', 'bob'])
        assert conv.conversation_id == 'conv1'
        assert conv.participants == ['alice', 'bob']
        assert conv.messages == []
        assert isinstance(conv.start_time, datetime)
        assert conv.end_time is None
        assert conv.context_summary is None

    def test_add_message(self):
        conv = Conversation('conv1', ['alice'])
        msg = Message('alice', 'Hi')
        conv.add_message(msg)
        assert len(conv.messages) == 1
        assert conv.messages[0] is msg

    def test_complete(self):
        conv = Conversation('conv1', ['alice'])
        assert conv.end_time is None
        conv.complete()
        assert conv.end_time is not None


class TestContextSummary:
    def test_creation(self):
        summary = ContextSummary()
        assert summary.key_points == []
        assert summary.entities == []
        assert summary.intents == []
        assert summary.sentiment == 'neutral'
        assert summary.relevance_score == 0.0


class TestDialogueContextManager:
    def test_init(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        assert mgr.context_manager is mock_cm
        assert mgr.conversations == {}

    def test_start_conversation(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        result = mgr.start_conversation('conv1', ['alice', 'bob'])
        assert result is True
        assert 'conv1' in mgr.conversations
        assert mgr.conversations['conv1'].participants == ['alice', 'bob']

    def test_add_message(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        mgr.start_conversation('conv1', ['alice'])
        result = mgr.add_message('conv1', 'alice', 'Hello!')
        assert result is True
        assert len(mgr.conversations['conv1'].messages) == 1
        assert mgr.conversations['conv1'].messages[0].content == 'Hello!'

    def test_add_message_conversation_not_found(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        result = mgr.add_message('nonexistent', 'alice', 'Hi')
        assert result is False

    def test_extract_key_points(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        text = 'This is a long enough sentence. Another significant point here. Short.'
        points = mgr.extract_key_points(text)
        assert len(points) == 2
        assert 'This is a long enough sentence' in points
        assert 'Another significant point here' in points

    def test_extract_entities(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        text = 'Contact test@example.com or visit https://example.com on 2024-01-01'
        entities = mgr.extract_entities(text)
        assert 'test@example.com' in entities
        assert 'https://example.com' in entities
        assert '2024-01-01' in entities

    def test_analyze_sentiment_positive(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        assert mgr.analyze_sentiment('This is great and wonderful!') == 'positive'

    def test_analyze_sentiment_negative(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        assert mgr.analyze_sentiment('This is terrible and awful!') == 'negative'

    def test_analyze_sentiment_neutral(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        assert mgr.analyze_sentiment('This is a table.') == 'neutral'

    def test_generate_context_summary(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        mgr.start_conversation('conv1', ['alice', 'bob'])
        mgr.add_message('conv1', 'alice', 'This is a great conversation about AI!')
        summary = mgr.generate_context_summary('conv1')
        assert summary is not None
        assert len(summary.key_points) > 0
        assert summary.sentiment == 'positive'

    def test_generate_context_summary_not_found(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        assert mgr.generate_context_summary('nonexistent') is None

    def test_get_conversation_context_not_found(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        assert mgr.get_conversation_context('nonexistent') is None

    def test_get_recent_conversations(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        mgr.start_conversation('conv1', ['alice'])
        mgr.start_conversation('conv2', ['bob'])
        recent = mgr.get_recent_conversations()
        assert len(recent) == 2
        assert recent[0]['conversation_id'] == 'conv2'
        assert recent[1]['conversation_id'] == 'conv1'

    def test_transfer_context(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        mgr.start_conversation('src', ['alice'])
        mgr.start_conversation('tgt', ['bob'])
        mgr.add_message('src', 'alice', 'Great work!')
        mgr.generate_context_summary('src')
        result = mgr.transfer_context('src', 'tgt')
        assert result is True
        assert mgr.conversations['tgt'].context_summary is not None

    def test_transfer_context_source_not_found(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        mgr.start_conversation('tgt', ['bob'])
        assert mgr.transfer_context('nonexistent', 'tgt') is False

    def test_transfer_context_target_not_found(self):
        mock_cm = MagicMock()
        mgr = DialogueContextManager(mock_cm)
        mgr.start_conversation('src', ['alice'])
        assert mgr.transfer_context('src', 'nonexistent') is False
