# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

from __future__ import annotations

import json
import math
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class AiCardReferenceConfig:
    pcie_generation: int = 5
    pcie_lanes: int = 16
    pcie_signaling_rate_gbps_per_lane: float = 32.0
    pcie_payload_encoding_ratio: float = 128.0 / 130.0
    pcie_effective_gbps_each_direction: Optional[float] = None
    main_width_bits: int = 16384
    main_compute_partitions: int = 16
    weight_update_width_bits: int = 1024
    secondary_update_partitions: int = 16
    secondary_update_partition_width_bits: int = 64
    target_clock_mhz: float = 250.0
    dma_tile_bytes: int = 1_048_576
    dma_credit_limit: int = 8
    cache_target_mb: int = 32
    cache_partitions_mb: Optional[Mapping[str, int]] = None
    external_memory_gb: int = 64
    prototype_power_limit_w: float = 300.0
    preferred_power_limit_w: float = 350.0
    prototype_bom_cap_usd: int = 3000

    def __post_init__(self) -> None:
        if self.pcie_generation < 1 or self.pcie_lanes < 1:
            raise ValueError("PCIe generation and lane count must be positive")
        if self.pcie_signaling_rate_gbps_per_lane <= 0:
            raise ValueError("PCIe signaling rate must be positive")
        if not 0 < self.pcie_payload_encoding_ratio <= 1:
            raise ValueError("PCIe payload encoding ratio must be in (0, 1]")
        if self.main_width_bits <= 0 or self.weight_update_width_bits <= 0:
            raise ValueError("internal fabric widths must be positive")
        if self.main_compute_partitions < 1 or self.secondary_update_partitions < 1:
            raise ValueError("compute and update partition counts must be positive")
        if self.secondary_update_partition_width_bits <= 0:
            raise ValueError("secondary update partition width must be positive")
        if (
            self.secondary_update_partitions * self.secondary_update_partition_width_bits
            != self.weight_update_width_bits
        ):
            raise ValueError("secondary update partitions must exactly cover the update bus")
        if self.target_clock_mhz <= 0 or self.dma_tile_bytes <= 0:
            raise ValueError("target clock and DMA tile size must be positive")
        if self.dma_credit_limit < 1 or self.cache_target_mb < 0:
            raise ValueError("DMA credits must be positive and cache target non-negative")
        if self.external_memory_gb <= 0 or self.prototype_power_limit_w <= 0:
            raise ValueError("external memory and prototype power limit must be positive")
        if self.preferred_power_limit_w <= 0 or self.prototype_bom_cap_usd < 0:
            raise ValueError("preferred power limit must be positive and BOM cap non-negative")
        computed = (
            self.pcie_signaling_rate_gbps_per_lane
            * self.pcie_lanes
            * self.pcie_payload_encoding_ratio
        )
        if self.pcie_effective_gbps_each_direction is None:
            object.__setattr__(self, "pcie_effective_gbps_each_direction", computed)
        elif not math.isclose(self.pcie_effective_gbps_each_direction, computed, rel_tol=1e-9):
            raise ValueError("PCIe effective bandwidth must match signaling and encoding")
        if self.cache_partitions_mb is None:
            object.__setattr__(
                self,
                "cache_partitions_mb",
                {"activation": 8, "weights": 16, "staging": 8},
            )

    @property
    def pcie_raw_gbps_each_direction(self) -> float:
        return self.pcie_signaling_rate_gbps_per_lane * self.pcie_lanes

    @property
    def pcie_effective_gbps(self) -> float:
        value = self.pcie_effective_gbps_each_direction
        if value is None:
            raise RuntimeError("PCIe effective bandwidth was not initialized")
        return value

    @property
    def pcie_effective_gbs_each_direction(self) -> float:
        return self.pcie_effective_gbps / 8.0


