import sys
from unittest.mock import MagicMock

_MODULE_MOCKS = {}
for name, mock in _MODULE_MOCKS.items():
    if name not in sys.modules:
        sys.modules[name] = mock

from datetime import datetime, timedelta

import pytest

from apps.backend.src.ai.context.memory_context import Memory, MemoryContextManager


class TestMemory:
    def test_creation(self):
        mem = Memory('Some content', 'short_term')
        assert mem.content == 'Some content'
        assert mem.memory_type == 'short_term'
        assert mem.access_count == 0
        assert mem.embedding is None
        assert mem.metadata == {}
        assert isinstance(mem.created_at, datetime)
        assert isinstance(mem.last_accessed, datetime)
        assert mem.memory_id.startswith('mem_')

    def test_default_memory_type(self):
        mem = Memory('content')
        assert mem.memory_type == 'short_term'

    def test_access(self):
        mem = Memory('content')
        old_time = mem.last_accessed
        assert mem.access_count == 0
        mem.access()
        assert mem.access_count == 1
        assert mem.last_accessed >= old_time


class TestMemoryContextManager:
    def test_init(self):
        mock_cm = MagicMock()
        mgr = MemoryContextManager(mock_cm)
        assert mgr.context_manager is mock_cm
        assert mgr.memories == {}

    def test_create_memory(self):
        mock_cm = MagicMock()
        mgr = MemoryContextManager(mock_cm)
        mem_id = mgr.create_memory('Test content', 'short_term')
        assert mem_id is not None
        assert mem_id in mgr.memories
        assert mgr.memories[mem_id].content == 'Test content'
        assert mgr.memories[mem_id].memory_type == 'short_term'

    def test_create_memory_with_metadata(self):
        mock_cm = MagicMock()
        mgr = MemoryContextManager(mock_cm)
        meta = {'source': 'test', 'priority': 1}
        mem_id = mgr.create_memory('content', metadata=meta)
        assert mgr.memories[mem_id].metadata == meta

    def test_access_memory(self):
        mock_cm = MagicMock()
        mgr = MemoryContextManager(mock_cm)
        mem_id = mgr.create_memory('Test content')
        result = mgr.access_memory(mem_id)
        assert result is not None
        assert result['content'] == 'Test content'
        assert result['access_count'] == 1
        assert mgr.memories[mem_id].access_count == 1

    def test_access_memory_not_found(self):
        mock_cm = MagicMock()
        mgr = MemoryContextManager(mock_cm)
        assert mgr.access_memory('nonexistent') is None

    def test_update_memory_embedding(self):
        mock_cm = MagicMock()
        mgr = MemoryContextManager(mock_cm)
        mem_id = mgr.create_memory('Test content')
        embedding = [0.1, 0.2, 0.3]
        result = mgr.update_memory_embedding(mem_id, embedding)
        assert result is True
        assert mgr.memories[mem_id].embedding == embedding

    def test_update_memory_embedding_not_found(self):
        mock_cm = MagicMock()
        mgr = MemoryContextManager(mock_cm)
        assert mgr.update_memory_embedding('nonexistent', [0.1]) is False

    def test_get_memory_context_not_found(self):
        mock_cm = MagicMock()
        mgr = MemoryContextManager(mock_cm)
        assert mgr.get_memory_context('nonexistent') is None

    def test_get_memories_by_type(self):
        mock_cm = MagicMock()
        mgr = MemoryContextManager(mock_cm)
        mgr.create_memory('Short term content', 'short_term')
        mgr.create_memory('Long term content', 'long_term')
        mgr.create_memory('Another short', 'short_term')
        short_memories = mgr.get_memories_by_type('short_term')
        assert len(short_memories) == 2
        long_memories = mgr.get_memories_by_type('long_term')
        assert len(long_memories) == 1

    def test_cleanup_old_memories(self):
        mock_cm = MagicMock()
        mgr = MemoryContextManager(mock_cm)
        mem_id = mgr.create_memory('Recent')
        old_mem = Memory('Old')
        old_mem.last_accessed = datetime.now() - timedelta(days=100)
        mgr.memories[old_mem.memory_id] = old_mem
        deleted = mgr.cleanup_old_memories(days=30)
        assert deleted == 1
        assert old_mem.memory_id not in mgr.memories
        assert mem_id in mgr.memories

    def test_transfer_memory(self):
        mock_cm = MagicMock()
        mgr = MemoryContextManager(mock_cm)
        src_id = mgr.create_memory('Important info', 'short_term')
        new_id = mgr.transfer_memory(src_id, 'long_term')
        assert new_id is not None
        assert new_id != src_id
        assert mgr.memories[new_id].memory_type == 'long_term'
        assert mgr.memories[new_id].content == 'Important info'

    def test_transfer_memory_with_embedding(self):
        mock_cm = MagicMock()
        mgr = MemoryContextManager(mock_cm)
        src_id = mgr.create_memory('Info', 'short_term')
        mgr.update_memory_embedding(src_id, [0.5, 0.5])
        new_id = mgr.transfer_memory(src_id, 'long_term')
        assert mgr.memories[new_id].embedding == [0.5, 0.5]

    def test_transfer_memory_not_found(self):
        mock_cm = MagicMock()
        mgr = MemoryContextManager(mock_cm)
        assert mgr.transfer_memory('nonexistent', 'long_term') is None
