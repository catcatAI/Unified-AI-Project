# ANGELA-MATRIX: L3 [βγδ] [B] [L2]
"""The pantry corpus's contract, checked without training anything.

The dataset's whole claim is that a model cannot pass it by matching a surface
form: the answer is a *combination* of testimony that no single turn states.
These tests are therefore about the corpus, not about a model:

* the oracle is absent from every ``user_input`` (a leak would turn reasoning
  into copying);
* the stated timeline is internally consistent, so "this time is impossible"
  is a fact about the data rather than a sentence in it;
* the ``dt_s`` gaps really cover short, mid and long absences, because a corpus
  of tiny gaps would make ``al_step`` untested;
* the environment is re-sampled per session (no fixed cast to memorise) and the
  testimony order is permuted;
* train and held-out are disjoint by session, by answer tuple and by verbatim
  text - names recur by design and that is asserted rather than glossed over;
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
    return module.PantryEcosystemSynthesizer(seed=4242, sessions=20).generate()


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
        assert set(oracle) == {"target_item", "culprit", "action_time", "evidence_tag"}
        assert oracle["culprit"] in session["environment"]["actors"]
        assert oracle["target_item"] in session["environment"]["items"]


def test_turns_are_contiguous_and_the_first_gap_is_zero(corpus):
    for session in _all(corpus):
        turns = session["turns"]
        assert [turn["turn_id"] for turn in turns] == list(range(len(turns)))
        assert turns[0]["dt_s"] == 0.0
        assert all(turn["dt_s"] >= 0.0 for turn in turns)
        assert len(turns) == 5  # opener, three testimony turns, final question


def test_only_the_final_turn_carries_the_deduction(corpus):
    for session in _all(corpus):
        turns = session["turns"]
        assert turns[-1]["expected_final_deduction"] == session["ground_truth_oracle"]["culprit"]
        for turn in turns[:-1]:
            assert "expected_final_deduction" not in turn
            assert turn["expected_internal_focus"]


# --------------------------------------------------------------------------- #
# the oracle must not be in the text
# --------------------------------------------------------------------------- #
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
        hour, minute = oracle["action_time"].split(":")
        assert oracle["evidence_tag"].endswith(f"{int(hour)}{minute}")


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


def test_a_leaked_oracle_is_caught(module, corpus):
    session = copy.deepcopy(_all(corpus)[0])
    tag = session["ground_truth_oracle"]["evidence_tag"]
    session["turns"][1]["user_input"] += f"（監視器 {tag}）"
    problems = module._validate_session(session, "train")
    assert any("camera tag" in problem for problem in problems)


def test_a_wrong_final_deduction_is_caught(module, corpus):
    session = copy.deepcopy(_all(corpus)[0])
    session["turns"][-1]["expected_final_deduction"] = "Nobody"
    problems = module._validate_session(session, "train")
    assert any("final deduction" in problem for problem in problems)


# --------------------------------------------------------------------------- #
# time, vocabulary, order: the three ways this corpus could be trivial
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
    """A fixed seven-name cast would let a model learn roles, not testimony."""
    seen = set()
    for session in _all(corpus):
        actors = tuple(sorted(session["environment"]["actors"]))
        assert 5 <= len(actors) <= 8
        seen.add(actors)
    assert len(seen) == len(_all(corpus)), "two sessions share the same cast"
    example = ("Alex", "Betty", "Chris", "David", "Elena", "Frank", "Grace")
    assert example not in seen


def test_every_actor_is_sometimes_the_culprit_and_sometimes_not(module, corpus):
    """Names recur across splits (recorded deviation), so a name cannot be the answer."""
    innocent = set()
    guilty = set()
    for session in _all(corpus):
        oracle = session["ground_truth_oracle"]
        guilty.add(oracle["culprit"])
        innocent.update(set(session["environment"]["actors"]) - {oracle["culprit"]})
    assert guilty <= innocent, "a name is only ever the culprit"


def test_step_updates_are_not_monotonic(module, corpus):
    """The last statement contradicts the manager's alibi; that is the point."""
    for session in _all(corpus):
        culprit = session["ground_truth_oracle"]["culprit"]
        conflict = [t for t in session["turns"] if "清潔阿姨" in t["user_input"]]
        assert conflict, "no turn overturns the alibi"
        assert any(culprit in turn["user_input"] for turn in conflict)


def test_the_testimony_order_is_permuted(module, corpus):
    orders = {tuple(session["session_meta"]["testimony_order"]) for session in _all(corpus)}
    assert len(orders) >= 3, orders
    for session in _all(corpus):
        assert sorted(session["session_meta"]["testimony_order"]) == [
            "conflict",
            "confusion",
            "herring",
        ]


def test_the_capacity_bound_holds(module, corpus):
    for session in _all(corpus):
        actors = len(session["environment"]["actors"])
        items = len(session["environment"]["items"])
        clues = 3  # red herring, impossible time, contradicting sighting
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


def test_splits_are_disjoint_by_session_answer_and_text(module, corpus):
    assert module._validate_split(corpus["train"], corpus["heldout"]) == []


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
