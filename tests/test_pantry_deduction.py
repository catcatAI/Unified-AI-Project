# ANGELA-MATRIX: L3 [βγδ] [B] [L2]
"""Stage P's contract: the registered corpus, the solver's targets, the gates.

These tests do not measure a model. They check the apparatus that §49 registers:

* the corpus is the same generator call as stage L - both digests, both sizes -
  because a different corpus would make P's held-out set a different test;
* the turn-by-turn runner is bitwise the contract's ``ai_step``/``al_step``
  sequence, including ``state_version`` and ``ticks`` (batching must not change
  what the state is);
* every target comes from ``derive()``, not from the culprit field: the full
  session has one answer on 200/200, and the pre-correction prefix has exactly
  one - the trap - on the 98 sessions §49.6 names;
* the format control replaces the answer with a real *other* actor, so it can
  only learn format;
* gate verdicts are recomputed from recorded numbers, and ``verdict`` counts
  booleans only (the §46.11 bug: a number in the checks dict made a perfect run
  impossible);
* a smoke report can never be picked up as the F-rand control.

The end-to-end pieces here are tiny (8 hidden); a random-weight run failing
G1-G10 is expected and is not the point.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "train_pantry_deduction.py"


@pytest.fixture(scope="module")
def stage():
    spec = importlib.util.spec_from_file_location("pantry_deduction_under_test", SCRIPT)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules["pantry_deduction_under_test"] = loaded
    spec.loader.exec_module(loaded)
    return loaded


@pytest.fixture(scope="module")
def corpus(stage):
    return stage.load_corpus()


# --------------------------------------------------------------------------- #
# the registered corpus
# --------------------------------------------------------------------------- #
def test_corpus_is_the_stage_l_call(stage, corpus):
    meta = corpus["meta"]
    assert meta["train_sessions"] == stage.TRAIN_SESSIONS == 800
    assert meta["heldout_sessions"] == stage.HOLDOUT_SESSIONS == 200
    assert meta["train_bytes"] == stage.TRAIN_BYTES == 1_014_924
    assert meta["heldout_bytes"] == stage.HOLDOUT_BYTES == 254_050
    assert meta["train_digest"] == stage.TRAIN_DIGEST
    assert meta["heldout_digest"] == stage.HOLDOUT_DIGEST
    assert meta["registered_sizes_match"] is True
    assert meta["registered_digests_match"] is True


def test_registered_constants_did_not_drift(stage):
    assert stage.TASK_VERSION == "pantry-deduction-v1"
    assert stage.SEED == 20261118
    assert stage.LEARNING_RATE == 5e-4
    assert stage.BATCH == 8
    assert stage.EPOCHS == 20
    assert stage.VOCAB_SIZE == 259
    assert stage.HIDDEN == 128 and stage.EMB == 64
    assert stage.CHUNK_SECONDS == 60.0
    assert stage.MAX_ANSWER_BYTES == 8
    assert stage.L_PARAMS == 124_611
    assert stage.L_WEIGHTS_HASH.startswith("sha256:")
    assert stage.L_INIT_HASH.startswith("sha256:")
    assert stage.L_WEIGHTS_HASH != stage.L_INIT_HASH
    assert len(stage.L_CHECKPOINT_SHA256) == 64
    assert stage.FIT_SESSIONS == 200
    assert stage.FIT_FLOOR == 0.25
    assert stage.SURFACE_BASELINE_UPPER == 0.25
    assert stage.GAP_MIN == 0.25
    assert stage.FLIP_MIN == 0.50
    assert stage.CHANCE_MARGIN == 0.10
    assert stage.TOP_SHARE_MAX == 0.35


def test_render_and_turn_tokens_are_the_same_stream(stage, corpus):
    for session in corpus["heldout"][:20]:
        tokens = stage.turn_tokens(session)
        rebuilt = b"".join(bytes(token - stage.BYTE_OFFSET for token in row) for row in tokens)
        assert rebuilt == stage.render_session(session)
        assert all(token >= stage.BYTE_OFFSET for row in tokens for token in row)
        assert all(row[-1] == stage.BYTE_OFFSET + 10 for row in tokens)  # newline


def test_every_session_has_eleven_turns_and_zero_first_gap(stage, corpus):
    for session in corpus["train"][:50] + corpus["heldout"][:50]:
        gaps = stage.turn_gaps(session)
        assert len(session["turns"]) == len(gaps) == 11
        assert gaps[0] == 0.0 and all(gap >= 0.0 for gap in gaps)


def test_leak_check_is_clean_and_rejects_a_leaky_session(stage, corpus):
    clean = stage.leak_report(corpus["heldout"])
    assert clean["clean"] is True, clean["problems"]

    leaky = json.loads(json.dumps(corpus["heldout"][0]))
    oracle = leaky["ground_truth_oracle"]
    leaky["turns"][0]["user_input"] += " " + oracle["evidence_tag"]
    broken = stage.leak_report([leaky])
    assert broken["clean"] is False
    assert any("evidence_tag" in problem for problem in broken["problems"])

    named = json.loads(json.dumps(corpus["heldout"][0]))
    named["turns"][-1]["user_input"] += " " + named["ground_truth_oracle"]["culprit"]
    assert stage.leak_report([named])["clean"] is False


# --------------------------------------------------------------------------- #
# the solver decides every target
# --------------------------------------------------------------------------- #
def test_full_testimony_derives_exactly_the_culprit(stage, corpus):
    module = stage._load_generator()
    for session in corpus["heldout"]:
        candidates = stage.solver_candidates(module, session, set())
        assert candidates == [session["ground_truth_oracle"]["culprit"]]


def test_pre_correction_prefix_is_singleton_on_98_and_is_not_the_culprit(stage, corpus):
    module = stage._load_generator()
    singleton = []
    chains = {}
    for session in corpus["heldout"]:
        dropped = stage.drop_indices(session, "no_correction")
        assert len(dropped) == 1
        candidates = stage.solver_candidates(module, session, dropped)
        if len(candidates) == 1:
            singleton.append(session)
            chain = session["session_meta"]["chain"]
            chains[chain] = chains.get(chain, 0) + 1
            assert candidates != [session["ground_truth_oracle"]["culprit"]]
    assert len(singleton) == 98
    assert chains == {"apron": 52, "badge": 46}


def test_ablation_turns_exist_everywhere_and_never_remove_the_question(stage, corpus):
    for session in corpus["heldout"]:
        last = len(session["turns"]) - 1
        for variant, count in (("no_roster", 1), ("no_correction", 1), ("no_bounds", 2)):
            dropped = stage.drop_indices(session, variant)
            assert len(dropped) == count, (variant, dropped)
            assert max(dropped) < last, (variant, dropped)
        assert stage.drop_indices(session, "full") == set()
        assert stage.drop_indices(session, "reset") == set()
        assert stage.drop_indices(session, "skip_al") == set()


def test_no_roster_removes_the_only_place_the_answer_can_come_from(stage, corpus):
    module = stage._load_generator()
    for session in corpus["heldout"][:40]:
        candidates = stage.solver_candidates(
            module, session, stage.drop_indices(session, "no_roster")
        )
        assert len(candidates) > 1  # the roster was what named one person


# --------------------------------------------------------------------------- #
# the runner is the contract's sequence
# --------------------------------------------------------------------------- #
def test_turn_runner_is_bitwise_ai_step_plus_al_step(stage, corpus):
    torch = pytest.importorskip("torch")
    core = stage.build_core(hidden=8, emb=4, device="cpu", seed=7)
    session = corpus["heldout"][0]
    turns = stage.turn_tokens(session)
    gaps = stage.turn_gaps(session)

    state = core.init_state(1)
    expected = None
    for index, row in enumerate(turns):
        if index > 0:
            gap = torch.as_tensor([gaps[index]], dtype=torch.float32)
            state = core.al_step(gap, state)
        _, state = core.ai_step(torch.as_tensor([row], dtype=torch.long), state)
        expected = state.tensors["h"].detach().clone()

    resulting, hidden = stage.run_session(core, [turns], [gaps])
    assert torch.allclose(hidden, expected, atol=1e-6)
    assert resulting.ticks == state.ticks
    assert resulting.state_version == state.state_version
    assert resulting.state_version == 2 * len(turns) - 1


def test_batching_does_not_change_a_sample_state(stage, corpus):
    torch = pytest.importorskip("torch")
    core = stage.build_core(hidden=8, emb=4, device="cpu", seed=11)
    sessions = corpus["heldout"][:3]
    turns = [stage.turn_tokens(session) for session in sessions]
    gaps = [stage.turn_gaps(session) for session in sessions]

    # different turn lengths inside one turn is the interesting case
    assert len({len(turns[0][0]), len(turns[1][0]), len(turns[2][0])}) > 1

    _, batched = stage.run_session(core, turns, gaps)
    for index in range(len(sessions)):
        _, alone = stage.run_session(core, [turns[index]], [gaps[index]])
        assert torch.allclose(batched[index : index + 1], alone, atol=1e-6)


def test_reset_variant_sees_only_the_last_turn(stage, corpus):
    torch = pytest.importorskip("torch")
    core = stage.build_core(hidden=8, emb=4, device="cpu", seed=13)
    session = corpus["heldout"][0]
    turns = stage.turn_tokens(session)
    gaps = stage.turn_gaps(session)

    _, reset = stage.run_session(core, [turns], [gaps], reset_before_last=True)
    fresh = core.init_state(1)
    _, expected = core.ai_step(torch.as_tensor([turns[-1]], dtype=torch.long), fresh)
    assert torch.allclose(reset, expected.tensors["h"].detach(), atol=1e-6)


def test_skip_al_changes_the_answer_when_the_next_turn_is_short(stage):
    """A 124-byte turn washes out a random GRU's state, so use short turns.

    This is not a detail: with random weights the update gate forgets the
    incoming state within a few dozen bytes, which is exactly why the trained
    run has to learn to hold it. The test only checks that ``al_step`` is on the
    path at all.
    """
    torch = pytest.importorskip("torch")
    core = stage.build_core(hidden=8, emb=4, device="cpu", seed=17)
    session = stage.load_corpus()["heldout"][1]
    turns = stage.turn_tokens(session)
    short = [turns[0][:6], turns[1][:6], [stage.BYTE_OFFSET + ord("A")]]
    gaps = [0.0, 3600.0, 7200.0]

    _, with_time = stage.run_session(core, [short], [gaps])
    _, without = stage.run_session(core, [short], [[0.0] * len(gaps)])
    assert not torch.allclose(with_time, without, atol=1e-6)


# --------------------------------------------------------------------------- #
# the format control and the answer loss
# --------------------------------------------------------------------------- #
def test_random_answer_is_a_real_actor_and_never_the_culprit(stage, corpus):
    for session in corpus["heldout"][:60]:
        first = stage.random_answer_ids(session, stage.SEED)
        again = stage.random_answer_ids(session, stage.SEED)
        assert first == again
        text = bytes(token - stage.BYTE_OFFSET for token in first).decode("utf-8")
        assert text.endswith("\n")
        name = text[:-1]
        assert name in session["environment"]["actors"]
        assert name != session["ground_truth_oracle"]["culprit"]


def test_answer_ids_are_the_culprit(stage, corpus):
    for session in corpus["heldout"][:20]:
        ids = stage.answer_ids(session)
        text = bytes(token - stage.BYTE_OFFSET for token in ids).decode("utf-8")
        assert text == session["ground_truth_oracle"]["culprit"] + "\n"
        assert len(ids) <= stage.MAX_ANSWER_BYTES + 1


def test_build_samples_switches_arm(stage, corpus):
    sessions = corpus["heldout"][:5]
    scored = stage.build_samples(sessions, seed=stage.SEED, control=None)
    control = stage.build_samples(sessions, seed=stage.SEED, control="rand")
    for left, right, session in zip(scored, control, sessions):
        assert left["answer"] == stage.answer_ids(session)
        assert right["answer"] == stage.random_answer_ids(session, stage.SEED)
        assert left["turns"] == right["turns"]
        assert left["gaps"] == right["gaps"]


# --------------------------------------------------------------------------- #
# decoding and scoring
# --------------------------------------------------------------------------- #
def test_generate_and_rank_are_bounded_and_deterministic(stage, corpus):
    pytest.importorskip("torch")
    core = stage.build_core(hidden=8, emb=4, device="cpu", seed=19)
    core.eval()
    session = corpus["heldout"][0]
    turns = stage.turn_tokens(session)
    gaps = stage.turn_gaps(session)
    with core._torch.no_grad():
        _, hidden = stage.run_session(core, [turns], [gaps])
        first = stage.generate_bytes(core, hidden)
        second = stage.generate_bytes(core, hidden)
    assert first == second
    assert len(first) == 1 and 0 <= len(first[0]) <= stage.MAX_ANSWER_BYTES

    ranked = stage.rank_actor(core, hidden, session["environment"]["actors"])
    assert ranked in session["environment"]["actors"]


def test_summarise_reports_chance_and_shares(stage):
    records = [
        {
            "session_id": "a",
            "chain": "apron",
            "actors": 4,
            "target": "Alex",
            "prediction": "Alex",
            "ranking": "Alex",
        },
        {
            "session_id": "b",
            "chain": "apron",
            "actors": 4,
            "target": "Betty",
            "prediction": "Alex",
            "ranking": "Betty",
        },
        {
            "session_id": "c",
            "chain": "badge",
            "actors": 5,
            "target": None,
            "prediction": "Alex",
            "ranking": "Alex",
        },
    ]
    summary = stage.summarise(records)
    assert summary["n"] == 2
    assert summary["correct"] == 1
    assert summary["exact"] == 0.5
    assert summary["ranking_correct"] == 2
    assert summary["chance"] == round((0.25 + 0.25) / 2, 4)
    assert summary["distinct_predictions"] == 1
    assert summary["top_share"] == round(3 / 3, 4)
    assert summary["per_chain"]["apron"]["n"] == 2
    assert "badge" not in summary["per_chain"]  # nothing targeted there


def test_flip_needs_both_sides_right(stage):
    full = [
        {"session_id": "a", "chain": "apron", "target": "Alex", "prediction": "Alex"},
        {"session_id": "b", "chain": "badge", "target": "Betty", "prediction": "Chris"},
    ]
    pre = [
        {"session_id": "a", "chain": "apron", "target": "David", "prediction": "David"},
        {"session_id": "b", "chain": "badge", "target": "Elena", "prediction": "Elena"},
    ]
    summary = stage.flip_summary(full, pre)
    assert summary["n"] == 2
    assert summary["flipped"] == 1
    assert summary["flip_rate"] == 0.5
    assert summary["changed_rate"] == 1.0
    assert summary["full_exact_on_subset"] == 0.5


def test_wilson_is_not_a_point_estimate(stage):
    low, high = stage.wilson(0, 200)
    assert low == 0.0 and high < 0.05
    low, high = stage.wilson(40, 200)
    assert 0.15 < low < 0.20 < high < 0.27
    assert stage.wilson(0, 0) == (0.0, 1.0)


# --------------------------------------------------------------------------- #
# gates
# --------------------------------------------------------------------------- #
def _perfect_report(stage):
    return {
        "corpus": {
            "registered_sizes_match": True,
            "registered_digests_match": True,
            "train_digest": stage.TRAIN_DIGEST,
            "heldout_digest": stage.HOLDOUT_DIGEST,
        },
        "start": {
            "checkpoint": "data/text_stage/x.pt",
            "weights_hash": stage.L_WEIGHTS_HASH,
            "checkpoint_sha256": stage.L_CHECKPOINT_SHA256,
            "params": stage.L_PARAMS,
        },
        "results": {
            "full": {
                "chance": 0.1591,
                "exact": 0.40,
                "wilson_lower": 0.35,
                "ranking_exact": 0.42,
                "ranking_lower": 0.36,
                "top_share": 0.20,
            },
            "reset": {"exact": 0.10},
            "train_fit": {"exact": 0.55},
            "flip": {"flip_rate": 0.60, "full_exact_on_subset": 0.40},
        },
        "control": {"exact": 0.16, "ranking_exact": 0.15},
        "cost": {"params": stage.L_PARAMS, "train_seconds": 10.0, "device": "cpu"},
    }


def test_all_gates_pass_on_a_perfect_report(stage):
    checks = stage.gate_values(_perfect_report(stage))
    assert all(checks.values()), checks


def test_gates_are_recomputed_not_trusted(stage):
    # G8: a format control that learned the answer is not a control
    leaky = _perfect_report(stage)
    leaky["control"]["exact"] = 0.40
    assert stage.gate_values(leaky)["G8_format_control_at_chance"] is False

    # G7: a reset that scores as well as the full session means the answer was
    # never in the state
    amnesiac = _perfect_report(stage)
    amnesiac["results"]["reset"]["exact"] = 0.39
    assert stage.gate_values(amnesiac)["G7_answer_lives_in_the_state"] is False

    # G4: the lower bound is the bar, not the point estimate
    noisy = _perfect_report(stage)
    noisy["results"]["full"]["wilson_lower"] = 0.24
    assert stage.gate_values(noisy)["G4_heldout_exact_beats_surface"] is False

    # G9: one name for every session is not selection
    constant = _perfect_report(stage)
    constant["results"]["full"]["top_share"] = 0.9
    assert stage.gate_values(constant)["G9_not_a_constant_answer"] is False

    # G1: starting anywhere other than stage L is a different experiment
    elsewhere = _perfect_report(stage)
    elsewhere["start"]["weights_hash"] = "sha256:" + "0" * 64
    assert stage.gate_values(elsewhere)["G1_start_is_stage_l"] is False

    # G6: the strong reading needs both sides right
    no_flip = _perfect_report(stage)
    no_flip["results"]["flip"]["flip_rate"] = 0.10
    assert stage.gate_values(no_flip)["G6_retraction_flips_the_answer"] is False


def test_verdict_counts_booleans_only(stage):
    assert stage.verdict({"a": True, "b": True}) is True
    assert stage.verdict({"a": True, "b": False}) is False
    assert stage.verdict({"a": 0.99}) is False
    assert stage.verdict({}) is False
    assert stage.verdict({"a": True, "b": 0.1557}) is True  # the §46.11 bug


# --------------------------------------------------------------------------- #
# the control report must be the right one
# --------------------------------------------------------------------------- #
def test_control_lookup_ignores_smoke_and_the_scored_arm(stage, tmp_path):
    def write(name, arm, smoke=False):
        path = tmp_path / name
        payload = {
            "task_version": stage.TASK_VERSION,
            "control_arm": arm,
            "smoke": smoke,
            "corpus": {"heldout_digest": stage.HOLDOUT_DIGEST},
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    write("pantry_deduction_0001.json", "answer")
    write("pantry_deduction_0002.json", "smoke", smoke=True)
    control = write("pantry_deduction_0003.json", "rand")
    assert stage._find_control_report(tmp_path) == control


def test_control_lookup_is_empty_without_a_control(stage, tmp_path):
    assert stage._find_control_report(tmp_path) is None
    assert stage._find_control_report(tmp_path / "missing") is None


def test_check_report_refuses_a_wrong_version_and_a_missing_file(stage, tmp_path):
    assert stage.check_report(tmp_path / "nope.json")

    wrong = tmp_path / "wrong.json"
    wrong.write_text(json.dumps({"task_version": "text-stage-v1"}), encoding="utf-8")
    problems = stage.check_report(wrong)
    assert any("task_version" in problem for problem in problems)


def test_stage_l_report_hash_named_the_initialisation(stage):
    """§48.7: L recorded the pre-training hash under ``weights_hash``.

    This test preserves the diagnosis instead of the mistake: the value in L's
    report is reproduced by the seed's initialisation, not by the checkpoint.
    """
    pytest.importorskip("torch")
    from ai.core.stateful_decoder import GRUCore

    core = GRUCore(259, hidden=128, emb=64, chunk_seconds=60.0, seed=20261116, device="cpu")
    assert core.weights_hash() == stage.L_INIT_HASH


def test_start_point_is_the_stage_l_artifact(stage):
    path = REPO_ROOT / stage.L_CHECKPOINT
    if not path.exists():
        pytest.skip("the stage-L checkpoint is a gitignored artifact")
    pytest.importorskip("torch")
    core = stage.build_core(device="cpu")
    assert stage.load_stage_l(core, path) == stage.L_WEIGHTS_HASH


def test_registered_corpus_reproduces_on_demand(stage):
    """The generator is deterministic: a second call must give the same bytes."""
    again = stage.load_corpus()
    assert again["meta"]["train_digest"] == stage.TRAIN_DIGEST
    assert again["meta"]["heldout_digest"] == stage.HOLDOUT_DIGEST


def test_baselines_are_below_the_registered_bar(stage):
    """§49.6: 0.25 is the strongest surface baseline's upper bound, not a mood."""
    audit = stage._load_generator().shortcut_audit(stage.load_corpus()["heldout"])
    assert audit
    upper = max(row["upper95"] for row in audit.values())
    assert math.isclose(upper, stage.SURFACE_BASELINE_UPPER, abs_tol=5e-3)
    assert all(row["upper95"] <= stage.SURFACE_BASELINE_UPPER + 5e-3 for row in audit.values())
