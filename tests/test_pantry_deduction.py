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


# --------------------------------------------------------------------------- #
# stage Q (§50): one auxiliary readout per turn, and one calibration arm
# --------------------------------------------------------------------------- #
def _aux_report(stage, *, overfit=False, aux_lambda=1.0, fit_exact=0.55):
    report = _perfect_report(stage)
    report["config"] = {"aux_lambda": aux_lambda}
    report["overfit"] = overfit
    report["results"]["train_fit"]["exact"] = fit_exact
    report["training"] = {
        "history": [
            {
                "epoch": 1,
                "mean_loss": 2.0,
                "mean_main_loss": 1.5,
                "mean_aux_loss": 0.5,
                "aux_lambda": aux_lambda,
            }
        ]
    }
    report["diagnostics"] = {
        "readout": {
            "turns": [
                {"turn": 0, "n": 0, "correct": 0, "exact": None},
                {"turn": 10, "n": 200, "correct": 17, "exact": 0.085},
            ]
        }
    }
    return report


def test_aux_loss_zero_keeps_stage_p_bitwise(stage, corpus):
    """λ=0 must be P's computation, not a numerically similar one."""
    torch = pytest.importorskip("torch")
    session = corpus["heldout"][0]
    core = stage.build_core(hidden=8, emb=4, device="cpu", seed=41)
    turns = [stage.turn_tokens(session)]
    gaps = [stage.turn_gaps(session)]
    answers = [stage.answer_ids(session)]

    _, hidden = stage.run_session(core, turns, gaps)
    boundaries: list = []
    _, with_hook = stage.run_session(core, turns, gaps, boundaries=boundaries)
    assert torch.equal(hidden, with_hook)  # the hook must not change the forward pass
    assert len(boundaries) == len(session["turns"]) == 11
    assert boundaries[-1] is with_hook

    main = stage._answer_loss(core, hidden, answers)
    total, recorded_main, aux = stage._training_loss(core, boundaries, answers, 0.0)
    assert aux is None
    assert torch.equal(total, main) and torch.equal(recorded_main, main)


def test_auxiliary_term_is_the_mean_of_the_earlier_turns(stage, corpus):
    torch = pytest.importorskip("torch")
    session = corpus["heldout"][0]
    core = stage.build_core(hidden=8, emb=4, device="cpu", seed=43)
    boundaries: list = []
    stage.run_session(
        core, [stage.turn_tokens(session)], [stage.turn_gaps(session)], boundaries=boundaries
    )
    answers = [stage.answer_ids(session)]

    main = stage._answer_loss(core, boundaries[-1], answers)
    manual = sum(stage._answer_loss(core, h, answers) for h in boundaries[:-1]) / len(
        boundaries[:-1]
    )
    total, recorded_main, aux = stage._training_loss(core, boundaries, answers, 1.0)
    assert torch.equal(recorded_main, main)
    assert torch.allclose(aux, manual, atol=1e-6)
    assert torch.allclose(total, main + manual, atol=1e-6)
    # the last turn is counted once (main), not again as an auxiliary boundary
    assert len(boundaries[:-1]) == len(session["turns"]) - 1 == 10


def test_auxiliary_loss_gives_every_turn_a_gradient(stage, corpus):
    """The mechanism Q exists for: without it, turn 0 gets nothing (§49.16)."""
    torch = pytest.importorskip("torch")
    sessions = corpus["heldout"][:2]
    turns = [stage.turn_tokens(session) for session in sessions]
    gaps = [stage.turn_gaps(session) for session in sessions]
    answers = [stage.answer_ids(session) for session in sessions]

    def profile(aux_lambda):
        core = stage.build_core(hidden=8, emb=4, device="cpu", seed=47)
        boundaries: list = []
        stage.run_session(core, turns, gaps, boundaries=boundaries)
        for hidden in boundaries:
            hidden.retain_grad()
        total, main, aux = stage._training_loss(core, boundaries, answers, aux_lambda)
        for parameter in core.parameters():
            parameter.grad = None
        total.backward()
        norms = [0.0 if h.grad is None else float(h.grad.norm()) for h in boundaries]
        return norms, main, aux

    without, main_without, aux_without = profile(0.0)
    with_aux, main_with, aux_with = profile(1.0)
    assert aux_without is None and aux_with is not None
    # the same initialisation and the same forward pass => the main term agrees
    assert torch.allclose(main_without, main_with, atol=1e-6)
    # the early turns are exactly what the auxiliary readout changes
    assert without[0] == 0.0 and without[1] == 0.0
    assert all(norm > 0.0 for norm in with_aux)
    assert with_aux[0] > 0.0


