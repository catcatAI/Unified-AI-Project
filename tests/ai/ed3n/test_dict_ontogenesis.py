# =============================================================================
# ANGELA-MATRIX: [L3] [αγδ] [C] [L2]
# =============================================================================
"""
Token Ontogenesis + pipeline-conflict regression tests.

Backs REFACTOR_PLAN.md §10 (Token Ontogenesis) and §11 (pipeline conflict
root-cause). These tests pin the behaviour described there so Phase 11 progress
is measurable and regressions are caught.

Coverage:
- P3 (§11.3): ResponseAnchorValidator now derives response keys from the
  dictionary instead of always rejecting (C4 root cause).
- P2 (§11.4/C1): placeholder entries never leak the raw key into output.
- P1 (§11.2/C2): resolve_concepts() converges duplicate/synonym concepts.
- P5 (§11.4/C5): _next_key_id is persisted across export/import.
- §10.6: grow() dedupes by concept (no duplicate placeholder keys).
- 11.3: dictionary singleton + backfill_placeholder().
"""

import json
import tempfile

import pytest

from ai.ed3n.dictionary_layer import DictionaryLayer, get_dictionary, reset_dictionary_singleton
from ai.ed3n.output_anchor import ResponseAnchorValidator, anchored_decode


@pytest.fixture
def dict_layer():
    dl = DictionaryLayer()
    dl.add_entry("k_cat", {"zh": "貓", "en": "cat"}, confidence=1.0)
    dl.add_entry("k_dog", {"zh": "狗", "en": "dog"}, confidence=1.0)
    return dl


def test_p3_validator_passes_topically_anchored_response(dict_layer):
    """C4 fix: a response built from the anchor's surface must validate."""
    v = ResponseAnchorValidator(dict_layer, max_drift=0.5)
    assert v.validate("貓", anchored_keys=["k_cat"]) is True


def test_p3_validator_rejects_unrelated_response(dict_layer):
    v = ResponseAnchorValidator(dict_layer, max_drift=0.5)
    assert v.validate("抱歉我沒聽懂", anchored_keys=["k_cat"]) is False


def test_p3_measure_drift_low_for_anchored(dict_layer):
    v = ResponseAnchorValidator(dict_layer, max_drift=0.5)
    assert v.measure_drift(["k_cat"], dict_layer.encode("貓")) == 0.0


# ---------------------------------------------------------------------------
# P2 (C1): placeholder must not leak the raw key
# ---------------------------------------------------------------------------


def test_c1_decode_skips_placeholder():
    dl = DictionaryLayer()
    dl.add_entry("l42", surface_forms={}, is_placeholder=True, concept_token="cat")
    assert dl.decode(["l42"]) == ""


def test_c1_anchored_decode_skips_placeholder():
    dl = DictionaryLayer()
    dl.add_entry("l42", surface_forms={}, is_placeholder=True, concept_token="cat")
    assert anchored_decode({"l42": 1.0}, ["l42"], dl) == ""


# ---------------------------------------------------------------------------
# P1 (C2): resolve_concepts converges synonyms / duplicate placeholders
# ---------------------------------------------------------------------------


def test_resolve_concepts_merges_synonyms():
    dl = DictionaryLayer()
    dl.add_entry("a", {"zh": "快樂", "en": "happy"}, relations={"synonym": ["b"]})
    dl.add_entry("b", {"zh": "開心", "en": "glad"})
    resolved = dl.resolve_concepts(["a", "b"])
    assert len(resolved) == 1
    assert resolved[0] in ("a", "b")


def test_resolve_concepts_prefers_real_surface():
    dl = DictionaryLayer()
    dl.add_entry("real", {"zh": "貓", "en": "cat"})
    dl.add_entry("ph", surface_forms={}, is_placeholder=True, concept_token="cat")
    dl.entries["real"].relations.setdefault("mapping", []).append("ph")
    dl.entries["ph"].relations.setdefault("mapping", []).append("real")
    resolved = dl.resolve_concepts(["real", "ph"])
    assert resolved == ["real"]


# ---------------------------------------------------------------------------
# P5 (C5): key counter persistence
# ---------------------------------------------------------------------------


def test_next_key_id_persisted():
    dl = DictionaryLayer()
    dl.grow("cat", "貓", 0.6)
    p = tempfile.mktemp(suffix=".json")
    dl.export_to_json(p)
    data = json.load(open(p, encoding="utf-8"))
    assert "next_key_id" in data and isinstance(data["next_key_id"], int)


def test_next_key_id_restored_on_import():
    dl = DictionaryLayer()
    dl.grow("cat", "貓", 0.6)
    p = tempfile.mktemp(suffix=".json")
    dl.export_to_json(p)
    dl2 = DictionaryLayer()
    dl2.import_from_json(p)
    # Next grown key must not collide with imported ids.
    new_key = dl2.grow("dog", "狗", 0.6)
    assert new_key not in dl.entries


# ---------------------------------------------------------------------------
# §10.6: grow() dedupes by concept (no duplicate placeholder keys)
# ---------------------------------------------------------------------------


def test_grow_dedupes_same_concept():
    dl = DictionaryLayer()
    k1 = dl.grow("cat", "貓", confidence=0.6)
    k2 = dl.grow("cat", "貓", confidence=0.6)
    assert k1 == k2  # same concept -> same key, not two placeholders


def test_grow_placeholder_dedupes():
    dl = DictionaryLayer()
    k1 = dl.grow("貓", "", confidence=0.6, placeholder=True)
    k2 = dl.grow("貓", "", confidence=0.6, placeholder=True)
    assert k1 == k2 and dl.entries[k1].is_placeholder


# ---------------------------------------------------------------------------
# 11.3: singleton + backfill
# ---------------------------------------------------------------------------


def test_dictionary_singleton():
    reset_dictionary_singleton()
    a = get_dictionary()
    b = get_dictionary()
    assert a is b
    reset_dictionary_singleton()


def test_backfill_placeholder_recovers_surface():
    dl = DictionaryLayer()
    dl.add_entry("real", {"zh": "貓", "en": "cat"})
    dl.add_entry("ph", surface_forms={}, is_placeholder=True, concept_token="cat")
    dl.entries["real"].relations.setdefault("mapping", []).append("ph")
    dl.entries["ph"].relations.setdefault("mapping", []).append("real")
    assert dl.backfill_placeholder("ph") is True
    assert dl.entries["ph"].is_placeholder is False
    assert dl.decode(["ph"]) == "貓"
