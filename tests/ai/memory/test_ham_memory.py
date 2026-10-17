"""Test HAM Memory System"""

import pytest


async def test_ham_types_import():
    """Test HAM types module can be imported"""
    from ai.memory.ham_memory.ham_types import (
        HAMDataPackageInternal,
        HAMMemory,
        HAMMemoryError,
        HAMRecallResult,
    )

    assert HAMDataPackageInternal is not None
    assert HAMMemory is not None
    assert HAMRecallResult is not None
    assert HAMMemoryError is not None


async def test_ham_errors_import():
    """Test HAM errors module can be imported"""
    from ai.memory.ham_memory.ham_errors import (
        HAMInitializationError,
        HAMMemoryError,
        HAMRetrievalError,
        HAMStorageError,
    )

    assert HAMMemoryError is not None
    assert HAMInitializationError is not None
    assert HAMStorageError is not None
    assert HAMRetrievalError is not None


async def test_ham_utils_import():
    """Test HAM utils module can be imported"""
    from ai.memory import ham_utils

    assert ham_utils is not None
    assert hasattr(ham_utils, "stopwords")


async def test_ham_manager_import():
    """Test HAM manager can be imported"""
    from ai.memory.ham_memory.ham_manager import HAMMemoryManager

    assert HAMMemoryManager is not None


async def test_ham_vector_store_import():
    """Test HAM vector store manager can be imported"""
    from ai.memory.ham_memory.ham_vector_store_manager import HAMVectorStoreManager

    assert HAMVectorStoreManager is not None


async def test_ham_query_engine_import():
    """Test HAM query engine can be imported"""
    from ai.memory.ham_memory.ham_query_engine import HAMQueryEngine

    assert HAMQueryEngine is not None


async def test_ham_memory_types():
    """Test HAMMemory TypedDict structure"""
    from ai.memory.ham_memory.ham_types import HAMMemory

    sample = HAMMemory(
        memory_id="test_001",
        content="Test content",
        metadata={"key": "value"},
        relevance=0.8,
    )
    assert sample["memory_id"] == "test_001"
    assert sample["content"] == "Test content"


class TestUnservableTemplateGuard:
    """Fossilized garbage must never be served (live poison 2026-10-09)."""

    def _manager(self, tmp_path):
        from ai.memory.ham_memory.ham_manager import HAMMemoryManager

        m = HAMMemoryManager(memory_file=str(tmp_path / "ham.json"), auto_save=False)
        return m

    def test_is_unservable_markers(self):
        from ai.memory.ham_memory.ham_manager import is_unservable_template

        assert is_unservable_template("User, the question redirecting you to look up x")
        assert is_unservable_template("User: foo\nAngela: bar")
        assert is_unservable_template("Hi there! I'm Gemma 4, cute AI")
        assert is_unservable_template("Got it! Deleting the files /tmp/x")
        assert is_unservable_template("User，這個問題我目前還沒有足夠的知識")
        assert not is_unservable_template("光合作用是植物利用阳光合成有机物的过程。")
        assert not is_unservable_template("我是Angela AI，很高兴认识你！")

    @pytest.mark.asyncio
    async def test_retrieve_skips_unservable(self, tmp_path):
        m = self._manager(tmp_path)
        m._data["templates"] = [
            {
                "content": "User, the question you're asking redirecting you to look up y.",
                "id": "poison",
                "keywords": ["如果下雨那麼地會濕", "現在下雨了", "地濕嗎"],
            },
            {
                "content": "真正的答案",
                "id": "good",
                "keywords": ["如果下雨那麼地會濕", "現在下雨了"],
            },
        ]
        results = await m.retrieve_response_templates("如果下雨那麼地會濕，現在下雨了，地濕嗎？")
        ids = [tpl.get("id") for tpl, _ in results]
        assert "poison" not in ids
        assert "good" in ids


class TestMetadataStamping:
    """P1-9: top-level metadata had NO writer (永遠 {} for ham_game_memory
    4982 conversations). Every save must stamp self-describing provenance."""

    def _read(self, tmp_path):
        import json
        from pathlib import Path

        return json.loads(Path(tmp_path / "ham.json").read_text(encoding="utf-8"))

    @pytest.mark.asyncio
    async def test_metadata_stamped_on_save(self, tmp_path):
        from datetime import datetime

        from ai.memory.ham_memory.ham_manager import HAMMemoryManager

        m = HAMMemoryManager(memory_file=str(tmp_path / "ham.json"), auto_save=False)
        m._data["conversations"] = [{"content": "a"}, {"content": "b"}]
        m._data["templates"] = [{"content": "t"}]
        m._write_to_disk()

        meta = self._read(tmp_path)["metadata"]
        assert meta["schema_version"] == 1
        assert meta["conversation_count"] == 2
        assert meta["template_count"] == 1
        assert meta["bucket_cap"] == m._max_entries_per_bucket
        # saved_at must be a real UTC ISO timestamp
        parsed = datetime.fromisoformat(meta["saved_at"])
        assert parsed.tzinfo is not None

    @pytest.mark.asyncio
    async def test_caller_metadata_keys_preserved(self, tmp_path):
        from ai.memory.ham_memory.ham_manager import HAMMemoryManager

        m = HAMMemoryManager(memory_file=str(tmp_path / "ham.json"), auto_save=False)
        m._data["metadata"] = {"custom_key": "keep-me"}
        m._write_to_disk()

        meta = self._read(tmp_path)["metadata"]
        assert meta["custom_key"] == "keep-me"
        assert meta["schema_version"] == 1

    @pytest.mark.asyncio
    async def test_legacy_empty_metadata_upgraded_on_reload(self, tmp_path):
        import json
        from pathlib import Path

        from ai.memory.ham_memory.ham_manager import HAMMemoryManager

        # reproduce the real on-disk state: metadata恒空
        legacy = {"templates": [], "conversations": [{"content": "old"}], "metadata": {}}
        Path(tmp_path / "ham.json").write_text(json.dumps(legacy), encoding="utf-8")

        m = HAMMemoryManager(memory_file=str(tmp_path / "ham.json"), auto_save=False)
        assert m._data["metadata"] == {}, "load must not mutate (read path stays pure)"
        m._write_to_disk()  # _save() early-returns when auto_save=False
        meta = self._read(tmp_path)["metadata"]
        assert meta["schema_version"] == 1
        assert meta["conversation_count"] == 1

    @pytest.mark.asyncio
    async def test_non_dict_metadata_replaced(self, tmp_path):
        from ai.memory.ham_memory.ham_manager import HAMMemoryManager

        m = HAMMemoryManager(memory_file=str(tmp_path / "ham.json"), auto_save=False)
        m._data["metadata"] = "corrupted"
        m._write_to_disk()

        meta = self._read(tmp_path)["metadata"]
        assert isinstance(meta, dict)
        assert meta["schema_version"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
