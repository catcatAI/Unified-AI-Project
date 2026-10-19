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


class TestSubjectCoverageGuard:
    """2026-10-19 稽核：'What is the capital of Australia?' 以 0.9 信心命中
    'what is the capital of Japan: Tokyo.' 模板（答錯國名 + 自我污染）。
    主體守衛：查詢 ≥2 非停用詞、模板只覆蓋 ≤1 且內容未提未覆蓋詞 → 拒絕。"""

    def _manager(self, tmp_path):
        from ai.memory.ham_memory.ham_manager import HAMMemoryManager

        return HAMMemoryManager(memory_file=str(tmp_path / "ham.json"), auto_save=False)

    @pytest.mark.asyncio
    async def test_wrong_subject_rejected(self, tmp_path):
        m = self._manager(tmp_path)
        m._data["templates"] = [
            {
                "content": "what is the capital of Japan: Tokyo.",
                "id": "japan_capital",
                "keywords": ["what", "is", "the", "capital", "of"],
            },
        ]
        results = await m.retrieve_response_templates("What is the capital of Australia?")
        assert results == []

    @pytest.mark.asyncio
    async def test_right_subject_still_serves(self, tmp_path):
        m = self._manager(tmp_path)
        m._data["templates"] = [
            {
                "content": "what is the capital of Japan: Tokyo.",
                "id": "japan_capital",
                "keywords": ["what", "is", "the", "capital", "of"],
            },
        ]
        results = await m.retrieve_response_templates("What is the capital of Japan?")
        ids = [tpl.get("id") for tpl, _ in results]
        assert "japan_capital" in ids

    @pytest.mark.asyncio
    async def test_filler_words_do_not_false_reject(self, tmp_path):
        """疑問填充詞（what's/like）不算 distinctive——天氣模板仍須命中。"""
        m = self._manager(tmp_path)
        m._data["templates"] = [
            {
                "content": "The weather is nice today! Wanna go out?",
                "id": "weather_en",
                "keywords": ["weather", "nice", "today"],
            },
        ]
        results = await m.retrieve_response_templates("what's the weather like?")
        ids = [tpl.get("id") for tpl, _ in results]
        assert "weather_en" in ids

    def test_extract_keywords_keeps_subject(self):
        """存庫端根因：_extract_keywords 曾存出全停用詞關鍵詞（主體被 [:5] 截掉）。"""
        from services.llm.router import AngelaLLMService

        kws = AngelaLLMService._extract_keywords(None, "What is the capital of Japan?")
        assert "Japan" in kws
        assert "capital" in kws
        assert "what" not in [k.lower() for k in kws]
        assert "the" not in [k.lower() for k in kws]


class TestUnservableEnglishAbstain:
    """router 英文 honest-abstain 文案必須被毒化守衛攔截（鏡像同步契約）。"""

    def test_honest_abstain_en_markers(self):
        from ai.memory.ham_memory.ham_manager import is_unservable_template

        assert is_unservable_template(
            "You, I don't have enough knowledge to answer this correctly yet. "
            "You can ask me math, logic, or facts I've learned."
        )
        assert is_unservable_template(
            "You, I can't complete this task right now (no language model is available)."
        )
        assert not is_unservable_template("The capital of France is Paris.")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
