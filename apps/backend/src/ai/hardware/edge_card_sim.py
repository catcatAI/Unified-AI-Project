# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

"""Structural discrete-event simulator for the edge card (hardware/edge_card).

Unlike bandwidth-ratio extrapolations, this module *executes* the card: the
model is partitioned by bit-width and clock into the simulated components
(LPDDR5-128b@6400MT/s, INT8 MAC array, bounded SRAM queue, PCIe Gen4 x1,
M.2 NVMe), the Gemma-4 workload is cut into items straight from the GGUF
tensor table (exact bytes from tensor offsets, MACs from tensor dims), and a
two-server event engine advances time hop by hop with per-hop invariants
(physical ceilings, buffer bounds, dependency ordering, progress).

Run it first for a handful of hops, then hundreds, thousands, ten-thousands,
then across full decode tokens; the run is valid only if every hop passes
every invariant, the workload totals are consumed exactly, and a replay is
bit-identical (deterministic digest).

Deliberate modelling choices (all are config, not hidden magic):
  * LPDDR5 service rate = raw rate x mem_util (refresh/bank-turnaround loss;
    raw physical rate is also enforced as a hard ceiling).
  * dense TOPS convention: spec's "50 dense INT8 TOPS @25W" is read
    conservatively as 2 ops per MAC -> mac_per_ns = 25 (override via
    `mac_convention`).
  * KV element bytes default to int8 (spec's @32K budget), f16 via config.
  * The tied lm_head streams the full token_embd matrix each token (no
    top-k shortcut assumed), which is the conservative real path.
"""

from __future__ import annotations

import hashlib
import math
import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

EPS = 1e-6


# -----------------------------------------------------------------------------
# GGUF structure reader (v3, verified: google q4_0 snapshot has NO padding
# between tensor infos and a 32-aligned data section)
# -----------------------------------------------------------------------------
@dataclass
class TensorInfo:
    name: str
    dims: list[int]
    type_id: int
    offset: int
    nbytes: int

    @property
    def macs(self) -> int:
        """MAC count if this tensor is streamed as a matmul/matvec this token."""
        prod = 1
        for d in self.dims:
            prod *= d
        return prod


_GGUF_VAL_FMT = {
    0: "B",
    1: "b",
    2: "H",
    3: "h",
    4: "I",
    5: "i",
    6: "f",
    7: "B",
    10: "Q",
    11: "q",
    12: "d",
}


def read_gguf_structure(path: str | Path) -> dict[str, Any]:
    """Return {'kv': dict, 'tensors': [TensorInfo sorted by offset], 'info_end': int}."""
    path = Path(path)
    file_size = path.stat().st_size
    with path.open("rb") as f:

        def rf(fmt: str) -> tuple:
            raw = f.read(struct.calcsize("<" + fmt))
            if len(raw) < struct.calcsize("<" + fmt):
                raise EOFError(f"gguf truncated while reading {fmt}")
            return struct.unpack("<" + fmt, raw)

        def rstr() -> str:
            (n,) = rf("Q")
            return f.read(n).decode("utf-8", "replace")

        def rval(t: int) -> Any:
            if t == 8:
                return rstr()
            if t == 9:
                (elem_t,) = rf("I")
                (count,) = rf("Q")
                return [rval(elem_t) for _ in range(count)]
            if t not in _GGUF_VAL_FMT:
                raise ValueError(f"unsupported gguf value type {t}")
            return rf(_GGUF_VAL_FMT[t])[0]

        magic, version, n_tensors, n_kv = rf("IIQQ")
        if magic != 0x46554747:
            raise ValueError(f"not a GGUF file: {path}")
        kv: dict[str, Any] = {}
        for _ in range(n_kv):
            key = rstr()
            (vtype,) = rf("I")
            kv[key] = rval(vtype)
        info_start = f.tell()
        tensors: list[TensorInfo] = []
        for _ in range(n_tensors):
            name = rstr()
            (nd,) = rf("I")
            dims = [rf("Q")[0] for _ in range(nd)]
            (type_id,) = rf("I")
            (offset,) = rf("Q")
            tensors.append(
                TensorInfo(name=name, dims=dims, type_id=type_id, offset=offset, nbytes=0)
            )
        info_end = f.tell()
        alignment = kv.get("general.alignment", 32)
        data_start = (info_end + alignment - 1) // alignment * alignment
        tensors.sort(key=lambda t: t.offset)
        for i, t in enumerate(tensors):
            end = tensors[i + 1].offset if i + 1 < len(tensors) else file_size - data_start
            t.nbytes = end - t.offset
        accounted = (file_size - data_start) if tensors else 0
        if tensors and sum(t.nbytes for t in tensors) != accounted:
            raise ValueError("tensor offsets do not tile the data section exactly")
        return {"kv": kv, "tensors": tensors, "info_end": info_end, "file_size": file_size}


