# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§66 contracts: the readout/state probe's arithmetic and its mechanical fork.

No training and no checkpoint: the integration cases build a small untrained
``TurnStoreCore`` and read the same held-out sessions the trainer would, which
is enough to pin the shapes, the identity re-read and the edit surgery. The
model-derived numbers are graded by the probe itself, never here.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "scripts" / "probe_pantry_readout.py"


@pytest.fixture(scope="module")
def probe():
    spec = importlib.util.spec_from_file_location("probe_pantry_readout_under_test", PROBE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_pantry_readout_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def trainer(probe):
    return probe.load_trainer()


@pytest.fixture(scope="module")
def module(trainer):
    return trainer._load_generator()


@pytest.fixture(scope="module")
def stage(probe, trainer, module):
    """A small untrained store core plus eight held-out sessions, per roster size."""
    names = sorted(module.ACTORS)
    out = {}
    for size in (2, 5):
        corpus = trainer.load_corpus(minimal_binding=True, order_augmented=True, roster_size=size)
        sessions = corpus["heldout"][:8]
        core = trainer.build_core(hidden=32, emb=16, device="cpu", kind="turnstore", memory=True)
        out[size] = {
            "sessions": sessions,
            "names": names,
            "indices": probe.roster_indices(sessions, names),
            "core": core,
            "identity": probe.read_variant(trainer, core, sessions, names, batch=8),
        }
    return out


# --------------------------------------------------------------------------- #
# the arithmetic
# --------------------------------------------------------------------------- #
def test_cosine_and_relative_change_are_the_textbook_quantities(probe):
    left = np.array([[1.0, 0.0], [1.0, 1.0]], dtype=np.float32)
    right = np.array([[1.0, 0.0], [-1.0, -1.0]], dtype=np.float32)
    cos = probe._cos_rows(left, right)
    assert cos[0] == pytest.approx(1.0)
    assert cos[1] == pytest.approx(-1.0)
    rel = probe._rel_rows(left, right)
    assert rel[0] == pytest.approx(0.0)
    assert rel[1] == pytest.approx(np.sqrt(8.0) / np.sqrt(2.0))


def test_distribution_reports_the_quantiles_it_names(probe):
    block = probe._distribution(np.arange(5, dtype=np.float64))
    assert block["min"] == 0.0
    assert block["median"] == 2.0
    assert block["max"] == 4.0
    assert block["mean"] == 2.0


def test_sensitivity_counts_the_sessions_below_each_registered_cut(probe):
    values = np.array([0.50, 0.96, 0.995, 0.9999], dtype=np.float64)
    block = probe._sensitivity(values)
    assert block["n"] == 4
    assert block["below_cut"]["0.9"] == 1
    assert block["below_cut"]["0.95"] == 1
    assert block["below_cut"]["0.99"] == 2
    assert block["below_cut"]["0.999"] == 3


def test_rate_is_the_share_of_true_flags(probe):
    assert probe._rate([True, False, True, True]) == 0.75
    assert probe._rate([]) == 0.0


# --------------------------------------------------------------------------- #
# the read
# --------------------------------------------------------------------------- #
def test_identity_re_read_is_exactly_itself(stage, probe):
    for size, block in stage.items():
        outcome = probe.compare_variant(
            block["identity"],
            block["identity"],
            block["sessions"],
            block["names"],
            block["indices"],
            label="identity",
        )
        assert outcome["same_prediction"] == 1.0
        assert outcome["same_roster_argmax"] == 1.0
        assert outcome["argmax_flip_rate"] == 0.0
        assert outcome["mean_abs_delta_roster"] == 0.0
        assert outcome["h_rel_final"]["max"] == 0.0


def test_the_probe_keeps_both_boundaries_and_the_store(stage, probe):
    for size, block in stage.items():
        read = block["identity"]
        n = len(block["sessions"])
        assert read["scores"].shape == (n, len(block["names"]))
        assert read["h_final"].shape[0] == n
        assert read["read_final"].shape[0] == n
        assert read["h_roster"].shape == read["h_final"].shape
        # the roster turn is not the answer turn, so the two states differ
        assert not np.allclose(read["h_roster"], read["h_final"])
        assert read["store_v"].shape[0] == n and read["store_v"].shape[1] > 0


def test_the_probe_scores_names_exactly_like_rank_actor(stage, probe, trainer):
    for size, block in stage.items():
        core = block["core"]
        sessions = block["sessions"]
        names = block["names"]
        scores = block["identity"]["scores"]
        for row, session in enumerate(sessions):
            roster = list(session["environment"]["actors"])
            expected = trainer.rank_actor(
                core, trainer._slice(_final_boundary(trainer, core, session), 0, 1), roster
            )
            index = [names.index(name) for name in roster]
            got = names[index[int(np.argmax(scores[row, index]))]]
            assert got == expected


def _final_boundary(trainer, core, session):
    """The answer boundary, read the same way `evaluate` reads it."""
    tokens = [
        [trainer.BYTE_OFFSET + byte for byte in (turn["user_input"] + "\n").encode("utf-8")]
        for turn in session["turns"]
    ]
    gaps = [float(turn["dt_s"]) for turn in session["turns"]]
    state, _ = trainer.run_session(core, [tokens], [gaps])
    return dict(state.tensors)


# --------------------------------------------------------------------------- #
# the edits (R2)
# --------------------------------------------------------------------------- #
def test_the_twin_and_the_reorder_change_only_the_roster_turn(stage, module, probe):
    for size, block in stage.items():
        twins = [module.minimal_twin(session) for session in block["sessions"]]
        reorders = [module.minimal_order_twin(session) for session in block["sessions"]]
        outcome = probe.verify_edits(module, block["sessions"], twins, reorders)
        assert outcome["violations"] == []
        assert outcome["checked"] == len(block["sessions"])


def test_the_verifier_catches_an_edit_outside_the_roster_turn(stage, module, probe):
    sessions = stage[2]["sessions"]
    twins = [module.minimal_twin(session) for session in sessions]
    reorders = [module.minimal_order_twin(session) for session in sessions]
    damaged = json.loads(json.dumps(reorders))
    damaged[0]["turns"][3]["user_input"] = damaged[0]["turns"][3]["user_input"] + "?"
    outcome = probe.verify_edits(module, sessions, twins, damaged)
    assert any("changed turns" in problem for problem in outcome["violations"])


def test_the_verifier_catches_a_twin_that_keeps_the_answer(stage, module, probe):
    sessions = stage[2]["sessions"]
    twins = [json.loads(json.dumps(session)) for session in sessions]
    reorders = [module.minimal_order_twin(session) for session in sessions]
    outcome = probe.verify_edits(module, sessions, twins, reorders)
    assert any("did not flip" in problem for problem in outcome["violations"])


def test_the_verifier_catches_a_reorder_that_moves_the_answer(stage, module, probe):
    sessions = stage[2]["sessions"]
    twins = [module.minimal_twin(session) for session in sessions]
    reorders = [module.minimal_twin(session) for session in sessions]
    outcome = probe.verify_edits(module, sessions, twins, reorders)
    assert any("reorder" in problem for problem in outcome["violations"])


# --------------------------------------------------------------------------- #
# the fork (§66.9)
# --------------------------------------------------------------------------- #
def _variant(read_median, *, store_median=0.05, moved=0.0):
    return {
        "read_cos_final": {"median": read_median},
        "store_v_rel_final": {"median": store_median},
        "moved_to_twin_target": moved,
    }


def test_fork_static_read_with_a_written_store_is_stored_not_read(probe):
    outcome = probe.branch(k=2, twin=_variant(read_median=0.999), reorder=_variant(0.998))
    assert outcome["id"] == "R3a-stored-not-read"


def test_fork_static_read_with_an_unwritten_store_is_not_stored(probe):
    outcome = probe.branch(
        k=5,
        twin=_variant(read_median=0.999, store_median=0.001),
        reorder=_variant(0.998, store_median=0.001),
    )
    assert outcome["id"] == "R3a-not-stored"


def test_fork_moving_read_without_following_the_mapping_is_head_ignores(probe):
    outcome = probe.branch(
        k=2,
        twin=_variant(read_median=0.80, moved=0.20),
        reorder=_variant(0.80),
    )
    assert outcome["id"] == "R3b-head-ignores"


def test_fork_moving_read_that_follows_the_mapping_is_read_out_used(probe):
    outcome = probe.branch(
        k=2,
        twin=_variant(read_median=0.80, moved=0.75),
        reorder=_variant(0.80),
    )
    assert outcome["id"] == "R3c-follows-but-wrong"


def test_fork_needs_both_edits_static_to_call_the_read_static(probe):
    static_twin = _variant(read_median=0.999)
    moving_reorder = _variant(read_median=0.70)
    outcome = probe.branch(k=2, twin=static_twin, reorder=moving_reorder)
    assert outcome["id"] != "R3a-stored-not-read"
    assert outcome["id"] == "R3b-head-ignores"


def test_fork_is_a_pure_function_of_the_stored_medians(probe):
    twin = _variant(read_median=0.995, moved=0.10)
    reorder = _variant(read_median=0.996)
    first = probe.branch(k=3, twin=twin, reorder=reorder)
    second = probe.branch(
        k=3,
        twin=json.loads(json.dumps(twin)),
        reorder=json.loads(json.dumps(reorder)),
    )
    assert first == second


# --------------------------------------------------------------------------- #
# the mechanical re-check
# --------------------------------------------------------------------------- #
def _synthetic_report(*, k=2, read_median=0.999, moved=0.1, store_median=0.05):
    summary = {"n": 200, "correct": 53, "exact": 0.265, "chance": 0.5}
    twin = _variant(read_median=read_median, store_median=store_median, moved=moved)
    reorder = _variant(read_median=read_median)
    fork = None
    return {
        "k": k,
        "r1_identity_reproduces_the_report": {
            "matches": True,
            "identity_summary": dict(summary),
            "report_full": dict(summary),
        },
        "r2_edits_are_surgical": {"checked": 200, "violations": []},
        "readout": {
            "identity": {"same_prediction": 1.0},
            "twin": twin,
            "reorder": reorder,
            "mismatch": {"n": 200},
        },
        "fork": fork,
        "r4_cost": {
            "sessions": 200,
            "weights_hash_before": "abc",
            "weights_hash_after": "abc",
            "checkpoint_sha256_before": "def",
            "checkpoint_sha256_after": "def",
            "checkpoint_unchanged": True,
        },
    }


def _write_check_report(probe, tmp_path, **overrides):
    data = _synthetic_report(**overrides)
    data["fork"] = probe.branch(
        k=data["k"], twin=data["readout"]["twin"], reorder=data["readout"]["reorder"]
    )
    path = tmp_path / "probe66.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_check_accepts_a_well_formed_report(probe, tmp_path):
    path = _write_check_report(probe, tmp_path)
    assert probe.check(path) == []


def test_check_rejects_a_stale_fork(probe, tmp_path):
    path = _write_check_report(probe, tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["fork"]["id"] = "R3b-head-ignores"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe.check(path)
    assert any("stale" in problem for problem in problems)


def test_check_rejects_a_changed_checkpoint(probe, tmp_path):
    path = _write_check_report(probe, tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["r4_cost"]["checkpoint_sha256_after"] = "changed"
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe.check(path)
    assert any("checkpoint bytes changed" in problem for problem in problems)


def test_check_rejects_a_report_whose_r1_no_longer_matches(probe, tmp_path):
    path = _write_check_report(probe, tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["r1_identity_reproduces_the_report"]["identity_summary"]["exact"] = 1.0
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe.check(path)
    assert any("R1 no longer matches" in problem for problem in problems)


def test_check_rejects_a_recorded_r2_violation(probe, tmp_path):
    path = _write_check_report(probe, tmp_path)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["r2_edits_are_surgical"]["violations"] = ["twin changed two turns"]
    path.write_text(json.dumps(data), encoding="utf-8")
    problems = probe.check(path)
    assert any("R2 violations" in problem for problem in problems)


def test_cli_requires_a_report_or_a_check(probe):
    with pytest.raises(SystemExit):
        probe.main([])


def test_cli_check_prints_ok_for_a_clean_report(probe, tmp_path, capsys):
    path = _write_check_report(probe, tmp_path)
    assert probe.main(["--check", str(path)]) == 0
    assert "check: OK" in capsys.readouterr().out