def test_prefix_candidates_resolve_at_the_roster_and_the_correction(stage, corpus):
    module = stage._load_generator()
    session = corpus["heldout"][0]
    assert stage.prefix_candidates(module, session, 10) == [
        session["ground_truth_oracle"]["culprit"]
    ]
    # before the roster nobody is named by a value, so nothing is decidable
    assert len(stage.prefix_candidates(module, session, 0)) > 1


def test_readout_profile_counts_only_resolved_prefixes(stage, corpus):
    pytest.importorskip("torch")
    core = stage.build_core(hidden=8, emb=4, device="cpu", seed=53)
    sessions = corpus["heldout"][:20]
    profile = stage.readout_profile(core, sessions, module=stage._load_generator(), batch=8)
    assert profile["sessions"] == 20
    assert len(profile["turns"]) == 11
    # turns 0-5 name everyone (a roll call), so they are not scoreable at all
    assert all(row["n"] == 0 and row["exact"] is None for row in profile["turns"][:6])
    # from the roster on, the solver has one answer on every session
    assert all(row["n"] == 20 for row in profile["turns"][7:])
    assert "diagnostic" in profile["note"]


def test_aux_gates_are_named_and_recomputed_from_numbers(stage):
    report = _aux_report(stage)
    checks = stage.gate_values(report)
    assert set(checks) == {
        "Q1_overfit_calibration",
        "Q2_instrument_fits_train",
        "Q3_heldout_exact_beats_surface",
        "Q4_heldout_ranking_beats_surface",
        "Q5_retraction_flips_the_answer",
        "Q6_answer_lives_in_the_state",
        "Q7_format_control_at_chance",
        "Q8_not_a_constant_answer",
        "Q9_cost_and_auxiliary_recorded",
    }
    assert checks["Q1_overfit_calibration"] is None  # not an overfit arm
    assert all(value is True for value in checks.values() if isinstance(value, bool))
    assert stage.verdict(checks) is True

    # the same numbers stage P would fail are failed here too (Q3 = G4)
    leaky = _aux_report(stage)
    leaky["results"]["full"]["wilson_lower"] = 0.24
    assert stage.gate_values(leaky)["Q3_heldout_exact_beats_surface"] is False


def test_overfit_calibration_is_q1_and_disables_the_score_gates(stage):
    passing = _aux_report(stage, overfit=True, fit_exact=stage.OVERFIT_FLOOR)
    checks = stage.gate_values(passing)
    assert checks["Q1_overfit_calibration"] is True
    assert all(checks[name] is None for name in checks if not name.startswith(("Q1", "Q9")))
    assert stage.verdict(checks) is True

    failing = _aux_report(stage, overfit=True, fit_exact=stage.OVERFIT_FLOOR - 0.01)
    assert stage.gate_values(failing)["Q1_overfit_calibration"] is False
    assert stage.verdict(stage.gate_values(failing)) is False


def test_q9_needs_the_auxiliary_loss_in_every_epoch(stage):
    missing = _aux_report(stage)
    missing["training"]["history"][0]["mean_aux_loss"] = None
    assert stage.gate_values(missing)["Q9_cost_and_auxiliary_recorded"] is False

    no_readout = _aux_report(stage)
    no_readout["diagnostics"] = {}
    assert stage.gate_values(no_readout)["Q9_cost_and_auxiliary_recorded"] is False

    no_history = _aux_report(stage)
    no_history["training"]["history"] = []
    assert stage.gate_values(no_history)["Q9_cost_and_auxiliary_recorded"] is False