# -----------------------------------------------------------------------------
# Card configuration (bit widths and frequencies live here)
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class CardConfig:
    # --- memory: LPDDR5-128bit @ 6400 MT/s -> 16 B per 0.15625 ns = 102.4 B/ns
    lpddr5_width_bit: int = 128
    lpddr5_data_rate_mts: int = 6400
    mem_util: float = 0.85
    # --- compute: dense 50 INT8 TOPS @25W, conservative 2 ops per MAC
    int8_dense_tops: float = 50.0
    mac_convention: int = 2
    # --- host link: PCIe Gen4 x1, 128b/130b @16GT/s -> 1.969231 B/ns payload
    pcie_payload_gbs: float = 1.969231
    # --- on-card storage: M.2 NVMe path used for preload
    nvme_gbs: float = 1.6
    # --- SRAM/scratchpad queue between memory and MAC array
    sram_bytes: int = 1_048_576
    # --- KV cache element width (spec: int8 @32K budget)
    kv_elem_bytes: int = 1
    swa_window: int = 512
    # --- display clocks (cycle accounting only)
    mac_ghz: float = 1.3
    lpddr5_ghz: float = 6.4
    pcie_gtps: float = 16.0

    @property
    def mem_raw_bytes_per_ns(self) -> float:
        return self.lpddr5_width_bit / 8 * self.lpddr5_data_rate_mts / 1000.0

    @property
    def mem_service_bytes_per_ns(self) -> float:
        return self.mem_raw_bytes_per_ns * self.mem_util

    @property
    def mac_per_ns(self) -> float:
        return self.int8_dense_tops / self.mac_convention

    @property
    def pcie_bytes_per_ns(self) -> float:
        return self.pcie_payload_gbs

    @property
    def nvme_bytes_per_ns(self) -> float:
        return self.nvme_gbs

    def frequency_table(self) -> list[tuple[str, str, str]]:
        return [
            (
                "LPDDR5 bus",
                f"{self.lpddr5_width_bit}b @ {self.lpddr5_data_rate_mts} MT/s",
                f"{self.mem_raw_bytes_per_ns:.2f} B/ns raw, {self.mem_service_bytes_per_ns:.2f} B/ns serviced",
            ),
            (
                "INT8 MAC array",
                f"dense {self.int8_dense_tops} TOPS ({self.mac_convention} ops/MAC)",
                f"{self.mac_per_ns:.2f} MAC/ns, {self.mac_per_ns / self.mac_ghz:.2f} MAC/clk @ {self.mac_ghz} GHz",
            ),
            (
                "PCIe Gen4 x1",
                f"128b/130b @ {self.pcie_gtps} GT/s",
                f"{self.pcie_bytes_per_ns:.3f} B/ns payload",
            ),
            ("M.2 NVMe", "x2 path", f"{self.nvme_bytes_per_ns:.2f} B/ns"),
            ("SRAM queue", f"{self.sram_bytes} B", "mem->MAC staging bound"),
        ]


# -----------------------------------------------------------------------------
# Workload items
# -----------------------------------------------------------------------------
@dataclass
class Item:
    idx: int
    name: str
    kind: str  # 'stream' | 'read' | 'write' | 'pcie'
    nbytes: int
    ops: int
    ready_after: int = -1  # 'write': compute must have completed this idx first
    token: int = 0

    @property
    def bytes_per_op(self) -> float:
        if self.ops <= 0:
            return 0.0
        return self.nbytes / self.ops


