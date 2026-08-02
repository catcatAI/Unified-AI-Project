"""ContextHAMIntegration 与 HAM 真实接口的集成测试"""

import tempfile

import pytest

from apps.backend.src.ai.context.integration_with_ham import ContextHAMIntegration
from apps.backend.src.ai.context.manager_fixed import ContextManager
from apps.backend.src.ai.memory.ham_memory.ham_manager import HAMMemoryManager


@pytest.fixture()
def integration():
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    ham = HAMMemoryManager(memory_file=tmp.name)
    mgr = ContextManager()
    return ContextHAMIntegration(mgr, ham), mgr, ham


class TestSyncContextToHAM:
    def test_sync_writes_conversation(self, integration):
        intg, mgr, ham = integration
        ctx_id = mgr.create_context("dialogue", {"hello": "world"})
        assert intg.sync_context_to_ham(ctx_id) is True
        assert len(ham._data["conversations"]) == 1
        record = ham._data["conversations"][0]
        assert record["context_id"] == ctx_id
        assert record["content"] == {"hello": "world"}

    def test_sync_missing_context_returns_false(self, integration):
        intg, mgr, ham = integration
        assert intg.sync_context_to_ham("does_not_exist") is False

    def test_sync_without_ham_returns_false(self, integration):
        intg, mgr, ham = integration
        intg.ham_manager = None
        ctx_id = mgr.create_context("dialogue", {"a": 1})
        assert intg.sync_context_to_ham(ctx_id) is False


class TestSyncHAMToContext:
    def test_roundtrip_sync_ham_to_context(self, integration):
        intg, mgr, ham = integration
        ctx_id = mgr.create_context("dialogue", {"k": "v"})
        intg.sync_context_to_ham(ctx_id)
        result = intg.sync_ham_to_context(ctx_id)
        assert result == f"ctx_ham_{ctx_id}"

    def test_sync_missing_ham_memory_returns_none(self, integration):
        intg, mgr, ham = integration
        assert intg.sync_ham_to_context("missing") is None

    def test_sync_without_ham_returns_none(self, integration):
        intg, mgr, ham = integration
        intg.ham_manager = None
        assert intg.sync_ham_to_context("any") is None


class TestCreateMemoryContextFromHAM:
    def test_create_memory_context(self, integration):
        intg, mgr, ham = integration
        ctx_id = intg.create_memory_context_from_ham({"content": "memory", "x": 1})
        assert ctx_id is not None
        ctx = mgr.get_context(ctx_id)
        assert ctx is not None
        assert ctx.content["x"] == 1

    def test_create_memory_context_returns_none_on_error(self, integration, monkeypatch):
        intg, mgr, ham = integration

        def _boom(*a, **k):
            raise RuntimeError("boom")

        monkeypatch.setattr(mgr, "create_context", _boom)
        assert intg.create_memory_context_from_ham({"content": "x"}) is None


class TestUpdateHAMFromMemoryContext:
    def test_update_existing_conversation(self, integration):
        intg, mgr, ham = integration
        ctx_id = mgr.create_context("dialogue", {"old": 1})
        intg.sync_context_to_ham(ctx_id)
        assert intg.update_ham_from_memory_context(ctx_id, {"content": {"new": 2}}) is True
        assert ham._data["conversations"][0]["content"] == {"new": 2}

    def test_update_missing_returns_false(self, integration):
        intg, mgr, ham = integration
        assert intg.update_ham_from_memory_context("missing", {"content": {}}) is False

    def test_update_without_ham_returns_false(self, integration):
        intg, mgr, ham = integration
        intg.ham_manager = None
        assert intg.update_ham_from_memory_context("any", {"content": {}}) is False


class TestTransferContextMemory:
    def test_transfer_creates_target(self, integration):
        intg, mgr, ham = integration
        ctx_id = mgr.create_context("dialogue", {"data": "value"})
        assert intg.transfer_context_memory(ctx_id, "long-term") is True
        matches = mgr.search_contexts("value")
        assert len(matches) >= 2

    def test_transfer_missing_source_returns_false(self, integration):
        intg, mgr, ham = integration
        assert intg.transfer_context_memory("missing", "long-term") is False

    def test_transfer_writes_to_ham(self, integration):
        intg, mgr, ham = integration
        ctx_id = mgr.create_context("dialogue", {"data": "value"})
        intg.transfer_context_memory(ctx_id, "long-term")
        records = [
            r for r in ham._data["conversations"] if r.get("memory_type") == "long-term"
        ]
        assert len(records) == 1
