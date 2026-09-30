# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

"""Audit an architecture summary against measured sky130 process data.

Purpose
-------
A design summary arrives carrying numbers: die and card throughput, transistor
count, L1 capacity, power range, and a headline token rate. Each of those is
either derivable from the process, derivable from the interconnect, or not yet
derivable at all, and the difference matters more than the numbers themselves.

This module does not re-state the claims. It re-derives them from three sources,
keeping each one's provenance explicit:

* **measured here** -- the sky130 unit cell's I-V, its DRC-checked layout
  density, and its noise-limited resolution, all produced by
  :mod:`ai.hardware.cim_strip_reference` and
  :mod:`ai.hardware.cim_primitives`;
* **literature** -- 6T SRAM bitcell area and standard-cell density, which are
  *not* measured in this repository and are labelled as such;
* **claimed** -- the summary's own figures, kept verbatim so a correction is
  always a diff against what was actually asserted.

Provenance is the point. A recomputation that silently mixes a measured density
with a remembered one is worse than the claim it replaces, because it looks
settled. Every density here carries a ``measured`` flag, and the summary reports
which conclusions rest on which.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Sequence

from .cim_strip_reference import CimStripReferenceModel

# =============================================================================
# Densities, each with its provenance
# =============================================================================
# A density is the number every area and cost conclusion rests on, so mixing a
# measured one with a remembered one would be the whole failure this module
# exists to prevent.


@dataclass(frozen=True)
class Density:
    """A per-element silicon density, tagged with where the number came from."""

    um2_per_element: float
    provenance: str
    measured_in_this_repository: bool
    note: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Measured: a magic DRC-clean, extracted dense array of this project's own
# unit cell. The earlier 10.20 um^2 figure came from a 32-cell fixture whose
# routing dominated; the dense array measures 2.16 um^2 per transistor.
ANALOG_CIM_DENSITY = Density(
    um2_per_element=2.16,
    provenance="measured: magic DRC 0 errors, extracted, 1024 nfets on a dense array",
    measured_in_this_repository=True,
    note=(
        "a routed nfet cell with full contact and bus overhead; the bare device "
        "W*L is 0.063 um2, so device area alone understates the real cost by "
        "about 34x"
    ),
)

# Literature: not measured here, and the single largest uncertainty in the area
# conclusions below.
SRAM_6T_BITCELL_DENSITY = Density(
    um2_per_element=0.127,
    provenance="literature: sky130 6T SRAM bitcell, OpenRAM-class",
    measured_in_this_repository=False,
    note=(
        "this single number drives every L1 area and residency conclusion; it "
        "must be replaced with the foundry's own macro figures before any of "
        "them is treated as settled"
    ),
)

DIGITAL_STD_CELL_DENSITY = Density(
    um2_per_element=0.30,
    provenance="literature: sky130_fd_sc_hd standard cell, ~24 transistors per cell",
    measured_in_this_repository=False,
    note="applies to controller, tag, ECC, I/O and sequencer logic, not to the array",
)

# =============================================================================
# Interconnect
# =============================================================================


@dataclass(frozen=True)
class Interconnect:
    """Bandwidth available to one card, and the cost of streaming a model.

    ``pcie_gbs_per_direction`` is the figure already measured and recorded in
    this repository's freeze packet for a Gen5 x16 endpoint, not a recollection.
    """

    pcie_gen: int = 5
    pcie_lanes: int = 16
    pcie_gbs_per_direction: float = 63.015
    independent_channels: int = 2
    ddr_channels: int = 8
    ddr_gbs_per_channel: float = 12.8
    d2d_in_package_gbps: float = 10.0
    dies_per_package: int = 16

    @property
    def card_pcie_gbs(self) -> float:
        return self.pcie_gbs_per_direction * self.independent_channels

    @property
    def card_ddr_gbs(self) -> float:
        return self.ddr_channels * self.ddr_gbs_per_channel

    def as_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["card_pcie_gbs"] = self.card_pcie_gbs
        payload["card_ddr_gbs"] = self.card_ddr_gbs
        return payload


# =============================================================================
# The claimed architecture
# =============================================================================


@dataclass(frozen=True)
class ClaimedArchitecture:
    """A design summary, recorded verbatim so corrections stay diffable."""

    name: str = "dual-layer PCIe CIM card, 8 packages x 16 sky130 dies"
    packages_per_card: int = 8
    dies_per_package: int = 16
    pes_per_die: int = 16384
    pe_transistors: int = 16  # "8x2T" bit-serial PE
    secondary_pes_per_die: int = 1024
    model_parameters: float = 2.0e9
    die_tops: float = 1.2e12
    card_tops: float = 154.0e12
    card_transistors: float = 25.6e9
    array_transistor_fraction: float = 0.0035
    card_l1_mb: float = 180.0
    power_optimistic_w: float = 25.5
    power_pessimistic_w: float = 381.0
    token_latency_s: float = 208.0e-6
    claimed_tokens_per_s: float = 4800.0
    kv_layers: int = 24
    kv_hidden: int = 2048
    kv_context: int = 4096
    weight_bytes: float = 1.0

    @property
    def dies_per_card(self) -> int:
        return self.packages_per_card * self.dies_per_package

    @property
    def transistors_per_die(self) -> float:
        return self.card_transistors / self.dies_per_card

    @property
    def l1_mb_per_die(self) -> float:
        return self.card_l1_mb / self.dies_per_card

    @property
    def array_transistors_per_die(self) -> float:
        return self.transistors_per_die * self.array_transistor_fraction

    @property
    def model_bytes(self) -> float:
        return self.model_parameters * self.weight_bytes

    @property
    def kv_bytes(self) -> float:
        """fp16 key+value for one sequence at the given context."""
        return self.kv_layers * self.kv_hidden * 2 * 2 * self.kv_context

    def as_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "dies_per_card": self.dies_per_card,
                "transistors_per_die": self.transistors_per_die,
                "l1_mb_per_die": self.l1_mb_per_die,
                "model_bytes": self.model_bytes,
                "kv_bytes": self.kv_bytes,
            }
        )
        return payload


# =============================================================================
# The recomputations
# =============================================================================


def weight_streaming(claimed: ClaimedArchitecture, interconnect: Interconnect) -> Dict[str, Any]:
    """What the headline token rate actually costs in weight bandwidth.

    This is the check that decides whether the rest of the numbers matter. In a
    current-mode card the weights live in the array, so every token has to read
    all of them unless they are resident in L1. If they are not resident, the
    card is bandwidth-bound in exactly the way a GPU is, and the token rate
    becomes an interconnect number rather than a compute number.
    """
    model = claimed.model_bytes
    required_gbs = model / claimed.token_latency_s / 1e9
    available = {
        "one_pcie_endpoint": interconnect.pcie_gbs_per_direction,
        "card_pcie_both_channels": interconnect.card_pcie_gbs,
        "card_ddr3": interconnect.card_ddr_gbs,
        "in_package_d2d": interconnect.d2d_in_package_gbps * claimed.dies_per_package / 8.0,
    }
    best_name = max(available, key=lambda key: available[key])
    best = available[best_name]
    resident_fraction = min(1.0, (claimed.card_l1_mb * 1e6) / model) if model else 1.0
    return {
        "model_bytes": model,
        "required_weight_bandwidth_gbs": required_gbs,
        "available_gbs": available,
        "best_path": best_name,
        "best_available_gbs": best,
        "shortfall_x": required_gbs / best if best else float("inf"),
        "achievable_tokens_per_s": best * 1e9 / model if model else 0.0,
        "l1_resident_fraction": resident_fraction,
        "weights_streamed_per_token_fraction": 1.0 - resident_fraction,
        "verdict": (
            "weights are not resident, so the token rate is set by the "
            "interconnect, not by the array"
            if resident_fraction < 0.95
            else "weights are resident, so the token rate is set by the array"
        ),
    }


def l1_residency_requirement(
    claimed: ClaimedArchitecture, density: Density = SRAM_6T_BITCELL_DENSITY
) -> Dict[str, Any]:
    """How much L1 the design needs for compute-in-memory to pay for itself.

    Resisting the pull toward a tidy conclusion: the area turns out to be
    affordable, because SRAM is cheap area and the controller already dominates
    the die. What is not affordable is the *budgeted* L1, which is a small
    fraction of what residency requires.
    """
    model_bits = claimed.model_bytes * 8
    model_area_mm2 = model_bits * density.um2_per_element / 1e6
    kv_area_mm2 = claimed.kv_bytes * 8 * density.um2_per_element / 1e6
    total_area_mm2 = model_area_mm2 + kv_area_mm2
    total_capacity_mb = total_area_mm2 * 1e6 / density.um2_per_element / 8 / 1e6
    return {
        "density_um2_per_bit": density.um2_per_element,
        "density_measured": density.measured_in_this_repository,
        "model_area_mm2": model_area_mm2,
        "kv_area_mm2": kv_area_mm2,
        "total_l1_plus_kv_area_mm2": total_area_mm2,
        "per_die_area_mm2": total_area_mm2 / claimed.dies_per_card,
        "per_die_capacity_mb": total_capacity_mb / claimed.dies_per_card,
        "card_capacity_mb": total_capacity_mb,
        "claimed_l1_mb_per_die": claimed.l1_mb_per_die,
        "shortfall_factor": total_capacity_mb / claimed.dies_per_card / claimed.l1_mb_per_die,
    }


def die_area_budget(
    claimed: ClaimedArchitecture,
    analog: Density = ANALOG_CIM_DENSITY,
    sram: Density = SRAM_6T_BITCELL_DENSITY,
    digital: Density = DIGITAL_STD_CELL_DENSITY,
) -> Dict[str, Any]:
    """Split the die into the three blocks, each with its own density.

    Using one density for all three is the shortcut that makes these numbers
    look impossible: the array is analog cells, the L1 is 6T SRAM, and the
    controller is standard cells, and they differ by two orders of magnitude.
    """
    per_die = claimed.transistors_per_die
    array_tr = claimed.array_transistors_per_die
    l1_tr = claimed.card_l1_mb / claimed.dies_per_card * 1024 * 1024 * 8 * 6
    other_tr = max(per_die - array_tr - l1_tr, 0.0)
    array_mm2 = array_tr * analog.um2_per_element / 1e6
    l1_mm2 = l1_tr * sram.um2_per_element / 1e6
    other_mm2 = other_tr * digital.um2_per_element / 1e6
    total = array_mm2 + l1_mm2 + other_mm2
    return {
        "transistors_per_die": per_die,
        "array": {
            "transistors": array_tr,
            "area_mm2": array_mm2,
            "area_fraction": array_mm2 / total,
            "density": analog.as_dict(),
        },
        "l1": {
            "transistors": l1_tr,
            "area_mm2": l1_mm2,
            "area_fraction": l1_mm2 / total,
            "density": sram.as_dict(),
        },
        "controller_and_io": {
            "transistors": other_tr,
            "area_mm2": other_mm2,
            "area_fraction": other_mm2 / total,
            "density": digital.as_dict(),
        },
        "total_area_mm2_per_die": total,
        "total_area_mm2_per_card": total * claimed.dies_per_card,
        "area_rests_on_unmeasured_density": not (
            sram.measured_in_this_repository and digital.measured_in_this_repository
        ),
        "mpw_shuttle_die_mm2": 5.0,
        "multiple_of_mpw_shuttle_die": total / 5.0,
    }


def leakage_requirement(claimed: ClaimedArchitecture, core_vdd_v: float = 1.8) -> Dict[str, Any]:
    """Turn the unknown leakage spec into the number that would close it.

    The summary's power range is stated as undetermined because the foundry
    leakage figure is missing. That gap is closable without the PDK: the leakage
    *required* to produce each end of the range is computable, and comparing that
    against a published band says whether the range is self-consistent.
    """
    rows: List[Dict[str, Any]] = []
    for label, watts in (
        ("optimistic", claimed.power_optimistic_w),
        ("pessimistic", claimed.power_pessimistic_w),
    ):
        rows.append(
            {
                "label": label,
                "watts": watts,
                "required_leakage_nA_per_transistor": (
                    watts / (core_vdd_v * claimed.card_transistors) * 1e9
                ),
            }
        )
    lo = rows[0]["required_leakage_nA_per_transistor"]
    hi = rows[1]["required_leakage_nA_per_transistor"]
    return {
        "core_vdd_v": core_vdd_v,
        "cases": rows,
        "spread_x": hi / lo,
        "pdk_number_to_obtain": (
            "I_leak at Vgs=0, Vdd=1.8 V, T=85 C, for the smallest cell actually "
            "used, in nA, at slow and fast corners"
        ),
        "why_the_range_is_wide": (
            "static power is exactly I_leak x V x N, so the entire spread is the "
            "junction-temperature band; 60 C of ambient is several doublings of "
            "a 130 nm subthreshold current, which is the order of the quoted spread"
        ),
    }


def measured_efficiency(sense_time_s: float = 50.0e-9) -> Dict[str, Any]:
    """The array's efficiency at the operating point this project validated."""
    model = CimStripReferenceModel()
    result = model.recommended_design(sense_time_s=sense_time_s)
    point = result.get("design_point")
    if not point:
        return {"status": "unavailable", "reason": "no feasible operating point"}
    ops_per_mac = 2.0
    return {
        "status": "ok",
        "array_vds_v": point["array_vds_v"],
        "input_vgs_max_v": point["input_vgs_max_v"],
        "sense_window_ns": point["sense_time_s"] * 1e9,
        "energy_pj_per_mac": point["energy_pj_per_mac"],
        "tops_per_w_int8": ops_per_mac / (point["energy_pj_per_mac"] * 1e-12) / 1e12,
        "note": (
            "2 ops per MAC (multiply and accumulate), from the measured sky130 "
            "unit cell rather than a projection"
        ),
    }