def build_decode_workload(
    structure: dict[str, Any], cfg: CardConfig, ctx: int, token_index: int, base_idx: int
) -> list[Item]:
    """Cut one decode step into hardware items straight from the tensor table.

    Bit widths: weights Q4_0/F16/F32 exactly as stored (nbytes from offsets),
    KV at cfg.kv_elem_bytes, tied lm_head streams the full token_embd matrix.
    """
    kv = structure["kv"]
    tensors: list[TensorInfo] = structure["tensors"]
    by_name = {t.name: t for t in tensors}
    n_layers: int = kv["gemma4.block_count"]
    n_heads: int = kv["gemma4.attention.head_count"]
    pattern: list[int] = kv["gemma4.attention.sliding_window_pattern"]
    n_vocab = max(t.dims[-1] for t in tensors if t.name.endswith("token_embd.weight"))
    items: list[Item] = []

    def add(name: str, kind: str, nbytes: int, ops: int, ready_after: int = -1) -> Item:
        item = Item(
            idx=base_idx + len(items),
            name=name,
            kind=kind,
            nbytes=int(nbytes),
            ops=int(ops),
            ready_after=ready_after,
            token=token_index,
        )
        items.append(item)
        return item

    embed = by_name["token_embd.weight"]
    ple_table = by_name["per_layer_token_embd.weight"]
    add("embed_gather", "read", embed.nbytes // embed.dims[-1], 0)
    add("ple_row_gather", "read", ple_table.nbytes // ple_table.dims[-1], 0)
    ple_proj = by_name["per_layer_model_proj.weight"]
    add("ple_model_proj", "stream", ple_proj.nbytes, ple_proj.macs)

    for layer in range(n_layers):
        prefix = f"blk.{layer}."
        q = by_name[prefix + "attn_q.weight"]
        head_dim = q.dims[1] // n_heads
        is_full = pattern[layer] == 0  # 0 = full attention (head_dim 512), 1 = sliding (256)
        window = ctx if is_full else min(ctx, cfg.swa_window)
        kv_dim = head_dim  # 1 KV head
        q_out = q.dims[1]

        kv_rd = add(
            f"kv_rd.L{layer}",
            "stream",
            window * kv_dim * 2 * cfg.kv_elem_bytes,
            2 * window * q_out,
        )
        has_own_kv = prefix + "attn_k.weight" in by_name
        if has_own_kv:
            add(
                f"kv_wr.L{layer}",
                "write",
                kv_dim * 2 * cfg.kv_elem_bytes,
                0,
                ready_after=kv_rd.idx,
            )
        for t in tensors:
            if t.name.startswith(prefix):
                add(t.name, "stream", t.nbytes, t.macs)

    add("lm_head_tied", "stream", embed.nbytes, embed.macs)
    add("softmax_logits", "stream", 0, n_vocab)
    add("pcie_emit_token", "pcie", 8, 0)
    return items


def workload_totals(items: list[Item]) -> dict[str, int]:
    return {
        "items": len(items),
        "bytes": sum(i.nbytes for i in items),
        "ops": sum(i.ops for i in items),
        "reads": sum(i.nbytes for i in items if i.kind in ("read", "stream")),
        "writes": sum(i.nbytes for i in items if i.kind == "write"),
        "pcie": sum(i.nbytes for i in items if i.kind == "pcie"),
    }


# -----------------------------------------------------------------------------
# Discrete-event engine: memory + compute + PCIe servers, continuous advance
#
# Each step() = one hop:
#   (A) zero-time structural transitions: the memory index walks past write
#       and pcie items (those are served out-of-band), a ready write starts
#       only while the memory server is between items (non-preemptive),
#       compute skips read/write items WITHOUT marking them done (memory
#       retires those), and the PCIe head starts once every earlier item is
#       done.
#   (B) candidate thresholds -> dt = min: memory completion (capped by SRAM
#       room, paced by the compute drain when the scratchpad is full),
#       compute done/starve (starve is a positive-dt pause, never dt==0),
#       PCIe completion.
#   (C) continuous advance over dt for ALL servers at once: memory serves
#       its target at its (possibly paced) rate, compute consumes staged
#       bytes at the MAC rate bounded by availability, PCIe streams.
#   (D) thresholds that fired are retired exactly; bytes/ops enter the
#       counters ONLY in phase (C), so nothing is double counted.
#
# A dt==0 hop must change state (defensive completions, structural moves);
# otherwise the no-progress watchdog raises - this guards against livelocks
# such as a starving compute server with nothing feeding it.
# -----------------------------------------------------------------------------
@dataclass
class HopRecord:
    hop: int
    t_ns: float
    event: str
    detail: str
    sram_bytes: int
    mem_idx: int
    comp_idx: int


@dataclass
class SimReport:
    ok: bool
    violations: list[str]
    hops: int
    tokens: int
    t_end_ns: float
    checkpoints: list[dict[str, Any]]
    digests: dict[int, str]
    per_token_ms: list[float]
    totals: dict[str, int]
    consumed: dict[str, int]
    utilization: dict[str, float]
    trace: list[HopRecord]
    kv_ctx_end: int


class Engine:
    def __init__(
        self, structure: dict[str, Any], cfg: CardConfig, ctx_start: int, trace_first: int = 0
    ):
        self.structure = structure
        self.cfg = cfg
        self.ctx = ctx_start
        self.base_idx = 0
        self.items: list[Item] = build_decode_workload(structure, cfg, ctx_start, 0, 0)
        self.t = 0.0
        self.hops = 0
        self.tokens_done = 0
        self.per_token_ms: list[float] = []
        self.violations: list[str] = []
        self.trace: list[HopRecord] = []
        self.trace_first = trace_first
        self.done_times: dict[int, float] = {}
        # per current-token progress
        self._reset_token_state()
        # cumulative (global)
        self.cum = {"mem_r": 0.0, "mem_w": 0.0, "macs": 0.0, "pcie": 0.0, "nvme": 0.0}
        self.token_start_t = 0.0
        # bumped once per hop in which any server moved bytes/ops: at very
        # high MAC rates dt can fall below ulp(t)/ulp(cum) so the aggregate
        # counters visibly do not change, yet item-local progress is real
        self._progress_marker = 0
        # exactly-consumed totals of COMPLETED tokens (for workload-exactness)
        self.done_cum = {"mem_r": 0.0, "mem_w": 0.0, "macs": 0.0, "pcie": 0.0}
        # integer retire counters: each item contributes its full nbytes/ops
        # EXACTLY once when it retires (sums stay < 2**53 -> float-exact, so
        # done_cum is exact by construction, independent of the float service
        # accumulation in self.cum which is only used for rates/utilization)
        self.exact = {"mem_r": 0, "mem_w": 0, "macs": 0, "pcie": 0}

    # -- token lifecycle ------------------------------------------------------
    def _reset_token_state(self) -> None:
        self.mem_idx = 0
        self.comp_idx = 0
        self.fetched: dict[int, float] = {i.idx: 0.0 for i in self.items}
        self.consumed: dict[int, float] = {i.idx: 0.0 for i in self.items}
        self.ops_done: dict[int, float] = {i.idx: 0.0 for i in self.items}
        self.item_done: set[int] = set()
        self.write_pending: list[int] = [i.idx for i in self.items if i.kind == "write"]
        self.write_in_service: int | None = None
        self.sram = 0.0
        self.pcie_busy: int | None = None

    @property
    def cfg_service(self) -> float:
        return self.cfg.mem_service_bytes_per_ns

    def _item(self, idx: int) -> Item:
        return self.items[idx - self.base_idx]

    def _is_complete(self) -> bool:
        return (
            self.mem_idx >= len(self.items)
            and self.comp_idx >= len(self.items)
            and not self.write_pending
            and self.pcie_busy is None
        )

    def _snapshot(self) -> tuple:
        """State identity for the no-progress watchdog (token-local indices).

        Includes the cumulative service counters and the per-hop progress
        marker: micro-steps (starved-queue pacing at very high MAC rates)
        can advance only item-local state - sometimes while dt is below
        ulp(t), so even t and the aggregates visibly do not change. Those
        are real progress and must not be mistaken for a stall.
        """
        return (
            round(self.t, 9),
            self.tokens_done,
            self.mem_idx,
            self.comp_idx,
            self.pcie_busy,
            self.write_in_service,
            len(self.item_done),
            len(self.write_pending),
            round(self.sram, 3),
            self._progress_marker,
            self.cum["mem_r"],
            self.cum["mem_w"],
            self.cum["macs"],
            self.cum["pcie"],
        )

    # -- helpers --------------------------------------------------------------
    def _record_hop(self, event: str, detail: str) -> None:
        self.hops += 1
        if len(self.trace) < self.trace_first:
            self.trace.append(
                HopRecord(
                    hop=self.hops,
                    t_ns=round(self.t, 6),
                    event=event,
                    detail=detail,
                    sram_bytes=int(self.sram),
                    mem_idx=self.mem_idx,
                    comp_idx=self.comp_idx,
                )
            )

    def check_invariants(self) -> list[str]:
        cfg = self.cfg
        slack_mem = 1.0 + 1e-9 * max(self.t, 1.0)
        out: list[str] = []
        if not math.isfinite(self.t) or self.t < 0:
            out.append(f"time not finite/monotonic: {self.t}")
        if not 0 - EPS <= self.sram <= cfg.sram_bytes + EPS:
            out.append(f"SRAM out of bounds: {self.sram}")
        if (
            self.cum["mem_r"] + self.cum["mem_w"]
            > cfg.mem_service_bytes_per_ns * self.t + slack_mem
        ):
            out.append("mem exceeded serviced ceiling")
        if self.cum["mem_r"] + self.cum["mem_w"] > cfg.mem_raw_bytes_per_ns * self.t + slack_mem:
            out.append("mem exceeded PHYSICAL LPDDR5 ceiling")
        if self.cum["macs"] > cfg.mac_per_ns * self.t + slack_mem:
            out.append("MAC array exceeded dense ceiling")
        if self.cum["pcie"] > cfg.pcie_bytes_per_ns * self.t + slack_mem:
            out.append("PCIe exceeded Gen4 x1 ceiling")
        staged = 0.0
        for i in self.items:
            fetched = self.fetched.get(i.idx, 0.0)
            consumed = self.consumed.get(i.idx, 0.0)
            ops_done = self.ops_done.get(i.idx, 0.0)
            if fetched > i.nbytes + EPS:
                out.append(f"{i.name}: fetched > required")
            if i.ops and ops_done > i.ops + EPS:
                out.append(f"{i.name}: ops > required")
            if consumed > fetched + EPS:
                out.append(f"{i.name}: consumed > fetched")
            if i.kind == "stream":
                staged += fetched - consumed
                if i.nbytes and i.ops:
                    if abs(ops_done * i.bytes_per_op - consumed) > 1e-6 * max(1.0, consumed):
                        out.append(f"{i.name}: ops/bytes decoupled")
        if abs(staged - self.sram) > 1e-3:
            out.append(f"SRAM bookkeeping mismatch: {self.sram} vs staged {staged}")
        for j in range(self.comp_idx):
            it = self.items[j]
            if it.kind in ("stream", "pcie") and it.idx not in self.item_done:
                out.append(f"{it.name}: past compute frontier but not done")
        return out

    # -- event step -----------------------------------------------------------
    def _ready_writes(self) -> list[int]:
        out = []
        for idx in self.write_pending:
            it = self._item(idx)
            if it.ready_after in self.item_done or it.ready_after < 0:
                out.append(idx)
        return out

    def _comp_drain_rate(self) -> float:
        """Bytes/ns the compute server can pull from SRAM right now."""
        if self.comp_idx >= len(self.items):
            return 0.0
        it = self.items[self.comp_idx]
        if it.kind != "stream" or it.nbytes == 0 or not it.ops:
            return 0.0
        if self.ops_done[it.idx] >= it.ops - EPS:
            return 0.0
        if self.fetched[it.idx] - self.consumed[it.idx] <= EPS:
            return 0.0
        return self.cfg.mac_per_ns * it.bytes_per_op

    def _comp_retire_ready(self, it: Item) -> bool:
        """True when a byte-backed compute item is within float noise of done.

        The ops and bytes residuals are checked in WHICHEVER unit is looser
        (byte-scaled: ops_left * bpo <= EPS), because with bpo < 1 the plain
        ops_left <= EPS gate is tighter than the byte gate and would strand
        the item with no candidate (deadlock). Requires memory finished
        feeding, so retiring never jumps `consumed` past `fetched`.
        """
        if self.fetched[it.idx] < it.nbytes - EPS:
            return False  # memory still feeding the tail bytes
        if self.consumed[it.idx] < it.nbytes - EPS:
            return False  # bytes still staged
        ops_left = it.ops - self.ops_done[it.idx]
        if ops_left <= 0:
            return True
        if it.nbytes == 0:  # ops-only item: byte-scaled gate would be vacuous
            return ops_left <= EPS
        # bytes fully consumed already; the ops residual is accumulated
        # float rounding (~1e-4), so bound it RELATIVE to the item size
        # instead of the absolute EPS - a tighter bound would strand the
        # item with no candidate (deadlock).
        tol_bytes = max(EPS, 1e-6 * it.nbytes)
        return ops_left <= EPS or ops_left * it.bytes_per_op <= tol_bytes

    def _structural_pass(self) -> tuple[str | None, bool]:
        """Zero-time transitions. Returns (last event name or None, changed)."""
        n = len(self.items)
        event: str | None = None
        changed = False
        while True:
            progressed = False
            # memory index walks past out-of-band items (write / pcie)
            while self.mem_idx < n and self.items[self.mem_idx].kind in ("write", "pcie"):
                self.mem_idx += 1
                progressed = True
            # a ready write starts only while memory is between items
            # (non-preemptive: never interrupts a read/stream fetch)
            if self.write_in_service is None and self.write_pending:
                mem_idle = (
                    self.mem_idx >= n or self.fetched.get(self.items[self.mem_idx].idx, 0.0) <= EPS
                )
                if mem_idle:
                    for widx in self._ready_writes():
                        self.write_in_service = widx
                        self.fetched.setdefault(widx, 0.0)
                        event = "write_start"
                        progressed = True
                        break
            # compute skips non-compute work in order; read/write are retired
            # by the memory server, so nothing is marked done here
            while self.comp_idx < n and self.items[self.comp_idx].kind in ("read", "write"):
                it = self.items[self.comp_idx]
                self.comp_idx += 1
                event = f"comp_skip:{it.name}"
                progressed = True
            # pcie head: starts when every earlier item is done, link free
            if (
                self.comp_idx < n
                and self.items[self.comp_idx].kind == "pcie"
                and self.pcie_busy is None
                and all(self.items[j].idx in self.item_done for j in range(self.comp_idx))
            ):
                self.pcie_busy = self.items[self.comp_idx].idx
                event = "pcie_start"
                progressed = True
            if not progressed:
                break
            changed = True
        return event, changed

    def step(self) -> str:
        """Advance to the next event. Returns a '+'-joined event name.

        Raises RuntimeError on deadlock (no candidate, no structural change)
        or on a no-progress (dt==0, state unchanged) hop.
        """
        cfg = self.cfg
        m_rate = cfg.mem_service_bytes_per_ns
        c_rate = cfg.mac_per_ns
        n = len(self.items)
        if self._is_complete():
            raise RuntimeError("engine stepped past end of workload")
        before = self._snapshot()

        # ---- (A) zero-time structural transitions ----
        events: list[str] = []
        struct_event, struct_changed = self._structural_pass()
        if struct_event:
            events.append(struct_event)
        elif struct_changed:
            events.append("structural")

        # ---- (B) candidate thresholds -> dt ----
        dt = 0.0
        mem_target: Item | None = None
        mem_rate = 0.0
        if not self._is_complete():
            cands: list[tuple[float, str, Item]] = []

            # memory server target (write priority, non-preemptive)
            if self.write_in_service is not None:
                mem_target = self._item(self.write_in_service)
            elif self.mem_idx < n and self.items[self.mem_idx].kind in ("read", "stream"):
                mem_target = self.items[self.mem_idx]
            if mem_target is not None:
                remaining = mem_target.nbytes - self.fetched.get(mem_target.idx, 0.0)
                if remaining <= EPS:
                    cands.append((0.0, "mem_done", mem_target))
                elif mem_target.kind == "stream":
                    drain = self._comp_drain_rate()
                    room = float(cfg.sram_bytes) - self.sram
                    mem_rate = m_rate
                    if room <= EPS:
                        if drain <= EPS:
                            mem_rate = 0.0  # scratchpad full, compute not pulling
                        else:
                            mem_rate = min(m_rate, drain)  # paced by the drain
                    if mem_rate > 0:
                        t_mem = remaining / mem_rate
                        net = mem_rate - drain
                        if room > EPS and net > EPS:
                            t_mem = min(t_mem, room / net)  # SRAM room exhausts first
                        cands.append((t_mem, "mem_done", mem_target))
                else:  # read / write bypass the scratchpad
                    if m_rate > 0:
                        mem_rate = m_rate
                        cands.append((remaining / m_rate, "mem_done", mem_target))

            # compute server (in-order; read/write already skipped structurally)
            if self.comp_idx < n:
                it = self.items[self.comp_idx]
                if it.kind == "stream":
                    ops_left = it.ops - self.ops_done[it.idx]
                    if it.nbytes == 0:  # ops-only (softmax over the vocab)
                        cands.append((max(ops_left, 0.0) / c_rate, "comp_done", it))
                    elif self._comp_retire_ready(it):
                        cands.append((0.0, "comp_done", it))
                    else:
                        avail = self.fetched[it.idx] - self.consumed[it.idx]
                        if avail > EPS:
                            t_ops = ops_left / c_rate
                            t_bytes = avail / (c_rate * it.bytes_per_op)
                            if t_ops <= t_bytes + EPS:
                                cands.append((t_ops, "comp_done", it))
                            else:
                                # conservative pause: re-evaluate as memory feeds;
                                # never dt==0 (avail > EPS)
                                cands.append((t_bytes, "comp_starve", it))
                        # else starved and unfed: NO dt==0 candidate - memory
                        # must feed first (the old comp_starve dt=0 livelock)

            # pcie server
            if self.pcie_busy is not None:
                it = self._item(self.pcie_busy)
                remaining = it.nbytes - self.fetched.get(it.idx, 0.0)
                cands.append((remaining / cfg.pcie_bytes_per_ns, "pcie_done", it))

            if cands:
                dt = min(c[0] for c in cands)
                if not math.isfinite(dt) or dt < -EPS:
                    raise RuntimeError(f"non-finite step dt={dt}")
                dt = max(dt, 0.0)
                for d, kind, payload in cands:
                    if kind == "comp_starve" and d <= dt + EPS:
                        events.append(f"comp_starve:{payload.name}")
            elif not struct_changed:
                raise RuntimeError(
                    f"DEADLOCK at t={self.t} hops={self.hops} mem={self.mem_idx} "
                    f"comp={self.comp_idx} writes={len(self.write_pending)}"
                )

        # ---- (C) continuous advance over dt for all servers ----
        served_mem = 0.0
        served_ops = 0.0
        served_pcie = 0.0
        if dt > 0:
            self.t += dt
            if mem_target is not None and mem_rate > 0:
                remaining = mem_target.nbytes - self.fetched.get(mem_target.idx, 0.0)
                served = min(remaining, mem_rate * dt)
                if served > 0:
                    served_mem = served
                    self.fetched[mem_target.idx] = self.fetched.get(mem_target.idx, 0.0) + served
                    if mem_target.kind == "write":
                        self.cum["mem_w"] += served
                    else:
                        self.cum["mem_r"] += served
                        if mem_target.kind == "stream":
                            self.sram += served
            if self.comp_idx < n:
                it = self.items[self.comp_idx]
                if it.kind == "stream":
                    add_ops = min(it.ops - self.ops_done[it.idx], c_rate * dt)
                    if it.nbytes > 0:
                        avail = self.fetched[it.idx] - self.consumed[it.idx]
                        add_ops = min(add_ops, avail / it.bytes_per_op)
                    if add_ops > 0:
                        served_ops = add_ops
                        self.ops_done[it.idx] += add_ops
                        add_bytes = add_ops * it.bytes_per_op
                        self.consumed[it.idx] += add_bytes
                        self.cum["macs"] += add_ops
                        if add_bytes > 0:
                            self.sram = max(0.0, self.sram - add_bytes)
            if self.pcie_busy is not None:
                it = self._item(self.pcie_busy)
                remaining = it.nbytes - self.fetched.get(it.idx, 0.0)
                served = min(remaining, cfg.pcie_bytes_per_ns * dt)
                if served > 0:
                    served_pcie = served
                    self.fetched[it.idx] = self.fetched.get(it.idx, 0.0) + served
                    self.cum["pcie"] += served
        if dt > 0 and not events:
            events.append(
                f"flow:mem={served_mem:.0f}B,mac={served_ops:.0f},pcie={served_pcie:.0f}B"
            )
        if served_mem > 0 or served_ops > 0 or served_pcie > 0:
            self._progress_marker += 1

        # ---- (D) retire thresholds hit at exactly self.t ----
        if mem_target is not None:
            it = mem_target
            if it.nbytes - self.fetched.get(it.idx, 0.0) <= EPS:
                # fold the sub-EPS residual into the counters so per-token
                # totals consume the workload bytes EXACTLY
                resid = it.nbytes - self.fetched.get(it.idx, 0.0)
                if resid > 0:
                    if it.kind == "write":
                        self.cum["mem_w"] += resid
                    else:
                        self.cum["mem_r"] += resid
                        if it.kind == "stream":
                            self.sram += resid
                self.fetched[it.idx] = float(it.nbytes)
                if it.kind == "write":
                    self.exact["mem_w"] += it.nbytes
                    self.item_done.add(it.idx)
                    self.done_times[it.idx] = self.t
                    self.write_pending.remove(it.idx)
                    self.write_in_service = None
                    events.append(f"mem_write_done:{it.name}")
                elif it.kind == "read":
                    self.exact["mem_r"] += it.nbytes
                    self.item_done.add(it.idx)
                    self.done_times[it.idx] = self.t
                    self.mem_idx += 1
                    events.append(f"mem_read_done:{it.name}")
                else:  # stream: fetch complete; compute retires it later
                    self.exact["mem_r"] += it.nbytes
                    self.mem_idx += 1
                    events.append(f"fetch_done:{it.name}")
        if self.comp_idx < n:
            it = self.items[self.comp_idx]
            if it.kind == "stream" and self._comp_retire_ready(it):
                # snap residuals so cumulative counters stay exact
                # (ops_done and cum["macs"] grow by identical amounts,
                # so adding the residual back makes the token totals exact)
                resid_ops = it.ops - self.ops_done[it.idx]
                resid_bytes = it.nbytes - self.consumed[it.idx]
                if resid_ops:
                    self.cum["macs"] += resid_ops
                if resid_bytes > 0:
                    self.sram = max(0.0, self.sram - resid_bytes)
                self.ops_done[it.idx] = float(it.ops)
                self.consumed[it.idx] = float(it.nbytes)
                self.exact["macs"] += it.ops
                self.item_done.add(it.idx)
                self.done_times[it.idx] = self.t
                self.comp_idx += 1
                events.append(f"comp_done:{it.name}")
        if self.pcie_busy is not None:
            it = self._item(self.pcie_busy)
            if it.nbytes - self.fetched.get(it.idx, 0.0) <= EPS:
                resid = it.nbytes - self.fetched.get(it.idx, 0.0)
                if resid > 0:
                    self.cum["pcie"] += resid
                self.fetched[it.idx] = float(it.nbytes)
                self.exact["pcie"] += it.nbytes
                self.item_done.add(it.idx)
                self.done_times[it.idx] = self.t
                self.pcie_busy = None
                self.comp_idx += 1
                events.append(f"pcie_done:{it.name}")

        # ---- record, verify, watchdog, finish ----
        self._record_hop("+".join(events) or "advance", "+".join(events))
        if self._snapshot() == before:
            raise RuntimeError(
                f"NO-PROGRESS step at t={self.t} hops={self.hops} "
                f"mem={self.mem_idx} comp={self.comp_idx} (dt={dt})"
            )
        v = self.check_invariants()
        if v:
            self.violations.extend([f"hop {self.hops}: {x}" for x in v])
        if self._is_complete():
            self._finish_token()
        return "+".join(events) or "advance"

    def _finish_token(self) -> None:
        self.per_token_ms.append((self.t - self.token_start_t) / 1e6)
        for k in self.done_cum:
            self.done_cum[k] = float(self.exact[k])
        self.tokens_done += 1
        self.ctx += 1
        self.base_idx += len(self.items)
        self.token_start_t = self.t
        self.items = build_decode_workload(
            self.structure, self.cfg, self.ctx, self.tokens_done, self.base_idx
        )
        self._reset_token_state()

    def run_hops(self, n: int) -> int:
        target = self.hops + n
        while self.hops < target:
            self.step()
        return self.hops

    def run_until_tokens(self, n_tokens: int) -> None:
        guard = 0
        while self.tokens_done < n_tokens:
            self.step()
            guard += 1
            if guard > 10_000_000:
                raise RuntimeError("runaway simulation (>10M hops without token completion)")

    # -- digest / report ------------------------------------------------------
    def digest(self) -> str:
        payload = (
            f"{self.t:.9f}|{self.mem_idx}|{self.comp_idx}|{self.sram:.3f}|"
            f"{self.cum['mem_r']:.3f}|{self.cum['mem_w']:.3f}|{self.cum['macs']:.3f}|"
            f"{len(self.item_done)}|{self.tokens_done}|{self.ctx}"
        )
        return hashlib.sha1(payload.encode()).hexdigest()[:16]

    def make_report(self, checkpoints: list[dict[str, Any]], totals: dict[str, int]) -> SimReport:
        consumed = {
            "reads": round(self.cum["mem_r"]),
            "writes": round(self.cum["mem_w"]),
            "pcie": round(self.cum["pcie"]),
        }
        span = max(self.t, EPS)
        utilization = {
            "mem_service": (self.cum["mem_r"] + self.cum["mem_w"])
            / (self.cfg.mem_service_bytes_per_ns * span),
            "mac_array": self.cum["macs"] / (self.cfg.mac_per_ns * span),
            "pcie": self.cum["pcie"] / (self.cfg.pcie_bytes_per_ns * span),
        }
        return SimReport(
            ok=not self.violations,
            violations=self.violations,
            hops=self.hops,
            tokens=self.tokens_done,
            t_end_ns=self.t,
            checkpoints=checkpoints,
            digests={},
            per_token_ms=self.per_token_ms,
            totals=totals,
            consumed=consumed,
            utilization=utilization,
            trace=self.trace,
            kv_ctx_end=self.ctx,
        )


def run_prefload(structure: dict[str, Any], cfg: CardConfig, file_bytes: int) -> float:
    """NVMe -> LPDDR5 preload phase; returns nanoseconds. Rate = min(nvme, mem write)."""
    rate = min(cfg.nvme_bytes_per_ns, cfg.mem_service_bytes_per_ns)
    return file_bytes / rate
