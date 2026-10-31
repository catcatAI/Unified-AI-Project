"""Contract for the AI+AL round loop (ISSUES §六.6: train -> auto next batch).

The loop's whole claim: the next batch appears **only after a successful
training run**, on a fresh slice, in its own files — and it never launches
the following round (that decision stays with a human).
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "ai_al_round_loop.py"


def _load():
    spec = importlib.util.spec_from_file_location("ai_al_round_loop_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def loop():
    return _load()


def _redirect_to(loop, tmp_path, monkeypatch):
    monkeypatch.setattr(loop, "PROCESSED", tmp_path)
    monkeypatch.setattr(loop, "REPORTS", tmp_path)


def test_generate_only_writes_the_next_batch(loop, tmp_path, monkeypatch):
    _redirect_to(loop, tmp_path, monkeypatch)
    rc = loop.main(["--round", "9", "--generate-only", "--next-rows", "5", "--next-skip", "0"])
    assert rc == 0
    assert (tmp_path / "ai_al_round10_dataset.json").is_file()
    assert (tmp_path / "ai_al_round10_train.jsonl").is_file()
    assert (tmp_path / "ai_al_round10_val.jsonl").is_file()
    assert (tmp_path / "ai_al_round10_manifest.json").is_file()
    man = json.loads((tmp_path / "ai_al_round9_loop.json").read_text(encoding="utf-8"))
    assert man["generated"] is True and man["checked"] is True
    assert man["train_rc"] is None  # generate-only runs no training
    assert man["next_batch"]["id_prefix"] == "r10_"
    assert man["next_batch"]["skip"] == 0
    assert man["next_batch"]["dataset_sha256"]
    # the following round is staged, never started
    assert "human" in man["next_step"]


def test_failed_training_produces_no_batch(loop, tmp_path, monkeypatch):
    _redirect_to(loop, tmp_path, monkeypatch)
    rc = loop.main(["--round", "9", "--", "false"])  # `false` exits 1
    assert rc == 1
    assert not (tmp_path / "ai_al_round10_dataset.json").exists()
    man = json.loads((tmp_path / "ai_al_round9_loop.json").read_text(encoding="utf-8"))
    assert man["train_rc"] == 1
    assert man["generated"] is False
    assert "failed" in man["next_step"]


def test_next_batch_schema_flags_pass_through(loop, tmp_path, monkeypatch):
    """MVE-1 round 4: the staged batch must carry the schema it was decided
    under — dt exposed and the carved cells — into generation and provenance."""
    _redirect_to(loop, tmp_path, monkeypatch)
    rc = loop.main(
        [
            "--round",
            "9",
            "--generate-only",
            "--next-rows",
            "40",
            "--next-skip",
            "0",
            "--next-holdout-cells",
            "unknown:conservative,knowledge_query:neutral",
            "--next-expose-dt",
        ]
    )
    assert rc == 0
    man = json.loads((tmp_path / "ai_al_round9_loop.json").read_text(encoding="utf-8"))
    assert man["next_batch"]["holdout_cells"] == "unknown:conservative,knowledge_query:neutral"
    assert man["next_batch"]["expose_dt"] is True
    data = json.loads((tmp_path / "ai_al_round10_dataset.json").read_text(encoding="utf-8"))
    assert data["provenance"]["expose_dt"] is True
    assert data["provenance"]["holdout_cells"] == {
        "unknown": "conservative",
        "knowledge_query": "neutral",
    }
    assert all("dt" in ex for ex in data["examples"])
    # prepare serialised dt into the trainer's input line
    train_row = json.loads(
        (tmp_path / "ai_al_round10_train.jsonl").read_text(encoding="utf-8").splitlines()[0]
    )
    assert " dt=" in train_row["input"]
    # without the flags the staged batch keeps the round-1-3 schema keys out
    plain = loop.main(["--round", "8", "--generate-only", "--next-rows", "5", "--next-skip", "0"])
    assert plain == 0
    data8 = json.loads((tmp_path / "ai_al_round9_dataset.json").read_text(encoding="utf-8"))
    assert "expose_dt" not in data8["provenance"]
    assert "holdout_cells" not in data8["provenance"]


def test_bad_cell_spec_fails_before_training(loop, tmp_path, monkeypatch):
    """A typo in the cell list must abort immediately — otherwise it would only
    surface after the hours-long training run has already finished."""
    _redirect_to(loop, tmp_path, monkeypatch)
    with pytest.raises(SystemExit):
        loop.main(["--round", "9", "--generate-only", "--next-holdout-cells", "unknown:sideways"])
    assert not (tmp_path / "ai_al_round9_loop.json").exists()  # nothing ran
    assert not (tmp_path / "ai_al_round10_dataset.json").exists()


def test_train_command_flags_are_extracted(loop, tmp_path, monkeypatch):
    _redirect_to(loop, tmp_path, monkeypatch)
    rc = loop.main(
        [
            "--round",
            "9",
            "--generate-only",
            "--",
            "./.venv/bin/python",
            "scripts/train_token_snn.py",
            "--out",
            "data/checkpoints/x.pt",
            "--report",
            "data/intelligence_reports/x.json",
        ]
    )
    # generate-only ignores the trailing command but must still record it
    assert rc == 0
    man = json.loads((tmp_path / "ai_al_round9_loop.json").read_text(encoding="utf-8"))
    assert man["checkpoint"] == "data/checkpoints/x.pt"
    assert man["report"] == "data/intelligence_reports/x.json"
