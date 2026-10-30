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