def test_aux_lambda_selects_the_gate_set(stage):
    plain = _perfect_report(stage)
    assert set(stage.gate_values(plain)) == {
        "G1_start_is_stage_l",
        "G2_corpus_is_registered",
        "G3_instrument_fits_train",
        "G4_heldout_exact_beats_surface",
        "G5_heldout_ranking_beats_surface",
        "G6_retraction_flips_the_answer",
        "G7_answer_lives_in_the_state",
        "G8_format_control_at_chance",
        "G9_not_a_constant_answer",
        "G10_cost_recorded",
    }
    zero = _aux_report(stage, aux_lambda=0.0)
    assert "G1_start_is_stage_l" in stage.gate_values(zero)


def test_control_lookup_skips_overfit_and_matches_the_auxiliary_loss(stage, tmp_path):
    def write(name, aux_lambda, overfit=False):
        path = tmp_path / name
        payload = {
            "task_version": stage.TASK_VERSION,
            "control_arm": "rand",
            "corpus": {"heldout_digest": stage.HOLDOUT_DIGEST},
            "config": {"aux_lambda": aux_lambda},
            "overfit": overfit,
        }
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    write("pantry_deduction_0001.json", 0.0)
    q_control = write("pantry_deduction_0002.json", 1.0)
    write("pantry_deduction_0003.json", 1.0, overfit=True)

    assert stage._find_control_report(tmp_path, aux_lambda=1.0) == q_control
    assert stage._find_control_report(tmp_path, aux_lambda=0.0).name.endswith("0001.json")
    assert stage._find_control_report(tmp_path, aux_lambda=0.5) is None


# --------------------------------------------------------------------------- #
# stage R (§51): supervise only the boundaries that already have an answer
# --------------------------------------------------------------------------- #
def test_resolvable_prefixes_start_at_the_roster(stage, corpus):
    """§50.13 measured where an answer exists; the loss must agree with it."""
    module = stage._load_generator()
    rows = stage.build_samples(
        corpus["train"][:32], seed=20261118, control=None, prefix_module=module
    )
    counts = [
        sum(1 for row in rows if row["prefix_answers"][boundary] is not None)
        for boundary in range(10)
    ]
    # turns 0-5 are a roll call: nobody is decidable yet, so nothing is asked
    assert counts[:6] == [0] * 6
    # turn 6 resolves to the pre-correction name on half of them, 7-9 to the culprit
    assert counts[6] == 16
    assert counts[7:] == [32, 32, 32]


def test_resolvable_loss_skips_boundaries_that_have_no_answer(stage, corpus):
    torch = pytest.importorskip("torch")
    session = corpus["heldout"][0]
    core = stage.build_core(hidden=8, emb=4, device="cpu", seed=67)
    boundaries: list = []
    stage.run_session(
        core, [stage.turn_tokens(session)], [stage.turn_gaps(session)], boundaries=boundaries
    )
    answers = [stage.answer_ids(session)]

    # every earlier boundary is ambiguous: the auxiliary term is not a loss at
    # all, it is "nothing to supervise" - not a zero that pulls the head
    empty = [[None] * len(boundaries[:-1])]
    total, main, aux = stage._training_loss(core, boundaries, answers, 1.0, empty)
    assert aux is None
    assert torch.equal(total, main)

    # one resolvable boundary supervises exactly that boundary
    one = [[None] * len(boundaries[:-1])]
    one[0][6] = answers[0]
    total, main, aux = stage._training_loss(core, boundaries, answers, 1.0, one)
    assert torch.allclose(aux, stage._answer_loss(core, boundaries[6], answers), atol=1e-6)
    assert torch.allclose(total, main + aux, atol=1e-6)


def test_format_control_prefix_never_carries_the_real_answer(stage, corpus):
    """The control must stay format-only at every boundary, or R7 is void."""
    module = stage._load_generator()
    rows = stage.build_samples(
        corpus["train"][:4], seed=20261118, control="rand", prefix_module=module
    )
    for row in rows:
        truth = stage.answer_ids(row["session"])
        assert row["answer"] != truth
        assert all(entry == row["answer"] for entry in row["prefix_answers"])
        assert all(entry != truth for entry in row["prefix_answers"])


