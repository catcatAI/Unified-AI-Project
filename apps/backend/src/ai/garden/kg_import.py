# =============================================================================
# ANGELA-MATRIX: [L3] [γδ] [B] [L2]
# =============================================================================
"""
GARDEN KG Import — Knowledge graph ingestion pipeline.

Implements Phase 3 of the GARDEN-1G roadmap:
  - Built-in synthetic knowledge graph generator (for demos/testing)
  - ConceptNet CSV parser (for production scale)
  - Wikidata simplified dump parser
  - Export to binary weight matrix format (BinaryStore)

Pipeline steps:
  1. Parse source data (synthetic, ConceptNet CSV, or Wikidata dump)
  2. Map entities to GARDEN concept keys
  3. Build relation triples (entity1, relation_type, entity2, weight)
  4. Export to BinaryStore .bin file + key registry JSON

Usage:
    from ai.garden.kg_import import KGImporter
    importer = KGImporter()
    # Generate synthetic graph (for testing)
    importer.generate_synthetic(num_entities=5000)
    importer.export_to_binary("./garden_relations.bin")
"""

from __future__ import annotations

import csv
import gzip
import json
import logging
import math
import os
import random
import re
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from ai.garden.dictionary import VectorDictionary
    from ai.garden.garden_engine import GARDENEngine
    from ai.garden.snn_core import TensorSNNCore

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Relation type constants
# ---------------------------------------------------------------------------

RELATION_WEIGHTS: Dict[str, float] = {
    "synonym": 0.9,
    "antonym": 0.5,
    "mapping": 0.7,
    "analogy": 0.6,
    "isa": 0.85,
    "hasa": 0.75,
    "usedfor": 0.65,
    "causes": 0.7,
    "partof": 0.8,
    "relatedto": 0.5,
    "locatedat": 0.6,
    "capableof": 0.6,
    "desires": 0.5,
    "createdby": 0.6,
    "distinctfrom": 0.3,
}


# ---------------------------------------------------------------------------
# KGImporter
# ---------------------------------------------------------------------------


