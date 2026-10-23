"""The layer contract: memory / knowledge / reasoning / learning / surface.

A claim is rejected when the module's declared layer, its path, its evidence or
its result contradict the registry — the failure mode that produced "a dict
called learning".
"""

import importlib.util
import json
from pathlib import Path

import pytest

from ai.meta.layers import validate_entry, validate_registry

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / "docs" / "06-project-management" / "LAYER_REGISTRY.json"


def _module(tmp_path: Path, name: str, layer: str, body: str = "VALUE = 1\n") -> str:
    path = tmp_path / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# LAYER: {layer}\n{body}", encoding="utf-8")
    return str(path.relative_to(tmp_path))


def _probe(tmp_path: Path) -> str:
    path = tmp_path / "scripts" / "probe.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("print('probe')\n", encoding="utf-8")
    return str(path.relative_to(tmp_path))


def _entry(tmp_path, layer, *, marker=None, must_not=None, source_deleted=False, status="pass"):
    return {
        "id": f"claim_{layer}",
        "claim": "a claim",
        "layer": layer,
        "implemented_in": _module(tmp_path, "pkg/mod.py", marker or layer),
        "evidence": {
            "probe": _probe(tmp_path),
            "method": "measures something",
            "source_deleted": source_deleted,
        },
        "result": {"status": status, "value": "x", "measured_at": "2026-10-23"},
        "must_not_be_used_as": must_not
        if must_not is not None
        else (["knowledge"] if layer == "learning" else ["knowledge", "learning", "intelligence"]),
    }


def test_real_registry_is_clean():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    assert validate_registry(registry, REPO) == []


def test_marker_must_match_the_claimed_layer(tmp_path):
    entry = _entry(tmp_path, "memory", marker="knowledge")
    problems = validate_entry(entry, tmp_path)
    assert any("marker" in str(p) for p in problems)


def test_memory_must_forbid_knowledge_and_intelligence(tmp_path):
    entry = _entry(tmp_path, "memory", must_not=["learning"])
    problems = validate_entry(entry, tmp_path)
    assert any("knowledge" in str(p) for p in problems)


def test_learning_claim_needs_source_deletion_evidence(tmp_path):
    entry = _entry(tmp_path, "learning", source_deleted=False)
    problems = validate_entry(entry, tmp_path)
    assert any("source_deleted" in str(p) for p in problems)


def test_learning_claim_with_deletion_evidence_passes(tmp_path):
    entry = _entry(tmp_path, "learning", source_deleted=True)
    assert validate_entry(entry, tmp_path) == []


def test_knowledge_module_may_not_import_memory(tmp_path):
    entry = _entry(tmp_path, "knowledge")
    (tmp_path / entry["implemented_in"]).write_text(
        "# LAYER: knowledge\nfrom ai.memory.taught_facts import get_taught_facts\n",
        encoding="utf-8",
    )
    problems = validate_entry(entry, tmp_path)
    assert any("memory" in str(p) for p in problems)


def test_surface_must_forbid_knowledge(tmp_path):
    entry = _entry(tmp_path, "surface", must_not=["learning"])
    problems = validate_entry(entry, tmp_path)
    assert any("knowledge" in str(p) for p in problems)


def test_missing_probe_is_rejected(tmp_path):
    entry = _entry(tmp_path, "memory")
    entry["evidence"]["probe"] = "scripts/does_not_exist.py"
    problems = validate_entry(entry, tmp_path)
    assert any("probe" in str(p) for p in problems)


def test_duplicate_ids_are_rejected(tmp_path):
    one = _entry(tmp_path, "memory")
    two = _entry(tmp_path, "knowledge")
    two["id"] = one["id"]
    problems = validate_registry({"claims": [one, two]}, tmp_path)
    assert any("duplicate" in str(p) for p in problems)


def test_structural_invariants_of_the_repository():
    spec = importlib.util.spec_from_file_location(
        "layer_guard_test", REPO / "scripts" / "check_layer_separation.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.structural_problems() == []


@pytest.mark.parametrize("layer", ["memory", "knowledge", "reasoning", "learning", "surface"])
def test_every_layer_is_registrable(tmp_path, layer):
    entry = _entry(tmp_path, layer, source_deleted=(layer == "learning"))
    assert validate_entry(entry, tmp_path) == []
