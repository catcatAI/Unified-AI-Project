# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

"""Audit tests for the edge card structural cycle simulator.

The simulator executes the card instead of extrapolating bandwidth ratios,
so these tests prove the engine itself: every hop keeps its invariants,
a replay is bit-identical, the workload totals are consumed exactly,
dependencies never reorder, and - where the local GGUF snapshot exists -
the real gemma-4-E2B tensor table drives 16..N hops without violations.

The synthetic fixture needs no model file; GGUF-backed tests skip when the
Hugging Face snapshot is absent.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from ai.hardware.edge_card_sim import (
    CardConfig,
    Engine,
    TensorInfo,
    build_decode_workload,
    read_gguf_structure,
    workload_totals,
)

GGUF_PATH = (
    Path.home()
    / ".cache/huggingface/hub/models--google--gemma-4-E2B-it-qat-q4_0-gguf"
    / "snapshots/675cff42a74c774d6cb76f76d8eacb49b48c9b93"
    / "gemma-4-E2B_q4_0-it.gguf"
)
requires_gguf = pytest.mark.skipif(
    not GGUF_PATH.is_file(), reason="gemma-4-E2B QAT Q4_0 GGUF snapshot not present"
)


def _synthetic_structure() -> dict:
    """2-layer toy model: layer0 owns KV, layer1 shares (no attn_k/v)."""
    kv = {
        "gemma4.block_count": 2,
        "gemma4.attention.head_count": 2,
        "gemma4.attention.sliding_window_pattern": [1, 0],
    }
    tensors: list[TensorInfo] = []

    def t(name: str, dims: list[int], nbytes: int, tid: int = 2) -> None:
        tensors.append(TensorInfo(name=name, dims=dims, type_id=tid, offset=0, nbytes=nbytes))

    t("token_embd.weight", [16, 64], 563)
    t("per_layer_token_embd.weight", [32, 64], 1408)
    t("per_layer_model_proj.weight", [16, 32], 512)
    t("blk.0.attn_q.weight", [16, 8], 70)
    t("blk.0.attn_k.weight", [16, 4], 35)
    t("blk.0.attn_v.weight", [16, 4], 35)
    t("blk.0.attn_norm.weight", [16], 64, tid=1)
    t("blk.0.ffn_gate.weight", [16, 32], 281)
    t("blk.0.ffn_down.weight", [32, 16], 281)
    t("blk.1.attn_q.weight", [16, 16], 140)
    t("blk.1.attn_norm.weight", [16], 64, tid=1)
    t("blk.1.ffn_gate.weight", [16, 32], 281)
    t("blk.1.ffn_down.weight", [32, 16], 281)
    return {"kv": kv, "tensors": tensors}


@pytest.fixture
def structure() -> dict:
    return _synthetic_structure()


@pytest.fixture
def cfg() -> CardConfig:
    return CardConfig()


# -----------------------------------------------------------------------------
# workload builder (structure straight from the tensor table)
# -----------------------------------------------------------------------------
def test_workload_shape_and_kinds(structure: dict, cfg: CardConfig) -> None:
    items = build_decode_workload(structure, cfg, ctx=8, token_index=0, base_idx=0)

    kinds = [i.kind for i in items]
    assert kinds[0] == "read" and kinds[1] == "read", "embed/ple gathers first"
    assert kinds[-1] == "pcie", "token emission is last"
    # kv write exists exactly once (layer0 owns KV) and depends on its kv_rd
    writes = [i for i in items if i.kind == "write"]
    assert [w.name for w in writes] == ["kv_wr.L0"]
    kv_rd = next(i for i in items if i.name == "kv_rd.L0")
    assert writes[0].ready_after == kv_rd.idx
    # shared-KV layer (1) must NOT write
    assert not any(i.name == "kv_wr.L1" for i in items)


def test_workload_totals_are_consistent(structure: dict, cfg: CardConfig) -> None:
    items = build_decode_workload(structure, cfg, ctx=8, token_index=0, base_idx=0)
    totals = workload_totals(items)

    assert totals["items"] == len(items)
    assert totals["bytes"] == sum(i.nbytes for i in items)
    assert totals["ops"] == sum(i.ops for i in items)
    assert totals["reads"] + totals["writes"] + totals["pcie"] == totals["bytes"]


# -----------------------------------------------------------------------------
# engine: invariants, determinism, exactness, dependency order
# -----------------------------------------------------------------------------
def test_sixteen_hops_pass_every_invariant(structure: dict, cfg: CardConfig) -> None:
    eng = Engine(structure, cfg, ctx_start=8)
    eng.run_hops(16)

    assert eng.hops == 16
    assert eng.violations == []
    assert eng.t > 0


def test_replay_is_bit_identical(structure: dict, cfg: CardConfig) -> None:
    a = Engine(structure, cfg, ctx_start=8)
    b = Engine(structure, cfg, ctx_start=8)
    for _ in range(400):
        assert a.step() == b.step()
    assert a.digest() == b.digest()
    assert a.violations == [] and b.violations == []


def test_workload_consumed_exactly_at_token_boundary(structure: dict, cfg: CardConfig) -> None:
    eng = Engine(structure, cfg, ctx_start=8)
    eng.run_until_tokens(4)

    assert eng.tokens_done == 4
    expected = {"mem_r": 0.0, "mem_w": 0.0, "macs": 0.0, "pcie": 0.0}
    for tk in range(4):
        tt = workload_totals(build_decode_workload(structure, cfg, 8 + tk, tk, 0))
        expected["mem_r"] += tt["reads"]
        expected["mem_w"] += tt["writes"]
        expected["macs"] += tt["ops"]
        expected["pcie"] += tt["pcie"]
    for key, exp in expected.items():
        assert eng.done_cum[key] == exp, f"{key}: {eng.done_cum[key]} != {exp}"


def test_write_waits_for_its_dependency(structure: dict, cfg: CardConfig) -> None:
    eng = Engine(structure, cfg, ctx_start=8)
    eng.run_until_tokens(2)

    kv_rd = next(i for i in build_decode_workload(structure, cfg, 8, 0, 0) if i.name == "kv_rd.L0")
    kv_wr = next(i for i in build_decode_workload(structure, cfg, 8, 0, 0) if i.name == "kv_wr.L0")
    assert eng.done_times[kv_wr.idx] >= eng.done_times[kv_rd.idx]


def test_pcie_emission_is_the_last_event_of_the_token(structure: dict, cfg: CardConfig) -> None:
    eng = Engine(structure, cfg, ctx_start=8)
    eng.run_until_tokens(2)

    token0 = build_decode_workload(structure, cfg, 8, 0, 0)
    pcie_idx = token0[-1].idx
    others = [eng.done_times[i.idx] for i in token0 if i.kind != "pcie"]
    assert eng.done_times[pcie_idx] >= max(others)


def test_step_past_end_raises(structure: dict, cfg: CardConfig) -> None:
    eng = Engine(structure, cfg, ctx_start=8)
    eng.mem_idx = len(eng.items)
    eng.comp_idx = len(eng.items)
    eng.write_pending = []
    with pytest.raises(RuntimeError, match="past end"):
        eng.step()


def test_no_progress_watchdog_trips_on_frozen_state(structure: dict, cfg: CardConfig) -> None:
    eng = Engine(structure, cfg, ctx_start=8)
    # freeze memory (rate 0) while compute sits starved: the engine must
    # raise instead of spinning on dt==0 forever
    frozen = CardConfig(mem_util=0.0)
    eng.cfg = frozen
    with pytest.raises(RuntimeError):
        for _ in range(50):
            eng.step()


# -----------------------------------------------------------------------------
# GGUF-backed (skipped when the snapshot is not on this machine)
# -----------------------------------------------------------------------------
@requires_gguf
def test_gguf_structure_tiles_exactly() -> None:
    st = read_gguf_structure(GGUF_PATH)

    assert len(st["tensors"]) == 541
    assert st["kv"]["general.architecture"] == "gemma4"
    assert st["kv"]["gemma4.block_count"] == 35
    data_bytes = st["file_size"] - (
        (st["info_end"] + st["kv"].get("general.alignment", 32) - 1)
        // st["kv"].get("general.alignment", 32)
        * st["kv"].get("general.alignment", 32)
    )
    assert sum(t.nbytes for t in st["tensors"]) == data_bytes


@requires_gguf
def test_real_workload_shape() -> None:
    st = read_gguf_structure(GGUF_PATH)
    cfg = CardConfig()
    items = build_decode_workload(st, cfg, ctx=32768, token_index=0, base_idx=0)

    assert sum(1 for i in items if i.kind == "write") == 15, "layers 0-14 own KV"
    assert sum(1 for i in items if i.kind == "read") == 2
    assert sum(1 for i in items if i.kind == "pcie") == 1
    totals = workload_totals(items)
    assert 1.3e9 < totals["reads"] < 1.8e9, f"reads={totals['reads']}"
    assert 3.5e9 < totals["ops"] < 5.0e9, f"macs={totals['ops']}"


@requires_gguf
def test_real_gguf_run_is_clean_and_deterministic() -> None:
    cfg = CardConfig()
    st = read_gguf_structure(GGUF_PATH)
    a = Engine(st, cfg, ctx_start=32768, trace_first=16)
    b = Engine(st, cfg, ctx_start=32768)
    for _ in range(600):
        a.step()
        b.step()
    assert a.violations == []
    assert a.digest() == b.digest()
    assert a.t > 0
