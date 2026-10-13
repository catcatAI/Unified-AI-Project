"""
ANGELA-MATRIX: [L4] [β] [C] [L0]

MemoryViewer panel contract — reproduces the live defect found 2026-10-13 by
simulating real chat turns: every row returned by GET /context/memory/recent
came back with ``type: ""``, ``importance: 0.0``, ``emotion: ""`` and
``timestamp: null``, so the panel was unusable.

Root causes guarded here:
  * ``store_experience()`` never stamped ``metadata.timestamp``
  * ``query_core_memory()`` filtered on the ``type`` key while the store
    writes ``data_type``
  * ``_as_memory_object()`` did not expose ``data_type``
  * the chat store path never wrote emotion/importance metadata
  * aware-UTC timestamps made the time-decay scorer fall back to 0.5
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apps", "backend", "src")
)

import pytest
from ai.memory.ham_memory.ham_importance_scorer import ImportanceScorer as _AsyncScorer
from ai.memory.ham_memory.ham_manager import HAMMemoryManager


@pytest.fixture
def ham(tmp_path):
    manager = HAMMemoryManager(memory_file=str(tmp_path / "ham.json"), auto_save=False)
    return manager


class TestStoreExperienceMetadata:
    def test_stamps_timestamp_when_absent(self, ham):
        entry_id = asyncio.run(
            ham.store_experience(
                raw_data={"user": "hi", "assistant": "hello"}, data_type="conversation"
            )
        )
        assert entry_id
        stored = ham._data["conversations"][-1]
        assert stored["metadata"].get("timestamp"), "timestamp must be stamped on store"

    def test_preserves_caller_supplied_timestamp(self, ham):
        iso = "2020-01-02T03:04:05+00:00"
        asyncio.run(
            ham.store_experience(
                raw_data="keep me", data_type="conversation", metadata={"timestamp": iso}
            )
        )
        stored = ham._data["conversations"][-1]
        assert stored["metadata"]["timestamp"] == iso

    def test_preserves_emotion_and_importance(self, ham):
        asyncio.run(
            ham.store_experience(
                raw_data="note",
                data_type="conversation",
                metadata={"emotion": "curious", "importance": 0.42},
            )
        )
        stored = ham._data["conversations"][-1]
        assert stored["metadata"]["emotion"] == "curious"
        assert stored["metadata"]["importance"] == pytest.approx(0.42)

    def test_conversation_bucket_not_templates(self, ham):
        asyncio.run(ham.store_experience(raw_data="x", data_type="conversation"))
        assert any(c.get("data_type") == "conversation" for c in ham._data["conversations"])
        assert not any(c.get("data_type") == "conversation" for c in ham._data["templates"])


class TestQueryCoreMemory:
    def test_data_type_filter_uses_data_type_key(self, ham):
        asyncio.run(ham.store_experience(raw_data="a", data_type="conversation"))
        asyncio.run(ham.store_experience(raw_data="b", data_type="behavior_learning"))

        matched = asyncio.run(ham.query_core_memory(data_type_filter="conversation"))
        assert matched, "filter must match records written with data_type="
        assert all(m.data_type == "conversation" for m in matched)

    def test_exposes_data_type_attribute(self, ham):
        asyncio.run(ham.store_experience(raw_data="a", data_type="conversation"))
        results = asyncio.run(ham.query_core_memory(limit=5))
        assert results
        assert results[0].data_type == "conversation"

    def test_metadata_carried_through(self, ham):
        asyncio.run(
            ham.store_experience(
                raw_data="a", data_type="conversation", metadata={"emotion": "calm"}
            )
        )
        results = asyncio.run(ham.query_core_memory(limit=1))
        assert results[0].metadata["emotion"] == "calm"
        assert results[0].metadata.get("timestamp")

    def test_keyword_still_filters(self, ham):
        asyncio.run(ham.store_experience(raw_data="I like python", data_type="conversation"))
        asyncio.run(ham.store_experience(raw_data="I like rust", data_type="conversation"))
        matched = asyncio.run(ham.query_core_memory(keywords=["python"]))
        assert len(matched) == 1
        assert "python" in matched[0].content


class TestMemoryObjectContract:
    def test_content_stays_raw_dict(self, ham):
        """game_memory_bridge branches on isinstance(content, dict) — it must not be str()."""
        asyncio.run(
            ham.store_experience(
                raw_data={"action": "dig", "position": "1,2", "outcome": "ok"},
                data_type="game_experience",
            )
        )
        results = asyncio.run(ham.query_core_memory(limit=1))
        assert isinstance(results[0].content, dict)
        assert results[0].content["action"] == "dig"

    def test_dict_like_get_for_cli(self, ham):
        asyncio.run(
            ham.store_experience(
                raw_data={"user": "a", "assistant": "b"},
                data_type="conversation",
                metadata={"importance": 0.7},
            )
        )
        r = asyncio.run(ham.query_core_memory(limit=1))[0]
        assert r.get("importance") == pytest.approx(0.7)
        assert r.get("category", "?") == "?"
        assert r.get("data_type") == "conversation"

    def test_string_content_unchanged(self, ham):
        asyncio.run(ham.store_experience(raw_data="plain string", data_type="conversation"))
        results = asyncio.run(ham.query_core_memory(limit=1))
        assert results[0].content == "plain string"


class TestMemoryRecentRendering:
    def test_dict_content_renders_speaker_parts(self):
        from api.routes.context_routes import _render_memory_content

        rendered = _render_memory_content({"user": "我不吃辣", "assistant": "我記住了"})
        assert rendered == "我不吃辣 | 我記住了"
        assert "{" not in rendered and "'" not in rendered

    def test_none_and_scalar_content(self):
        from api.routes.context_routes import _render_memory_content

        assert _render_memory_content(None) == ""
        assert _render_memory_content("plain text") == "plain text"
        assert len(_render_memory_content("x" * 500)) == 200


class TestChatMetadataBuilder:
    def test_emotion_dict_and_importance(self):
        from services.chat_service import ChatService

        metadata = asyncio.run(
            ChatService._build_memory_metadata(
                None, "user asks about python", {"emotion": {"emotion": "curious"}}
            )
        )
        assert metadata["emotion"] == "curious"
        assert isinstance(metadata["importance"], float)
        assert 0.0 <= metadata["importance"] <= 1.0

    def test_emotion_string_and_no_context(self):
        from services.chat_service import ChatService

        metadata = asyncio.run(ChatService._build_memory_metadata(None, "hello", None))
        assert "emotion" not in metadata
        assert isinstance(metadata.get("importance"), float)


class TestImportanceScorerTimestamp:
    def test_aware_timestamp_scores_as_recent(self):
        """Aware ISO timestamps must not hit the naive/aware TypeError fallback."""
        scorer = _AsyncScorer()
        aware = datetime.now(timezone.utc).isoformat()
        score = asyncio.run(scorer.calculate("remember this", {"timestamp": aware}))
        assert score > 0.0
        assert scorer._calculate_time_score(aware) == 1.0

    def test_naive_timestamp_still_works(self):
        scorer = _AsyncScorer()
        assert scorer._calculate_time_score(datetime.now()) == 1.0

    def test_missing_timestamp_is_maximally_recent(self):
        scorer = _AsyncScorer()
        assert scorer._calculate_time_score(None) == 1.0