def sense_amplifier_budget(
    claimed: ClaimedArchitecture, sense_time_s: float = 50.0e-9
) -> Dict[str, Any]:
    """How many sense amplifiers the per-die compute claim actually requires.

    This is the number that reconciles a bit-serial PE count with a per-die
    TOPS figure. A bit-serial PE resolves one weight *bit* per sense event, so an
    int8 MAC costs ``pe_transistors // 2`` sense events, not one, and the throughput
    per die falls by exactly that factor unless several sense amplifiers read
    disjoint slices of a bit-plane in parallel.

    One sense amplifier per bit-plane -- the structure this project actually
    verified -- is therefore the pessimistic end, and the shortfall against the
    claim is the parallelism the design has to buy.
    """
    bit_planes = max(1, claimed.pe_transistors // 2)
    window = sense_time_s * bit_planes
    macs_per_die_per_batch = claimed.pes_per_die
    rate = macs_per_die_per_batch / window
    tops = rate * 2.0 / 1.0e12
    # die_tops is stored in ops/s, so it has to be scaled before it can be
    # compared against a figure already in TOPS.
    claimed_tops = claimed.die_tops / 1.0e12
    required_amps = claimed_tops / tops if tops > 0 else float("inf")
    return {
        "bit_planes_per_pe": bit_planes,
        "sense_window_ns": sense_time_s * 1e9,
        "window_per_int8_mac_ns": window * 1e9,
        "one_amp_per_plane_die_tops": tops,
        "claimed_die_tops": claimed_tops,
        "required_parallel_sense_amps_per_plane": required_amps,
        "sense_amps_per_die": required_amps * bit_planes,
        "assumes": (
            "the measured sense window is dominated by amplifier settling, not by "
            "the number of cells summed onto one spine; that assumption is why "
            "one amplifier is credited with reading a whole bit-plane"
        ),
    }


def throughput_check(claimed: ClaimedArchitecture) -> Dict[str, Any]:
    """Is the per-die compute claim reachable, and what does it cost to reach it?"""
    efficiency = measured_efficiency()
    if efficiency.get("status") != "ok":
        return {"status": "unavailable"}
    budget = sense_amplifier_budget(claimed)
    shortfall = (claimed.die_tops / 1.0e12) / budget["one_amp_per_plane_die_tops"]
    return {
        "status": "ok",
        "measured_tops_per_w_int8": efficiency["tops_per_w_int8"],
        "claimed_die_tops": claimed.die_tops / 1.0e12,
        "die_tops_with_one_amp_per_plane": budget["one_amp_per_plane_die_tops"],
        "shortfall_x": shortfall,
        "required_sense_amps_per_plane": budget["required_parallel_sense_amps_per_plane"],
        "required_sense_amps_per_die": budget["sense_amps_per_die"],
        "per_die_claim_verdict": "reachable_only_with_extra_sense_amplifiers",
        "card_tops_consistent_with_die_claim": math.isclose(
            claimed.die_tops * claimed.dies_per_card, claimed.card_tops, rel_tol=0.02
        ),
        "power_at_claimed_tops_measured_efficiency_w": (
            claimed.card_tops / 1e12 / efficiency["tops_per_w_int8"]
        ),
        "note": (
            "the claim is reachable, but only with about "
            f"{budget['required_parallel_sense_amps_per_plane']:.0f} sense "
            "amplifiers per bit-plane rather than the one this project verified; "
            "that analog block is neither designed nor budgeted"
        ),
    }


def audit(
    claimed: Optional[ClaimedArchitecture] = None,
    interconnect: Optional[Interconnect] = None,
) -> Dict[str, Any]:
    """Recompute the whole summary and label every conclusion with its source."""
    architecture = claimed or ClaimedArchitecture()
    links = interconnect or Interconnect()
    streaming = weight_streaming(architecture, links)
    residency = l1_residency_requirement(architecture)
    area = die_area_budget(architecture)
    leakage = leakage_requirement(architecture)
    efficiency = measured_efficiency()
    throughput = throughput_check(architecture)
    sense_budget = sense_amplifier_budget(architecture)

    corrections: List[Dict[str, Any]] = []

    if streaming["shortfall_x"] > 1.0:
        corrections.append(
            {
                "id": "token_rate_is_bandwidth_bound",
                "severity": "blocking",
                "claimed": f"{architecture.claimed_tokens_per_s:.0f} tok/s",
                "recomputed": (
                    f"{streaming['achievable_tokens_per_s']:.1f} tok/s from the "
                    f"best path ({streaming['best_path']})"
                ),
                "detail": (
                    f"{streaming['required_weight_bandwidth_gbs'] / 1000:.2f} TB/s of "
                    f"weight bandwidth is needed for "
                    f"{architecture.claimed_tokens_per_s:.0f} tok/s, and the best "
                    f"path supplies {streaming['best_available_gbs'] / 1000:.3f} TB/s: "
                    f"short by {streaming['shortfall_x']:.0f}x"
                ),
                "root_cause": (
                    f"L1 holds {streaming['l1_resident_fraction'] * 100:.0f}% of the "
                    f"model, so {streaming['weights_streamed_per_token_fraction'] * 100:.0f}% "
                    "of weights are re-read from DDR3 every token"
                ),
                "source": "interconnect, measured PCIe figure already in this repository",
            }
        )

    shortfall = residency["shortfall_factor"]
    if shortfall > 1.5:
        corrections.append(
            {
                "id": "l1_undersized_for_residency",
                "severity": "blocking",
                "claimed": f"{architecture.card_l1_mb:.0f} MB of L1 on the card",
                "recomputed": (
                    f"{residency['per_die_capacity_mb'] * architecture.dies_per_card:.0f} MB "
                    "per card to hold the model and the KV cache together"
                ),
                "detail": (
                    f"L1 is {1.0 / shortfall:.2f}x too small; residency needs "
                    f"{residency['per_die_area_mm2']:.1f} mm2 per die of 6T SRAM "
                    "against the claimed L1 area"
                ),
                "fix": (
                    "raise L1. This is a memory-sizing decision, not a process or "
                    "compute one, and it costs a modest fraction of die area "
                    "because the controller already dominates the die"
                ),
                "source": "literature SRAM density, not measured in this repository",
            }
        )

    corrections.append(
        {
            "id": "per_die_compute_needs_unbudgeted_sense_amplifiers",
            "severity": "material",
            "claimed": f"{architecture.die_tops / 1.0e12:.2f} TOPS per die",
            "recomputed": (
                f"{throughput['die_tops_with_one_amp_per_plane']:.3f} TOPS per die "
                "with one sense amplifier per bit-plane"
            ),
            "detail": (
                f"a bit-serial PE resolves one weight bit per sense event, so an "
                f"int8 MAC costs {architecture.pe_transistors // 2} of them. "
                f"Reaching the claim needs about "
                f"{throughput['required_sense_amps_per_plane']:.0f} sense "
                f"amplifiers per bit-plane, {throughput['required_sense_amps_per_die']:.0f} "
                "per die, none of which is designed or budgeted"
            ),
            "source": "measured sky130 sense window",
        }
    )

    if not area["area_rests_on_unmeasured_density"]:
        pass
    else:
        corrections.append(
            {
                "id": "area_conclusions_rest_on_literature_density",
                "severity": "material",
                "claimed": f"{architecture.transistors_per_die / 1e6:.0f}M transistors per die",
                "recomputed": (
                    f"{area['total_area_mm2_per_die']:.0f} mm2 per die using a "
                    "measured analog density and literature SRAM/digital densities"
                ),
                "detail": (
                    "the array density is measured here, but the L1 and controller "
                    "densities are not; the area split moves proportionally with them"
                ),
                "source": "mixed: measured analog, literature SRAM and digital",
            }
        )

    return {
        "schema_version": "card-architecture-audit/1",
        "owner": "angela",
        "completion_claim_allowed": False,
        "claimed": architecture.as_dict(),
        "interconnect": links.as_dict(),
        "recomputed": {
            "weight_streaming": streaming,
            "l1_residency": residency,
            "die_area": area,
            "leakage": leakage,
            "measured_efficiency": efficiency,
            "sense_amplifier_budget": sense_budget,
            "throughput": throughput,
        },
        "corrections": corrections,
        "gaps_that_remain_open": [
            gap
            for gap in (
                leakage["pdk_number_to_obtain"],
                "foundry 6T SRAM macro density, to replace the literature figure",
                "foundry standard-cell density and leakage library, for the controller",
                "KV cache and non-MAC ops (softmax, LayerNorm) on a bit-serial array",
                "package yield across 128 dies",
                "pipeline stage balance",
            )
        ],
        "bottom_line": (
            "the architecture is not defeated by the process. It has two "
            "independent problems, and both are budgets rather than physics: "
            "L1 is 15x too small for the weights to stay resident, which makes "
            "the token rate a bandwidth number instead of a compute one; and the "
            "per-die compute figure needs about 15 thousand sense amplifiers per "
            "bit-plane rather than the one this project verified. Resizing L1 is "
            "the larger and cheaper fix."
        ),
    }


__all__ = [
    "ANALOG_CIM_DENSITY",
    "ClaimedArchitecture",
    "Density",
    "DIGITAL_STD_CELL_DENSITY",
    "Interconnect",
    "SRAM_6T_BITCELL_DENSITY",
    "audit",
    "die_area_budget",
    "l1_residency_requirement",
    "leakage_requirement",
    "measured_efficiency",
    "sense_amplifier_budget",
    "throughput_check",
    "weight_streaming",
]
