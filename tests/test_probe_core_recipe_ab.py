# =============================================================================
# ANGELA-MATRIX: [L4] [βγ] [B] [L3]
# LAYER: learning
# =============================================================================
"""§90's contract is the decision rule and the controls, not the scores.

``CORE_GAP_ANALYSIS.md`` §90 fixes, before any scored run: the corpus, the
checkpoint's own vocabulary, 100 epochs x 81 batches, batch 64, cosine 3e-3,
seeds {0, 1}, validation-loss selection, the §89 producer/scorer, and a decision
threshold of 10 hold-out rows with **disjoint per-seed ranges**.

What is tested here:

* the registered constants (and that the wall-clock guard is the amended one);
* that the GRU arm is parameter-matched by an explicit sweep (418 -> 2,489,219
  against the SNN's 2,491,227), not by ``match_gru_hidden``'s sqrt centre;
* the decision table, including "a difference under 10 rows is not a difference"
  and "overlapping ranges lose even when the mean differs";
* that unscored smoke runs cannot produce a verdict;
* that both arm checkpoints reload and regenerate identically (the ``--check``
  path depends on it);
* that the vocabulary really is the checkpoint's, not a corpus rebuild.

No checkpoint is trained and no threshold is asserted against a measured run.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROBE = REPO_ROOT / "scripts" / "probe_core_recipe_ab.py"
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _load():
    spec = importlib.util.spec_from_file_location("probe_core_recipe_ab_under_test", PROBE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_core_recipe_ab_under_test"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def probe():
    return _load()


def _runs(*rows, arm_seed=None):
    """Build report rows: ``(kind, seed, exact_raw[, scored])``."""
    out = []
    for row in rows:
        kind, seed, exact = row[0], row[1], row[2]
        scored = row[3] if len(row) > 3 else True
        out.append(
            {
                "arm": kind,
                "seed": seed,
                "scored": scored,
                "holdout": {"n": 248, "exact_raw": exact} if scored else {},
            }
        )
    return out


# -- registration -----------------------------------------------------------
def test_registered_constants(probe):
    assert probe.ARMS == ("snn", "gru")
    assert probe.SEEDS == (0, 1)
    assert probe.EPOCHS == 100
    assert probe.BATCH == 64
    assert probe.LR == 3e-3
    assert probe.MIN_LR == 1e-5
    assert probe.GRU_HIDDEN == 418
    assert probe.MOVE_ROWS == 10
    assert probe.MAX_SECONDS == 10800.0
    assert probe.HOLDOUT.name == "distill_val_holdout.jsonl"
    assert probe.REFERENCE.name == "token_snn_distill.pt"


#: Registered in §90.2; hard-coded here so the test fails if the arm's size drifts.
SNN_PARAMS = 2491227


def test_vocabulary_is_the_checkpoint_not_a_corpus_rebuild(probe):
    vocab, cfg = probe.load_vocab()
    assert len(vocab) == 3577
    assert cfg.d_hidden == 512 and cfg.d_emb == 96 and cfg.max_len == 192
    assert cfg.readout == "membrane"


def test_gru_hidden_is_parameter_matched(probe):
    vocab, cfg = probe.load_vocab()
    hidden, count = probe.nearest_gru_hidden(len(vocab), cfg, SNN_PARAMS)
    assert (hidden, count) == (probe.GRU_HIDDEN, 2489219)
    assert abs(count - SNN_PARAMS) / SNN_PARAMS < 0.001


def test_gru_sweep_beats_the_sqrt_centre_helper(probe):
    """The helper the §36 code ships with would pick d=911 (~2.7x) here."""
    from compare_snn_gru import gru_param_count, match_gru_hidden

    vocab, cfg = probe.load_vocab()
    helper_hidden, _ = match_gru_hidden(len(vocab), cfg, SNN_PARAMS)
    assert helper_hidden != probe.GRU_HIDDEN
    gap_helper = abs(gru_param_count(len(vocab), cfg, helper_hidden) - SNN_PARAMS)
    gap_sweep = abs(gru_param_count(len(vocab), cfg, probe.GRU_HIDDEN) - SNN_PARAMS)
    assert gap_sweep < gap_helper


# -- schedule ---------------------------------------------------------------
def test_cosine_schedule_matches_the_cli_shape(probe):
    assert probe.cosine_lr(0, 100) == pytest.approx(probe.LR)
    assert probe.cosine_lr(99, 100) < probe.cosine_lr(50, 100) < probe.cosine_lr(1, 100)
    # the floor is min_lr, never below it
    assert probe.cosine_lr(1000, 100) == pytest.approx(probe.MIN_LR)
    assert probe.cosine_lr(99, 100) > probe.MIN_LR


# -- decision (registered §90.5) -------------------------------------------
@pytest.mark.parametrize(
    "snn,gru,expected",
    [
        ((28, 30), (29, 31), "recipe-invariant"),  # overlapping ranges
        ((28, 30), (50, 52), "recipe-moves"),  # disjoint, +22 rows
        ((28, 30), (5, 8), "recipe-moves-against"),  # disjoint, -22.5 rows
        ((28, 30), (36, 39), "recipe-invariant"),  # disjoint but only +8.5 rows
        ((28, 28), (38, 38), "recipe-moves"),  # exactly the 10-row boundary, disjoint
        ((28, 28), (38, 39), "recipe-moves"),  # 10.5 rows and disjoint
    ],
)
def test_decision_table(probe, snn, gru, expected):
    runs = _runs(("snn", 0, snn[0]), ("snn", 1, snn[1]), ("gru", 0, gru[0]), ("gru", 1, gru[1]))
    assert probe.decide(runs)["verdict"] == expected


def test_decision_reports_rows_and_pp(probe):
    runs = _runs(("snn", 0, 28), ("snn", 1, 28), ("gru", 0, 40), ("gru", 1, 41))
    got = probe.decide(runs)
    assert got["delta_rows"] == pytest.approx(12.5)
    assert got["delta_pp"] == pytest.approx(100 * 12.5 / 248, abs=0.01)
    assert got["ranges_separated"] is True
    assert got["n_rows"] == 248


def test_unscored_runs_cannot_decide(probe):
    runs = _runs(("snn", 0, 0, False), ("gru", 0, 0, False))
    assert probe.decide(runs)["verdict"] == "not-decided-missing-arm"


def test_missing_arm_cannot_decide(probe):
    runs = _runs(("snn", 0, 28), ("snn", 1, 30))
    assert probe.decide(runs)["verdict"] == "not-decided-missing-arm"


# -- checkpoints ------------------------------------------------------------
def _tiny(probe, kind):
    from ai.ed3n.token_snn import TokenConfig, TokenSNN, TokenVocab

    vocab = TokenVocab.build(["ab\ncd", "ef\ngh"], min_count=1, max_vocab=64)
    cfg = TokenConfig(d_emb=8, d_hidden=8, max_len=16)
    if kind == "snn":
        return TokenSNN(vocab, cfg, device="cpu"), None
    from compare_snn_gru import GRUDecoder

    return GRUDecoder(vocab, cfg, device="cpu", d_hidden=12), 12


@pytest.mark.parametrize("kind", ["snn", "gru"])
def test_both_arm_checkpoints_reload(probe, kind, tmp_path):
    import torch

    model, _ = _tiny(probe, kind)
    path = tmp_path / f"{kind}.pt"
    model.save(path)
    assert path.is_file()

    back = probe.load_model(kind, path)
    before = [p.detach().cpu() for p in model.net.parameters()]
    after = [p.detach().cpu() for p in back.net.parameters()]
    assert len(before) == len(after)
    assert all(torch.equal(a, b) for a, b in zip(before, after))
    assert isinstance(back.generate("ab", max_new=4), str)
    assert back.net.training is False


def test_holdout_digest_is_order_sensitive(probe):
    """The 248 rows are measured in file order; a shuffle is a different split."""
    rows = probe.read_pairs(probe.HOLDOUT)
    assert len(rows) == 248
    swapped = list(rows)
    swapped[0], swapped[1] = swapped[1], swapped[0]
    assert probe.rows_digest(rows) != probe.rows_digest(swapped)


def test_display_path_falls_back_outside_the_repo(probe):
    assert probe._display(probe.REFERENCE).startswith("apps/backend/data/models/")
    assert probe._display(Path("/tmp/opencode/x.pt")) == "/tmp/opencode/x.pt"
