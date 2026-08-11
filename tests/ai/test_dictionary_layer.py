"""Tests for DictionaryLayer — including word sense disambiguation."""

import pytest


@pytest.fixture
def dictionary():
    from ai.ed3n.dictionary_layer import DictionaryLayer
    d = DictionaryLayer(max_entries=500)
    d.load_preset_responses()
    return d


class TestDisambiguate:

    def test_disambiguate_returns_all_keys(self, dictionary):
        keys = list(dictionary.entries.keys())[:3]
        allowed: int = dict  # placeholder
        from ai.ed3n.dictionary_layer import Dict
        result = dictionary.disambiguate(keys, {"topic": "greeting"})
        assert len(result) == len(keys)
        assert isinstance(result, list)

    def test_disambiguate_empty_context_returns_original(self, dictionary):
        keys = list(dictionary.entries.keys())[:2]
        result = dictionary.disambiguate(keys, {})
        assert result == keys

    def test_disambiguate_empty_keys_returns_empty(self, dictionary):
        assert dictionary.disambiguate([], {"key": "val"}) == []

    def test_disambiguate_context_reorders(self, dictionary):
        # Get emotion-related and greeting-related keys
        positive_key = "e1"
        hello_key = "g1"
        keys = [positive_key, hello_key]
        result = dictionary.disambiguate(keys, {"topic": "hello"})
        # The key matching "hello" should be first
        hello_entry = dictionary.entries.get(hello_key)
        if hello_entry and "hello" in hello_entry.surface_forms.get("en", "").lower():
            assert result[0] == hello_key


class TestAssignKey:
    def test_grow_does_not_overwrite_existing_key(self, dictionary):
        # grow() must never reuse an existing key (regression: _assign_key
        # started from _next_key_id=1 after JSON reload, overwriting l1..l1221)
        entries_before = len(dictionary.entries)
        key1 = dictionary.grow("AlphaTerm", "AlphaTerm", confidence=0.6)
        assert key1
        first_surface = dict(dictionary.entries.get(key1).surface_forms or {})
        key2 = dictionary.grow("BetaTerm", "BetaTerm", confidence=0.6)
        assert key2 != key1
        assert len(dictionary.entries) == entries_before + 2
        assert (dictionary.entries.get(key1).surface_forms or {}) == first_surface

    def test_grow_keys_unique_across_bulk_and_grow(self):
        from ai.ed3n.dictionary_layer import DictionaryLayer
        d = DictionaryLayer(max_entries=500)
        d.add_entry("c1", {"en": "existing"})
        # force _next_key_id to collide with c1
        d._next_key_id = 1
        key = d.grow("NewConcept", "NewConcept", confidence=0.6)
        assert key != "c1"
        assert key in d.entries
        assert "existing" in d.entries["c1"].surface_forms.values()
