# ANGELA-MATRIX: L3 [βγδ] [B] [L2]
"""The pantry corpus's contract, checked without training anything.

The dataset's whole claim is that a model cannot pass it by matching a surface
form: the answer is a *combination* of testimony that no single turn states, and
one of the statements that points at a person has to be **retracted** before the
right person falls out. These tests are about the corpus, not about a model:

* no evidence turn names anyone, and every turn that names people names all of
  them - so "read the name out of the turn with 主管" is chance by construction;
* the stated timeline is internally consistent, so "this time is impossible" is
  a fact about the data rather than a sentence in it;
* the solver really needs every load-bearing turn (drop one and the answer is
  no longer uniquely the culprit);
* ignoring the retraction really gives a different answer, which is what makes
  "accumulate everything" a losing strategy;
* the ``dt_s`` gaps cover short, mid and long absences;
* the environment is re-sampled per session, and no name is only ever the
  culprit;
* train and held-out are disjoint by session and by *answer tuple*. Verbatim
  text is **not** disjoint - that is the recorded deviation the two-stage plan
  depends on, so it is asserted rather than glossed over;
* regenerating from the recorded seed reproduces the file byte for byte, so a
  later result can be traced to a corpus rather than to "some jsonl".

No training happens here.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "gen_pantry_ecosystem.py"


@pytest.fixture(scope="module")
def module():
    spec = importlib.util.spec_from_file_location("pantry_under_test", SCRIPT)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules["pantry_under_test"] = loaded
    spec.loader.exec_module(loaded)
    return loaded


@pytest.fixture(scope="module")
def corpus(module):
    # 200 sessions is the smallest size at which every shortcut baseline has
    # the statistical power the gate requires (POWER_MIN answered sessions).
    return module.PantryEcosystemSynthesizer(seed=4242, sessions=200).generate()


def _all(corpus):
    return corpus["train"] + corpus["heldout"]


# --------------------------------------------------------------------------- #
# shape
# --------------------------------------------------------------------------- #
def test_every_session_has_the_spec_shape(module, corpus):
    for session in _all(corpus):
        assert set(session) >= {
            "session_id",
            "schema_version",
            "session_meta",
            "environment",
            "ground_truth_oracle",
            "turns",
        }
        assert session["schema_version"] == module.SCHEMA_VERSION
        oracle = session["ground_truth_oracle"]
        assert set(oracle) == {
            "chain",
            "target_item",
            "culprit",
            "action_time",
            "window",
            "window_bounds",
            "evidence_tag",
        }
        assert oracle["chain"] in module.CHAINS
        assert oracle["culprit"] in session["environment"]["actors"]
        assert oracle["target_item"] in session["environment"]["items"]


def test_every_chain_type_is_generated(module, corpus):
    chains = {session["session_meta"]["chain"] for session in _all(corpus)}
    assert chains == set(module.CHAINS)


def test_turns_are_contiguous_and_the_first_gap_is_zero(corpus):
    for session in _all(corpus):
        turns = session["turns"]
        assert [turn["turn_id"] for turn in turns] == list(range(len(turns)))
        assert turns[0]["dt_s"] == 0.0
        assert all(turn["dt_s"] >= 0.0 for turn in turns)
        assert len(turns) == 11


def test_only_the_final_turn_carries_the_deduction(corpus):
    for session in _all(corpus):
        turns = session["turns"]
        assert turns[-1]["expected_final_deduction"] == session["ground_truth_oracle"]["culprit"]
        for turn in turns[:-1]:
            assert "expected_final_deduction" not in turn
            assert turn["expected_internal_focus"]


def test_each_assert_is_owned_by_the_turn_that_carries_it(corpus):
    for session in _all(corpus):
        for turn in session["turns"]:
            for item in turn["asserts"]:
                assert item["turn"] == turn["turn_id"]


# --------------------------------------------------------------------------- #
# no turn gives the answer
# --------------------------------------------------------------------------- #
def test_no_turn_names_exactly_one_actor(module, corpus):
    """The structural claim: a naming turn names *everybody*."""
    for session in _all(corpus):
        actors = session["environment"]["actors"]
        for turn in session["turns"]:
            named = [name for name in actors if name in turn["user_input"]]
            assert len(named) in (
                0,
                len(actors),
            ), f"{session['session_id']} turn {turn['turn_id']} names {named}"


def test_a_turn_that_names_one_actor_is_caught(module, corpus):
    session = copy.deepcopy(_all(corpus)[0])
    session["turns"][0]["user_input"] += f" {session['environment']['actors'][0]} 說他不知道。"
    problems = module._validate_name_balance(session)
    assert any("names 1 of" in problem for problem in problems)


def test_the_culprit_is_not_first_in_the_roll_call(module, corpus):
    """If the roll-call order leaked, ``first_named`` would beat chance."""
    first = 0
    total = 0
    for session in _all(corpus):
        text = session["turns"][1]["user_input"]
        named = [name for name in text.split("：")[-1].split("，")[0].split("、")]
        if not named:
            continue
        total += 1
        first += int(named[0] == session["ground_truth_oracle"]["culprit"])
    assert total == len(_all(corpus))
    assert first / total < 0.4, first / total


def test_shortcut_baselines_are_at_chance(module, corpus):
    report = module.shortcut_audit(_all(corpus))
    powered = [row for row in report.values() if row["answered"] >= module.POWER_MIN]
    assert powered, "no baseline had enough answers to be a gate"
    for name, row in report.items():
        if row["answered"] < module.POWER_MIN:
            assert row["powered"] is False, name
            continue
        assert row["powered"] is True
        assert row["upper95"] <= row["chance"] + module.CHANCE_MARGIN, (name, row)


def test_the_audit_detects_a_planted_leak(module, corpus):
    session = copy.deepcopy(_all(corpus)[0])
    culprit = session["ground_truth_oracle"]["culprit"]
    session["turns"][1]["user_input"] = f"主管說這件事是 {culprit} 做的。"
    report = module.shortcut_audit([session])
    assert report["turn_with:主管"]["accuracy"] == 1.0
    assert report["first_named"]["accuracy"] == 1.0


def test_the_camera_tag_never_appears_in_the_testimony(module, corpus):
    for session in _all(corpus):
        tag = session["ground_truth_oracle"]["evidence_tag"]
        for turn in session["turns"]:
            assert tag not in turn["user_input"]
            assert "surveillance" not in turn["user_input"].lower()


def test_no_turn_states_the_verdict(module, corpus):
    for session in _all(corpus):
        for turn in session["turns"]:
            lowered = turn["user_input"].lower()
            for marker in module.VERDICT_MARKERS:
                assert marker.lower() not in lowered


def test_the_tag_is_consistent_with_the_action_time(corpus):
    for session in _all(corpus):
        oracle = session["ground_truth_oracle"]
        assert oracle["evidence_tag"].endswith(f"t={oracle['action_time']}")


# --------------------------------------------------------------------------- #
# the solver: evidence, filter, roster, retraction
# --------------------------------------------------------------------------- #
def test_derive_needs_the_roster(module):
    actors = ["A", "B", "C"]
    asserts = [
        (0, {"kind": "seen", "value": "red", "t": "10:10"}),
    ]
    assert module.derive(asserts, actors) == ["A", "B", "C"]
    asserts.append((1, {"kind": "roster", "value": {"red": "B"}}))
    assert module.derive(asserts, actors) == ["B"]


def test_derive_needs_both_item_and_time(module):
    """A checkout row counts only when the item *and* the window both match."""
    actors = ["A", "B", "C"]
    asserts = [
        (0, {"kind": "window", "lo": "10:00", "hi": "10:20"}),
        (1, {"kind": "checkout", "id": "X", "item": "pizza", "target": "pizza", "t": "10:10"}),
        (1, {"kind": "checkout", "id": "Y", "item": "pizza", "target": "pizza", "t": "09:00"}),
        (1, {"kind": "checkout", "id": "Z", "item": "mochi", "target": "pizza", "t": "10:10"}),
        (2, {"kind": "roster", "value": {"X": "A", "Y": "B", "Z": "C"}}),
    ]
    assert module.derive(asserts, actors) == ["A"]


def test_derive_uses_overlap_for_access_intervals(module):
    """An interval that merely overlaps the window still counts - that is why
    widening the window must admit another person."""
    actors = ["A", "B", "C"]
    asserts = [
        (0, {"kind": "window", "lo": "10:00", "hi": "10:20"}),
        (1, {"kind": "access", "id": "X", "lo": "09:00", "hi": "09:30"}),
        (1, {"kind": "access", "id": "Y", "lo": "10:10", "hi": "10:40"}),
        (1, {"kind": "access", "id": "Z", "lo": "10:00", "hi": "10:20"}),
        (2, {"kind": "roster", "value": {"X": "A", "Y": "B", "Z": "C"}}),
    ]
    assert module.derive(asserts, actors) == ["B", "C"]


def test_derive_honours_the_retraction(module):
    actors = ["A", "B", "C"]
    asserts = [
        (0, {"kind": "window", "lo": "10:00", "hi": "10:20"}),
        (1, {"kind": "seen", "value": "red", "t": "10:10"}),
        (2, {"kind": "seen", "value": "blue", "t": "10:10"}),
        (2, {"kind": "retract", "target": 1}),
        (3, {"kind": "roster", "value": {"red": "A", "blue": "B"}}),
    ]
    assert module.derive(asserts, actors) == ["B"]
    # A reader who never drops anything sees two suspects, not one.
    assert module.derive(asserts, actors, honour_retract=False) == ["A", "B"]


def test_every_session_derives_exactly_the_culprit(module, corpus):
    for session in _all(corpus):
        derived = module.derive(module._all_asserts(session), session["environment"]["actors"])
        assert derived == [session["ground_truth_oracle"]["culprit"]], session["session_id"]


def test_every_session_needs_its_load_bearing_turns(module, corpus):
    for session in _all(corpus):
        assert module._validate_necessity(session) == [], session["session_id"]
        assert module._validate_retraction(session) == [], session["session_id"]


def test_a_decoration_turn_is_caught(module, corpus):
    session = copy.deepcopy(_all(corpus)[0])
    session["session_meta"]["chain_turns"].append(len(session["turns"]) - 1)
    problems = module._validate_necessity(session)
    assert any("can be dropped" in problem for problem in problems)


def test_a_session_without_a_retraction_is_caught(module, corpus):
    session = copy.deepcopy(_all(corpus)[0])
    for turn in session["turns"]:
        turn["asserts"] = [item for item in turn["asserts"] if item["kind"] != "retract"]
    problems = module._validate_retraction(session)
    assert any("no retraction" in problem for problem in problems)


def test_a_retraction_that_retracts_nothing_is_caught(module, corpus):
    """If the wrong value is never asserted, ignoring the retraction is enough."""
    session = copy.deepcopy(_all(corpus)[0])
    session["turns"][session["session_meta"]["evidence_turn"]]["asserts"] = []
    problems = module._validate_retraction(session)
    assert any("ignoring the retraction" in problem for problem in problems)


def test_the_correction_retracts_the_turn_before_it(module, corpus):
    for session in _all(corpus):
        correction = session["session_meta"]["correction_turn"]
        assert correction > session["session_meta"]["evidence_turn"]
        targets = [
            item["target"]
            for item in session["turns"][correction]["asserts"]
            if item["kind"] == "retract"
        ]
        assert targets == [session["session_meta"]["evidence_turn"]]


# --------------------------------------------------------------------------- #
# the timeline described in prose is actually consistent
# --------------------------------------------------------------------------- #
def test_the_stated_timeline_is_ordered(module, corpus):
    for session in _all(corpus):
        assert (
            module._validate_timeline(
                session["session_meta"], session["ground_truth_oracle"], "train", "x"
            )
            == []
        )
        timeline = session["session_meta"]["timeline"]
        assert timeline["action"] == session["ground_truth_oracle"]["action_time"]


def test_a_broken_timeline_is_caught(module, corpus):
    session = copy.deepcopy(_all(corpus)[0])
    timeline = session["session_meta"]["timeline"]
    timeline["impossible_claim"] = timeline["action"]  # "impossible" is the theft itself
    problems = module._validate_timeline(
        session["session_meta"], session["ground_truth_oracle"], "train", "x"
    )
    assert any("impossible" in problem for problem in problems)


def test_a_bound_inside_the_window_is_caught(module, corpus):
    session = copy.deepcopy(_all(corpus)[0])
    timeline = session["session_meta"]["timeline"]
    session["ground_truth_oracle"][
        "window_bounds"
    ] = f"{timeline['window_lo']}-{timeline['window_hi']}"
    problems = module._validate_timeline(
        session["session_meta"], session["ground_truth_oracle"], "train", "x"
    )
    assert any("bound" in problem for problem in problems)


def test_a_leaked_oracle_is_caught(module, corpus):
    session = copy.deepcopy(_all(corpus)[0])
    tag = session["ground_truth_oracle"]["evidence_tag"]
    session["turns"][1]["user_input"] += f"（監視器 {tag}）"
    problems = module._validate_session(session, "train")
    assert any("leaks the oracle tag" in problem for problem in problems)


def test_a_wrong_final_deduction_is_caught(module, corpus):
    session = copy.deepcopy(_all(corpus)[0])
    session["turns"][-1]["expected_final_deduction"] = "Nobody"
    problems = module._validate_session(session, "train")
    assert any("final deduction" in problem for problem in problems)


def test_a_retraction_of_a_later_turn_is_caught(module, corpus):
    session = copy.deepcopy(_all(corpus)[0])
    correction = session["session_meta"]["correction_turn"]
    for item in session["turns"][correction]["asserts"]:
        if item["kind"] == "retract":
            item["target"] = correction + 1
    problems = module._validate_session(session, "train")
    assert any("not earlier" in problem for problem in problems)


# --------------------------------------------------------------------------- #
# time, vocabulary, order: the ways this corpus could still be trivial
# --------------------------------------------------------------------------- #
def test_all_three_gap_bands_occur(module, corpus):
    bands = {"short": 0, "mid": 0, "long": 0}
    for session in _all(corpus):
        for turn in session["turns"]:
            bands[module._band_for(turn["dt_s"])] += 1
    assert all(count > 0 for count in bands.values()), bands
    assert bands["long"] >= 1


def test_gaps_are_log_uniform_inside_each_band(module):
    import random

    rng = random.Random(7)
    drawn = [module._sample_dt(rng) for _ in range(400)]
    assert min(drawn) >= module.DT_BANDS[0][1]
    assert max(drawn) <= module.DT_BANDS[-1][2]
    assert sum(1 for value in drawn if value < 300) > 50


def test_the_cast_is_resampled_per_session(module, corpus):
    """A fixed cast would let a model learn roles, not testimony.

    Duplicates are expected (12 actors choose 5-8); the claim is that the cast
    is drawn per session rather than fixed, so nearly every session differs.
    """
    seen = []
    for session in _all(corpus):
        actors = tuple(sorted(session["environment"]["actors"]))
        assert 5 <= len(actors) <= 8
        seen.append(actors)
    assert len(set(seen)) >= 0.75 * len(seen), "the cast is nearly fixed"
    assert len(set(seen)) > 50


def test_every_actor_is_sometimes_the_culprit_and_sometimes_not(module, corpus):
    """Names recur across splits (recorded deviation), so a name cannot be the answer."""
    innocent = set()
    guilty = set()
    for session in _all(corpus):
        oracle = session["ground_truth_oracle"]
        guilty.add(oracle["culprit"])
        innocent.update(set(session["environment"]["actors"]) - {oracle["culprit"]})
    assert guilty <= innocent, "a name is only ever the culprit"


def test_the_capacity_bound_holds(module, corpus):
    for session in _all(corpus):
        actors = len(session["environment"]["actors"])
        items = len(session["environment"]["items"])
        clues = 3  # window bounds are two slots' worth of state, plus the trap
        assert actors + items + clues <= module.MAX_SLOTS
        assert session["session_meta"]["slots"] == actors + items + clues


# --------------------------------------------------------------------------- #
# splits
# --------------------------------------------------------------------------- #
def test_both_splits_exist_and_are_interleaved(module):
    synth = module.PantryEcosystemSynthesizer(seed=1, sessions=20)
    flags = [synth.is_heldout(index) for index in range(20)]
    assert flags.count(True) == 4
    assert flags == [synth.is_heldout(index) for index in range(20)]


def test_splits_are_disjoint_by_session_and_answer(module, corpus):
    assert module._validate_split(corpus["train"], corpus["heldout"]) == []


def test_text_may_repeat_across_splits(module, corpus):
    """The recorded deviation: the language stage shares text, the reasoning
    stage is gated on answer tuples. If text were disjoint the template family
    would collapse to a handful of sentences."""
    train_lines = {turn["user_input"] for session in corpus["train"] for turn in session["turns"]}
    heldout_lines = {
        turn["user_input"] for session in corpus["heldout"] for turn in session["turns"]
    }
    assert train_lines & heldout_lines


def test_a_shared_answer_tuple_is_caught(module, corpus):
    train = corpus["train"]
    heldout = copy.deepcopy(corpus["heldout"])
    heldout[0]["ground_truth_oracle"] = dict(train[0]["ground_truth_oracle"])
    problems = module._validate_split(train, heldout)
    assert any("answer tuples" in problem for problem in problems)


def test_a_session_in_both_splits_is_caught(module, corpus):
    train = corpus["train"]
    heldout = copy.deepcopy(corpus["heldout"])
    heldout[0]["session_id"] = train[0]["session_id"]
    problems = module._validate_split(train, heldout)
    assert any("session ids" in problem for problem in problems)


def test_validate_reports_a_mislabelled_split(module, corpus):
    session = copy.deepcopy(corpus["train"][0])
    session["session_meta"]["split"] = "heldout"
    problems = module._validate_session(session, "train")
    assert any("meta.split" in problem for problem in problems)


# --------------------------------------------------------------------------- #
# determinism and the file-level gates
# --------------------------------------------------------------------------- #
def test_the_same_seed_reproduces_the_corpus(module):
    first = module.PantryEcosystemSynthesizer(seed=99, sessions=10).generate()
    second = module.PantryEcosystemSynthesizer(seed=99, sessions=10).generate()
    assert module._payload(first) == module._payload(second)
    other = module.PantryEcosystemSynthesizer(seed=100, sessions=10).generate()
    assert module._payload(first) != module._payload(other)


def test_a_session_does_not_depend_on_how_many_follow_it(module):
    """Session i must be stable, or a small debug corpus is not the real thing."""
    small = module.PantryEcosystemSynthesizer(seed=5, sessions=6).generate()
    large = module.PantryEcosystemSynthesizer(seed=5, sessions=30).generate()
    small_by_id = {session["session_id"]: session for session in _all(small)}
    large_by_id = {session["session_id"]: session for session in _all(large)}
    shared = set(small_by_id).intersection(large_by_id)
    assert shared
    for session_id in shared:
        assert small_by_id[session_id] == large_by_id[session_id]


def test_written_corpus_passes_its_own_check(module, tmp_path):
    path = tmp_path / "sessions.jsonl"
    module.write_corpus(path, seed=2026, sessions=15, fraction=0.2)
    assert module.check_corpus(path) == []
    manifest = json.loads(path.with_suffix(".manifest.json").read_text(encoding="utf-8"))
    assert manifest["counts"]["train"] + manifest["counts"]["heldout"] == 15
    assert set(manifest["dt_bands"]) == {"short", "mid", "long"}
    assert set(manifest["chains"]) == set(module.CHAINS)
    assert manifest["shortcuts"], "the manifest must record the audit"


def test_an_edited_corpus_fails_the_check(module, tmp_path):
    path = tmp_path / "sessions.jsonl"
    module.write_corpus(path, seed=7, sessions=10, fraction=0.2)
    text = path.read_text(encoding="utf-8").replace("Alex", "Alexandra", 1)
    path.write_text(text, encoding="utf-8")
    problems = module.check_corpus(path)
    assert any("manifest digest" in problem for problem in problems)


def test_a_changed_generator_fails_the_check(module, tmp_path):
    path = tmp_path / "sessions.jsonl"
    module.write_corpus(path, seed=7, sessions=10, fraction=0.2)
    manifest_path = path.with_suffix(".manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["generator_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    problems = module.check_corpus(path)
    assert any("generator changed" in problem for problem in problems)


def test_check_reports_a_missing_file(module, tmp_path):
    problems = module.check_corpus(tmp_path / "absent.jsonl")
    assert problems and "does not exist" in problems[0]


def test_the_cli_writes_then_verifies(module, tmp_path, capsys):
    path = tmp_path / "cli.jsonl"
    assert module.main(["--sessions", "12", "--seed", "3", "--out", str(path)]) == 0
    assert module.main(["--check", "--out", str(path)]) == 0
    assert "OK" in capsys.readouterr().out