class KGImporter:
    """
    Knowledge graph importer for GARDEN-1G.

    Supports multiple data sources:
      - generate_synthetic(): built-in random graph generator
      - parse_conceptnet(): ConceptNet CSV format
      - parse_wikidata(): simplified Wikidata format
      - merge(): combine multiple source graphs

    Output:
      - export_to_binary(): BinaryStore .bin + key registry JSON
      - export_to_json(): human-readable JSON format
      - apply_to_dictionary(): load entries into a VectorDictionary
    """

    def __init__(self):
        # entity_key -> {"surface": str, "relations": {rel_type: [target_key]}}
        self.entities: Dict[str, Dict[str, Any]] = {}
        self.triples: List[Tuple[str, str, str, float]] = []
        self._next_id: int = 0

    # ------------------------------------------------------------------
    # Synthetic graph generator
    # ------------------------------------------------------------------

    SYNTHETIC_CONCEPTS: List[Dict[str, Any]] = [
        # (category, zh_name, en_name, relations_template)
        {"cat": "animal", "zh_prefix": "动", "en_prefix": "animal_", "count": 20},
        {"cat": "plant", "zh_prefix": "植", "en_prefix": "plant_", "count": 15},
        {"cat": "food", "zh_prefix": "食", "en_prefix": "food_", "count": 20},
        {"cat": "color", "zh_prefix": "颜", "en_prefix": "color_", "count": 12},
        {"cat": "body", "zh_prefix": "身", "en_prefix": "body_", "count": 15},
        {"cat": "place", "zh_prefix": "地", "en_prefix": "place_", "count": 18},
        {"cat": "tool", "zh_prefix": "工", "en_prefix": "tool_", "count": 15},
        {"cat": "profession", "zh_prefix": "职", "en_prefix": "job_", "count": 12},
        {"cat": "sport", "zh_prefix": "运", "en_prefix": "sport_", "count": 10},
        {"cat": "music", "zh_prefix": "音", "en_prefix": "music_", "count": 10},
        {"cat": "weather", "zh_prefix": "天", "en_prefix": "weather_", "count": 10},
        {"cat": "transport", "zh_prefix": "交", "en_prefix": "trans_", "count": 10},
        {"cat": "furniture", "zh_prefix": "家", "en_prefix": "furn_", "count": 10},
        {"cat": "clothing", "zh_prefix": "衣", "en_prefix": "cloth_", "count": 10},
        {"cat": "emotion", "zh_prefix": "情", "en_prefix": "emot_", "count": 8},
    ]

    SYNTHETIC_SUFFIXES = {
        "animal": [
            ("狗", "dog"),
            ("猫", "cat"),
            ("鸟", "bird"),
            ("鱼", "fish"),
            ("马", "horse"),
            ("牛", "cow"),
            ("猪", "pig"),
            ("羊", "sheep"),
            ("鸡", "chicken"),
            ("鸭", "duck"),
            ("兔", "rabbit"),
            ("蛇", "snake"),
            ("鼠", "mouse"),
            ("熊", "bear"),
            ("狼", "wolf"),
            ("虎", "tiger"),
            ("狮", "lion"),
            ("象", "elephant"),
            ("鹿", "deer"),
            ("猴", "monkey"),
        ],
        "plant": [
            ("树", "tree"),
            ("花", "flower"),
            ("草", "grass"),
            ("竹", "bamboo"),
            ("松", "pine"),
            ("梅", "plum"),
            ("兰", "orchid"),
            ("菊", "chrysanthemum"),
            ("荷", "lotus"),
            ("柳", "willow"),
            ("枫", "maple"),
            ("橡", "oak"),
            ("棕", "palm"),
            ("蕨", "fern"),
            ("苔", "moss"),
        ],
        "food": [
            ("米饭", "rice"),
            ("面包", "bread"),
            ("面条", "noodle"),
            ("蛋糕", "cake"),
            ("苹果", "apple"),
            ("香蕉", "banana"),
            ("橙子", "orange"),
            ("葡萄", "grape"),
            ("西瓜", "watermelon"),
            ("牛奶", "milk"),
            ("咖啡", "coffee"),
            ("茶", "tea"),
            ("果汁", "juice"),
            ("巧克力", "chocolate"),
            ("冰淇淋", "ice cream"),
            ("沙拉", "salad"),
            ("汤", "soup"),
            ("披萨", "pizza"),
            ("汉堡", "hamburger"),
            ("寿司", "sushi"),
        ],
    }

    def _synthetic_key(self, cat: str, idx: int) -> str:
        return f"syn_{cat}_{idx}"

    def generate_synthetic(self, num_entities: int = 10000):
        """
        Generate a synthetic knowledge graph with N entities.
        Creates entities with category-based naming and random relations.
        """
        random.seed(42)
        self.entities.clear()
        self.triples.clear()

        category_allocation = self._allocate_categories(num_entities)
        entities_created = 0

        for cat_info in self.SYNTHETIC_CONCEPTS:
            cat = cat_info["cat"]
            count = category_allocation.get(cat, 0)
            suffixes = self.SYNTHETIC_SUFFIXES.get(cat, [])

            for i in range(count):
                key = self._synthetic_key(cat, i)
                if i < len(suffixes):
                    zh_name = suffixes[i][0]
                    en_name = suffixes[i][1]
                else:
                    zh_name = f"{cat_info['zh_prefix']}{i}"
                    en_name = f"{cat_info['en_prefix']}{i}"

                self.entities[key] = {
                    "surface": {"zh": zh_name, "en": en_name},
                    "relations": {},
                    "category": cat,
                }
                entities_created += 1

        # Add relations (connect entities with similar categories)
        for key, entity in self.entities.items():
            cat = entity["category"]
            # Connect to same-category entities (synonym-like)
            same_cat = [
                k for k in self.entities if k != key and self.entities[k]["category"] == cat
            ]
            random.shuffle(same_cat)
            for peer in same_cat[:3]:
                self._add_triple(key, "relatedto", peer, weight=0.5)
                self._add_triple(peer, "relatedto", key, weight=0.5)

            # Connect cross-category (mapping-ish)
            other_cats = [k for k in self.entities if self.entities[k]["category"] != cat]
            random.shuffle(other_cats)
            for peer in other_cats[:2]:
                self._add_triple(key, "mapping", peer, weight=0.35)

        # Add category-level isa relations
        cat_groups: Dict[str, List[str]] = {}
        for key, entity in self.entities.items():
            cat_groups.setdefault(entity["category"], []).append(key)

        for cat, members in cat_groups.items():
            # Create a category key
            cat_key = f"syn_cat_{cat}"
            self.entities[cat_key] = {
                "surface": {"zh": f"{cat}类", "en": f"{cat}_category"},
                "relations": {},
                "category": "meta",
            }
            for member in members[:10]:
                self._add_triple(member, "isa", cat_key, weight=0.85)

        logger.info(
            "KGImporter: generated synthetic graph with %d entities, %d triples",
            len(self.entities),
            len(self.triples),
        )
        return self

    def _allocate_categories(self, num_entities: int) -> Dict[str, int]:
        """Distribute N entities across categories proportionally."""
        total_weight = sum(c["count"] for c in self.SYNTHETIC_CONCEPTS)
        allocation: Dict[str, int] = {}
        remaining = num_entities
        for i, cat_info in enumerate(self.SYNTHETIC_CONCEPTS):
            if i < len(self.SYNTHETIC_CONCEPTS) - 1:
                count = max(1, int(num_entities * cat_info["count"] / total_weight))
                allocation[cat_info["cat"]] = count
                remaining -= count
            else:
                allocation[cat_info["cat"]] = remaining
        return allocation

    # ------------------------------------------------------------------
    # Triple management
    # ------------------------------------------------------------------

    def _add_triple(self, src: str, rel: str, tgt: str, weight: float = 0.5):
        """Internal: record a triple and update entity relations dict."""
        self.triples.append((src, rel, tgt, weight))
        if src in self.entities:
            rels = self.entities[src].setdefault("relations", {})
            rels.setdefault(rel, [])
            if tgt not in rels[rel]:
                rels[rel].append(tgt)

    # ------------------------------------------------------------------
    # ConceptNet CSV parser
    # ------------------------------------------------------------------

    def parse_conceptnet(self, csv_path: str, max_entities: int = 500000) -> "KGImporter":
        """
        Parse a ConceptNet CSV file.

        Expected format (ConceptNet 5.7+):
          /c/en/dog,IsA,/c/en/animal
          /c/en/dog,RelatedTo,/c/en/canine

        Args:
            csv_path: Path to ConceptNet CSV (may be .gz compressed).
            max_entities: Maximum number of distinct entities to load.

        Returns:
            self for chaining.
        """
        open_func = gzip.open if csv_path.endswith(".gz") else open
        count = 0
        entity_set: Set[str] = set()

        with open_func(csv_path, "rt", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) < 3:
                    continue
                src_full, rel_type, tgt_full = row[0].strip(), row[1].strip(), row[2].strip()

                # Only English/Chinese
                if not (src_full.startswith("/c/en/") or src_full.startswith("/c/zh/")):
                    continue
                if not (tgt_full.startswith("/c/en/") or tgt_full.startswith("/c/zh/")):
                    continue

                src_lang = "en" if src_full.startswith("/c/en/") else "zh"
                tgt_lang = "en" if tgt_full.startswith("/c/en/") else "zh"
                src_name = self._conceptnet_name(src_full)
                tgt_name = self._conceptnet_name(tgt_full)
                src_key = self._conceptnet_key(src_name, src_lang)
                tgt_key = self._conceptnet_key(tgt_name, tgt_lang)

                # Add entities
                if src_key not in self.entities:
                    if len(self.entities) >= max_entities:
                        continue
                    self.entities[src_key] = {
                        "surface": {src_lang: src_name},
                        "relations": {},
                        "source": "conceptnet",
                    }
                else:
                    if src_lang not in self.entities[src_key]["surface"]:
                        self.entities[src_key]["surface"][src_lang] = src_name

                if tgt_key not in self.entities:
                    if len(self.entities) >= max_entities:
                        continue
                    self.entities[tgt_key] = {
                        "surface": {tgt_lang: tgt_name},
                        "relations": {},
                        "source": "conceptnet",
                    }
                else:
                    if tgt_lang not in self.entities[tgt_key]["surface"]:
                        self.entities[tgt_key]["surface"][tgt_lang] = tgt_name

                # Normalize relation type
                norm_rel = self._normalize_conceptnet_rel(rel_type)
                weight = RELATION_WEIGHTS.get(norm_rel, 0.5)
                self._add_triple(src_key, norm_rel, tgt_key, weight=weight)
                count += 1

                if count % 100000 == 0:
                    logger.info("KGImporter: parsed %d ConceptNet triples...", count)

        logger.info(
            "KGImporter: ConceptNet parsing complete — %d entities, %d triples",
            len(self.entities),
            count,
        )
        return self

    @staticmethod
    def _conceptnet_name(full_path: str) -> str:
        """Extract the concept name from a ConceptNet path."""
        # /c/en/dog -> dog
        # /c/zh/狗 -> 狗
        parts = full_path.strip("/").split("/")
        if len(parts) >= 3:
            return parts[2].replace("_", " ")
        return full_path

    @staticmethod
    def _conceptnet_key(name: str, lang: str) -> str:
        """Generate a key from a concept name."""
        short = name.lower().replace(" ", "_")[:40]
        return f"cn_{lang}_{short}"

    @staticmethod
    def _normalize_conceptnet_rel(rel: str) -> str:
        """Map ConceptNet relation names to GARDEN relation types."""
        mapping = {
            "IsA": "isa",
            "PartOf": "partof",
            "HasA": "hasa",
            "UsedFor": "usedfor",
            "CapableOf": "capableof",
            "Causes": "causes",
            "Desires": "desires",
            "CreatedBy": "createdby",
            "LocatedAt": "locatedat",
            "RelatedTo": "relatedto",
            "Synonym": "synonym",
            "Antonym": "antonym",
            "DistinctFrom": "distinctfrom",
            "MannerOf": "mapping",
            "HasProperty": "mapping",
        }
        return mapping.get(rel, "relatedto")

    # ------------------------------------------------------------------
    # Wikidata simplified parser
    # ------------------------------------------------------------------

    def parse_wikidata(self, jsonl_path: str, max_entities: int = 500000) -> "KGImporter":
        """
        Parse a simplified Wikidata JSONL dump (one JSON object per line).

        Expected per-line format:
          {"id": "Q42", "labels": {"en": "Douglas Adams"}, "claims": {"P31": ["Q5"]}}

        Args:
            jsonl_path: Path to simplified Wikidata JSONL (may be .gz).
            max_entities: Maximum entities to load.

        Returns:
            self for chaining.
        """
        open_func = gzip.open if jsonl_path.endswith(".gz") else open
        count = 0

        with open_func(jsonl_path, "rt", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                qid = obj.get("id", "")
                labels = obj.get("labels", {})
                en_label = labels.get("en", "")
                zh_label = labels.get("zh", "")
                if not en_label and not zh_label:
                    continue

                key = f"wd_{qid}"
                if key in self.entities:
                    continue
                if len(self.entities) >= max_entities:
                    break

                surface = {}
                if en_label:
                    surface["en"] = en_label
                if zh_label:
                    surface["zh"] = zh_label
                self.entities[key] = {
                    "surface": surface,
                    "relations": {},
                    "source": "wikidata",
                }

                # Process claims as relations
                claims = obj.get("claims", {})
                for prop, values in claims.items():
                    if not isinstance(values, list):
                        continue
                    norm_rel = self._wikidata_prop_to_rel(prop)
                    weight = RELATION_WEIGHTS.get(norm_rel, 0.5)
                    for val in values:
                        if isinstance(val, str):
                            tgt_key = f"wd_{val}"
                            if tgt_key not in self.entities and len(self.entities) < max_entities:
                                self.entities[tgt_key] = {
                                    "surface": {"en": val},
                                    "relations": {},
                                    "source": "wikidata",
                                }
                            self._add_triple(key, norm_rel, tgt_key, weight=weight)
                            count += 1

                if count > 0 and count % 50000 == 0:
                    logger.info("KGImporter: parsed %d Wikidata triples...", count)

        logger.info(
            "KGImporter: Wikidata parsing complete — %d entities, %d triples",
            len(self.entities),
            count,
        )
        return self

    @staticmethod
    def _wikidata_prop_to_rel(prop: str) -> str:
        """Map Wikidata property IDs to GARDEN relation types."""
        # Common property mappings
        prop_map = {
            "P31": "isa",  # instance of
            "P279": "isa",  # subclass of
            "P361": "partof",  # part of
            "P527": "hasa",  # has part
            "P1542": "causes",  # has effect
            "P828": "causes",  # has cause
            "P4482": "usedfor",  # has use
            "P366": "usedfor",  # has use
            "P1889": "distinctfrom",  # different from
            "P460": "relatedto",  # said to be the same as
            "P461": "antonym",  # opposite of
            "P1552": "relatedto",  # has quality
            "P1034": "relatedto",  # main subject
        }
        return prop_map.get(prop, "relatedto")

    # ------------------------------------------------------------------
    # Merge multiple sources
    # ------------------------------------------------------------------

    def merge(self, other: "KGImporter") -> "KGImporter":
        """
        Merge another KGImporter's data into this one.
        Duplicate entities are merged (surfaces combined, relations appended).
        """
        for key, entity in other.entities.items():
            if key in self.entities:
                # Merge surface forms
                for lang, name in entity["surface"].items():
                    if lang not in self.entities[key]["surface"]:
                        self.entities[key]["surface"][lang] = name
                # Merge relations
                for rel, targets in entity.get("relations", {}).items():
                    existing = self.entities[key]["relations"].setdefault(rel, [])
                    for t in targets:
                        if t not in existing:
                            existing.append(t)
            else:
                self.entities[key] = entity

        # Merge triples (deduplicate)
        existing_triples = set(self.triples)
        for triple in other.triples:
            if triple not in existing_triples:
                self.triples.append(triple)
                existing_triples.add(triple)

        logger.info(
            "KGImporter: merged — total %d entities, %d triples",
            len(self.entities),
            len(self.triples),
        )
        return self

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_to_binary(self, bin_path: str, key_registry_path: str = "") -> Dict[str, Any]:
        """
        Export relation graph to BinaryStore .bin file + key registry.

        The key registry maps entity keys to matrix row indices.

        Args:
            bin_path: Output .bin file path.
            key_registry_path: Optional JSON path for key -> index mapping.
                              If empty, derived from bin_path.

        Returns:
            Statistics dict.
        """
        from .binary_store import BinaryStore

        if not key_registry_path:
            key_registry_path = bin_path.replace(".bin", "_keys.json")

        V = len(self.entities)
        all_keys = list(self.entities.keys())
        key_to_idx = {k: i for i, k in enumerate(all_keys)}

        # Create binary store
        store = BinaryStore.create(bin_path, V, fill_value=0.0)

        # Fill from triples
        weight_sum = 0.0
        edge_count = 0
        for src, rel, tgt, weight in self.triples:
            i = key_to_idx.get(src)
            j = key_to_idx.get(tgt)
            if i is not None and j is not None and i != j:
                store[i, j] = min(1.0, float(store[i, j]) + weight)
                store[j, i] = min(1.0, float(store[j, i]) + weight)
                weight_sum += weight
                edge_count += 1

        store.flush()
        store.close()

        # Save key registry
        registry = {
            "version": "garden-1.0",
            "V": V,
            "entities": {
                key: {
                    "idx": idx,
                    "surface": self.entities[key].get("surface", {}),
                    "category": self.entities[key].get("category", ""),
                }
                for key, idx in key_to_idx.items()
            },
            "relation_weights": RELATION_WEIGHTS,
        }
        os.makedirs(os.path.dirname(bin_path) if os.path.dirname(bin_path) else ".", exist_ok=True)
        with open(key_registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, ensure_ascii=False, indent=2)

        stats = {
            "V": V,
            "edges": edge_count,
            "avg_weight": round(weight_sum / edge_count, 4) if edge_count > 0 else 0,
            "density": round(edge_count / (V * V), 6) if V > 0 else 0,
            "bin_file": os.path.abspath(bin_path),
            "registry_file": os.path.abspath(key_registry_path),
            "memory_mb": round(V * V * 4 / (1024 * 1024), 1),
        }
        logger.info("KGImporter: exported to binary — %s", stats)
        return stats

    def export_to_json(self, json_path: str) -> None:
        """Export graph to human-readable JSON (dictionary entries format)."""
        entries = []
        for key, entity in self.entities.items():
            entries.append(
                {
                    "key": key,
                    "surface_forms": entity.get("surface", {}),
                    "relations": entity.get("relations", {}),
                    "confidence": 0.85,
                }
            )
        data = {
            "version": "garden-1.0",
            "source": "kg_import",
            "entries": entries,
        }
        os.makedirs(
            os.path.dirname(json_path) if os.path.dirname(json_path) else ".", exist_ok=True
        )
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("KGImporter: exported %d entries to %s", len(entries), json_path)

    def apply_to_dictionary(self, dictionary: "VectorDictionary") -> int:
        """
        Load all entities into a GARDEN VectorDictionary.

        Args:
            dictionary: VectorDictionary instance.

        Returns:
            Number of new entries added.
        """
        count = 0
        for key, entity in self.entities.items():
            if key not in dictionary.entries:
                dictionary.add_entry(
                    key=key,
                    surface_forms=entity.get("surface", {"en": key}),
                    relations=entity.get("relations"),
                    confidence=0.85,
                )
                count += 1
        dictionary._dirty = True
        logger.info("KGImporter: applied %d entries to dictionary", count)
        return count

    def apply_to_snn(self, snn_core: "TensorSNNCore") -> int:
        """
        Load all triples into a GARDEN TensorSNNCore.

        Args:
            snn_core: TensorSNNCore instance.

        Returns:
            Number of relations added.
        """
        count = 0
        for src, rel, tgt, weight in self.triples:
            snn_core.add_relation(src, tgt, weight=weight, bidirectional=True)
            count += 1
        logger.info("KGImporter: applied %d relations to SNN core", count)
        return count

    # ------------------------------------------------------------------
    # Merged bulk load (dictionary + SNN)
    # ------------------------------------------------------------------

    def bulk_load(self, engine: "GARDENEngine") -> Dict[str, int]:
        """
        Load the full knowledge graph into a GARDENEngine.

        Args:
            engine: GARDENEngine instance with loaded presets.

        Returns:
            Dict with "dictionary_entries" and "snn_relations" counts.
        """
        dict_count = self.apply_to_dictionary(engine.dictionary)
        snn_count = self.apply_to_snn(engine.snn)
        engine._presets_loaded = True
        return {
            "dictionary_entries": dict_count,
            "snn_relations": snn_count,
        }

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Return statistics about the loaded graph."""
        rel_counts: Dict[str, int] = {}
        for _, rel, _, _ in self.triples:
            rel_counts[rel] = rel_counts.get(rel, 0) + 1
        return {
            "entities": len(self.entities),
            "triples": len(self.triples),
            "relation_types": len(rel_counts),
            "relation_breakdown": rel_counts,
            "avg_relations_per_entity": round(len(self.triples) / max(1, len(self.entities)), 1),
        }
