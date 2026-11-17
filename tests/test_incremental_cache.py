# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""The cache decides what is *not* recomputed, so its misses must be tested.

Three properties matter and none of them is "it stores a file":

* the key covers the plan (a changed input is a different unit);
* a unit is reused only when its artifacts still hash to what was recorded;
* a broken or half-written unit is a miss, never a silent reuse.

The tests use real files in ``tmp_path`` because the artifact check is the part
that would otherwise be a comment.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE = REPO_ROOT / "scripts" / "incremental.py"


def _load():
    spec = importlib.util.spec_from_file_location("incremental_under_test", MODULE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["incremental_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def incremental():
    return _load()


@pytest.fixture()
def plan():
    return {
        "arm": "warm",
        "seed": 0,
        "parent": "sha256:aaa",
        "rows": {"train": 5144, "val": 281},
        "protocol": {"epochs": 2, "batch": 8, "lr": 0.001},
    }


def test_key_is_independent_of_dict_order(incremental, plan):
    reordered = {key: plan[key] for key in reversed(list(plan))}
    assert incremental.unit_key(plan) == incremental.unit_key(reordered)


@pytest.mark.parametrize("field", ["arm", "seed", "parent", "rows", "protocol"])
def test_any_plan_field_changes_the_key(incremental, plan, field):
    changed = json.loads(json.dumps(plan))
    changed[field] = {
        "arm": "cold",
        "seed": 1,
        "parent": "sha256:bbb",
        "rows": {"train": 1, "val": 1},
        "protocol": {"epochs": 3, "batch": 8, "lr": 0.001},
    }[field]
    assert incremental.unit_key(changed) != incremental.unit_key(plan)


def test_store_then_lookup_returns_the_payload(incremental, plan, tmp_path):
    cache = incremental.UnitCache(tmp_path / "cache", base=tmp_path)
    artifact = tmp_path / "model.pt"
    artifact.write_bytes(b"weights")
    cache.store(plan, {"val_ce": 5.5}, artifacts=[artifact], seconds=12.0)
    unit = cache.lookup(plan)
    assert unit is not None
    assert unit.payload["val_ce"] == 5.5
    assert unit.seconds == 12.0
    assert unit.artifact("model.pt")["sha256"] == incremental.file_digest(artifact)


def test_an_artifact_can_be_found_by_its_role(incremental, plan, tmp_path):
    # The probe asks for ``opt_state``; the file is ``warm_0_2_opt.pt``. A
    # filename-keyed lookup would answer None and silently disable extension.
    cache = incremental.UnitCache(tmp_path / "cache", base=tmp_path)
    checkpoint = tmp_path / "warm_0_2.pt"
    optimizer = tmp_path / "warm_0_2_opt.pt"
    checkpoint.write_bytes(b"weights")
    optimizer.write_bytes(b"adam")
    cache.store(
        plan,
        {"ok": True},
        artifacts=[("checkpoint", checkpoint), ("opt_state", optimizer)],
    )
    unit = cache.lookup(plan)
    assert unit is not None
    assert unit.artifact("opt_state")["file"] == "warm_0_2_opt.pt"
    assert unit.artifact("checkpoint")["path"].endswith("warm_0_2.pt")
    assert unit.artifact("absent") is None


def test_a_different_plan_is_a_miss(incremental, plan, tmp_path):
    cache = incremental.UnitCache(tmp_path / "cache", base=tmp_path)
    cache.store(plan, {"ok": True})
    other = dict(plan, seed=1)
    assert cache.lookup(other) is None
    assert cache.explain_miss(other) == "no unit for this plan"


def test_a_changed_artifact_is_a_miss(incremental, plan, tmp_path):
    cache = incremental.UnitCache(tmp_path / "cache", base=tmp_path)
    artifact = tmp_path / "model.pt"
    artifact.write_bytes(b"weights")
    cache.store(plan, {"ok": True}, artifacts=[artifact])
    assert cache.lookup(plan) is not None
    artifact.write_bytes(b"weights, edited after the run")
    assert cache.lookup(plan) is None
    assert "artifact changed" in cache.explain_miss(plan)


def test_a_missing_artifact_is_a_miss(incremental, plan, tmp_path):
    cache = incremental.UnitCache(tmp_path / "cache", base=tmp_path)
    artifact = tmp_path / "model.pt"
    artifact.write_bytes(b"weights")
    cache.store(plan, {"ok": True}, artifacts=[artifact])
    artifact.unlink()
    assert cache.lookup(plan) is None
    assert "artifact missing" in cache.explain_miss(plan)


def test_a_corrupt_unit_is_a_miss(incremental, plan, tmp_path):
    cache = incremental.UnitCache(tmp_path / "cache", base=tmp_path)
    unit = cache.store(plan, {"ok": True})
    (cache.unit_dir(unit.key) / incremental.MANIFEST).write_text("{not json", encoding="utf-8")
    assert cache.lookup(plan) is None


def test_a_unit_from_another_schema_is_a_miss(incremental, plan, tmp_path):
    cache = incremental.UnitCache(tmp_path / "cache", base=tmp_path)
    unit = cache.store(plan, {"ok": True})
    path = cache.unit_dir(unit.key) / incremental.MANIFEST
    data = json.loads(path.read_text(encoding="utf-8"))
    data["schema"] = incremental.SCHEMA + 1
    path.write_text(json.dumps(data), encoding="utf-8")
    assert cache.lookup(plan) is None


def test_a_tampered_plan_is_a_miss(incremental, plan, tmp_path):
    cache = incremental.UnitCache(tmp_path / "cache", base=tmp_path)
    unit = cache.store(plan, {"ok": True})
    path = cache.unit_dir(unit.key) / incremental.MANIFEST
    data = json.loads(path.read_text(encoding="utf-8"))
    data["plan"]["seed"] = 99
    path.write_text(json.dumps(data), encoding="utf-8")
    assert cache.lookup(plan) is None


def test_storing_a_missing_artifact_is_refused(incremental, plan, tmp_path):
    cache = incremental.UnitCache(tmp_path / "cache", base=tmp_path)
    with pytest.raises(FileNotFoundError):
        cache.store(plan, {"ok": True}, artifacts=[tmp_path / "absent.pt"])
    assert cache.keys() == []


def test_validate_all_reports_broken_units(incremental, plan, tmp_path):
    cache = incremental.UnitCache(tmp_path / "cache", base=tmp_path)
    artifact = tmp_path / "model.pt"
    artifact.write_bytes(b"weights")
    good = cache.store(plan, {"ok": True}, artifacts=[artifact])
    other = cache.store(dict(plan, seed=1), {"ok": True})
    (cache.unit_dir(other.key) / incremental.MANIFEST).write_text("oops", encoding="utf-8")
    problems = cache.validate_all()
    assert good.key not in problems
    assert problems[other.key] == ["unreadable unit"]


def test_impl_digest_tracks_the_code(incremental, tmp_path):
    first = tmp_path / "a.py"
    second = tmp_path / "b.py"
    first.write_text("x = 1\n", encoding="utf-8")
    second.write_text("y = 2\n", encoding="utf-8")
    before = incremental.impl_digest([first, second])
    assert before == incremental.impl_digest([second, first])
    second.write_text("y = 3\n", encoding="utf-8")
    assert incremental.impl_digest([first, second]) != before
