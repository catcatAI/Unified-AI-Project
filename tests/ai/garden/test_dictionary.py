# =============================================================================
# ANGELA-MATRIX: [L3] [αβ] [C] [L0]
# =============================================================================
"""
Tests for GARDEN VectorDictionary.
"""

import json
import os
import tempfile

import pytest

from apps.backend.src.ai.garden.dictionary import VectorDictionary


class TestVectorDictionaryInit:
    """Tests for VectorDictionary construction and basic properties."""

    def test_init_defaults(self):
        d = VectorDictionary()
        assert d.top_k == 8
        assert d.similarity_threshold == 0.30
        assert d.growth_threshold == 0.6
        assert len(d.entries) == 0
        assert d._matrix is None

    def test_init_custom(self):
        d = VectorDictionary(top_k=5, similarity_threshold=0.5, device="cpu")
        assert d.top_k == 5
        assert d.similarity_threshold == 0.5

    def test_encoder_created(self):
        d = VectorDictionary()
        assert d._encoder is not None

    def test_encoder_is_char_bag_fallback(self):
        """Without sentence-transformers, encoder should be char-bag."""
        d = VectorDictionary()
        assert "CharBag" in type(d._encoder).__name__ or "STEncoder" in type(d._encoder).__name__


class TestVectorDictionaryEntryManagement:
    """Tests for adding, finding, and managing concept entries."""

    def test_add_entry(self, dictionary: VectorDictionary):
        d = dictionary
        count_before = len(d.entries)
        d.add_entry(key="test1", surface_forms={"zh": "测试", "en": "test"})
        assert len(d.entries) == count_before + 1
        assert d.entries["test1"].key == "test1"
        assert d.entries["test1"].surface_forms["zh"] == "测试"

    def test_add_entry_with_relations(self, dictionary: VectorDictionary):
        d = dictionary
        d.add_entry(
            key="test_rel",
            surface_forms={"en": "test relation"},
            relations={"synonym": ["g1"], "mapping": ["r1"]},
        )
        assert "g1" in d.entries["test_rel"].relations["synonym"]
        assert "r1" in d.entries["test_rel"].relations["mapping"]

    def test_add_entry_dirty_flag(self, dictionary: VectorDictionary):
        d = dictionary
        d._dirty = False
        d.add_entry(key="new_entry", surface_forms={"en": "new"})
        assert d._dirty is True

    def test_grow_new_concept(self, dictionary: VectorDictionary):
        d = dictionary
        count_before = len(d.entries)
        key = d.grow("completely novel phrase", "全新短语", confidence=0.9)
        assert key.startswith("l")
        assert len(d.entries) == count_before + 1
        assert d.entries[key].surface_forms["en"] == "completely novel phrase"

    def test_grow_low_confidence(self, dictionary: VectorDictionary):
        d = dictionary
        count_before = len(d.entries)
        key = d.grow("novel", "新", confidence=0.1)
        assert key.startswith("l")  # grow still adds it (no threshold check in grow itself)

    def test_grow_duplicate(self, dictionary: VectorDictionary):
        d = dictionary
        key1 = d.grow("unique phrase here", "独特短语", confidence=0.9)
        key2 = d.grow("unique phrase here", "独特短语", confidence=0.9)
        assert key1 == key2  # Should return existing key

    def test_find_similar_key_exact(self, dictionary: VectorDictionary):
        d = dictionary
        key = d._find_similar_key("你好", threshold=0.85)
        assert key == "g1"

    def test_find_similar_key_none(self, dictionary: VectorDictionary):
        d = dictionary
        key = d._find_similar_key("zzz_nonexistent_zzz", threshold=0.85)
        assert key is None

    def test_get_synonyms_known(self, dictionary: VectorDictionary):
        d = dictionary
        syns = d.get_synonyms("g1")
        assert "g2" in syns
        assert "g3" in syns
        assert "g5" in syns

    def test_get_synonyms_unknown(self, dictionary: VectorDictionary):
        d = dictionary
        assert d.get_synonyms("nonexistent") == []

    def test_get_related_all(self, dictionary: VectorDictionary):
        d = dictionary
        related = d.get_related("e1")
        assert len(related) >= 1

    def test_get_related_by_type(self, dictionary: VectorDictionary):
        d = dictionary
        syn = d.get_related("e1", relation_type="synonym")
        assert "e5" in syn