def test_resolvable_reports_are_graded_as_r_not_q(stage):
    report = _aux_report(stage)
    report["config"]["aux_mode"] = "resolvable"
    checks = stage.gate_values(report)
    assert set(checks) == {("R" + name[1:]) for name in stage.gate_values(_aux_report(stage))}
    assert "R1_overfit_calibration" in checks and "Q1_overfit_calibration" not in checks


def test_control_lookup_does_not_cross_aux_modes(stage, tmp_path):
    payload = {
        "task_version": stage.TASK_VERSION,
        "control_arm": "rand",
        "corpus": {"heldout_digest": stage.HOLDOUT_DIGEST},
        "config": {"aux_lambda": 1.0, "aux_mode": "all"},
        "overfit": False,
    }
    (tmp_path / "pantry_deduction_0001.json").write_text(json.dumps(payload), encoding="utf-8")
    assert stage._find_control_report(tmp_path, aux_lambda=1.0, aux_mode="all") is not None
    assert stage._find_control_report(tmp_path, aux_lambda=1.0, aux_mode="resolvable") is None


def test_gate_prefix_labels_a_stage_with_its_own_letter(stage):
    """§52: a stage that changes a different variable gets its own S1-S9."""
    report = _aux_report(stage)
    report["config"]["aux_mode"] = "resolvable"
    report["config"]["gate_prefix"] = "S"
    checks = stage.gate_values(report)
    assert len(checks) == 9
    assert all(name.startswith("S") for name in checks)
    assert "S1_overfit_calibration" in checks


def test_gate_prefix_defaults_by_aux_mode(stage):
    report = _aux_report(stage)
    assert "Q1_overfit_calibration" in stage.gate_values(report)
    report["config"]["aux_mode"] = "resolvable"
    assert "R1_overfit_calibration" in stage.gate_values(report)


def test_gate_prefix_must_be_one_upper_letter(stage):
    for bad in ("SS", "s", "1", ""):
        report = _aux_report(stage)
        report["config"]["gate_prefix"] = bad
        with pytest.raises(SystemExit):
            stage.gate_values(report)


def test_cli_rejects_a_bad_gate_prefix_before_running(stage):
    with pytest.raises(SystemExit):
        stage.main(["--overfit", "1", "--gate-prefix", "ss"])


# --------------------------------------------------------------------------- #
# stage S (§52.4): the width rung must widen, not replace, the carrier
# --------------------------------------------------------------------------- #
def _stage_l_and_widened(stage, widened_hidden):
    path = REPO_ROOT / stage.L_CHECKPOINT
    if not path.exists():
        pytest.skip("the stage-L checkpoint is a gitignored artifact")
    pytest.importorskip("torch")
    torch = pytest.importorskip("torch")
    narrow = stage.build_core(device="cpu")
    assert stage.load_stage_l(narrow, path) == stage.L_WEIGHTS_HASH
    wide = stage.build_core(hidden=widened_hidden, device="cpu")
    digest = stage.widen_from_stage_l(wide, path, source_hidden=stage.HIDDEN)
    return torch, narrow, wide, digest


def test_widened_core_is_behaviourally_stage_l(stage):
    """§52.4: the width rung may add capacity, not change the start point."""
    torch, narrow, wide, digest = _stage_l_and_widened(stage, 256)
    assert wide.hidden == 256 and wide.emb == narrow.emb
    assert digest != stage.L_WEIGHTS_HASH

    tokens = torch.as_tensor([[11, 12, 13, 14, 15], [21, 22, 23, 24, 25]], dtype=torch.long)
    narrow_state = narrow.init_state(2)
    wide_state = wide.init_state(2)
    narrow_logits, narrow_state = narrow.ai_step(tokens, narrow_state)
    wide_logits, wide_state = wide.ai_step(tokens, wide_state)
    assert torch.allclose(narrow_logits, wide_logits, atol=1e-6)

    narrow_state = narrow.al_step(180.0, narrow_state)
    wide_state = wide.al_step(180.0, wide_state)
    assert torch.allclose(narrow_state.tensors["h"], wide_state.tensors["h"][:, :128], atol=1e-6)
    follow = torch.as_tensor([[16], [26]], dtype=torch.long)
    narrow_logits, _ = narrow.ai_step(follow, narrow_state)
    wide_logits, _ = wide.ai_step(follow, wide_state)
    assert torch.allclose(narrow_logits, wide_logits, atol=1e-6)


