import sys
from unittest.mock import MagicMock, patch

_MODULE_MOCKS = {}
for name, mock in _MODULE_MOCKS.items():
    if name not in sys.modules:
        sys.modules[name] = mock

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from apps.backend.src.ai.context.manager_fixed import ContextManager, get_context_manager
from apps.backend.src.ai.context.storage.base import Context, ContextStatus, ContextType


class TestContextManager:
    def test_init(self):
        mgr = ContextManager()
        assert mgr.memory_storage is not None
        assert mgr.disk_storage is not None
        assert mgr._context_cache == {}

    def test_init_with_custom_storage(self):
        mock_mem = MagicMock()
        mock_disk = MagicMock()
        mgr = ContextManager(memory_storage=mock_mem, disk_storage=mock_disk)
        assert mgr.memory_storage is mock_mem
        assert mgr.disk_storage is mock_disk

    def test_create_context(self):
        mgr = ContextManager()
        ctx_id = mgr.create_context(ContextType.TOOL, {'key': 'value'})
        assert ctx_id is not None
        assert isinstance(ctx_id, str)
        assert ctx_id in mgr._context_cache
        ctx = mgr.get_context(ctx_id)
        assert ctx is not None
        assert ctx.context_type == ContextType.TOOL
        assert ctx.content['key'] == 'value'

    def test_create_context_without_content(self):
        mgr = ContextManager()
        ctx_id = mgr.create_context(ContextType.MEMORY)
        assert ctx_id is not None
        ctx = mgr.get_context(ctx_id)
        assert ctx.context_type == ContextType.MEMORY

    def test_create_context_all_types(self):
        mgr = ContextManager()
        for ctype in ContextType:
            ctx_id = mgr.create_context(ctype)
            ctx = mgr.get_context(ctx_id)
            assert ctx.context_type == ctype

    def test_get_context_not_found(self):
        mgr = ContextManager()
        assert mgr.get_context('nonexistent') is None

    def test_get_context_from_cache(self):
        mgr = ContextManager()
        ctx_id = mgr.create_context(ContextType.TOOL)
        ctx1 = mgr.get_context(ctx_id)
        # Should come from cache the second time
        mgr.memory_storage.load_context = MagicMock(return_value=None)
        ctx2 = mgr.get_context(ctx_id)
        assert ctx2 is not None
        assert ctx2.context_id == ctx1.context_id

    def test_update_context(self):
        mgr = ContextManager()
        ctx_id = mgr.create_context(ContextType.TOOL, {'a': 1})
        result = mgr.update_context(ctx_id, {'b': 2})
        assert result is True
        ctx = mgr.get_context(ctx_id)
        assert ctx.content['a'] == 1
        assert ctx.content['b'] == 2

    def test_update_context_not_found(self):
        mgr = ContextManager()
        result = mgr.update_context('nonexistent', {'a': 1})
        assert result is False

    def test_delete_context(self):
        mgr = ContextManager()
        ctx_id = mgr.create_context(ContextType.TOOL)
        result = mgr.delete_context(ctx_id)
        assert result is True
        assert mgr.get_context(ctx_id) is None

    def test_delete_context_not_found(self):
        mgr = ContextManager()
        # Deleting nonexistent should return False (both storage delete return False)
        result = mgr.delete_context('nonexistent')
        assert result is False

    def test_search_contexts(self):
        mgr = ContextManager()
        ctx_id = mgr.create_context(ContextType.TOOL, {'name': 'calculator'})
        mgr.create_context(ContextType.MEMORY, {'name': 'memories'})
        results = mgr.search_contexts('calculator')
        assert len(results) == 1
        assert results[0].context_id == ctx_id

    def test_search_contexts_by_type(self):
        mgr = ContextManager()
        mgr.create_context(ContextType.TOOL, {'name': 'hammer'})
        mgr.create_context(ContextType.MEMORY, {'name': 'hammer'})
        results = mgr.search_contexts('hammer', context_types=[ContextType.TOOL])
        assert len(results) == 1
        assert results[0].context_type == ContextType.TOOL

    def test_transfer_context(self):
        mgr = ContextManager()
        src_id = mgr.create_context(ContextType.TOOL, {'data': 'important'})
        tgt_id = mgr.create_context(ContextType.TOOL, {})
        result = mgr.transfer_context(src_id, tgt_id)
        assert result is True
        tgt = mgr.get_context(tgt_id)
        assert tgt.content['data'] == 'important'

    def test_transfer_context_source_not_found(self):
        mgr = ContextManager()
        tgt_id = mgr.create_context(ContextType.TOOL)
        assert mgr.transfer_context('nonexistent', tgt_id) is False

    def test_transfer_context_target_not_found(self):
        mgr = ContextManager()
        src_id = mgr.create_context(ContextType.TOOL)
        assert mgr.transfer_context(src_id, 'nonexistent') is False

    def test_transfer_context_with_filter(self):
        mgr = ContextManager()
        src_id = mgr.create_context(ContextType.TOOL, {'keep': 'this', 'drop': 'that'})
        tgt_id = mgr.create_context(ContextType.TOOL, {})
        result = mgr.transfer_context(src_id, tgt_id, filter_criteria={'drop': 'other'})
        assert result is True
        tgt = mgr.get_context(tgt_id)
        assert 'keep' in tgt.content
        assert 'drop' not in tgt.content

    def test_get_context_summary(self):
        mgr = ContextManager()
        ctx_id = mgr.create_context(ContextType.TOOL, {'key': 'val'})
        summary = mgr.get_context_summary(ctx_id)
        assert summary['context_id'] == ctx_id
        assert summary['context_type'] == 'tool'
        assert summary['content_keys'] == ['key']
        assert summary['status'] == 'active'

    def test_get_context_summary_not_found(self):
        mgr = ContextManager()
        assert mgr.get_context_summary('nonexistent') == {}

    def test_context_lifecycle(self):
        mgr = ContextManager()
        ctx_id = mgr.create_context(ContextType.DIALOGUE, {'msg': 'hello'})
        assert mgr.get_context(ctx_id) is not None
        assert mgr.update_context(ctx_id, {'msg': 'world'}) is True
        ctx = mgr.get_context(ctx_id)
        assert ctx.content['msg'] == 'world'
        assert mgr.delete_context(ctx_id) is True
        assert mgr.get_context(ctx_id) is None


class TestGetContextManager:
    def setup_method(self):
        from apps.backend.src.ai.context.manager_fixed import _context_manager
        self._old = _context_manager

    def teardown_method(self):
        from apps.backend.src.ai.context.manager_fixed import _context_manager
        import apps.backend.src.ai.context.manager_fixed as m
        m._context_manager = self._old

    def test_get_context_manager(self):
        from apps.backend.src.ai.context import manager_fixed as m
        m._context_manager = None
        instance = get_context_manager()
        assert isinstance(instance, ContextManager)

    def test_get_context_manager_singleton(self):
        from apps.backend.src.ai.context import manager_fixed as m
        m._context_manager = None
        instance1 = get_context_manager()
        instance2 = get_context_manager()
        assert instance1 is instance2

    def test_get_context_manager_with_storage(self):
        from apps.backend.src.ai.context import manager_fixed as m
        m._context_manager = None
        mock_mem = MagicMock()
        mock_disk = MagicMock()
        instance = get_context_manager(mock_mem, mock_disk)
        assert instance.memory_storage is mock_mem
        assert instance.disk_storage is mock_disk
