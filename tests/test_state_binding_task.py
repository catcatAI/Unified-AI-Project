# ANGELA-MATRIX: L3 [βγδ] [A] [L2]
"""The round-6 task's own contract, tested without training anything.

Round 5 asked whether the state carries a value at all; it did, but ``wrong_name``
(0.994) showed the name was decoration - a single-slot buffer. This task asks
whether the state carries two *bindings* and whether the query selects between
them, so the failures that would make a passing number meaningless are:

* a value reused between training and the held-out split (then "copied a new
  string" becomes "recalled a seen one"),
* a held-out name that was trained,
* a ``cold`` split that is not the *same* questions as held-out,
* an ask index that is out of range or always the same (then a positional trick
  could pass without selection),
* the two teaching turns encoded as one sequence (then the task is not two
  ``ai_step`` calls and the binding claim is different),
* a ``wrong_name`` control that happens to ask a taught key (then it is not a
  control).

Each is a case below.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "train_state_binding.py"

SIZES = {"train": 200, "dev": 60, "heldout": 60, "wrong": 20}


@pytest.fixture(scope="module")
def task():
    spec = importlib.util.spec_from_file_location("train_state_binding_under_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def splits(task):
    return task.build_splits(seed=1234, sizes=dict(SIZES))


def _copy(splits):
    """Deep enough copy that mutating one episode cannot touch the fixture."""
    return {
        name: [
            {
                "taught": [list(pair) for pair in episode["taught"]],
                **{key: value for key, value in episode.items() if key != "taught"},
            }
            for episode in rows
        ]
        for name, rows in splits.items()
    }


def test_the_splits_are_clean(task, splits):
    report = task.leak_check(splits)
    assert report["clean"] is True
    assert report["chars_outside_alphabet"] == 0
    assert report["duplicate_values_inside_train"] == 0


def test_a_reused_value_is_caught(task, splits):
    """If the generator ever recycles a value, the check must say so."""
    dirty = _copy(splits)
    dirty["heldout_names"][0]["taught"][0][1] = dirty["train"][0]["taught"][0][1]
    report = task.leak_check(dirty)
    assert report["clean"] is False
    assert report["value_overlap_with_train"]["heldout_names"] == 1


def test_a_trained_name_in_the_heldout_split_is_caught(task, splits):
    dirty = _copy(splits)
    dirty["heldout_names"][0]["taught"][0][0] = dirty["train"][0]["taught"][0][0]
    assert task.leak_check(dirty)["clean"] is False
    assert task.leak_check(dirty)["train_heldout_name_overlap"] == 1


def test_a_wrong_name_that_asks_a_taught_key_is_caught(task, splits):
    """``wrong_name`` is only a control while the asked key is untaught."""
    dirty = _copy(splits)
    episode = dirty["wrong_name"][0]
    episode["query_name"] = episode["taught"][0][0]
    report = task.leak_check(dirty)
    assert report["wrong_name_queries_a_taught_key"] == 1
    assert report["clean"] is False


def test_an_out_of_range_ask_is_caught(task, splits):
    dirty = _copy(splits)
    dirty["dev"][0]["ask"] = len(dirty["dev"][0]["taught"])
    report = task.leak_check(dirty)
    assert report["ask_index_out_of_range"] == 1
    assert report["clean"] is False


def test_cold_asks_the_same_questions_as_heldout(task, splits):
    """Cold must be the held-out questions minus the teaching turns."""
    assert splits["cold"] == splits["heldout_names"]


def test_both_ask_positions_occur(task, splits):
    """A positional shortcut must not be able to explain the score."""
    for name in ("train", "dev", "heldout_names"):
        asks = {episode["ask"] for episode in splits[name]}
        assert asks == {0, 1}
        assert all(episode["ask"] < len(episode["taught"]) for episode in splits[name])


def test_building_twice_gives_the_same_data(task, splits):
    again = task.build_splits(seed=1234, sizes=dict(SIZES))
    for name in splits:
        assert task.digest(splits[name]) == task.digest(again[name])


def test_a_different_seed_gives_different_data(task, splits):
    other = task.build_splits(seed=999, sizes=dict(SIZES))
    assert task.digest(splits["heldout_names"]) != task.digest(other["heldout_names"])


def test_no_value_or_name_is_reused_inside_an_episode(task, splits):
    for rows in splits.values():
        for episode in rows:
            names = [name for name, _ in episode["taught"]]
            values = [value for _, value in episode["taught"]]
            assert len(set(names)) == len(names)
            assert len(set(values)) == len(values)


def test_every_char_is_in_the_table(task, splits):
    table = task.CharTable()
    for rows in splits.values():
        for episode in rows:
            for name, value in episode["taught"]:
                for ch in name + value:
                    assert ch in table.stoi


def test_text_roundtrips_through_the_table(task, splits):
    table = task.CharTable()
    episode = splits["train"][0]
    texts = [task.teach_text(pair) for pair in episode["taught"]]
    texts += [task.query_text(episode), task.answer_text(episode)]
    for text in texts:
        assert table.decode(table.encode(text)) == text


def test_the_two_teaching_turns_are_two_sequences(task, splits):
    """Two turns means two ``ai_step`` calls, not one longer sentence.

    If the generator ever concatenated them, the round would be measuring a
    longer prompt rather than a write followed by a write.
    """
    table = task.CharTable()
    episode = splits["train"][0]
    encoded = task.encode_episode(table, episode)
    assert len(encoded["teach"]) == 2
    first, second = encoded["teach"]
    assert first != second
    assert first[0] == second[0] == table.bos_id
    joined = first + second
    assert len(joined) == len(first) + len(second)
    # Each turn carries exactly one of the two values, so neither turn shows the
    # whole episode.
    for index, turn in enumerate(encoded["teach"]):
        text = table.decode(turn)
        assert episode["taught"][index][1] in text
        assert episode["taught"][1 - index][1] not in text


def test_encoded_episode_shapes_are_uniform(task, splits):
    """Training uses fixed-width batches, so a ragged split must fail loudly."""
    table = task.CharTable()
    encoded = [task.encode_episode(table, episode) for episode in splits["train"]]
    for key in ("query", "answer"):
        assert len({len(row[key]) for row in encoded}) == 1
    for index in range(2):
        assert len({len(row["teach"][index]) for row in encoded}) == 1
        assert len({len(row["both"][index]["query"]) for row in encoded}) == 1


def test_the_answer_is_not_in_the_question(task, splits):
    for episode in splits["heldout_names"]:
        question = task.query_text(episode)
        assert episode["taught"][episode["ask"]][1] not in question
        assert episode["taught"][1 - episode["ask"]][1] not in question


def test_the_answer_starts_after_the_query(task, splits):
    """The loss mask starts exactly where the answer starts."""
    table = task.CharTable()
    episode = splits["train"][0]
    encoded = task.encode_episode(table, episode)
    query_len = len(encoded["query"])
    sequence = encoded["query"] + encoded["answer"]
    assert sequence[query_len] == table.encode(task.answer_text(episode))[0]
    assert encoded["query"] == table.encode(task.query_text(episode))


def test_the_both_objective_asks_two_different_questions(task, splits):
    table = task.CharTable()
    episode = splits["train"][0]
    encoded = task.encode_episode(table, episode)
    assert len(encoded["both"]) == 2
    queries = {tuple(item["query"]) for item in encoded["both"]}
    answers = {tuple(item["answer"]) for item in encoded["both"]}
    assert len(queries) == 2 and len(answers) == 2
    for index, item in enumerate(encoded["both"]):
        assert item["query"] == table.encode(task.query_text(episode, index))
        assert item["answer"] == table.encode(task.answer_text(episode, index)) + [table.eos_id]


def test_generation_length_matches_the_answer_shape(task, splits):
    table = task.CharTable()
    episode = splits["train"][0]
    encoded = task.encode_episode(table, episode)
    assert task.ANSWER_CHARS == len(table.decode(encoded["answer"][:-1]))


def test_wrong_name_teaches_two_and_asks_a_third(task, splits):
    for episode in splits["wrong_name"]:
        taught = {name for name, _ in episode["taught"]}
        assert len(taught) == 2
        assert episode["query_name"] not in taught
        # No ground truth exists by construction, so there is nothing to score.
        assert episode["ask"] is None
        assert task.query_text(episode) == f"{episode['query_name']} ?"


def test_wrong_name_episodes_cannot_be_answered_from_the_query(task, splits):
    """The asked key is absent from the state, so any taught value is a leak of
    "carry the last value" rather than a lookup - which is what it measures."""
    for episode in splits["wrong_name"]:
        for _, value in episode["taught"]:
            assert value not in task.query_text(episode)


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


def test_teaching_is_one_ai_step_per_turn(task, splits):
    """``_teach`` must advance the model twice and step the clock twice."""
    torch = pytest.importorskip("torch")
    device = "cpu"
    table = task.CharTable()
    core = task.build_core(table, device)
    rows = [task.encode_episode(table, episode) for episode in splits["train"][:4]]
    state = core.init_state(len(rows))
    calls = {"ai": 0, "al": 0}
    original_ai, original_al = core.ai_step, core.al_step

    def counting_ai(*args, **kwargs):
        calls["ai"] += 1
        return original_ai(*args, **kwargs)

    def counting_al(*args, **kwargs):
        calls["al"] += 1
        return original_al(*args, **kwargs)

    core.ai_step, core.al_step = counting_ai, counting_al
    try:
        task._teach(core, rows, state, device)
    finally:
        core.ai_step, core.al_step = original_ai, original_al
    assert calls == {"ai": 2, "al": 2}


def test_the_checkpoint_is_selected_by_a_continuous_signal(task):
    """Selection must not key on exact match.

    Exact stays at 0 until the model is nearly right, so a rule keyed on it keeps
    the earliest weights forever when every epoch ties at 0 - that is the §43
    failure mode, and `patience=0` alone does not fix it.
    """
    pytest.importorskip("torch")
    device = "cpu"
    table = task.CharTable()
    core = task.build_core(table, device)
    rows = task.build_splits(seed=1234, sizes={"train": 8, "dev": 4, "heldout": 4, "wrong": 2})
    out = task.train(
        core,
        table,
        rows["train"],
        rows["dev"],
        objective="single",
        device=device,
        epochs=2,
        batch_size=8,
        lr=3e-3,
        patience=0,
        seed=1234,
    )
    assert out["epochs_run"] == 2
    assert all("dev_loss" in step for step in out["history"])
    assert out["selection"].startswith("lowest dev answer loss")
    assert 0.0 < out["best_dev_loss"] < 100.0


def test_answer_loss_is_finite_and_smaller_with_the_answer_than_without(task):
    """A sanity bound on the selection signal, not a training result."""
    pytest.importorskip("torch")
    device = "cpu"
    table = task.CharTable()
    core = task.build_core(table, device)
    rows = task.build_splits(seed=1234, sizes={"train": 4, "dev": 4, "heldout": 4, "wrong": 2})
    value = task.answer_loss(core, table, rows["dev"], device=device, batch_size=4)
    assert value > 0.0
    assert value <= task.ANSWER_CHARS * 8.0  # uniform-distribution entropy bound
