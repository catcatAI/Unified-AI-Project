# =============================================================================
# ANGELA-MATRIX: [L3] [γδ] [C] [L0]
# =============================================================================
"""
Tests for GARDEN KGImporter (knowledge graph ingestion).
"""

import json
import os
import tempfile

import pytest

from apps.backend.src.ai.garden.kg_import import KGImporter, RELATION_WEIGHTS


class TestKGImporterInit:
    """Tests for construction and basic properties."""

    def test_init(self, kg_importer: KGImporter):
        assert kg_importer.entities == {}
        assert kg_importer.triples == []

    def test_relation_weights(self):
        assert RELATION_WEIGHTS["synonym"] == 0.9
        assert RELATION_WEIGHTS["antonym"] == 0.5
        assert RELATION_WEIGHTS["isa"] == 0.85
        assert len(RELATION_WEIGHTS) >= 14


class TestKGImporterSynthetic:
    """Tests for synthetic graph generation."""

    def test_generate_synthetic_small(self, kg_importer: KGImporter):
        kg_importer.generate_synthetic(num_entities=100)
        assert len(kg_importer.entities) >= 100
        assert len(kg_importer.triples) >= 50

    def test_generate_synthetic_large(self, kg_importer: KGImporter):
        kg_importer.generate_synthetic(num_entities=5000)
        assert len(kg_importer.entities) >= 5000
        assert len(kg_importer.triples) >= 1000

    def test_generate_synthetic_keys(self, kg_importer: KGImporter):
        kg_importer.generate_synthetic(num_entities=200)
        for key in kg_importer.entities.keys():
            assert key.startswith("syn_")

    def test_generate_synthetic_surface_forms(self, kg_importer: KGImporter):
        kg_importer.generate_synthetic(num_entities=100)
        for key, entity in kg_importer.entities.items():
            assert "zh" in entity["surface"]
            assert "en" in entity["surface"]

    def test_generate_synthetic_categories(self, kg_importer: KGImporter):
        kg_importer.generate_synthetic(num_entities=500)
        categories = set(entity["category"] for entity in kg_importer.entities.values())
        assert "animal" in categories
        assert "food" in categories
        assert "emotion" in categories

    def test_generate_synthetic_relations(self, kg_importer: KGImporter):
        kg_importer.generate_synthetic(num_entities=200)
        rel_types = set(rel for _, rel, _, _ in kg_importer.triples)
        assert "relatedto" in rel_types
        assert "mapping" in rel_types
        assert "isa" in rel_types

    def test_generate_synthetic_stats(self, kg_importer: KGImporter):
        kg_importer.generate_synthetic(num_entities=1000)
        stats = kg_importer.get_stats()
        assert stats["entities"] >= 1000
        assert stats["triples"] > 0
        assert stats["relation_types"] >= 3


class TestKGImporterExport:
    """Tests for exporting knowledge graph data."""

    def test_export_to_json(self, kg_importer: KGImporter):
        kg_importer.generate_synthetic(num_entities=100)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "kg.json")
            kg_importer.export_to_json(path)
            assert os.path.exists(path)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data["version"] == "garden-1.0"
            assert len(data["entries"]) >= 100

    def test_export_to_binary(self, kg_importer: KGImporter):
        kg_importer.generate_synthetic(num_entities=100)
        with tempfile.TemporaryDirectory() as tmp:
            bin_path = os.path.join(tmp, "garden_relations.bin")
            stats = kg_importer.export_to_binary(bin_path)
            assert stats["V"] == 100
            assert stats["edges"] > 0
            assert os.path.exists(bin_path)
            assert os.path.exists(bin_path.replace(".bin", "_keys.json"))

    def test_binary_export_stats(self, kg_importer: KGImporter):
        kg_importer.generate_synthetic(num_entities=500)
        with tempfile.TemporaryDirectory() as tmp:
            bin_path = os.path.join(tmp, "test_relations.bin")
            stats = kg_importer.export_to_binary(bin_path)
            assert stats["edges"] > 0
            assert stats["avg_weight"] > 0
            assert stats["density"] > 0
            assert stats["memory_mb"] > 0


