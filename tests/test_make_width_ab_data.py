"""Contracts for scripts/make_width_ab_data.py (synthetic width A/B splits).

These tests pin the three properties the A/B depends on: the pair space per
difficulty, a deterministic split with no overlap, and labels that are the
rule (not a stored answer list).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "make_width_ab_data", REPO / "scripts" / "make_width_ab_data.py"
)
gen = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(gen)


def test_pair_space_sizes():
    assert len(gen.pairs(gen.SPECS["d1"])) == 100
    assert len(gen.pairs(gen.SPECS["d2"])) == 900
    assert len(gen.pairs(gen.SPECS["d3"])) == 8100


def test_difficulties_are_disjoint():
    seen = {}
    for name, spec in gen.SPECS.items():
        for pair in gen.pairs(spec):
            assert pair not in seen, f"{pair} appears in {seen.get(pair)} and {name}"
            seen[pair] = name


def test_split_is_deterministic_and_disjoint():
    spec = gen.SPECS["d2"]
    train_a, val_a = gen.split(spec, "salt", 200)
    train_b, val_b = gen.split(spec, "salt", 200)
    assert train_a == train_b
    assert val_a == val_b
    assert not (set(train_a) & set(val_a))
    assert len(train_a) + len(val_a) == 900


def test_a_different_salt_moves_rows_across_the_split():
    spec = gen.SPECS["d3"]
    _, val_a = gen.split(spec, "salt-a", 200)
    _, val_b = gen.split(spec, "salt-b", 200)
    assert val_a != val_b


def test_rows_are_the_rule_not_a_lookup_table():
    rows = gen.rows([(7, 8), (23, 9), (99, 99)])
    assert [r["input"] for r in rows] == ["7+8", "23+9", "99+99"]
    assert [r["output"] for r in rows] == ["15", "32", "198"]


def test_build_then_check_roundtrip(tmp_path):
    manifest = gen.build(tmp_path, "s", 200)
    assert gen.check(tmp_path, manifest) == []
    for name in gen.SPECS:
        assert (tmp_path / f"{name}_train.jsonl").is_file()
        assert (tmp_path / f"{name}_val.jsonl").is_file()


def test_check_detects_a_tampered_split(tmp_path):
    manifest = gen.build(tmp_path, "s", 200)
    path = tmp_path / "d1_train.jsonl"
    path.write_text(path.read_text(encoding="utf-8") + '{"input": "1+1", "output": "3"}\n')
    problems = gen.check(tmp_path, manifest)
    assert any("content differs" in p for p in problems)
    assert any("row count differs" in p for p in problems)


def test_check_detects_a_missing_split(tmp_path):
    manifest = gen.build(tmp_path, "s", 200)
    (tmp_path / "d2_val.jsonl").unlink()
    assert any("missing" in p for p in gen.check(tmp_path, manifest))


def test_cli_writes_and_validates(tmp_path, capsys):
    out = tmp_path / "data"
    assert gen.main(["--out-dir", str(out), "--salt", "s"]) == 0
    assert (out / "manifest.json").is_file()
    assert gen.main(["--out-dir", str(out), "--check"]) == 0
    assert "agree with the manifest" in capsys.readouterr().out


def test_cli_rejects_an_out_of_range_test_share(tmp_path):
    assert gen.main(["--out-dir", str(tmp_path), "--test-per-mille", "0"]) == 1
    assert gen.main(["--out-dir", str(tmp_path), "--test-per-mille", "1000"]) == 1


def test_manifest_records_the_rule_and_hashes(tmp_path):
    gen.main(["--out-dir", str(tmp_path), "--salt", "s"])
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["rule"].startswith("a+b")
    for cell in manifest["difficulties"].values():
        assert len(cell["train_sha256"]) == 64
        assert len(cell["val_sha256"]) == 64
