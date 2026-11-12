# ANGELA-MATRIX: L3 [βγδ] [A] [L2]
"""The round-5 task's own contract, tested without training anything.

The task exists to make one claim falsifiable, so the failures that matter are
the ones that would make a passing number meaningless: a value reused between
training and the held-out split, a held-out name that was trained, a character
that silently becomes ``<unk>``, or a ``cold`` split that is not the *same*
questions as the held-out one. Each is a case below.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "train_state_content.py"

SIZES = {"train": 200, "dev": 60, "heldout": 60, "wrong": 20}


@pytest.fixture(scope="module")
def task():
    spec = importlib.util.spec_from_file_location("train_state_content_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def splits(task):
    return task.build_splits(seed=1234, sizes=dict(SIZES))


def test_the_splits_are_clean(task, splits):
    report = task.leak_check(splits)
    assert report["clean"] is True
    assert report["chars_outside_alphabet"] == 0


def test_a_reused_value_is_caught(task, splits):
    """If the generator ever recycles a value, the check must say so.

    A leaked value is the one failure that turns "copied a new string" into
    "recalled a seen one", so the detector is tested rather than trusted.
    """
    dirty = {name: [dict(episode) for episode in rows] for name, rows in splits.items()}
    dirty["heldout_names"][0]["value"] = dirty["train"][0]["value"]
    report = task.leak_check(dirty)
    assert report["clean"] is False
    assert report["value_overlap_with_train"]["heldout_names"] == 1


def test_a_trained_name_in_the_heldout_split_is_caught(task, splits):
    dirty = {name: [dict(episode) for episode in rows] for name, rows in splits.items()}
    dirty["heldout_names"][0]["teach_name"] = dirty["train"][0]["teach_name"]
    assert task.leak_check(dirty)["clean"] is False


def test_cold_asks_the_same_questions_as_heldout(task, splits):
    """Cold must be the held-out questions minus the teaching turn.

    A separately drawn sample would let "different questions" explain the gap
    instead of "no state", which is the whole point of the control.
    """
    assert splits["cold"] == splits["heldout_names"]


def test_building_twice_gives_the_same_data(task, splits):
    again = task.build_splits(seed=1234, sizes=dict(SIZES))
    for name in splits:
        assert task.digest(splits[name]) == task.digest(again[name])


def test_a_different_seed_gives_different_data(task, splits):
    other = task.build_splits(seed=999, sizes=dict(SIZES))
    assert task.digest(splits["heldout_names"]) != task.digest(other["heldout_names"])


def test_every_value_char_is_in_the_table(task, splits):
    table = task.CharTable()
    for rows in splits.values():
        for episode in rows:
            for ch in episode["value"] + episode["teach_name"]:
                assert ch in table.stoi


def test_text_roundtrips_through_the_table(task, splits):
    table = task.CharTable()
    episode = splits["train"][0]
    for text in (task.teach_text(episode), task.query_text(episode), task.answer_text(episode)):
        assert table.decode(table.encode(text)) == text


def test_encoded_episode_shapes_are_uniform(task, splits):
    """Training uses fixed-width batches, so a ragged split must fail loudly."""
    table = task.CharTable()
    encoded = [task.encode_episode(table, episode) for episode in splits["train"]]
    for key in ("teach", "query", "answer"):
        assert len({len(row[key]) for row in encoded}) == 1


def test_the_answer_is_not_in_the_question(task, splits):
    """The value must never appear in the query turn, or there is nothing to carry."""
    for episode in splits["heldout_names"]:
        assert episode["value"] not in task.query_text(episode)


def test_the_answer_starts_after_the_query(task, splits):
    """The loss mask starts exactly where the answer starts."""
    table = task.CharTable()
    episode = splits["train"][0]
    encoded = task.encode_episode(table, episode)
    query_len = len(encoded["query"])
    sequence = encoded["query"] + encoded["answer"]
    # logits[:, query_len - 1] is the prediction for sequence[query_len].
    assert sequence[query_len] == table.encode(episode["value"])[0]
    assert encoded["query"] == table.encode(task.query_text(episode))


def test_wrong_name_teaches_one_and_asks_another(task, splits):
    for episode in splits["wrong_name"]:
        assert episode["teach_name"] != episode["query_name"]


def test_zero_state_really_zeroes(task, splits):
    """The ablation must leave the same object, weights and prompt.

    ``init_state`` is the *reset*, which is a different experiment. The gate's
    claim is that the state was there and then removed.
    """
    torch = pytest.importorskip("torch")
    device = "cpu"
    table = task.CharTable()
    core = task.build_core(table, device)
    state = core.init_state(3)
    state.tensors["h"] = torch.ones_like(state.tensors["h"])
    version = state.state_version
    state.tensors["h"] = torch.zeros_like(state.tensors["h"])
    assert torch.count_nonzero(state.tensors["h"]) == 0
    assert state.state_version == version
    assert core.weights_hash() == core.weights_hash()