def test_widening_keeps_l_block_and_zero_connects_the_new_units(stage):
    torch, narrow, wide, _ = _stage_l_and_widened(stage, 256)
    for gate in range(3):
        # L's rows are copied per gate; the new units' hidden rows never see L's
        assert torch.equal(
            wide.cell.weight_ih[gate * 256 : gate * 256 + 128],
            narrow.cell.weight_ih[gate * 128 : gate * 128 + 128],
        )
        assert torch.equal(
            wide.cell.weight_hh[gate * 256 : gate * 256 + 128, :128],
            narrow.cell.weight_hh[gate * 128 : gate * 128 + 128, :128],
        )
        assert torch.count_nonzero(wide.cell.weight_hh[gate * 256 : gate * 256 + 128, 128:]) == 0
        assert torch.equal(
            wide.cell.bias_ih[gate * 256 : gate * 256 + 128],
            narrow.cell.bias_ih[gate * 128 : gate * 128 + 128],
        )
        assert torch.equal(
            wide.cell.bias_hh[gate * 256 : gate * 256 + 128],
            narrow.cell.bias_hh[gate * 128 : gate * 128 + 128],
        )
    assert torch.equal(wide.head.weight[:, :128], narrow.head.weight)
    assert torch.count_nonzero(wide.head.weight[:, 128:]) == 0
    assert torch.equal(wide.embedding.weight, narrow.embedding.weight)
    assert torch.equal(wide.dt_proj.weight, narrow.dt_proj.weight)


def test_widened_start_is_accepted_only_when_it_names_stage_l(stage):
    ok = {
        "checkpoint": stage.L_CHECKPOINT,
        "checkpoint_sha256": stage.L_CHECKPOINT_SHA256,
        "weights_hash": stage.L_WEIGHTS_HASH,
        "params": stage.L_PARAMS,
    }
    assert stage.start_is_stage_l(ok)

    widened = {
        "checkpoint": stage.L_CHECKPOINT,
        "checkpoint_sha256": stage.L_CHECKPOINT_SHA256,
        "weights_hash": "sha256:" + "0" * 64,
        "params": stage.L_PARAMS + 1,
        "widened_from_hidden": 128,
        "source_weights_hash": stage.L_WEIGHTS_HASH,
        "hidden": 256,
    }
    assert stage.start_is_stage_l(widened)

    for broken in (
        {**widened, "source_weights_hash": "sha256:" + "f" * 64},
        {**widened, "widened_from_hidden": 64},
        {**widened, "hidden": 128},
        {**widened, "checkpoint_sha256": "0" * 64},
        {**widened, "params": stage.L_PARAMS},
        {**ok, "weights_hash": "sha256:" + "0" * 64},
        {**ok, "params": stage.L_PARAMS + 1},
        {**ok, "checkpoint": ""},
    ):
        assert not stage.start_is_stage_l(broken)

    # G1 is graded from this predicate: a widened start passes, a forged one does not
    report = _perfect_report(stage)
    report["start"] = widened
    assert stage.gate_values(report)["G1_start_is_stage_l"] is True
    report["start"] = {**widened, "source_weights_hash": "sha256:" + "f" * 64}
    assert stage.gate_values(report)["G1_start_is_stage_l"] is False


def test_cli_rejects_a_malformed_width_rung(stage):
    for argv in (
        ["--overfit", "1", "--widen-to", "128"],
        ["--overfit", "1", "--widen-to", "64"],
        ["--overfit", "1", "--widen-to", "256", "--hidden", "256"],
        ["--overfit", "1", "--widen-to", "256", "--emb", "32"],
    ):
        with pytest.raises(SystemExit):
            stage.main(argv)