class TestKGImporterApply:
    """Tests for applying graph to dictionary and SNN."""

    def test_apply_to_dictionary(self, kg_importer: KGImporter, dictionary):
        kg_importer.generate_synthetic(num_entities=200)
        count = kg_importer.apply_to_dictionary(dictionary)
        assert count >= 200
        assert "syn_animal_0" in dictionary.entries

    def test_apply_to_snn(self, kg_importer: KGImporter, snn_core):
        kg_importer.generate_synthetic(num_entities=100)
        count = kg_importer.apply_to_snn(snn_core)
        assert count > 0
        assert snn_core.vocab_size >= 100

    def test_bulk_load(self, kg_importer: KGImporter, engine):
        kg_importer.generate_synthetic(num_entities=200)
        result = kg_importer.bulk_load(engine)
        assert result["dictionary_entries"] >= 200
        assert result["snn_relations"] > 0

    def test_bulk_load_preserves_existing(self, kg_importer: KGImporter, engine):
        """Existing preset entries should not be overwritten."""
        before = len(engine.dictionary.entries)
        kg_importer.generate_synthetic(num_entities=100)
        kg_importer.bulk_load(engine)
        assert "g1" in engine.dictionary.entries  # Preserved


class TestKGImporterMerge:
    """Tests for merging multiple KGImporters."""

    def test_merge(self, kg_importer: KGImporter):
        kg1 = KGImporter()
        kg1.generate_synthetic(num_entities=100)

        kg2 = KGImporter()
        kg2.generate_synthetic(num_entities=200)

        kg1.merge(kg2)
        assert len(kg1.entities) >= 300

    def test_merge_deduplicates_triples(self):
        kg1 = KGImporter()
        kg1.generate_synthetic(num_entities=50)
        triple_count = len(kg1.triples)

        kg1.merge(kg1)  # Merge with itself
        assert len(kg1.triples) == triple_count  # No duplicates


class TestKGImporterConceptNet:
    """Tests for ConceptNet parsing (without real file)."""

    def test_conceptnet_name_parsing(self, kg_importer: KGImporter):
        assert kg_importer._conceptnet_name("/c/en/dog") == "dog"
        assert kg_importer._conceptnet_name("/c/zh/狗") == "狗"
        assert kg_importer._conceptnet_name("/c/en/solar_system") == "solar system"

    def test_conceptnet_key_generation(self, kg_importer: KGImporter):
        key = kg_importer._conceptnet_key("dog", "en")
        assert key == "cn_en_dog"

    def test_conceptnet_rel_normalization(self, kg_importer: KGImporter):
        assert kg_importer._normalize_conceptnet_rel("IsA") == "isa"
        assert kg_importer._normalize_conceptnet_rel("RelatedTo") == "relatedto"
        assert kg_importer._normalize_conceptnet_rel("Synonym") == "synonym"
        assert kg_importer._normalize_conceptnet_rel("Unknown") == "relatedto"

    def test_parse_conceptnet_no_file(self, kg_importer: KGImporter):
        """Should handle missing file gracefully."""
        with pytest.raises(FileNotFoundError):
            kg_importer.parse_conceptnet("/nonexistent/conceptnet.csv")


class TestKGImporterWikidata:
    """Tests for Wikidata parsing (without real file)."""

    def test_wikidata_prop_to_rel(self, kg_importer: KGImporter):
        assert kg_importer._wikidata_prop_to_rel("P31") == "isa"
        assert kg_importer._wikidata_prop_to_rel("P279") == "isa"
        assert kg_importer._wikidata_prop_to_rel("P361") == "partof"
        assert kg_importer._wikidata_prop_to_rel("UNKNOWN") == "relatedto"

    def test_parse_wikidata_no_file(self, kg_importer: KGImporter):
        """Should handle missing file gracefully."""
        with pytest.raises(FileNotFoundError):
            kg_importer.parse_wikidata("/nonexistent/wikidata.jsonl")
