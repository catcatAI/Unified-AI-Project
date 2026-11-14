# ANGELA-MATRIX: L3 [βγδ] [B] [L2]
"""§59 stage B's contract: the token-cache arm's state, masking and wiring.

These tests do not measure the model. They pin the things that would make a
stage-B result unreadable if they were wrong:

* ``tokencache`` is a registered model kind and its state really is ``h`` plus a
  token cache plus a mask;
* the start is still L: with an empty cache the logits are L's, bit for bit, and
  the new head columns are zero until training moves them;
* padding never enters the read - a padded row and the same row alone produce the
  same read, so a batch size cannot change an answer;
* truncation keeps the **first** ``slots`` tokens, because the roster is early in
  the session and a ring buffer would evict exactly the pairs the arm exists to
  keep;
* ``memory=False`` keeps every parameter, writes nothing and reads exactly zero,
  so it is the drop-in ablation for the pair comparison;
* ``al_step`` leaves the cache alone and matches the GRU's ``h``;
* an earlier turn's boundary is a snapshot, not a view of the live cache (the
  auxiliary loss reads those boundaries, so a shared view would score later
  turns' writes against earlier turns);
* the trainer writes the cache from the same stacked states the turn was
  computed from, and the mask marks each sample's real length.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "train_pantry_deduction.py"
TOKENS = 259


@pytest.fixture(scope="module")
def stage():
    spec = importlib.util.spec_from_file_location("pantry_deduction_tokencache", SCRIPT)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


@pytest.fixture(scope="module")
def torch():
    return pytest.importorskip("torch")


def _stage_l_path(stage):
    path = REPO_ROOT / stage.L_CHECKPOINT
    if not path.exists():
        pytest.skip("the stage-L checkpoint is a gitignored artifact")
    return path


def _pair(stage, *, hidden=128, emb=64, memory=True, seed=20261118):
    """A GRU carrier loaded from L and a cache arm derived from the same file."""
    from ai.core.stateful_decoder import GRUCore, TokenCacheCore

    path = _stage_l_path(stage)
    gru = GRUCore(TOKENS, hidden=hidden, emb=emb, chunk_seconds=60.0, seed=seed, device="cpu")
    assert stage.load_stage_l(gru, path) == stage.L_WEIGHTS_HASH
    cache = TokenCacheCore(
        TOKENS,
        hidden=hidden,
        emb=emb,
        chunk_seconds=60.0,
        seed=seed,
        device="cpu",
        memory=memory,
    )
    digest = stage.start_from_stage_l(cache, path, source_hidden=hidden)
    return gru, cache, digest


def test_tokencache_is_a_registered_model_kind(torch):
    from ai.core.core_state import MODEL_KINDS
    from ai.core.stateful_decoder import TokenCacheCore

    assert "tokencache" in MODEL_KINDS
    core = TokenCacheCore(TOKENS, hidden=8, emb=4, chunk_seconds=60.0, seed=3, device="cpu")
    state = core.init_state(2)
    assert state.model_kind == "tokencache"
    assert {name: tuple(value.shape) for name, value in state.tensors.items()} == {
        "h": (2, 8),
        "ck": (2, 0, 64),
        "cv": (2, 0, 64),
        "mask": (2, 0),
    }
    config = core.config()
    assert config["slots"] == 1024
    assert config["slot_dim"] == 64
    assert config["value_dim"] == 64
    assert config["memory"] is True


def test_start_from_stage_l_is_behaviourally_l_until_the_first_token(stage, torch):
    gru, cache, digest = _pair(stage)
    assert digest != stage.L_WEIGHTS_HASH
    assert cache.parameter_count() > stage.L_PARAMS

    tokens = torch.as_tensor([[11, 12, 13, 14], [21, 22, 23, 24]], dtype=torch.long)
    _, gru_state = gru.ai_step(tokens, gru.init_state(2))
    cache_logits, cache_state = cache.ai_step(tokens, cache.init_state(2))

    # the start is L, not a fresh init: the recurrence is copied wholesale, so
    # the two arms must be bit-identical on the same tokens (the arm must not
    # "start better" by accident)
    assert torch.equal(cache_state.tensors["h"], gru_state.tensors["h"])
    # the new head columns are zero, so `head([h, read])` starts from L's head
    assert torch.count_nonzero(cache.head.weight[:, gru.hidden :]) == 0
    assert torch.equal(cache.head.weight[:, : gru.hidden], gru.head.weight)
    assert int(cache_state.tensors["ck"].shape[1]) == tokens.shape[1]
    assert int(torch.count_nonzero(cache_state.tensors["cv"])) > 0
    assert torch.isfinite(cache_logits).all()


def test_an_empty_cache_reads_exactly_zero_and_matches_the_gru_head(stage, torch):
    gru, cache, _ = _pair(stage)
    state = cache.init_state(2)
    read = cache.read_vector(state.tensors)
    assert torch.equal(read, torch.zeros_like(read))

    tokens = torch.as_tensor([[5, 6], [7, 8]], dtype=torch.long)
    hidden = cache.consume(tokens[:, 0], state.tensors)["h"]
    with torch.no_grad():
        both = cache.token_logits(
            {
                "h": hidden,
                "ck": state.tensors["ck"],
                "cv": state.tensors["cv"],
                "mask": state.tensors["mask"],
            }
        )
        only_h = gru.token_logits({"h": hidden})
    assert torch.allclose(both, only_h, atol=1e-5)


def test_padding_never_enters_the_read(stage, torch):
    """A padded row and the same row alone must produce the same read."""
    from ai.core.stateful_decoder import TokenCacheCore

    core = TokenCacheCore(TOKENS, hidden=16, emb=8, chunk_seconds=60.0, seed=11, device="cpu")
    row = [5, 6, 7, 8]
    padded = [[5, 6, 7, 8, 0, 0], [5, 6, 7, 8, 9, 10]]
    lengths = [4, 6]
    batch = torch.as_tensor(padded)
    with torch.no_grad():
        state = core.init_state(2)
        hidden = state.tensors["h"]
        states = []
        for position in range(batch.shape[1]):
            hidden = core.cell(core.embedding(batch[:, position]), hidden)
            states.append(hidden)
        stacked = torch.stack(states, dim=1)
        picks = torch.as_tensor([n - 1 for n in lengths]).reshape(-1, 1, 1)
        state.tensors["h"] = stacked.gather(1, picks.expand(-1, 1, stacked.shape[-1])).reshape(
            2, -1
        )
        valid = torch.arange(batch.shape[1]).unsqueeze(0) < torch.as_tensor(lengths).unsqueeze(1)
        state.tensors = core.cache_write(state.tensors, stacked, valid)
        padded_read = core.read_vector(state.tensors)

        single = core.init_state(1)
        hidden = single.tensors["h"]
        states = []
        for token in row:
            hidden = core.cell(core.embedding(torch.as_tensor([token])), hidden)
            states.append(hidden)
        single.tensors["h"] = hidden
        single.tensors = core.cache_write(
            single.tensors,
            torch.stack(states, dim=1),
            torch.ones(1, len(row), dtype=torch.bool),
        )
        alone_read = core.read_vector(single.tensors)

    assert torch.allclose(padded_read[0], alone_read[0], atol=1e-6)
    assert state.tensors["mask"][0].tolist() == [1.0, 1.0, 1.0, 1.0, 0.0, 0.0]
    # the long row still sees its own six tokens; the equality above is not
    # "everything is masked"
    assert state.tensors["mask"][1].tolist() == [1.0] * 6
    assert not torch.allclose(padded_read[0], padded_read[1])


def test_truncation_keeps_the_first_slots_not_the_last(stage, torch):
    """The roster is early in the session; a ring buffer would evict it."""
    from ai.core.stateful_decoder import TokenCacheCore

    core = TokenCacheCore(
        TOKENS,
        hidden=8,
        emb=4,
        slots=3,
        slot_dim=4,
        value_dim=4,
        chunk_seconds=60.0,
        seed=1,
        device="cpu",
    )
    empty = {"ck": torch.zeros(1, 0, 4), "cv": torch.zeros(1, 0, 4), "mask": torch.zeros(1, 0)}
    states = torch.arange(5, dtype=torch.float32).reshape(1, 5, 1).repeat(1, 1, 8)
    written = core.cache_write(empty, states, torch.ones(1, 5, dtype=torch.bool))
    assert written["ck"].shape[1] == 3
    assert written["mask"].tolist() == [[1.0, 1.0, 1.0]]
    # slots 0..2 keep the states of tokens 0..2 (key_proj is linear, so the
    # first key is key_proj(state[0]), not key_proj(state[4]))
    expected = core.key_proj(states[0, :3])
    assert torch.allclose(written["ck"][0], expected, atol=1e-6)

    # a later turn cannot evict what is already stored
    again = core.cache_write(written, torch.randn(1, 4, 8), torch.ones(1, 4, dtype=torch.bool))
    assert again["ck"].shape[1] == 3
    assert torch.equal(again["ck"], written["ck"])


def test_memory_false_keeps_every_parameter_writes_nothing_and_reads_zero(stage, torch):
    _, on, _ = _pair(stage, memory=True)
    gru, off, _ = _pair(stage, memory=False)
    assert off.parameter_count() == on.parameter_count()

    state = off.init_state(2)
    tokens = torch.as_tensor([[40, 41, 42], [43, 44, 45]], dtype=torch.long)
    state.tensors = off.cache_write(
        state.tensors,
        torch.randn(2, 3, off.hidden),
        torch.ones(2, 3, dtype=torch.bool),
    )
    assert int(state.tensors["ck"].shape[1]) == 0
    read = off.read_vector(state.tensors)
    assert torch.equal(read, torch.zeros_like(read))

    # and it is functionally the GRU on the same start
    turns = [[[3 + i, 4 + i, 5 + i] for i in range(3)]]
    gaps = [[120.0, 60.0, 240.0]]
    gru_state, gru_hidden = stage.run_session(gru, turns, gaps)
    cache_state, _ = stage.run_session(off, turns, gaps)
    assert torch.equal(gru_hidden, cache_state.tensors["h"])
    assert stage.generate_bytes(gru, gru_hidden) == stage.generate_bytes(
        off, dict(cache_state.tensors)
    )


def test_ai_step_grows_the_cache_once_per_token_and_al_step_leaves_it_alone(stage, torch):
    gru, cache, _ = _pair(stage)
    state = cache.init_state(2)
    logits, state = cache.ai_step(torch.as_tensor([[7, 8, 9], [10, 11, 12]]), state)
    assert tuple(logits.shape) == (2, 3, TOKENS)
    assert int(state.tensors["ck"].shape[1]) == 3
    before = {name: value.clone() for name, value in state.tensors.items()}

    cache.al_step([180.0, 30.0], state)
    assert int(state.tensors["ck"].shape[1]) == 3
    for name in ("ck", "cv", "mask"):
        assert torch.equal(state.tensors[name], before[name])

    gru_state = gru.init_state(2)
    gru_state.tensors["h"] = before["h"]
    gru.al_step([180.0, 30.0], gru_state)
    assert torch.allclose(state.tensors["h"], gru_state.tensors["h"], atol=1e-6)
    assert state.ticks == gru_state.ticks


def test_an_earlier_boundary_does_not_see_later_writes(stage, torch):
    """The auxiliary loss reads every boundary; a shared view would leak."""
    _, cache, _ = _pair(stage)
    short = [[[3 + i, 4 + i] for i in range(3)]]
    long = [[[3 + i, 4 + i] for i in range(3)] + [[60, 61, 62]]]
    gaps = [[120.0, 60.0, 240.0]]
    early = []
    stage.run_session(cache, short, gaps, boundaries=early)
    late = []
    stage.run_session(cache, long, [[120.0, 60.0, 240.0, 90.0]], boundaries=late)

    assert isinstance(early[1], dict) and set(early[1]) == {"h", "ck", "cv", "mask"}
    for name in ("h", "ck", "cv", "mask"):
        assert torch.equal(early[1][name], late[1][name])
    # and the later turn did write, so the equality is not "nothing happens"
    assert late[2]["ck"].shape[1] > late[1]["ck"].shape[1]


def test_the_trainer_writes_the_cache_from_the_turn_it_computed(stage, torch):
    _, cache, _ = _pair(stage)
    turns = [[[3, 4], [5, 6], [7, 8], [9, 10]]]
    gaps = [[120.0, 60.0, 120.0, 60.0]]
    state, _ = stage.run_session(cache, turns, gaps)
    # two turns of four tokens each, no padding inside either turn
    assert int(state.tensors["ck"].shape[1]) == 8
    assert state.tensors["mask"].tolist() == [[1.0] * 8]

    # padding inside a turn is marked invalid but keeps positions aligned: the
    # batch is what creates it (a turn is padded to the batch's widest sample)
    ragged = [[[3, 4], [8, 9, 10]], [[3, 4, 5], [8, 9]]]
    state, _ = stage.run_session(cache, ragged, [[120.0, 60.0], [120.0, 60.0]])
    assert state.tensors["mask"].tolist() == [
        [1.0, 1.0, 0.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0, 1.0, 0.0],
    ]
    # and the shorter sample's read ignores the two padded positions
    assert state.tensors["mask"][0].sum().item() == 5.0
    assert state.tensors["mask"][1].sum().item() == 5.0


def test_start_predicate_accepts_the_cache_derivation_and_rejects_a_forgery(stage):
    derived = {
        "checkpoint": stage.L_CHECKPOINT,
        "checkpoint_sha256": stage.L_CHECKPOINT_SHA256,
        "weights_hash": "sha256:" + "0" * 64,
        "params": stage.L_PARAMS + 41_345,
        "derived_from": "tokencache",
        "source_weights_hash": stage.L_WEIGHTS_HASH,
        "hidden": 128,
    }
    assert stage.start_is_stage_l(derived)
    for broken in (
        {**derived, "source_weights_hash": "sha256:" + "f" * 64},
        {**derived, "hidden": 64},
        {**derived, "params": stage.L_PARAMS},
        {**derived, "checkpoint_sha256": "0" * 64},
        {**derived, "derived_from": "gru"},
    ):
        assert not stage.start_is_stage_l(broken)


def test_cli_refuses_combinations_that_change_the_arm(stage):
    assert "tokencache" in stage.STORE_ARMS
    for argv in (
        ["--overfit", "1", "--core", "tokencache", "--hidden", "64"],
        ["--overfit", "1", "--core", "tokencache", "--emb", "32"],
        ["--overfit", "1", "--core", "tokencache", "--widen-to", "256"],
        ["--overfit", "1", "--no-memory"],
    ):
        with pytest.raises(SystemExit):
            stage.main(argv)


def test_weights_hash_survives_a_round_trip(tmp_path, torch):
    from ai.core.stateful_decoder import TokenCacheCore

    core = TokenCacheCore(
        TOKENS, hidden=8, emb=4, slots=4, slot_dim=4, value_dim=4, seed=2, device="cpu"
    )
    path = str(tmp_path / "cache.pt")
    core.save_weights(path)
    digest = core.weights_hash()

    restored = TokenCacheCore(
        TOKENS, hidden=8, emb=4, slots=4, slot_dim=4, value_dim=4, seed=99, device="cpu"
    )
    restored.load_weights(path, strict_config=True)
    assert restored.weights_hash() == digest
    assert restored.config()["model_kind"] == "tokencache"


def test_cache_report_says_how_much_the_cache_dropped(stage):
    """B4 is "cost recorded", and for a cache arm that includes the truncation."""
    sessions = [
        {"turns": [{"user_input": "ab"}, {"user_input": "cd"}]},  # 3 + 3 tokens
        {"turns": [{"user_input": "a"}, {"user_input": "b"}]},  # 2 + 2 tokens
    ]
    report = stage.cache_report(sessions, slots=4)
    assert report["slots"] == 4
    assert report["sessions"] == 2
    assert report["tokens_total"] == 10
    assert report["tokens_dropped"] == 2  # only the first session is over 4
    assert report["sessions_truncated"] == 1
    assert report["max_tokens"] == 6
    assert report["tokens_dropped_share"] == 0.2

    untruncated = stage.cache_report(sessions, slots=64)
    assert untruncated["tokens_dropped"] == 0
    assert untruncated["sessions_truncated"] == 0


def _g_report(stage, core, cache):
    report = {
        "config": {"core": core, "gate_prefix": "G", "memory": True},
        "results": {
            "train_fit": {"exact": 0.95},
            "full": {"chance": 0.1591, "wilson_lower": 0.2, "exact": 0.25},
        },
        "cost": {"params": 168_150, "train_seconds": 10.0, "device": "cpu"},
    }
    if cache is not None:
        report["cost"]["cache"] = cache
    return report


def test_b4_gate_requires_the_cache_cost_only_for_a_cache_arm(stage):
    measured = {
        "heldout": {"slots": 1024, "tokens_dropped": 900},
        "train_subset": {"slots": 1024, "tokens_dropped": 1600},
    }
    assert stage.gate_values(_g_report(stage, "tokencache", measured))["G4_cost_recorded"] is True
    # a cache arm without the cache cost does not pass B4
    assert stage.gate_values(_g_report(stage, "tokencache", None))["G4_cost_recorded"] is False
    # a report missing the dropped count is not "recorded" either
    partial = {"heldout": {"slots": 1024}}
    assert stage.gate_values(_g_report(stage, "tokencache", partial))["G4_cost_recorded"] is False
    # arms before §59 keep their measured verdict (no cache to record)
    assert stage.gate_values(_g_report(stage, "turnstore", None))["G4_cost_recorded"] is True
    assert stage.gate_values(_g_report(stage, "gru", None))["G4_cost_recorded"] is True
