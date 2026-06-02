"""Tests for MemoryStorage"""
import pytest
from apps.backend.src.ai.context.storage.memory import MemoryStorage
from apps.backend.src.ai.context.storage.base import Context, ContextType


class TestMemoryStorage:
    def test_import(self):
        from apps.backend.src.ai.context.storage.memory import MemoryStorage
        assert hasattr(MemoryStorage, 'save_context')
        assert hasattr(MemoryStorage, 'load_context')
        assert hasattr(MemoryStorage, 'delete_context')
        assert hasattr(MemoryStorage, 'list_contexts')
        assert hasattr(MemoryStorage, 'update_context_metadata')
        assert hasattr(MemoryStorage, 'get_storage_info')

    def test_instantiation(self):
        instance = MemoryStorage(max_size=100)
        assert instance.max_size == 100
        assert len(instance._storage) == 0

    def test_save_and_load_context(self):
        instance = MemoryStorage(max_size=100)
        ctx = Context("ctx-1", ContextType.DIALOGUE)
        assert instance.save_context(ctx) is True
        loaded = instance.load_context("ctx-1")
        assert loaded is not None
        assert loaded.context_id == "ctx-1"
        assert loaded.context_type == ContextType.DIALOGUE

    def test_load_nonexistent_context(self):
        instance = MemoryStorage(max_size=100)
        loaded = instance.load_context("no-such-ctx")
        assert loaded is None

    def test_delete_context(self):
        instance = MemoryStorage(max_size=100)
        ctx = Context("del-ctx", ContextType.MEMORY)
        instance.save_context(ctx)
        assert instance.delete_context("del-ctx") is True
        assert instance.load_context("del-ctx") is None

    def test_delete_nonexistent_context(self):
        instance = MemoryStorage(max_size=100)
        assert instance.delete_context("not-there") is False

    def test_list_contexts_all(self):
        instance = MemoryStorage(max_size=100)
        instance.save_context(Context("a", ContextType.DIALOGUE))
        instance.save_context(Context("b", ContextType.TOOL))
        instance.save_context(Context("c", ContextType.DIALOGUE))
        assert len(instance.list_contexts()) == 3

    def test_list_contexts_filtered(self):
        instance = MemoryStorage(max_size=100)
        instance.save_context(Context("a", ContextType.DIALOGUE))
        instance.save_context(Context("b", ContextType.TOOL))
        result = instance.list_contexts(ContextType.TOOL)
        assert result == ["b"]

    def test_update_context_metadata(self):
        instance = MemoryStorage(max_size=100)
        ctx = Context("meta-ctx", ContextType.CUSTOM)
        instance.save_context(ctx)
        assert instance.update_context_metadata("meta-ctx", {"key": "val"}) is True
        loaded = instance.load_context("meta-ctx")
        assert loaded.metadata["key"] == "val"

    def test_update_context_metadata_nonexistent(self):
        instance = MemoryStorage(max_size=100)
        assert instance.update_context_metadata("ghost", {"k": "v"}) is False

    def test_get_storage_info(self):
        instance = MemoryStorage(max_size=100)
        info = instance.get_storage_info()
        assert info["total_contexts"] == 0
        assert info["max_size"] == 100
        assert info["usage_percentage"] == 0.0
        instance.save_context(Context("x", ContextType.MEMORY))
        info = instance.get_storage_info()
        assert info["total_contexts"] == 1
        assert info["usage_percentage"] == 1.0

    def test_lru_eviction(self):
        instance = MemoryStorage(max_size=2)
        instance.save_context(Context("k1", ContextType.DIALOGUE))
        instance.save_context(Context("k2", ContextType.DIALOGUE))
        instance.save_context(Context("k3", ContextType.DIALOGUE))
        assert instance.load_context("k1") is None
        assert instance.load_context("k2") is not None
        assert instance.load_context("k3") is not None
