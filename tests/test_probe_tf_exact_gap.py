# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§88's contract is the partition, not the numbers.

The registered rule (``docs/06-project-management/CORE_GAP_ANALYSIS.md`` §88.5,
amended by §88.10) says the failures of a free-running decode split into
"a top-k search could still find the gold answer" and "gold is outside the top
k everywhere". Amendment #2 proved that ``O <=> G`` for a causal argmax decoder,
so the algebra is ``S(k) = T_k - G`` and ``M(k) = N - T_k``; ``D`` and ``X``
must be zero on real rows and are kept only as consistency checks.

What is tested here:

* the majority rule, including the 0.5/0.5 tie (``mixed``) and the empty
  failure set (``no-gap``);
* the closed form and its k-sensitivity (a bigger k can flip distribution to
  decoding, which is why k=5 is fixed in advance);
* Wilson intervals at a 0/248 and a 248/248 edge;
* the endpoints on a tiny model: f=0 is greedy (``G``) and f=1.0 is the EOS
  prediction under the full gold prefix (``eos_argmax``), by two independent
  paths;
* the monotonicity of ``topk_all`` and that ``argmax_exact`` implies ``G``;
* the registered defaults (four arms, k = 3/5/10/20/50, 248 rows) and that
  ``--check`` refuses a report from another stage.

