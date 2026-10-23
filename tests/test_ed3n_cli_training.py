"""ED3N CLI training must train the path that ``generate()`` reads."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "apps" / "backend" / "src"


@pytest.fixture(scope="module")
def cli():
    import sys

    sys.path.insert(0, str(SRC))
    from ai.ed3n import __main__ as module

    return module


def test_alpaca_rows_keep_the_instruction(cli, tmp_path):
    path = tmp_path / "alpaca.json"
    path.write_text(
        json.dumps(
            [
                {"instruction": "Say hello", "input": "", "output": "hello"},
                {"instruction": "Add", "input": "1+1", "output": "2"},
            ]
        ),
        encoding="utf-8",
    )
    rows = cli._load_train_examples(str(path))
    assert rows[0]["input"] == "Say hello"
    assert rows[1]["input"].startswith("Add")


def test_train_step_receives_the_sequence_batch(cli, tmp_path, monkeypatch):
    """Regression: the CLI only trained associations, so generate() was random."""
    path = tmp_path / "pairs.json"
    path.write_text(
        json.dumps([{"input": "1 + 1", "output": "2"}, {"input": "2 + 2", "output": "4"}]),
        encoding="utf-8",
    )
    seen = []

    class _FakeTrainer:
        def __init__(self, *args, **kwargs):
            pass

        def train_step(self, batch, seq_batch=None):
            seen.append(seq_batch)
            return SimpleNamespace(loss=0.0, accuracy=1.0)

        def save(self, path):
            return None

    monkeypatch.setattr(cli, "JointTrainer", _FakeTrainer)
    cli.cmd_train(SimpleNamespace(data=str(path), epochs=1, lr=0.05, output="", checkpoint=""))
    assert seen, "train_step was never called"
    assert seen[0] is not None, "the sequence decoder was not trained"
    assert len(seen[0].examples) == len(cli._load_train_examples(str(path)))