class TestVectorDictionaryEncodeDecode:
    """Tests for the core encode/decode pipeline."""

    def test_encode_known_text(self, dictionary: VectorDictionary):
        d = dictionary
        keys = d.encode("你好")
        assert "g1" in keys
        assert isinstance(keys, list)

    def test_encode_english(self, dictionary: VectorDictionary):
        d = dictionary
        keys = d.encode("thank you")
        assert "p1" in keys

    def test_encode_unknown(self, dictionary: VectorDictionary):
        d = dictionary
        keys = d.encode("zxvqwpbj")
        assert keys == [] or not keys

    def test_encode_empty(self, dictionary: VectorDictionary):
        d = dictionary
        assert d.encode("") == []

    def test_encode_none(self, dictionary: VectorDictionary):
        d = dictionary
        assert d.encode(None) == []

    def test_encode_special_chars(self, dictionary: VectorDictionary):
        d = dictionary
        keys = d.encode("!!! @@@ ###")
        assert isinstance(keys, list)

    def test_decode_known(self, dictionary: VectorDictionary):
        d = dictionary
        text = d.decode(["g1", "p1"])
        assert "你好" in text
        assert "谢谢" in text

    def test_decode_empty(self, dictionary: VectorDictionary):
        d = dictionary
        assert d.decode([]) == ""

    def test_decode_unknown(self, dictionary: VectorDictionary):
        d = dictionary
        assert d.decode(["nonexistent"]) == ""

    def test_decode_mixed(self, dictionary: VectorDictionary):
        d = dictionary
        text = d.decode(["g1", "nonexistent", "p1"])
        assert "你好" in text
        assert "谢谢" in text

    def test_encode_emotion(self, dictionary: VectorDictionary):
        d = dictionary
        keys = d.encode("happy")
        assert "e1" in keys or "e5" in keys

    def test_encode_math(self, dictionary: VectorDictionary):
        d = dictionary
        keys = d.encode("five")
        assert "m5" in keys

    def test_encode_boolean(self, dictionary: VectorDictionary):
        d = dictionary
        keys = d.encode("true")
        assert "b1" in keys

    def test_encode_numbers(self, dictionary: VectorDictionary):
        d = dictionary
        keys = d.encode("zero")
        assert "m0" in keys

    def test_encode_angela_identity(self, dictionary: VectorDictionary):
        d = dictionary
        keys = d.encode("angela")
        assert "id1" in keys

    def test_encode_question_words(self, dictionary: VectorDictionary):
        d = dictionary
        keys = d.encode("why")
        assert "q2" in keys


class TestVectorDictionaryPersistence:
    """Tests for save/load and export/import."""

    def test_export_import_json(self, dictionary: VectorDictionary):
        d = dictionary
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "dict.json")
            d.export_to_json(path)
            d2 = VectorDictionary()
            count = d2.import_from_json(path)
        assert count == len(d.entries)
        assert "g1" in d2.entries

    def test_export_import_preserves_relations(self, dictionary: VectorDictionary):
        d = dictionary
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "dict.json")
            d.export_to_json(path)
            d2 = VectorDictionary()
            d2.import_from_json(path)
        assert d2.entries["g1"].relations.get("synonym", []) == ["g2", "g3", "g5"]

    def test_import_duplicate_skips(self, dictionary: VectorDictionary):
        d = dictionary
        count_before = len(d.entries)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "dict.json")
            d.export_to_json(path)
            count = d.import_from_json(path)
        assert count == 0  # All already exist

    def test_load_presets(self):
        d = VectorDictionary()
        d.load_presets()
        assert len(d.entries) >= 50
        assert "g1" in d.entries
        assert "e1" in d.entries
        assert "m5" in d.entries
        assert "id1" in d.entries
        assert "q2" in d.entries

    def test_load_presets_dirty_flag(self):
        d = VectorDictionary()
        d.load_presets()
        assert d._dirty is True


class TestVectorDictionaryEmpty:
    """Tests for edge cases with empty dictionary."""

    def test_encode_empty_dict(self):
        d = VectorDictionary()
        assert d.encode("hello") == []

    def test_decode_empty_dict(self):
        d = VectorDictionary()
        assert d.decode(["key1"]) == ""

    def test_stats_empty(self):
        d = VectorDictionary()
        s = d.get_stats()
        assert s["entry_count"] == 0
        assert s["embedding_dim"] == 0

    def test_stats_with_presets(self, dictionary: VectorDictionary):
        d = dictionary
        s = d.get_stats()
        assert s["entry_count"] > 0
        assert s["embedding_dim"] > 0
        assert s["encoder_type"] != ""
        assert s["index_built"] is True or s["index_built"] is False


class TestVectorDictionaryConfigLoading:
    """Tests for loading config from directory."""

    def test_config_files_exist(self):
        """Verify that config JSON files exist."""
        config_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "..",
            "apps", "backend", "src", "ai", "garden", "config"
        )
        assert os.path.isdir(config_dir)
        files = [f for f in os.listdir(config_dir) if f.endswith(".json")]
        assert len(files) >= 3  # conversation, emotion, science
        assert "conversation.json" in files
        assert "emotion_knowledge.json" in files
        assert "science_knowledge.json" in files
