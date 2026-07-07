# =============================================================================
# ANGELA-MATRIX: [L3] [αδ] [B] [L2]
# =============================================================================

"""Tests for DictionaryClassifier online learning and calibration."""

from typing import Generator, List

import pytest

from ai.core.dictionary_classifier import DictionaryClassifier


@pytest.fixture
def dc() -> Generator[DictionaryClassifier, None, None]:
    classifier = DictionaryClassifier()
    classifier._ensure_loaded()
    yield classifier
    # Cleanup in-memory test entries (no persist)
    for key in list(classifier._training_data.keys()):
        if key.startswith("cls_learn_"):
            classifier._training_data.pop(key)
            if classifier._dictionary and key in classifier._dictionary.entries:
                del classifier._dictionary.entries[key]


def _learn_no_persist(dc: DictionaryClassifier, text: str, qtype: str,
                       action: str = "none", conf: float = 0.5) -> str:
    """Learn without persisting to JSON (for test isolation)."""
    return dc.learn(text, qtype, action, confidence=conf, persist=False)


def _cleanup_keys(dc: DictionaryClassifier, keys: List[str]):
    """Remove test keys from memory only."""
    for key in keys:
        if key in dc._training_data:
            sf = dc._training_data[key].get("surface_forms", {}).get("zh", "")
            dc._training_data.pop(key)
            if dc._dictionary and key in dc._dictionary.entries:
                del dc._dictionary.entries[key]
            if sf and sf in dc._keyword_index:
                dc._keyword_index[sf] = [k for k in dc._keyword_index[sf] if k != key]
                if not dc._keyword_index[sf]:
                    del dc._keyword_index[sf]


class TestDictionaryClassifierLearning:
    """Online incremental learning tests (no persist)."""

    def test_learn_new_keyword_changes_classification(self, dc):
        r = dc.classify("播放一些輕音樂")

        key = _learn_no_persist(dc, "輕音樂", "audio", "read", conf=0.6)
        assert key.startswith("cls_learn_")

        r2 = dc.classify("播放一些輕音樂")
        assert r2[0] == "audio"
        assert r2[2] >= 0.5

        _cleanup_keys(dc, [key])

    def test_learn_exact_keyword_gets_confidence_boost(self, dc):
        key = _learn_no_persist(dc, "量子計算", "knowledge", "query", conf=0.5)
        r = dc.classify("量子計算")
        assert r[0] == "knowledge"
        _cleanup_keys(dc, [key])

    def test_learn_multiple_keywords_all_classify(self, dc):
        keys = []
        for word, qtype in [("冥想", "knowledge"), ("烘焙", "search"), ("笑話", "creative")]:
            k = _learn_no_persist(dc, word, qtype, "read", conf=0.5)
            keys.append(k)
            r = dc.classify(word)
            assert r[0] == qtype, f"{word} should be {qtype}, got {r[0]}"

        _cleanup_keys(dc, keys)

    def test_learn_idempotent_same_keyword(self, dc):
        key1 = _learn_no_persist(dc, "測試指令", "file", "action", conf=0.5)
        key2 = _learn_no_persist(dc, "測試指令", "file", "action", conf=0.5)
        assert key1 == key2
        _cleanup_keys(dc, [key1])

    def test_learn_overwrite_different_type(self, dc):
        key = _learn_no_persist(dc, "重要", "knowledge", "query", conf=0.5)
        r1 = dc.classify("重要")
        assert r1[0] == "knowledge"

        key2 = _learn_no_persist(dc, "重要", "task", "object", conf=0.5)
        assert key == key2

        r2 = dc.classify("重要")
        assert r2[0] == "task"
        _cleanup_keys(dc, [key])

    def test_forget_removes_entry(self, dc):
        key = _learn_no_persist(dc, "臨時指令", "execute", "action", conf=0.6)
        assert dc.forget(key)
        assert key not in dc._training_data
        if dc._dictionary:
            assert key not in dc._dictionary.entries

    def test_forget_unknown_key_returns_false(self, dc):
        assert not dc.forget("nonexistent_key")

    def test_cached_classification_invalidated_after_learn(self, dc):
        text = "祖魯語學習技巧"
        r_before = dc.classify(text)
        assert r_before[2] < 0.3, f"Expected low conf, got {r_before[2]}: {r_before}"

        key = _learn_no_persist(dc, "祖魯語", "knowledge", "query", conf=0.6)
        r_after = dc.classify(text)
        assert r_after[0] == "knowledge"
        assert r_after[2] >= 0.3

        _cleanup_keys(dc, [key])

    def test_learn_empty_text_returns_empty(self, dc):
        assert _learn_no_persist(dc, "", "knowledge", "query") == ""
        assert _learn_no_persist(dc, "   ", "knowledge", "query") == ""