No checkpoint is trained, no threshold is asserted against a measured run.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "scripts" / "probe_tf_exact_gap.py"
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _load():
    spec = importlib.util.spec_from_file_location("probe_tf_exact_gap_under_test", PROBE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_tf_exact_gap_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load()


@pytest.fixture(scope="module")
def tiny():
    from ai.ed3n.token_snn import TokenConfig, TokenSNN, TokenVocab

    texts = [
        "the capital of Zorb is Quux",
        "what is the capital of Zorb",
        "Quux is north of Ondrast",
        "where is Quux",
        "the river runs past Ondrast",
    ]
    vocab = TokenVocab.build(texts, min_count=1, max_vocab=128)
    config = TokenConfig(
        d_emb=8,
        d_hidden=16,
        layers=1,
        timesteps=1,
        max_len=48,
        readout="membrane",
    )
    return TokenSNN(vocab, config, device="cpu")


def _row(*, g, o, eos, topk, tf_hits=0, ranks=None, first_div=-1, sha="x"):
    """A row shaped exactly like ``measure_row``'s return value."""
    ranks = ranks if ranks is not None else [1] * max(1, tf_hits)
    return {
        "prompt_sha": sha,
        "gold_len": len(ranks),
        "gold_unk": 0,
        "gold_text": "t",
        "truncated": False,
        "argmax_exact": o,
        "eos_argmax": eos,
        "tf_hits": tf_hits,
        "token_tf": (tf_hits / len(ranks)) if ranks else 0.0,
        "ranks": ranks,
        "rank_median": 1.0,
        "gold_logprob": -1.0,
        "topk_all": {str(k): bool(v) for k, v in topk.items()},
        "exact_g": g,
        "exact_model": g,
        "exact_raw": g,
        "first_div": first_div,
        "greedy_len": len(ranks),
        "greedy_sha": sha,
        "prefix_curve": {"0.0": g, "0.25": g, "0.5": g, "0.75": g, "1.0": eos},
    }


ALL_TRUE = {3: True, 5: True, 10: True, 20: True, 50: True}


# -- the decision rule ------------------------------------------------------
def test_majority_rule_and_tie(probe):
    assert probe._verdict_from_counts(0, 0) == "no-gap"
    assert probe._verdict_from_counts(6, 4) == "gap=decoding"
    assert probe._verdict_from_counts(4, 6) == "gap=distribution"
    # 0.5 / 0.5 is neither ">= 0.5 and the other < 0.5" nor "> 0.5" -> mixed
    assert probe._verdict_from_counts(5, 5) == "gap=mixed"
    # an all-failures-one-side case still reads as itself
    assert probe._verdict_from_counts(9, 1) == "gap=decoding"
    assert probe._verdict_from_counts(1, 9) == "gap=distribution"


def test_verdict_reads_only_the_closed_form_fields(probe):
    aggregate = {"S_top5_search_could": 6, "M_distribution": 4}
    assert probe.verdict(aggregate) == "gap=decoding"
    aggregate = {"S_top5_search_could": 4, "M_distribution": 6}
    assert probe.verdict(aggregate) == "gap=distribution"


# -- the partition algebra --------------------------------------------------
def test_partition_is_the_closed_form_and_k_sensitivity(probe):
    rows = [
        # a greedy success: inside every top-k
        _row(g=True, o=True, eos=True, topk=ALL_TRUE, tf_hits=4, ranks=[1, 1, 1, 1], sha="a"),
        # gold outside the top 50 somewhere -> M at every k
        _row(
            g=False,
            o=False,
            eos=False,
            topk={3: False, 5: False, 10: False, 20: False, 50: False},
            tf_hits=1,
            ranks=[1, 80, 1, 1],
            sha="b",
        ),
        # inside top 3 -> S at every k
        _row(
            g=False,
            o=False,
            eos=False,
            topk={3: True, 5: True, 10: True, 20: True, 50: True},
            tf_hits=3,
            ranks=[1, 2, 1, 1],
            sha="c",
        ),
        # rank 7: outside 3/5, inside 10/20/50 -> the k choice matters
        _row(
            g=False,
            o=False,
            eos=False,
            topk={3: False, 5: False, 10: True, 20: True, 50: True},
            tf_hits=3,
            ranks=[1, 7, 1, 1],
            sha="d",
        ),
    ]
    agg = probe._aggregate(rows)

    assert agg["rows"] == 4
    assert agg["greedy_exact"] == 1
    assert agg["failures"] == 3
    assert agg["argmax_exact"] == 1
    assert agg["D_gold_prefix_fixes"] == 0
    assert agg["X_greedy_luck"] == 0
    assert agg["theorem_gold_path_equals_greedy"] is True

    # k=5: T5 = 2 (rows a, c), so S = 1 and M = 2
    assert agg["topk_all"]["5"] == 2
    assert agg["S_top5_search_could"] == 1
    assert agg["M_distribution"] == 2
    assert agg["partition_sums_to_failures"] is True
    assert probe.verdict(agg) == "gap=distribution"

    # k=3: rows a and c -> S = 1, M = 2 (still a distribution majority)
    assert agg["k_sensitivity"]["3"]["S"] == 1
    assert agg["k_sensitivity"]["3"]["M"] == 2
    assert agg["k_sensitivity"]["3"]["verdict"] == "gap=distribution"

    # k=10: rows a, c, d -> S = 2, M = 1 -> the decision would flip
    assert agg["k_sensitivity"]["10"]["S"] == 2
    assert agg["k_sensitivity"]["10"]["M"] == 1
    assert agg["k_sensitivity"]["10"]["verdict"] == "gap=decoding"

    # every k's two buckets still sum to the failures
    for k in (3, 5, 10, 20, 50):
        entry = agg["k_sensitivity"][str(k)]
        assert entry["S"] + entry["M"] == agg["failures"]


def test_theorem_check_catches_an_impossible_row(probe):
    """``D`` is a consistency check: a row claiming it must flip the flag."""
    rows = [
        _row(g=False, o=True, eos=True, topk=ALL_TRUE, tf_hits=2, ranks=[1, 1], sha="bad"),
    ]
    agg = probe._aggregate(rows)
    assert agg["D_gold_prefix_fixes"] == 1
    assert agg["theorem_gold_path_equals_greedy"] is False
    # The closed form relies on D == 0, so a violating row must break the sum:
    # that is exactly what makes it a detector instead of a decoration, and it
    # is why --check refuses a report whose partition does not add up.
    assert agg["partition_sums_to_failures"] is False


def test_aggregate_weighted_tf_uses_hits_not_the_rounded_rate(probe):
    rows = [
        _row(g=True, o=True, eos=True, topk=ALL_TRUE, tf_hits=3, ranks=[1, 1, 1], sha="a"),
        _row(g=False, o=False, eos=False, topk=ALL_TRUE, tf_hits=1, ranks=[1, 2], sha="b"),
    ]
    agg = probe._aggregate(rows)
    assert agg["token_tf_weighted"] == round(4 / 5, 4)
    assert agg["mean_row_tf"] == round((1.0 + 0.5) / 2, 4)


def test_aggregate_survives_the_json_round_trip(probe):
    """``--check`` compares a recomputation with the stored report: Wilson
    intervals come back as lists, so the comparison must canonicalise."""
    rows = [_row(g=True, o=True, eos=True, topk=ALL_TRUE, tf_hits=2, ranks=[1, 1], sha="a")]
    aggregate = probe._aggregate(rows)
    stored = json.loads(json.dumps(aggregate, sort_keys=True))
    assert isinstance(stored["greedy_exact_ci"], list)
    assert probe._canonical(probe._aggregate(rows)) == probe._canonical(stored)


def test_wilson_intervals_at_the_edges(probe):
    low, high = probe.wilson(0, 248)
    assert low == 0.0
    assert 0.0 < high < 0.02
    low, high = probe.wilson(248, 248)
    assert high == 1.0
    assert 0.9 < low < 1.0
    assert probe.wilson(0, 0) == (0.0, 0.0)


# -- the endpoints, on a real (tiny) model ----------------------------------
def test_endpoints_are_g_and_eos_argmax(probe, tiny):
    prompt, answer = "what is the capital of Zorb", "Quux"
    row = probe.measure_row(tiny, prompt, answer)

    assert sorted(row["prefix_curve"]) == ["0.0", "0.25", "0.5", "0.75", "1.0"]
    assert row["exact_g"] == row["prefix_curve"]["0.0"]
    assert row["eos_argmax"] == row["prefix_curve"]["1.0"]
    assert row["truncated"] is False
    assert row["tf_hits"] == sum(1 for rank in row["ranks"] if rank == 1)
    assert row["argmax_exact"] == (row["tf_hits"] == len(row["ranks"]))


def test_argmax_exact_implies_greedy_exact_and_topk_is_monotone(probe, tiny):
    for prompt, answer in (
        ("what is the capital of Zorb", "Quux"),
        ("where is Quux", "north"),
        ("the capital of Zorb is", "Quux"),
    ):
        row = probe.measure_row(tiny, prompt, answer)
        if row["argmax_exact"]:
            assert row["exact_g"] is True
        flags = [row["topk_all"][str(k)] for k in (3, 5, 10, 20, 50)]
        assert flags == sorted(flags)


def test_continue_exact_endpoints_by_two_paths(probe, tiny):
    prompt, answer = "what is the capital of Zorb", "Quux"
    gold = probe._gold_pass(tiny, prompt, answer)
    body = gold["gold"][:-1]
    prefix = gold["ids"][: gold["a_start"]]

    produced, ok = probe._continue_exact(tiny, prefix, body, 0)
    assert ok == (produced == body + [tiny.vocab.eos_id])
    assert ok == probe.measure_row(tiny, prompt, answer)["exact_g"]

    produced, ok = probe._continue_exact(tiny, prefix, body, len(body))
    assert produced == ([tiny.vocab.eos_id] if ok else produced)
    assert ok == all(gold["correct"])


# -- the registered surface -------------------------------------------------
def test_registered_defaults(probe):
    args = probe.build_parser().parse_args([])
    assert args.arms == "distill_holdout,core_holdout,distill_train,core_train"
    assert probe.TOP_K == (3, 5, 10, 20, 50)
    assert probe.CURVE_FRACTIONS[0] == 0.0
    assert probe.CURVE_FRACTIONS[-1] == 1.0
    assert probe.ROWS == 248
    assert probe.PRIMARY == "distill_holdout"
    assert probe.MAX_SECONDS == 1800.0


def test_check_refuses_a_foreign_report(probe, tmp_path):
    wrong = tmp_path / "wrong.json"
    wrong.write_text('{"stage": "probe_ladder87"}', encoding="utf-8")
    ok, message = probe.check(wrong)
    assert ok is False
    assert "not a probe_tf_exact_gap report" in message