class AiCardReferenceModel:
    def __init__(self, config: Optional[AiCardReferenceConfig] = None):
        self.config = config or AiCardReferenceConfig()

    def bandwidth_report(self) -> Dict[str, Any]:
        config = self.config
        clock_hz = config.target_clock_mhz * 1_000_000
        main_gbps = config.main_width_bits * clock_hz / 1_000_000_000
        weight_gbps = config.weight_update_width_bits * clock_hz / 1_000_000_000
        main_gbs = main_gbps / 8.0
        weight_gbs = weight_gbps / 8.0
        pcie_effective_gbs = config.pcie_effective_gbs_each_direction
        return {
            "pcie_generation": config.pcie_generation,
            "pcie_lanes": config.pcie_lanes,
            "pcie_signaling_rate_gbps_per_lane": config.pcie_signaling_rate_gbps_per_lane,
            "pcie_payload_encoding_ratio": config.pcie_payload_encoding_ratio,
            "pcie_raw_gbps_each_direction": round(config.pcie_raw_gbps_each_direction, 3),
            "pcie_effective_gbps_each_direction": round(config.pcie_effective_gbps, 3),
            "pcie_effective_gbs_each_direction": round(pcie_effective_gbs, 3),
            "pcie_bidirectional_effective_gbs": round(pcie_effective_gbs * 2, 3),
            "main_internal_raw_gbps": round(main_gbps, 3),
            "main_internal_raw_gbs": round(main_gbs, 3),
            "weight_update_internal_raw_gbps": round(weight_gbps, 3),
            "weight_update_internal_raw_gbs": round(weight_gbs, 3),
            "main_to_host_ratio": round(main_gbs / pcie_effective_gbs, 3),
            "main_to_performance_target_ratio": round(main_gbs / 50.0, 3),
            "main_is_internal_fabric": True,
            "bandwidth_derivation": "bits_per_cycle * clock_hz / 1e9; GB/s = Gbps / 8",
            "host_dma_tile_bytes": config.dma_tile_bytes,
            "host_dma_target_gbs": round(pcie_effective_gbs, 3),
        }

    def cache_report(self) -> Dict[str, Any]:
        partitions = {
            str(name): int(size)
            for name, size in (
                self.config.cache_partitions_mb or {"activation": 8, "weights": 16, "staging": 8}
            ).items()
        }
        if any(size < 0 for size in partitions.values()):
            raise ValueError("cache partitions must be non-negative")
        addresses: Dict[str, Dict[str, int]] = {}
        cursor = 0
        for name, size in partitions.items():
            addresses[name] = {
                "start_mb": cursor,
                "end_mb_exclusive": cursor + size,
                "size_mb": size,
            }
            cursor += size
        total = cursor
        ranges = list(addresses.values())
        overlap = any(
            left["end_mb_exclusive"] > right["start_mb"]
            for index, left in enumerate(ranges)
            for right in ranges[index + 1 :]
        )
        return {
            "scope": "die_internal_l1",
            "implementation": "self_developed_cache",
            "target_mb": self.config.cache_target_mb,
            "partitions_mb": partitions,
            "addresses_mb": addresses,
            "total_mb": total,
            "unallocated_mb": max(self.config.cache_target_mb - total, 0),
            "address_overlap": overlap,
            "within_target": total <= self.config.cache_target_mb,
            "l2_memory_scope": "card_external_to_die",
            "external_memory_gb": self.config.external_memory_gb,
        }

    def hierarchy_report(self) -> Dict[str, Any]:
        config = self.config
        return {
            "die": {
                "boundary": "self_developed_chip",
                "implementation_owner": "angela",
                "main_compute": {
                    "role": "input_output",
                    "partitions": config.main_compute_partitions,
                    "fabric_width_bits": config.main_width_bits,
                },
                "secondary_compute": {
                    "role": "sparse_hot_weight_update",
                    "partitions": config.secondary_update_partitions,
                    "input_width_bits": config.weight_update_width_bits,
                    "cache_partition_width_bits": config.secondary_update_partition_width_bits,
                    "mapping_owner": "angela",
                },
                "l1_cache": {
                    "scope": "die_internal",
                    "implementation": "self_developed_cache",
                    "target_mb": config.cache_target_mb,
                    "implementation_owner": "angela",
                },
            },
            "card": {
                "boundary": "card_external_to_die",
                "l2_memory": {
                    "scope": "card",
                    "implementation": "purchased_memory",
                    "capacity_gb": config.external_memory_gb,
                    "selection_owner": "angela",
                },
                "electronics": {
                    "scope": "card",
                    "selection_owner": "angela",
                },
            },
            "host": {
                "boundary": "outside_card",
                "l3": {
                    "scope": "outside_card",
                    "interface": "PCIe",
                    "role": "host_access_boundary",
                    "target": "host_memory_or_storage",
                    "pcie_generation": config.pcie_generation,
                    "pcie_lanes": config.pcie_lanes,
                    "pcie_payload_gbs_each_direction": round(
                        config.pcie_effective_gbs_each_direction, 3
                    ),
                },
            },
        }

    @staticmethod
    def ownership_report() -> Dict[str, Any]:
        return {
            "product_architecture": "angela",
            "chip_microarchitecture": "angela",
            "main_secondary_cache_mapping": "angela",
            "component_selection_and_bom": "angela",
            "environment_and_validation": "environment_support",
            "tool_installation": "explicit_human_approval_after_software_gate",
        }

    def power_report(self) -> Dict[str, Any]:
        allocation = {
            "compute_and_fpga": 105.0,
            "memory": 75.0,
            "pcie_and_retimers": 25.0,
            "power_conversion_loss": 35.0,
            "cooling_and_board": 20.0,
            "measurement_and_safety_headroom": 40.0,
        }
        total = sum(allocation.values())
        return {
            "allocation_w": allocation,
            "planning_total_w": total,
            "prototype_limit_w": self.config.prototype_power_limit_w,
            "preferred_limit_w": self.config.preferred_power_limit_w,
            "within_prototype_limit": total <= self.config.prototype_power_limit_w,
            "measurement_status": "planning_only_not_measured",
            "cooling": "passive_heatsink_with_host_airflow",
        }

    def cost_report(self) -> Dict[str, Any]:
        items = [
            "compute_silicon_or_fpga",
            "pcb_and_package",
            "external_memory",
            "power_delivery",
            "connectors_and_retimers",
            "mechanical_and_heatsink",
        ]
        return {
            "currency": "USD",
            "prototype_bom_cap": self.config.prototype_bom_cap_usd,
            "items": [
                {"item": item, "unit_cost": None, "status": "RFQ_REQUIRED"} for item in items
            ],
            "known_total": None,
            "decision": "BLOCKED_PENDING_QUOTES",
            "rule": "never estimate a price without a manufacturer or authorized distributor quote",
        }

    def simulate_dma(self, tile_count: int = 16, credits: Optional[int] = None) -> Dict[str, Any]:
        if tile_count < 0:
            raise ValueError("tile_count must be non-negative")
        credit_limit = credits if credits is not None else self.config.dma_credit_limit
        if credit_limit < 1:
            raise ValueError("DMA credit limit must be positive")
        outstanding = 0
        completed = 0
        stalls = 0
        peak_outstanding = 0
        for _ in range(tile_count):
            if outstanding >= credit_limit:
                stalls += 1
                outstanding -= 1
                completed += 1
            outstanding += 1
            peak_outstanding = max(peak_outstanding, outstanding)
        while outstanding:
            outstanding -= 1
            completed += 1
        return {
            "tile_count": tile_count,
            "tile_bytes": self.config.dma_tile_bytes,
            "credit_limit": credit_limit,
            "completed_tiles": completed,
            "backpressure_events": stalls,
            "peak_outstanding_tiles": peak_outstanding,
            "protocol": "burst-admission-drain-with-credit-backpressure",
            "model_scope": "admission_model_not_timing_model",
        }

    def simulate_weight_updates(self, updates: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
        committed: List[Dict[str, Any]] = []
        last_sequence = -1
        for update in updates:
            sequence_value = update.get("sequence", -1)
            if isinstance(sequence_value, bool) or not isinstance(sequence_value, int):
                raise ValueError("weight update sequence must be an integer")
            if sequence_value < 0:
                raise ValueError("weight update sequence must be non-negative")
            payload = update.get("payload", b"")
            if not isinstance(payload, (bytes, bytearray)):
                raise ValueError("weight update payload must be bytes")
            if sequence_value <= last_sequence:
                raise ValueError("weight update sequence must be strictly increasing")
            committed.append(
                {
                    "sequence": sequence_value,
                    "bytes": len(payload),
                    "crc32": f"{zlib.crc32(payload) & 0xFFFFFFFF:08x}",
                    "state": "committed",
                }
            )
            last_sequence = sequence_value
        return {
            "update_count": len(committed),
            "committed": committed,
            "ordering_validated": True,
            "per_update_digest_contract": True,
            "rollback_implemented": False,
            "atomicity_scope": "single-update-digest-commit-only",
        }

    def simulate_main_compute(
        self,
        inputs: Sequence[Sequence[int]],
        weights: Sequence[Sequence[int]],
    ) -> Dict[str, Any]:
        tile_size = 16
        if len(inputs) != tile_size or any(len(row) != tile_size for row in inputs):
            raise ValueError("main compute inputs must be a 16x16 matrix")
        if len(weights) != tile_size or any(len(row) != tile_size for row in weights):
            raise ValueError("main compute weights must be a 16x16 matrix")
        if any(
            not isinstance(value, int) or isinstance(value, bool) or not -128 <= value <= 127
            for row in inputs
            for value in row
        ):
            raise ValueError("main compute inputs must be signed INT8 values")
        if any(
            not isinstance(value, int) or isinstance(value, bool) or not -128 <= value <= 127
            for row in weights
            for value in row
        ):
            raise ValueError("main compute weights must be signed INT8 values")
        outputs: List[List[int]] = []
        max_abs_accumulator = 0
        for output_row in range(tile_size):
            output_row_values: List[int] = []
            for column in range(tile_size):
                accumulator = sum(
                    weights[output_row][reduction] * inputs[reduction][column]
                    for reduction in range(tile_size)
                )
                max_abs_accumulator = max(max_abs_accumulator, abs(accumulator))
                output_row_values.append(accumulator)
            outputs.append(output_row_values)
        checksum = sum(sum(row) for row in outputs)
        return {
            "tile": "16x16-signed-int8-mac",
            "accumulator_width_bits": 32,
            "outputs": outputs,
            "checksum": checksum,
            "max_abs_accumulator": max_abs_accumulator,
            "int32_range_pass": max_abs_accumulator <= (1 << 31) - 1,
            "used_llm": False,
        }

    def simulate_sparse_partition_update(
        self,
        payload: bytes,
        hit_masks: Sequence[int],
        deltas: Sequence[int],
    ) -> Dict[str, Any]:
        expected_bytes = self.config.weight_update_width_bits // 8
        partition_bytes = self.config.secondary_update_partition_width_bits // 8
        if len(payload) != expected_bytes:
            raise ValueError("sparse update payload width does not match the update bus")
        if len(hit_masks) != self.config.secondary_update_partitions:
            raise ValueError("sparse update hit mask count does not match the bus partitions")
        if len(deltas) != expected_bytes:
            raise ValueError("sparse update delta count does not match the payload")
        if any(
            not isinstance(mask, int) or isinstance(mask, bool) or not 0 <= mask <= 0xFF
            for mask in hit_masks
        ):
            raise ValueError("each sparse update hit mask must be an 8-bit value")
        if any(
            not isinstance(delta, int) or isinstance(delta, bool) or not -128 <= delta <= 127
            for delta in deltas
        ):
            raise ValueError("sparse update deltas must be signed INT8 values")
        updated = bytearray(payload)
        touched = [False] * expected_bytes
        modified_bytes = 0
        for partition, hit_mask in enumerate(hit_masks):
            base = partition * partition_bytes
            for lane in range(partition_bytes):
                if not hit_mask & (1 << lane):
                    continue
                index = base + lane
                old_value = payload[index] - 256 if payload[index] >= 128 else payload[index]
                new_value = max(-128, min(127, old_value + deltas[index]))
                updated[index] = new_value & 0xFF
                touched[index] = True
                if old_value != new_value:
                    modified_bytes += 1
        unselected_unchanged = all(
            updated[index] == payload[index]
            for index in range(expected_bytes)
            if not touched[index]
        )
        return {
            "update_width_bits": self.config.weight_update_width_bits,
            "partition_count": self.config.secondary_update_partitions,
            "partition_width_bits": self.config.secondary_update_partition_width_bits,
            "selected_bytes": sum(touched),
            "modified_bytes": modified_bytes,
            "unselected_bytes_unchanged": unselected_unchanged,
            "updated_payload_hex": bytes(updated).hex(),
            "crc32": f"{zlib.crc32(updated) & 0xFFFFFFFF:08x}",
            "mapping_status": "project_ai_decision_pending",
            "used_llm": False,
        }

    def design_verification(self) -> Dict[str, Any]:
        identity = [[1 if row == column else 0 for column in range(16)] for row in range(16)]
        main_compute = self.simulate_main_compute(identity, identity)
        sparse_update = self.simulate_sparse_partition_update(
            bytes(range(128)),
            [0x01] * self.config.secondary_update_partitions,
            [1] * (self.config.weight_update_width_bits // 8),
        )
        cache = self.cache_report()
        dma = self.simulate_dma()
        hierarchy = self.hierarchy_report()
        technical_checks = {
            "main_compute_reference": main_compute["outputs"] == identity
            and main_compute["int32_range_pass"],
            "secondary_partition_width": (
                sparse_update["partition_count"] * sparse_update["partition_width_bits"]
                == self.config.weight_update_width_bits
            ),
            "sparse_update_selectivity": sparse_update["unselected_bytes_unchanged"],
            "cache_no_aliasing": cache["within_target"] and not cache["address_overlap"],
            "dma_completion": dma["completed_tiles"] == dma["tile_count"],
            "l1_l2_l3_boundaries": (
                hierarchy["die"]["l1_cache"]["scope"] == "die_internal"
                and hierarchy["card"]["l2_memory"]["scope"] == "card"
                and hierarchy["host"]["l3"]["interface"] == "PCIe"
            ),
        }
        return {
            "status": (
                "reference_verified_acceptance_check_pending"
                if all(technical_checks.values())
                else "partial"
            ),
            "validation_level": "L1",
            "technical_checks": technical_checks,
            "technical_checks_pass": all(technical_checks.values()),
            "gates": {
                "acceptance_check": False,
                "hdl_gate_level": False,
                "physical_hardware": False,
            },
            "vectors": {
                "main_compute": main_compute,
                "sparse_update": sparse_update,
            },
            "blockers": [
                "the main/secondary-to-L1 mapping has not passed the acceptance check",
                "numeric and protocol reference does not prove RTL or physical implementation",
            ],
        }

    def run(self) -> Dict[str, Any]:
        bandwidth = self.bandwidth_report()
        cache = self.cache_report()
        design_verification = self.design_verification()
        hierarchy = self.hierarchy_report()
        ownership = self.ownership_report()
        power = self.power_report()
        cost = self.cost_report()
        dma = self.simulate_dma()
        weight_updates = self.simulate_weight_updates(
            [{"sequence": 0, "payload": b"reference-weight-digest"}]
        )
        checks = {
            "main_fabric_exceeds_host_path": bandwidth["main_to_host_ratio"] > 1.0,
            "design_reference_verified": design_verification["technical_checks_pass"],
            "secondary_update_partition_contract": (
                self.config.secondary_update_partitions
                * self.config.secondary_update_partition_width_bits
                == self.config.weight_update_width_bits
            ),
            "cache_partition_valid": cache["within_target"] and not cache["address_overlap"],
            "power_budget_within_prototype_limit": power["within_prototype_limit"],
            "dma_completes_with_backpressure": dma["completed_tiles"] == dma["tile_count"],
            "weight_update_contract": weight_updates["ordering_validated"]
            and weight_updates["per_update_digest_contract"],
            "cost_verified": cost["decision"] != "BLOCKED_PENDING_QUOTES",
        }
        status = "pass" if all(checks.values()) else "partial"
        return {
            "schema_version": "ai-compute-card-reference/1",
            "status": status,
            "validation": {
                "level": "L1",
                "mode": "software_only",
                "professional_hdl_simulation": False,
                "physical_hardware": False,
                "cost_verified": False,
                "evidence_rule": "hierarchy and numeric contract only; project AI owns implementation",
                "design_scope": "software_reference_only_not_physical_fabrication",
                "bandwidth_units": "Gbps and GB/s are reported separately; 8 bits per byte",
            },
            "ownership": ownership,
            "terminology_guard": {
                "project_map_labels": "software_project_structure_and_tooling_labels",
                "context_block_labels": "software_context_categories",
                "compute_card_levels": {
                    "die_l1": "self_developed_die_internal_cache",
                    "card_l2": "purchased_card_memory",
                    "host_l3": "outside_card_pcie_boundary",
                },
                "labels_are_not_interchangeable": True,
            },
            "hierarchy": hierarchy,
            "requirements": {
                "pcie": "Gen5-x16-host-link",
                "pcie_payload_gbs_each_direction": round(
                    self.config.pcie_effective_gbs_each_direction, 3
                ),
                "main_compute_partitions": self.config.main_compute_partitions,
                "main_width_bits": self.config.main_width_bits,
                "secondary_update_partitions": self.config.secondary_update_partitions,
                "secondary_update_partition_width_bits": self.config.secondary_update_partition_width_bits,
                "weight_update_width_bits": self.config.weight_update_width_bits,
                "l1_cache_scope": "die_internal_self_developed",
                "l1_cache_target_mb": self.config.cache_target_mb,
                "l2_memory_scope": "card_purchased_memory",
                "l2_memory_gb": self.config.external_memory_gb,
                "l3_scope": "outside_card_pcie_boundary",
                "l3_target": "host_memory_or_storage",
                "prototype_power_limit_w": self.config.prototype_power_limit_w,
            },
            "bandwidth": bandwidth,
            "cache": cache,
            "design_verification": design_verification,
            "power": power,
            "cost": cost,
            "dma": dma,
            "weight_updates": weight_updates,
            "checks": checks,
            "blockers": [
                "the die/cache partition interface has not passed the acceptance check",
                "component prices and lifecycle are not quoted",
                "exact FPGA/ASIC package and memory controller are not selected",
                "PCIe electrical/CEM and thermal design are not simulated",
                "L3 gate-level and L4 timing/synthesis evidence are deferred",
            ],
        }

    def write_json(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.run(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path


__all__ = ["AiCardReferenceConfig", "AiCardReferenceModel"]
