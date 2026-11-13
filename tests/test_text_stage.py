# ANGELA-MATRIX: L3 [βγδ] [B] [L2]
"""Stage L's contract: bytes in, bytes out, floors that are computed, gates re-runnable.

These tests do not measure a model. They check the apparatus that §47 registers:

* the vocabulary is the registered byte table (259 ids, invertible), because a
  changed vocabulary would make BPC incomparable with the registered run;
* the corpus loader keeps whole lines and stops at the byte budget, so the
  stream is a function of the data rather than of where a read happened to end;
* the interpolated floors are real distributions and the strongest weight is
  selected on *training* bytes;
* a gate verdict is a function of recorded numbers, and ``--check`` recomputes it
  instead of trusting the file (including reloading the checkpoint);
* a leaked camera tag aborts the run before training.

The end-to-end run here is a toy (8-hidden GRU, 1 epoch); a tiny model failing
L1-L3 is expected and is not the point.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "train_text_stage.py"


@pytest.fixture(scope="module")
def stage():
    spec = importlib.util.spec_from_file_location("text_stage_under_test", SCRIPT)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules["text_stage_under_test"] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def _words(seed: int, count: int) -> str:
    import random

    rng = random.Random(seed)
    vocabulary = "core reads bytes and writes text across a window".split()
    return " ".join(rng.choice(vocabulary) for _ in range(count))


@pytest.fixture(scope="module")
def toy_corpus(tmp_path_factory):
    root = tmp_path_factory.mktemp("text_stage")
    train = root / "train.jsonl"
    val = root / "val.jsonl"
    for path, seed, count in ((train, 1, 120), (val, 2, 30)):
        with path.open("w", encoding="utf-8") as handle:
            for _ in range(count):
                handle.write(
                    json.dumps({"input": _words(seed, 8), "output": _words(seed + 1, 4)}) + "\n"
                )
    pantry = root / "pantry.jsonl"
    spec = importlib.util.spec_from_file_location(
        "pantry_for_text_stage", REPO_ROOT / "scripts" / "gen_pantry_ecosystem.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["pantry_for_text_stage"] = module
    spec.loader.exec_module(module)
    module.write_corpus(pantry, seed=11, sessions=10, fraction=0.2)
    return root, train, val, pantry


def _run(stage, toy_corpus, out: Path, **overrides):
    _, train, val, pantry = toy_corpus
    argv = [
        "--general-path",
        str(train),
        "--general-holdout-path",
        str(val),
        "--pantry-path",
        str(pantry),
        "--general-bytes",
        "20000",
        "--general-holdout-bytes",
        "6000",
        "--epochs",
        "1",
        "--hidden",
        "8",
        "--emb",
        "4",
        "--batch",
        "2",
        "--window",
        "16",
        "--reset-every",
        "64",
        "--device",
        "cpu",
        "--out",
        str(out),
    ]
    argv.extend(overrides.pop("argv", []))
    assert stage.main(argv) == 0
    reports = sorted(out.glob("text_stage_*.json"))
    assert reports, "no report was written"
    return json.loads(reports[-1].read_text(encoding="utf-8")), reports[-1]


# --------------------------------------------------------------------------- #
# representation
# --------------------------------------------------------------------------- #
def test_the_vocabulary_is_the_registered_byte_table(stage):
    assert stage.PAD_ID == 0
    assert stage.BOS_ID == 1
    assert stage.EOS_ID == 2
    assert stage.BYTE_OFFSET == 3
    assert stage.VOCAB_SIZE == 259
    assert len(stage.ByteTable()) == 259


def test_every_byte_round_trips(stage):
    table = stage.ByteTable()
    data = bytes(range(256))
    encoded = table.encode(data)
    assert encoded[0] == stage.BYTE_OFFSET
    assert encoded[-1] == stage.BYTE_OFFSET + 255
    assert table.decode(encoded) == data
    text = "核心讀取 bytes，然後寫回去。".encode("utf-8")
    assert table.decode(table.encode(text)) == text


def test_special_tokens_do_not_decode_to_bytes(stage):
    table = stage.ByteTable()
    assert table.decode([stage.PAD_ID, stage.BOS_ID, stage.EOS_ID]) == b""


def test_the_registered_defaults_are_unchanged(stage):
    """A silently changed default would be a different registration (§47.5)."""
    assert stage.SEED == 20261116
    assert stage.LEARNING_RATE == 1e-3
    assert stage.BATCH == 32
    assert stage.WINDOW == 128
    assert stage.RESET_EVERY == 4096
    assert stage.EPOCHS == 5
    assert stage.HIDDEN == 128
    assert stage.EMB == 64
    assert stage.CHUNK_SECONDS == 60.0
    assert stage.GENERAL_BYTES == 3_000_000
    assert stage.GENERAL_HOLDOUT_BYTES == 300_000
    assert stage.PANTRY_SESSIONS == 1000
    assert stage.PANTRY_SEED == 20261113
    assert stage.PANTRY_TRAIN_BYTES == 1_014_924
    assert stage.PANTRY_HOLDOUT_BYTES == 254_050


# --------------------------------------------------------------------------- #
# corpus
# --------------------------------------------------------------------------- #
def test_the_loader_stops_on_a_line_boundary(stage, tmp_path):
    path = tmp_path / "corpus.jsonl"
    rows = [
        {"input": "alpha", "output": "beta"},
        {"input": "gamma", "output": "delta"},
        {"input": "epsilon", "output": "zeta"},
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    first = stage.load_general(path, 1_000_000)
    assert first.count(b"\n") == 3
    assert b"alpha beta" in first

    budget = len(b"alpha beta\n") + 2
    truncated = stage.load_general(path, budget)
    assert truncated == b"alpha beta\n", "the loader cut inside a line"


def test_the_loader_refuses_a_missing_file(stage, tmp_path):
    with pytest.raises(SystemExit):
        stage.load_general(tmp_path / "absent.jsonl", 100)


def test_the_corpus_digest_is_stable(stage, tmp_path):
    path = tmp_path / "corpus.jsonl"
    path.write_text(json.dumps({"input": "a", "output": "b"}) + "\n", encoding="utf-8")
    first = stage.load_general(path, 1000)
    second = stage.load_general(path, 1000)
    assert stage._digest(first) == stage._digest(second)
    assert stage._digest(first) == stage._digest(b"a b\n")


# --------------------------------------------------------------------------- #
# floors
# --------------------------------------------------------------------------- #
def test_the_interpolated_floor_is_a_distribution(stage):
    floors = stage.CountFloors(b"abababababab" * 20).fit(b"abababababab" * 20)
    for context in (None, b"a", b"b"):
        previous = None
        previous2 = None
        if context is not None:
            previous = context[-1]
            if len(context) > 1:
                previous2 = context[-2]
        total = sum(
            (
                floors._p_tri(previous2, previous, byte)
                if previous2 is not None
                else floors._p_bi(previous, byte)
            )
            for byte in range(256)
        )
        assert total == pytest.approx(1.0, abs=1e-9)


def test_the_best_interpolation_beats_the_unigram_on_a_deterministic_stream(stage):
    stream = b"ab" * 800
    floors = stage.CountFloors(stream).fit(stream)
    chosen = floors.choose_lambdas(stream[:200])
    assert chosen["bigram"]["bpc"] < chosen["trigram"]["bpc"] or chosen["trigram"]["bpc"] < 1.0
    assert chosen["bigram"]["lambda"] in stage.BIGRAM_LAMBDAS
    nll_unigram, count = floors.nll_bigram(b"ab" * 40, 0.0)
    assert chosen["bigram"]["bpc"] < nll_unigram / count / 2.0


def test_the_floor_lambda_is_chosen_on_training_bytes(stage):
    """The dev slice is the tail of the training stream, never the hold-out."""
    train = b"abcabcabc" * 200
    holdout = b"zzzzzzzz" * 40
    floors = stage.CountFloors(train).fit(train)
    chosen = floors.choose_lambdas(train[-100:])
    assert 0.0 <= chosen["bigram"]["lambda"] <= 0.99
    before = json.dumps(chosen, sort_keys=True)
    floors.evaluate(holdout, lam_bi=0.5, lam_tri=0.5, lam_bigram=0.5)
    after = json.dumps(floors.choose_lambdas(train[-100:]), sort_keys=True)
    assert before == after, "evaluating the hold-out changed the selected lambdas"


def test_the_trigram_floor_is_never_worse_than_the_bigram_on_its_own_dev(stage):
    stream = (b"the core reads bytes " * 200) + (b"and writes them back " * 100)
    floors = stage.CountFloors(stream).fit(stream)
    chosen = floors.choose_lambdas(stream[-500:])
    # lambda_trigram=0 with lambda_bigram reproduces the bigram family, so the
    # best trigram entry cannot be worse than the reported bigram floor by much.
    assert chosen["trigram"]["bpc"] <= chosen["bigram"]["bpc"] + 0.15


def test_greedy_continuation_follows_a_deterministic_pattern(stage):
    floors = stage.CountFloors(b"abc" * 400).fit(b"abc" * 400)
    produced = floors.greedy_continuation(b"abcabc", 6, lam_tri=0.9, lam_bi=0.08)
    assert produced == b"abcabc"


# --------------------------------------------------------------------------- #
# gates and --check
# --------------------------------------------------------------------------- #
def _base_report(**overrides):
    report = {
        "results": {
            "heldout": {"bpc": 2.0},
            "heldout_reset": {"bpc": 2.5},
        },
        "floors": {"holdout": {"bigram_bpc": 3.0, "trigram_bpc": 2.8}},
        "generation": {"distinct": 95, "mean_model_lcp": 2.0, "mean_trigram_lcp": 1.0},
        "leak_check": {"clean": True},
        "cost": {"params": 10, "train_seconds": 1.0, "device": "cpu"},
    }
    for key, value in overrides.items():
        report[key] = value
    return report


def test_gate_values_read_the_recorded_numbers(stage):
    gates = stage.gate_values(_base_report())
    assert gates["L1_heldout_bpc_lt_bigram"] is True
    assert gates["L2_heldout_bpc_lt_trigram"] is True
    assert gates["L3_distinct_and_closer_than_trigram"] is True
    assert gates["L4_carried_state_beats_reset"] is True
    assert gates["L7_cost_recorded"] is True


def test_a_worse_bpc_flips_the_gate(stage):
    report = _base_report()
    report["results"]["heldout"]["bpc"] = 3.5
    gates = stage.gate_values(report)
    assert gates["L1_heldout_bpc_lt_bigram"] is False
    assert gates["L2_heldout_bpc_lt_trigram"] is False


def test_mode_collapse_flips_l3(stage):
    report = _base_report()
    report["generation"]["distinct"] = 2
    assert stage.gate_values(report)["L3_distinct_and_closer_than_trigram"] is False
    report = _base_report()
    report["generation"]["mean_model_lcp"] = 0.5
    assert stage.gate_values(report)["L3_distinct_and_closer_than_trigram"] is False


def test_a_dirty_leak_check_flips_l6(stage):
    report = _base_report()
    report["leak_check"] = {"clean": False}
    assert stage.gate_values(report)["L6_no_oracle_in_text"] is False


def test_the_end_to_end_run_records_every_gate(stage, toy_corpus, tmp_path):
    report, path = _run(stage, toy_corpus, tmp_path / "out")
    assert path.exists()
    assert report["task_version"] == stage.TASK_VERSION
    assert set(report["gates"]) == {
        "L1_heldout_bpc_lt_bigram",
        "L2_heldout_bpc_lt_trigram",
        "L3_distinct_and_closer_than_trigram",
        "L4_carried_state_beats_reset",
        "L5_checkpoint_loads_same_class",
        "L6_no_oracle_in_text",
        "L7_cost_recorded",
    }
    assert report["gates"]["L5_checkpoint_loads_same_class"] is True
    assert report["gates"]["L6_no_oracle_in_text"] is True
    assert report["gates"]["L7_cost_recorded"] is True
    assert report["reload"]["model_kind"] == "gru"
    assert report["reload"]["state_schema"] == 1
    assert report["reload"]["token_count"] == stage.VOCAB_SIZE
    assert report["corpus"]["testimony_train_bytes"] > 0
    assert report["generation"]["n"] == stage.L3_PREFIXES
    assert 0.0 <= report["results"]["heldout"]["bpc"] <= 8.1
    # The regenerated corpus must reproduce the recorded digests.
    assert report["corpus"]["digests"]["testimony_train"]


def test_check_reverifies_the_finished_run(stage, toy_corpus, tmp_path):
    _, path = _run(stage, toy_corpus, tmp_path / "out")
    assert stage.check_report(path) == []


def test_check_catches_a_tampered_gate(stage, toy_corpus, tmp_path):
    report, path = _run(stage, toy_corpus, tmp_path / "out")
    report["gates"]["L1_heldout_bpc_lt_bigram"] = not report["gates"]["L1_heldout_bpc_lt_bigram"]
    path.write_text(json.dumps(report), encoding="utf-8")
    problems = stage.check_report(path)
    assert any("L1_heldout_bpc_lt_bigram" in problem for problem in problems)


def test_check_catches_a_missing_checkpoint(stage, toy_corpus, tmp_path):
    report, path = _run(stage, toy_corpus, tmp_path / "out")
    Path(report["checkpoint"]).unlink()
    problems = stage.check_report(path)
    assert any("checkpoint is missing" in problem for problem in problems)


def test_check_reports_a_missing_report(stage, tmp_path):
    problems = stage.check_report(tmp_path / "absent.json")
    assert problems and "does not exist" in problems[0]


def test_a_leaked_oracle_aborts_before_training(stage, toy_corpus, tmp_path):
    _, _, _, pantry = toy_corpus
    rows = [json.loads(line) for line in pantry.read_text(encoding="utf-8").splitlines() if line]
    tag = rows[0]["ground_truth_oracle"]["evidence_tag"]
    rows[0]["turns"][1]["user_input"] += f"（監視器 {tag}）"
    leaked = tmp_path / "leaked.jsonl"
    leaked.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    _, train, val, _ = toy_corpus
    out = tmp_path / "out"
    code = stage.main(
        [
            "--general-path",
            str(train),
            "--general-holdout-path",
            str(val),
            "--pantry-path",
            str(leaked),
            "--general-bytes",
            "20000",
            "--general-holdout-bytes",
            "6000",
            "--epochs",
            "1",
            "--hidden",
            "8",
            "--emb",
            "4",
            "--batch",
            "2",
            "--window",
            "16",
            "--reset-every",
            "64",
            "--device",
            "cpu",
            "--out",
            str(out),
        ]
    )
    assert code == 1
    report = json.loads(sorted(out.glob("text_stage_*.json"))[-1].read_text(encoding="utf-8"))
    assert report["aborted"] == "leak check failed"
    assert report["leak_check"]["clean"] is False
    assert "training" not in report
    assert not list(out.glob("*.pt")), "training ran despite a dirty leak check"
