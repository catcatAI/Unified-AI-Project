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

import math
import struct
from pathlib import Path

import pytest
from ai.hardware.edge_card_sim import (
    CardConfig,
    Engine,
    Item,
    TensorInfo,
    _gguf_tile_nbytes,
    build_decode_workload,
    read_gguf_structure,
    run_prefload,
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


# -----------------------------------------------------------------------------
# GGUF reader error paths (the valid file is covered above; these pin the
# refusals, because a parser that accepts a truncated/wrong file silently
# produces a workload from garbage instead of failing).
# -----------------------------------------------------------------------------
def test_read_gguf_rejects_bad_magic(tmp_path: Path) -> None:
    path = tmp_path / "bad_magic.gguf"
    path.write_bytes(struct.pack("<IIQQ", 0x12345678, 3, 0, 0))
    with pytest.raises(ValueError, match="not a GGUF file"):
        read_gguf_structure(path)


def test_read_gguf_reports_truncation(tmp_path: Path) -> None:
    path = tmp_path / "truncated.gguf"
    # Header claims one key/value pair but the file ends immediately.
    path.write_bytes(struct.pack("<IIQQ", 0x46554747, 3, 0, 1))
    with pytest.raises(EOFError, match="truncated"):
        read_gguf_structure(path)


def test_read_gguf_rejects_an_unknown_value_type(tmp_path: Path) -> None:
    path = tmp_path / "bad_type.gguf"
    blob = struct.pack("<IIQQ", 0x46554747, 3, 0, 1)
    blob += struct.pack("<Q", 1) + b"k" + struct.pack("<I", 99)
    path.write_bytes(blob)
    with pytest.raises(ValueError, match="unsupported gguf value type 99"):
        read_gguf_structure(path)


def test_gguf_tile_rejects_offsets_past_the_data_section() -> None:
    # offset 4 with an empty data section gives a negative tile, so the sum
    # cannot equal the accounted bytes: the reader must refuse the file.
    tensor = TensorInfo(name="x", dims=[1], type_id=2, offset=4, nbytes=0)
    with pytest.raises(ValueError, match="tile the data section exactly"):
        _gguf_tile_nbytes([tensor], data_start=0, file_size=0)


# -----------------------------------------------------------------------------
# Derived config values and the report/preload helpers
# -----------------------------------------------------------------------------
def test_card_config_derived_values_and_frequency_table() -> None:
    cfg = CardConfig()
    assert cfg.nvme_bytes_per_ns == cfg.nvme_gbs
    table = cfg.frequency_table()
    assert len(table) == 5
    assert table[0][0] == "LPDDR5 bus"
    assert "B/ns" in table[0][2]


def test_item_bytes_per_op_is_zero_for_an_ops_free_item() -> None:
    assert Item(idx=0, name="meta", kind="read", nbytes=8, ops=0).bytes_per_op == 0.0


def test_make_report_and_preload_read_the_same_rates(cfg: CardConfig) -> None:
    eng = _engine(cfg)
    report = eng.make_report([], {})
    assert report.ok is True
    assert report.consumed == {"reads": 0, "writes": 0, "pcie": 0}
    assert report.utilization["mem_service"] == 0.0
    assert report.utilization["mac_array"] == 0.0
    assert report.utilization["pcie"] == 0.0

    rate = min(cfg.nvme_bytes_per_ns, cfg.mem_service_bytes_per_ns)
    assert run_prefload({"kv": {}, "tensors": []}, cfg, file_bytes=1_000_000) == 1_000_000 / rate


def _engine(cfg: CardConfig | None = None) -> Engine:
    return Engine(_synthetic_structure(), cfg or CardConfig(), ctx_start=8)


def _stream_index(eng: Engine) -> int:
    return next(k for k, item in enumerate(eng.items) if item.kind == "stream" and item.ops > 0)


# -----------------------------------------------------------------------------
# Invariant checks: every refusal has to name its own cause, otherwise a real
# violation is reported as an anonymous list entry.
# -----------------------------------------------------------------------------
def test_ceiling_checks_name_each_violation() -> None:
    eng = _engine()
    eng.t = float("nan")
    assert any("time not finite" in v for v in eng.check_invariants())

    eng.t = 1.0
    eng.sram = -5.0
    violations = eng.check_invariants()
    assert any("SRAM out of bounds" in v for v in violations)

    eng.sram = 0.0
    eng.cum["mem_r"] = eng.cfg.mem_raw_bytes_per_ns * 10.0
    violations = eng.check_invariants()
    assert "mem exceeded serviced ceiling" in violations
    assert "mem exceeded PHYSICAL LPDDR5 ceiling" in violations

    eng.cum["mem_r"] = 0.0
    eng.cum["macs"] = eng.cfg.mac_per_ns * 10.0
    assert "MAC array exceeded dense ceiling" in eng.check_invariants()

    eng.cum["macs"] = 0.0
    eng.cum["pcie"] = eng.cfg.pcie_bytes_per_ns * 10.0
    assert "PCIe exceeded Gen4 x1 ceiling" in eng.check_invariants()


def test_item_checks_name_each_violation() -> None:
    fetched = _engine()
    item = fetched.items[0]
    fetched.fetched[item.idx] = item.nbytes + 1.0
    assert any("fetched > required" in v for v in fetched.check_invariants())

    over_ops = _engine()
    stream = over_ops.items[_stream_index(over_ops)]
    over_ops.ops_done[stream.idx] = stream.ops + 1.0
    assert any("ops > required" in v for v in over_ops.check_invariants())

    over_consumed = _engine()
    item = over_consumed.items[0]
    over_consumed.consumed[item.idx] = item.nbytes + 1.0
    assert any("consumed > fetched" in v for v in over_consumed.check_invariants())

    decoupled = _engine()
    stream = decoupled.items[_stream_index(decoupled)]
    decoupled.fetched[stream.idx] = 10.0
    decoupled.consumed[stream.idx] = 10.0
    decoupled.ops_done[stream.idx] = 0.0
    assert any("ops/bytes decoupled" in v for v in decoupled.check_invariants())


def test_frontier_and_bookkeeping_violations_are_reported() -> None:
    frontier = _engine()
    index = _stream_index(frontier)
    frontier.comp_idx = index + 1
    frontier.item_done.discard(frontier.items[index].idx)
    assert any("past compute frontier but not done" in v for v in frontier.check_invariants())

    mismatch = _engine()
    mismatch.sram = 5.0
    assert any("SRAM bookkeeping mismatch" in v for v in mismatch.check_invariants())


# -----------------------------------------------------------------------------
# Server candidate / advance / retire edge cases
# -----------------------------------------------------------------------------
def test_cfg_service_exposes_the_memory_rate() -> None:
    eng = _engine()
    assert eng.cfg_service == eng.cfg.mem_service_bytes_per_ns


def test_comp_drain_rate_is_zero_when_nothing_can_be_pulled() -> None:
    eng = _engine()
    eng.comp_idx = len(eng.items)
    assert eng._comp_drain_rate() == 0.0  # past the end

    eng.comp_idx = 0  # read item, not a compute stream
    assert eng._comp_drain_rate() == 0.0

    index = _stream_index(eng)
    eng.comp_idx = index
    item = eng.items[index]
    eng.ops_done[item.idx] = item.ops
    assert eng._comp_drain_rate() == 0.0  # already retired

    eng.ops_done[item.idx] = 0.0
    eng.fetched[item.idx] = 0.0
    eng.consumed[item.idx] = 0.0
    assert eng._comp_drain_rate() == 0.0  # nothing staged yet


def test_comp_retire_ready_ops_only_item_uses_the_absolute_residual() -> None:
    eng = _engine()
    item = Item(idx=999, name="softmax", kind="stream", nbytes=0, ops=100)
    eng.fetched[999] = 0.0
    eng.consumed[999] = 0.0
    eng.ops_done[999] = 100.0 - 1e-9
    assert eng._comp_retire_ready(item) is True
    eng.ops_done[999] = 50.0
    assert eng._comp_retire_ready(item) is False


def test_mem_candidate_stops_when_scratchpad_is_full_and_compute_stalls() -> None:
    eng = _engine()
    index = _stream_index(eng)
    eng.mem_idx = index
    eng.comp_idx = index  # same item: nothing fetched yet, so drain is zero
    eng.sram = float(eng.cfg.sram_bytes)
    candidate, rate, target = eng._step_candidate_mem(eng.cfg.mac_per_ns)
    assert candidate is None and rate == 0.0 and target is not None


def test_comp_candidate_handles_past_end_and_a_ready_retire() -> None:
    eng = _engine()
    eng.comp_idx = len(eng.items)
    assert eng._step_candidate_comp(eng.cfg.mac_per_ns) is None

    index = _stream_index(eng)
    eng.comp_idx = index
    item = eng.items[index]
    eng.fetched[item.idx] = item.nbytes
    eng.consumed[item.idx] = item.nbytes
    eng.ops_done[item.idx] = item.ops
    candidate = eng._step_candidate_comp(eng.cfg.mac_per_ns)
    assert candidate is not None
    assert candidate[0] == 0.0 and candidate[1] == "comp_done"


def test_advance_comp_past_end_is_a_no_op() -> None:
    eng = _engine()
    eng.comp_idx = len(eng.items)
    assert eng._step_advance_comp(1.0) == 0.0


def test_retire_mem_folds_a_write_residual_into_the_counter() -> None:
    eng = _engine()
    write = next(item for item in eng.items if item.kind == "write")
    eng.fetched[write.idx] = write.nbytes - 1e-9
    before = eng.cum["mem_w"]
    events: list[str] = []
    eng._step_retire_mem(write, events)
    assert eng.cum["mem_w"] > before
    assert write.idx in eng.item_done
    assert any(event.startswith("mem_write_done") for event in events)


def test_retire_past_end_and_unfinished_pcie_are_no_ops() -> None:
    eng = _engine()
    eng.comp_idx = len(eng.items)
    eng._step_retire_comp([])  # past the end: no exception, no event

    pcie = next(item for item in eng.items if item.kind == "pcie")
    eng.pcie_busy = pcie.idx
    eng.fetched[pcie.idx] = pcie.nbytes - 1.0
    events: list[str] = []
    eng._step_retire_pcie(events)
    assert events == [] and pcie.idx not in eng.item_done


def test_collect_cands_returns_an_empty_set_when_complete() -> None:
    eng = _engine()
    eng.mem_idx = len(eng.items)
    eng.comp_idx = len(eng.items)
    eng.write_pending = []
    eng.pcie_busy = None
    assert eng._step_collect_cands(eng.cfg.mac_per_ns) == ([], 0.0, None, 0.0)


def test_collect_cands_rejects_a_non_finite_step() -> None:
    eng = _engine()
    eng._step_candidate_mem = lambda rate: (None, 0.0, None)
    eng._step_candidate_comp = lambda rate: None
    eng._step_candidate_pcie = lambda: (math.inf, "pcie_done", eng.items[-1])
    with pytest.raises(RuntimeError, match="non-finite step dt"):
        eng._step_collect_cands(eng.cfg.mac_per_ns)


# -----------------------------------------------------------------------------
# step() watchdogs and the report guard
# -----------------------------------------------------------------------------
def test_step_raises_when_a_hop_changes_nothing() -> None:
    eng = _engine()
    eng.mem_idx = len(eng.items)
    eng.comp_idx = len(eng.items)
    # A pending write keeps the token incomplete, so step() reaches the
    # watchdog instead of the "past end" guard.
    eng._step_structural = lambda events: False
    eng._step_collect_cands = lambda rate: ([(0.0, "mem_done", eng.items[0])], 0.0, None, 0.0)
    with pytest.raises(RuntimeError, match="NO-PROGRESS"):
        eng.step()


def test_step_keeps_invariant_violations_in_the_report() -> None:
    eng = _engine()
    eng.check_invariants = lambda: ["synthetic violation"]
    eng.step()
    assert eng.violations
    assert eng.violations[0].startswith("hop ") and "synthetic violation" in eng.violations[0]


def test_run_until_tokens_stops_a_simulator_that_never_finishes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ai.hardware.edge_card_sim as sim

    monkeypatch.setattr(sim, "RUN_GUARD", 3)
    eng = _engine()
    eng.step = lambda: None
    with pytest.raises(RuntimeError, match="runaway simulation"):
        eng.run_until_tokens(1)
