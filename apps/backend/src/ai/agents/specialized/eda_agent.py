# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

"""Angela's sandboxed EDA experiment agent."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from ai.core.eda_episode import build_eda_episode
from core.tools.eda_tool_adapter import EdaToolAdapter, EdaWorkspace

logger = logging.getLogger(__name__)

_ENG_FACTORS = {
    "": 1.0,
    "k": 1e3,
    "m": 1e6,
    "u": 1e-6,
    "n": 1e-9,
    "p": 1e-12,
}
_NUMBER_WITH_SUFFIX = r"([0-9]+(?:\.[0-9]*)?|\.[0-9]+)\s*([kKmMuUnNpP]?)"


def _engineering_number(value: str) -> float:
    match = re.fullmatch(_NUMBER_WITH_SUFFIX, value.strip())
    if not match:
        raise ValueError(f"invalid engineering number: {value}")
    return float(match.group(1)) * _ENG_FACTORS[match.group(2).lower()]


def _query_numbers(query: str, name: str) -> List[float]:
    start_pattern = re.compile(rf"\b{name}\s*[=:：]?\s*", re.IGNORECASE)
    number_pattern = re.compile(_NUMBER_WITH_SUFFIX)
    values: List[float] = []
    for start in start_pattern.finditer(query or ""):
        tail = (query or "")[start.end() : start.end() + 160]
        position = 0
        while position < len(tail):
            number = number_pattern.match(tail, position)
            if not number:
                break
            try:
                value = _engineering_number(number.group(1) + number.group(2))
            except ValueError:
                break
            if value > 0:
                values.append(value)
            position = number.end()
            separator = re.match(r"\s*(?:[,，/]\s*|\s+)", tail[position:])
            if not separator:
                break
            next_position = position + separator.end()
            if next_position >= len(tail) or not re.match(r"\d|\.", tail[next_position:]):
                break
            position = next_position
    return values


class EdaAgent:
    """Generate layouts, simulate circuits, and explore design parameters."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        self.config = config or {}
        self.agent_id = kwargs.get("agent_id")
        adapter = kwargs.get("adapter")
        self.training_coordinator = kwargs.get("training_coordinator")
        self.adapter: EdaToolAdapter = adapter or EdaToolAdapter(config=self.config)
        self.config = self.adapter.config
        self.collect_learning_episodes = bool(self.config.get("collect_learning_episodes", True))
        self.capabilities = [
            {
                "name": "eda_probe",
                "capability_id": "eda_probe",
                "description": "探測本機 EDA 工具",
                "version": "1.0.0",
            },
            {
                "name": "eda_generate",
                "capability_id": "eda_generate",
                "description": "生成 KLayout layout 與 SPICE netlist",
                "version": "1.0.0",
            },
            {
                "name": "eda_explore",
                "capability_id": "eda_explore",
                "description": "用 ngspice 探索電路參數",
                "version": "1.0.0",
            },
            {
                "name": "eda_magic_check",
                "capability_id": "eda_magic_check",
                "description": "嘗試 Magic DRC 與 layout round-trip",
                "version": "1.0.0",
            },
            {
                "name": "eda_kicad",
                "capability_id": "eda_kicad",
                "description": "生成 KiCad PCB、Gerber 與 DRC",
                "version": "1.0.0",
            },
            {
                "name": "eda_easyeda",
                "capability_id": "eda_easyeda",
                "description": "準備 EasyEDA 檔案 bridge handoff",
                "version": "1.0.0",
            },
            {
                "name": "eda_jlcone",
                "capability_id": "eda_jlcone",
                "description": "準備 JLCONE 訂單 handoff",
                "version": "1.0.0",
            },
            {
                "name": "eda_learn",
                "capability_id": "eda_learn",
                "description": "記錄可驗證 EDA episode 供離線回放與訓練",
                "version": "1.0.0",
            },
            {
                "name": "logic_gate_learn",
                "capability_id": "logic_gate_learn",
                "description": "從少量 truth-table 教學資料推導 Boolean gate 規則",
                "version": "1.0.0",
            },
            {
                "name": "logic_gate_verify",
                "capability_id": "logic_gate_verify",
                "description": "用獨立 Boolean oracle 驗證未見輸入",
                "version": "1.0.0",
            },
            {
                "name": "mvu_reference",
                "capability_id": "mvu_reference",
                "description": "在軟件中建立並驗證 MVU 硬體參考模型",
                "version": "0.1.0",
            },
            {
                "name": "ai_card_reference",
                "capability_id": "ai_card_reference",
                "description": "在軟件中建立 PCIe AI 計算卡架構、成本與功耗模型",
                "version": "0.1.0",
            },
            {
                "name": "ai_card_interface_packet",
                "capability_id": "ai_card_interface_packet",
                "description": "讀取 Angela interface-freeze 決策包與待凍結項目",
                "version": "0.1.0",
            },
            {
                "name": "hardware_standards",
                "capability_id": "hardware_standards",
                "description": "查詢 PCIe、AXI、SystemVerilog 等官方標準來源與版本",
                "version": "1.0.0",
            },
            {
                "name": "rtl_generate",
                "capability_id": "rtl_generate",
                "description": "由已提供的硬體 header 生成受限 SystemVerilog 結構投影",
                "version": "0.1.0",
            },
        ]

    def get_status(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "enabled": self.adapter.enabled,
            "output_root": str(self.adapter.output_root),
            "tools": list(self.adapter.config.get("tools", {}).keys()),
            "learning_episodes": {
                "enabled": self.collect_learning_episodes,
                "coordinator_wired": self.training_coordinator is not None,
            },
        }

    def get_ai_card_interface_packet(self) -> Dict[str, Any]:
        packet_path = (
            Path(__file__).resolve().parents[6]
            / "hardware/ai_compute_card/angela_interface_freeze_packet.yaml"
        )
        try:
            import yaml

            packet = yaml.safe_load(packet_path.read_text(encoding="utf-8"))
            if not isinstance(packet, dict):
                raise ValueError("interface packet must be a mapping")
            return {"ok": True, "path": str(packet_path), "packet": packet}
        except Exception as exc:
            logger.warning("AI card interface packet unavailable: %s", exc)
            return {"ok": False, "path": str(packet_path), "error": str(exc)}

    def get_hardware_standards(self, query: str = "") -> Dict[str, Any]:
        from ai.hardware.standards_catalog import search_standards

        return search_standards(query)

    async def run_rtl_experiment(self, clock_mhz: Optional[float] = 250.0) -> Dict[str, Any]:
        if not self.adapter.enabled:
            return {
                "status": "unavailable",
                "message": "EDA integration is disabled by configuration",
                "diagnostics": ["eda.enabled=false"],
            }
        try:
            from ai.hardware.mvu_reference import MvuReferenceModel
            from ai.hardware.rtl_generator import (
                generate_mvu_header_projection,
                generate_mvu_header_projection_testbench,
            )

            header = MvuReferenceModel().header_recalculation(clock_mhz=clock_mhz)
            source = generate_mvu_header_projection(header)
            testbench_source = generate_mvu_header_projection_testbench(header)
            workspace = self.adapter.create_workspace("rtl")
            rtl_generation = self.adapter.generate_rtl_artifact(
                workspace, "mvu_header_projection", source
            )
            rtl_artifact = rtl_generation["artifact"]
            testbench_generation = self.adapter.generate_rtl_artifact(
                workspace, "mvu_header_projection_tb", testbench_source
            )
            testbench_artifact = testbench_generation["artifact"]
            result = {
                "status": "generated_structural_projection",
                "validation_level": "L1",
                "source_kind": "user_provided_header",
                "professional_hdl_simulation": False,
                "physical_hardware": False,
                "architecture_frozen": False,
                "clock_mhz": clock_mhz,
                "header_recalculation": header,
                "rtl_artifact": rtl_artifact,
                "rtl_generation": rtl_generation,
                "testbench_artifact": testbench_artifact,
                "next_step": "provide_or_install_verified_simulator_then_run_compile_and_simulation",
            }
            summary_artifact = self.adapter.write_text_artifact(
                workspace,
                "rtl_structural_projection_result",
                json.dumps(result, ensure_ascii=False, indent=2),
                "rtl-result",
            )
            learning = await self._record_learning_episode(
                workflow="rtl",
                parameters={
                    "source_kind": "user_provided_header",
                    "clock_mhz": clock_mhz,
                    "architecture_frozen": False,
                },
                tools=self.adapter.config.get("tools", {}),
                results={"rtl": result},
                artifacts=[rtl_artifact, testbench_artifact, summary_artifact],
                workspace=workspace,
            )
            finalized = self.adapter.finalize(
                workspace,
                {
                    "status": result["status"],
                    "tool": "rtl_structural_projection",
                    "result": result,
                    "artifacts": [rtl_artifact, summary_artifact],
                    "learning": learning,
                    "message": "RTL structural projection generated; simulation not run",
                },
            )
            finalized["status"] = result["status"]
            finalized["message"] = "RTL structural projection generated; simulation not run"
            return finalized
        except Exception as exc:
            logger.warning("RTL structural projection failed", exc_info=True)
            return {
                "status": "error",
                "message": f"RTL structural projection failed: {exc}",
                "diagnostics": [str(exc)],
            }

    async def probe_tools(self, **_: Any) -> Dict[str, Any]:
        result = await self.adapter.probe()
        available = [name for name, value in result["tools"].items() if value.get("available")]
        result["message"] = (
            "EDA tools available: " + ", ".join(available)
            if available
            else "No supported EDA executable is available"
        )
        return result

    async def _record_learning_episode(
        self,
        workflow: str,
        parameters: Dict[str, Any],
        tools: Dict[str, Any],
        results: Dict[str, Dict[str, Any]],
        artifacts: Sequence[Dict[str, Any]],
        workspace: Optional[EdaWorkspace] = None,
    ) -> Dict[str, Any]:
        if not self.collect_learning_episodes:
            return {"status": "disabled"}
        if self.training_coordinator is None:
            return {"status": "not_wired"}
        episode = build_eda_episode(
            workflow=workflow,
            parameters=parameters,
            tools=tools,
            results=results,
            artifacts=artifacts,
        )
        try:
            queued = await self.training_coordinator.enqueue_eda_episode(episode)
        except (AttributeError, TypeError, ValueError) as exc:
            logger.warning("EDA learning episode enqueue failed", exc_info=True)
            return {
                "status": "unavailable",
                "episode_id": episode["episode_id"],
                "fingerprint": episode["fingerprint"],
                "diagnostics": [str(exc)],
            }
        metadata: Dict[str, Any] = {
            "status": "queued" if queued else "duplicate",
            "episode_id": episode["episode_id"],
            "fingerprint": episode["fingerprint"],
            "quality": episode["outcome"]["quality"],
            "eligible": episode["outcome"]["eligible"],
            "reasons": episode["outcome"]["reasons"],
        }
        if workspace is not None:
            try:
                metadata["artifact"] = self.adapter.write_text_artifact(
                    workspace,
                    "eda_episode",
                    json.dumps(episode, ensure_ascii=False, indent=2),
                    "eda-episode",
                )
            except OSError as exc:
                logger.warning("EDA episode artifact write failed", exc_info=True)
                metadata["artifact_error"] = str(exc)
        return metadata

    async def record_learning_episode(
        self,
        workflow: str,
        parameters: Dict[str, Any],
        tools: Dict[str, Any],
        results: Dict[str, Dict[str, Any]],
        artifacts: Sequence[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return await self._record_learning_episode(
            workflow=workflow,
            parameters=parameters,
            tools=tools,
            results=results,
            artifacts=artifacts,
        )

    async def run_logic_gate_experiment(
        self,
        training_rows: Sequence[Dict[str, Any]],
        evaluation_rows: Sequence[Dict[str, Any]],
        oracle_expression: str,
        active: bool = False,
    ) -> Dict[str, Any]:
        """Teach a Boolean hypothesis, then verify unseen rows independently."""
        if not self.adapter.enabled:
            return {
                "status": "unavailable",
                "message": "EDA integration is disabled by configuration",
                "diagnostics": ["eda.enabled=false"],
            }
        try:
            from ai.arithmetic.boolean_gate_learner import (
                run_active_logic_gate_experiment,
                run_logic_gate_experiment,
            )

            if active:
                experiment = run_active_logic_gate_experiment(
                    seed_rows=training_rows,
                    query_rows=evaluation_rows,
                    oracle_expression=oracle_expression,
                )
            else:
                experiment = run_logic_gate_experiment(
                    training_rows=training_rows,
                    evaluation_rows=evaluation_rows,
                    oracle_expression=oracle_expression,
                )
            learning: Dict[str, Any] = {"status": "not_wired"}
            if self.training_coordinator is not None:
                fingerprint = hashlib.sha256(
                    json.dumps(
                        experiment,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ).hexdigest()
                try:
                    queued = await self.training_coordinator.enqueue_logic_episode(
                        {
                            "kind": "logic_gate_episode",
                            "fingerprint": fingerprint,
                            "workflow": "logic_gate",
                            "result": experiment,
                        }
                    )
                    learning = {
                        "status": "queued" if queued else "duplicate",
                        "fingerprint": fingerprint,
                        "eligible": experiment["all_rows_pass"],
                    }
                except (AttributeError, TypeError, ValueError) as exc:
                    learning = {"status": "unavailable", "diagnostics": [str(exc)]}
            workspace = self.adapter.create_workspace("logic_gate")
            artifact = self.adapter.write_text_artifact(
                workspace,
                "logic_gate_episode",
                json.dumps(experiment, ensure_ascii=False, indent=2),
                "logic-gate-episode",
            )
            status = "success" if experiment["all_rows_pass"] else "partial"
            summary = {
                "status": status,
                "tool": "logic_gate",
                "result": experiment,
                "learning": learning,
                "artifacts": [artifact],
                "message": (
                    f"Boolean hypothesis={experiment['hypothesis']}，"
                    f"驗證={experiment['passed_count']}/{experiment['evaluation_count']}，"
                    f"LLM_used={experiment['used_llm']}"
                ),
            }
            result = self.adapter.finalize(workspace, summary)
            result["status"] = status
            result["message"] = summary["message"]
            return result
        except Exception as exc:
            logger.warning("Logic gate experiment failed", exc_info=True)
            return {
                "status": "error",
                "message": f"Logic gate experiment failed: {exc}",
                "diagnostics": [str(exc)],
            }

    async def run_mvu_reference_experiment(
        self, rounds: int = 2, clock_mhz: Optional[float] = None
    ) -> Dict[str, Any]:
        """Run the software-only MVU reference model and persist its evidence."""
        if not self.adapter.enabled:
            return {
                "status": "unavailable",
                "message": "EDA integration is disabled by configuration",
                "diagnostics": ["eda.enabled=false"],
            }
        try:
            from ai.hardware.mvu_reference import MvuReferenceConfig, MvuReferenceModel

            experiment = MvuReferenceModel(MvuReferenceConfig(rounds=rounds)).run(clock_mhz)
            workspace = self.adapter.create_workspace("mvu_reference")
            artifact = self.adapter.write_text_artifact(
                workspace,
                "mvu_reference_result",
                json.dumps(experiment, ensure_ascii=False, indent=2),
                "mvu-reference-episode",
            )
            summary = {
                "status": experiment["status"],
                "tool": "mvu_reference",
                "result": experiment,
                "artifacts": [artifact],
                "message": (
                    f"MVU software reference={experiment['status']}，"
                    f"stalls={experiment['metrics']['pipeline_stalls_status']}，"
                    f"collisions={experiment['metrics']['raw_collision_count']}，"
                    f"modified={experiment['metrics']['modified_bit_ratio']:.5%}"
                ),
            }
            result = self.adapter.finalize(workspace, summary)
            result["status"] = experiment["status"]
            result["message"] = summary["message"]
            return result
        except Exception as exc:
            logger.warning("MVU reference experiment failed", exc_info=True)
            return {
                "status": "error",
                "message": f"MVU reference experiment failed: {exc}",
                "diagnostics": [str(exc)],
            }

    async def run_ai_card_reference_experiment(self) -> Dict[str, Any]:
        """Run the software-only PCIe AI compute-card reference model."""
        if not self.adapter.enabled:
            return {
                "status": "unavailable",
                "message": "EDA integration is disabled by configuration",
                "diagnostics": ["eda.enabled=false"],
            }
        try:
            from ai.hardware.ai_card_reference import AiCardReferenceModel

            experiment = AiCardReferenceModel().run()
            packet_state = self.get_ai_card_interface_packet()
            packet = packet_state.get("packet", {}) if packet_state.get("ok") else {}
            pending_decisions = packet.get("pending_angela_decisions", [])
            workspace = self.adapter.create_workspace("ai_compute_card")
            artifact = self.adapter.write_text_artifact(
                workspace,
                "ai_card_reference_result",
                json.dumps(experiment, ensure_ascii=False, indent=2),
                "ai-compute-card-reference-episode",
            )
            learning = await self._record_learning_episode(
                workflow="ai_card_reference",
                parameters={
                    "schema_version": experiment.get("schema_version"),
                    "target_level": "L1",
                    "owner": "angela",
                    "support_owner": "environment_support",
                },
                tools=self.adapter.config.get("tools", {}),
                results={"ai_card_reference": experiment},
                artifacts=[artifact],
                workspace=workspace,
            )
            all_artifacts = [artifact]
            learning_artifact = learning.pop("artifact", None)
            if learning_artifact:
                all_artifacts.append(learning_artifact)
            technical_checks = experiment.get("design_verification", {}).get("technical_checks", {})
            verified = [name for name, passed in technical_checks.items() if passed]
            blockers = list(experiment.get("blockers", []))
            research_summary = {
                "verified_checks": verified,
                "blockers": blockers,
                "interface_freeze_packet": {
                    "status": packet.get("status", "unavailable"),
                    "pending_decision_count": len(pending_decisions),
                    "path": "hardware/ai_compute_card/angela_interface_freeze_packet.yaml",
                },
                "next_owner": "angela",
                "completion_claim_allowed": False,
            }
            summary = {
                "status": experiment["status"],
                "tool": "ai_compute_card",
                "result": experiment,
                "learning": learning,
                "artifacts": all_artifacts,
                "research_summary": research_summary,
                "message": (
                    f"AI card software reference={experiment['status']}，"
                    f"host={experiment['bandwidth']['pcie_effective_gbs_each_direction']}GB/s，"
                    f"internal={experiment['bandwidth']['main_internal_raw_gbs']}GB/s，"
                    f"cost={experiment['cost']['decision']}；"
                    f"已驗證={len(verified)} 項；"
                    f"阻塞={len(blockers)} 項（{blockers[0] if blockers else 'none'}）；"
                    f"待凍結決策={len(pending_decisions)} 項；"
                    "目前不可宣稱完成最終設計。"
                ),
            }
            result = self.adapter.finalize(workspace, summary)
            result["status"] = experiment["status"]
            result["message"] = summary["message"]
            return result
        except Exception as exc:
            logger.warning("AI compute card reference experiment failed", exc_info=True)
            return {
                "status": "error",
                "message": f"AI compute card reference experiment failed: {exc}",
                "diagnostics": [str(exc)],
            }

    def _spec_from_query(
        self,
        query: str,
        resistance_ohm: float,
        capacitance_f: float,
        width_um: float,
        height_um: float,
        sweep: bool,
    ) -> Dict[str, Any]:
        resistances = _query_numbers(query, "R")
        capacitances = _query_numbers(query, "C")
        if not resistances:
            base_resistance = float(resistance_ohm) if float(resistance_ohm) > 0 else 1_000.0
            resistances = list(dict.fromkeys([base_resistance, 4_700.0, 10_000.0]))
        if not capacitances:
            base_capacitance = float(capacitance_f) if float(capacitance_f) > 0 else 1e-6
            capacitances = list(dict.fromkeys([base_capacitance, 2.2e-7, 1e-6]))
        widths = _query_numbers(query, "W") or _query_numbers(query, "width")
        heights = _query_numbers(query, "H") or _query_numbers(query, "height")
        return {
            "resistance_ohm": resistances[0],
            "capacitance_f": capacitances[0],
            "width_um": widths[0] if widths else float(width_um),
            "height_um": heights[0] if heights else float(height_um),
            "sweep": sweep or bool(re.search(r"探索|扫描|掃描|sweep|explore", query or "", re.I)),
            "resistances": resistances,
            "capacitances": capacitances,
        }

    @staticmethod
    def _merge_artifacts(*groups: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        merged: Dict[Tuple[str, str], Dict[str, Any]] = {}
        for group in groups:
            for artifact in group:
                key = (str(artifact.get("type", "")), str(artifact.get("path", "")))
                merged[key] = artifact
        return list(merged.values())

    async def _run_sweep(
        self,
        workspace: EdaWorkspace,
        resistances: Sequence[float],
        capacitances: Sequence[float],
    ) -> Dict[str, Any]:
        combinations = [
            (resistance, capacitance) for resistance in resistances for capacitance in capacitances
        ]
        combinations = combinations[: self.adapter.max_sweep_points]
        rows: List[Dict[str, Any]] = []
        for resistance, capacitance in combinations:
            result = await self.adapter.run_ngspice(
                self.adapter.build_rc_netlist(resistance, capacitance),
                workspace=workspace,
                label=f"sweep_r{resistance:g}_c{capacitance:g}",
                finalize=False,
            )
            metrics = result.get("metrics", {})
            theoretical = 1.0 / (2.0 * math.pi * resistance * capacitance)
            measured = metrics.get("cutoff_hz")
            rows.append(
                {
                    "resistance_ohm": resistance,
                    "capacitance_f": capacitance,
                    "status": result.get("status"),
                    "measured_cutoff_hz": measured,
                    "theoretical_cutoff_hz": round(theoretical, 6),
                    "error_percent": (
                        round(abs(measured - theoretical) / theoretical * 100.0, 4)
                        if measured is not None
                        else None
                    ),
                }
            )
        successful = [row for row in rows if row.get("status") == "success"]
        successful.sort(
            key=lambda row: (
                row["error_percent"] if row["error_percent"] is not None else float("inf")
            )
        )
        csv_lines = ["resistance_ohm,capacitance_f,status,measured_hz,theoretical_hz,error_percent"]
        for row in rows:
            csv_lines.append(
                ",".join(
                    [
                        str(row["resistance_ohm"]),
                        str(row["capacitance_f"]),
                        str(row["status"]),
                        "" if row["measured_cutoff_hz"] is None else str(row["measured_cutoff_hz"]),
                        str(row["theoretical_cutoff_hz"]),
                        "" if row["error_percent"] is None else str(row["error_percent"]),
                    ]
                )
            )
        csv_artifact = self.adapter.write_text_artifact(
            workspace, "sweep_csv", "\n".join(csv_lines), "sweep-csv"
        )
        json_artifact = self.adapter.write_text_artifact(
            workspace,
            "sweep_json",
            json.dumps({"rows": rows, "best": successful[0] if successful else None}, indent=2),
            "sweep-json",
        )
        return {
            "status": "success" if successful else "unavailable",
            "point_count": len(rows),
            "successful_count": len(successful),
            "rows": rows,
            "best": successful[0] if successful else None,
            "artifacts": [csv_artifact, json_artifact],
        }

    @staticmethod
    def _is_design_request(query: str, workflow: str = "auto") -> bool:
        if workflow in {"all", "kicad", "easyeda", "jlcone", "pcb"}:
            return True
        return bool(
            re.search(
                r"\b(?:kicad|easyeda|jlcone|jlcpcb|pcb|gerber|bom)\b|電路板|电路板|印刷電路|PCB",
                query or "",
                re.IGNORECASE,
            )
        )

    async def run_design_experiment(
        self,
        query: str = "",
        width_mm: float = 40.0,
        height_mm: float = 30.0,
        easyeda_source: Optional[str] = None,
        easyeda_footprint: bool = False,
        workflow: str = "auto",
    ) -> Dict[str, Any]:
        """Run KiCad generation and explicit EasyEDA/JLCONE handoff workflows."""
        if not self.adapter.enabled:
            return {
                "status": "unavailable",
                "message": "EDA integration is disabled by configuration",
                "diagnostics": ["eda.enabled=false"],
            }
        requested = {
            "kicad": workflow in {"all", "kicad", "pcb"}
            or bool(re.search(r"kicad|gerber|pcb|電路板|电路板", query or "", re.I)),
            "easyeda": workflow in {"all", "easyeda"}
            or bool(re.search(r"easyeda", query or "", re.I)),
            "jlcone": workflow in {"all", "jlcone"}
            or bool(re.search(r"jlcone|jlcpcb", query or "", re.I)),
        }
        if not any(requested.values()):
            requested["kicad"] = True
        probe = await self.adapter.probe()
        workspace = self.adapter.create_workspace("angela_pcb")
        kicad: Dict[str, Any] = {
            "status": "skipped",
            "tool": "kicad",
            "artifacts": [],
            "metrics": {},
            "diagnostics": [],
        }
        easyeda: Dict[str, Any] = {
            "status": "skipped",
            "tool": "easyeda",
            "artifacts": [],
            "metrics": {},
            "diagnostics": [],
        }
        jlcone: Dict[str, Any] = {
            "status": "skipped",
            "tool": "jlcone",
            "artifacts": [],
            "metrics": {},
            "diagnostics": [],
        }
        try:
            if requested["kicad"]:
                kicad = await self.adapter.generate_kicad_board(
                    workspace, width_mm=width_mm, height_mm=height_mm
                )
            if requested["easyeda"]:
                if easyeda_source and easyeda_footprint:
                    easyeda = await self.adapter.convert_easyeda_footprint(
                        easyeda_source, workspace=workspace
                    )
                elif easyeda_source:
                    easyeda = await self.adapter.stage_easyeda_file(
                        easyeda_source, workspace=workspace
                    )
                else:
                    easyeda = self.adapter.prepare_easyeda_handoff(
                        workspace, kicad.get("artifacts", [])
                    )
            if requested["jlcone"]:
                jlcone = self.adapter.prepare_jlcone_handoff(workspace, kicad.get("artifacts", []))
            all_artifacts = self._merge_artifacts(
                kicad.get("artifacts", []),
                easyeda.get("artifacts", []),
                jlcone.get("artifacts", []),
            )
            learning = await self._record_learning_episode(
                workflow="pcb",
                parameters={
                    "width_mm": width_mm,
                    "height_mm": height_mm,
                    "requested": requested,
                },
                tools=probe["tools"],
                results={"kicad": kicad, "easyeda": easyeda, "jlcone": jlcone},
                artifacts=all_artifacts,
                workspace=workspace,
            )
            learning_artifact = learning.pop("artifact", None)
            if learning_artifact:
                all_artifacts.append(learning_artifact)
            result_by_tool = {"kicad": kicad, "easyeda": easyeda, "jlcone": jlcone}
            active = [name for name in requested if requested[name]]
            good = {
                name
                for name in active
                if result_by_tool[name].get("status")
                in {"success", "ready_for_client", "bridge_required"}
            }
            bridge_required = any(
                result_by_tool[name].get("status") == "bridge_required" for name in active
            )
            if not good:
                status = "unavailable"
            elif len(good) < len(active) or bridge_required:
                status = "partial"
            else:
                status = "success"
            summary = {
                "query": query,
                "workflow": workflow,
                "requested": requested,
                "tools": probe["tools"],
                "kicad": kicad,
                "easyeda": easyeda,
                "jlcone": jlcone,
                "learning": learning,
                "artifacts": all_artifacts,
                "status": status,
                "message": (
                    f"Angela PCB workflow：KiCad={kicad.get('status')}，"
                    f"EasyEDA={easyeda.get('status')}，JLCONE={jlcone.get('status')}；"
                    f"產物目錄={workspace.root}"
                ),
            }
            summary_artifact = self.adapter.write_text_artifact(
                workspace,
                "pcb_experiment_summary",
                json.dumps(summary, ensure_ascii=False, indent=2),
                "pcb-experiment-summary",
            )
            all_artifacts.append(summary_artifact)
            summary["artifacts"] = all_artifacts
            result = self.adapter.finalize(workspace, summary)
            result["status"] = status
            result["artifacts"] = all_artifacts
            result["message"] = (
                f"Angela PCB workflow：KiCad={kicad.get('status')}，"
                f"EasyEDA={easyeda.get('status')}，JLCONE={jlcone.get('status')}；"
                f"產物目錄={workspace.root}"
            )
            return result
        except Exception as exc:
            logger.warning("Angela PCB workflow failed", exc_info=True)
            return {
                "status": "error",
                "message": f"PCB workflow failed: {exc}",
                "diagnostics": [str(exc)],
            }

    async def run_experiment(
        self,
        query: str = "",
        resistance_ohm: float = 1_000.0,
        capacitance_f: float = 1e-6,
        width_um: float = 20.0,
        height_um: float = 10.0,
        sweep: bool = True,
        workflow: str = "auto",
        width_mm: float = 40.0,
        height_mm: float = 30.0,
        easyeda_source: Optional[str] = None,
        easyeda_footprint: bool = False,
    ) -> Dict[str, Any]:
        """Run Angela's bounded generate → simulate → explore → check pipeline."""
        if not self.adapter.enabled:
            return {
                "status": "unavailable",
                "message": "EDA integration is disabled by configuration",
                "diagnostics": ["eda.enabled=false"],
            }
        if workflow != "ic" and self._is_design_request(query, workflow):
            return await self.run_design_experiment(
                query=query,
                width_mm=width_mm,
                height_mm=height_mm,
                easyeda_source=easyeda_source,
                easyeda_footprint=easyeda_footprint,
                workflow=workflow,
            )
        try:
            spec = self._spec_from_query(
                query, resistance_ohm, capacitance_f, width_um, height_um, sweep
            )
            probe = await self.adapter.probe()
            workspace = self.adapter.create_workspace("angela_eda")
            layout = await self.adapter.generate_layout(
                workspace,
                label="layout",
                width_um=spec["width_um"],
                height_um=spec["height_um"],
            )
            deck = self.adapter.build_rc_netlist(spec["resistance_ohm"], spec["capacitance_f"])
            simulation = await self.adapter.run_ngspice(
                deck, workspace=workspace, label="rc_filter", finalize=False
            )
            exploration = (
                await self._run_sweep(workspace, spec["resistances"], spec["capacitances"])
                if spec["sweep"]
                else {
                    "status": "skipped",
                    "point_count": 0,
                    "successful_count": 0,
                    "rows": [],
                    "best": None,
                    "artifacts": [],
                }
            )
            magic: Dict[str, Any] = {
                "status": "skipped",
                "tool": "magic",
                "artifacts": [],
                "metrics": {},
                "diagnostics": ["KLayout did not produce a GDS input"],
            }
            gds_artifact = next(
                (item for item in layout.get("artifacts", []) if item.get("type") == "gds"),
                None,
            )
            magic_available = probe["tools"].get("magic", {}).get("available", False)
            if gds_artifact and magic_available:
                magic = await self.adapter.run_magic(
                    gds_artifact["path"], workspace=workspace, label="magic_layout"
                )
            all_artifacts = self._merge_artifacts(
                layout.get("artifacts", []),
                simulation.get("artifacts", []),
                exploration.get("artifacts", []),
                magic.get("artifacts", []),
            )
            learning = await self._record_learning_episode(
                workflow="ic",
                parameters=spec,
                tools=probe["tools"],
                results={
                    "layout": layout,
                    "simulation": simulation,
                    "exploration": exploration,
                    "magic": magic,
                },
                artifacts=all_artifacts,
                workspace=workspace,
            )
            learning_artifact = learning.pop("artifact", None)
            if learning_artifact:
                all_artifacts.append(learning_artifact)
            successful_tools = [
                name
                for name, result in (
                    ("klayout", layout),
                    ("ngspice", simulation),
                )
                if result.get("status") == "success"
            ]
            if not successful_tools:
                status = "unavailable"
            elif len(successful_tools) < 2:
                status = "partial"
            else:
                status = "success"
            magic_metrics = magic.get("metrics", {})
            if magic.get("status") == "success":
                magic_note = "Magic DRC 已驗證"
            elif magic_metrics.get("drc_error_count"):
                magic_note = f"Magic DRC 發現 {magic_metrics['drc_error_count']} 個錯誤"
            elif magic_metrics.get("pdk_ready"):
                magic_note = "Magic PDK 已載入，但 headless DRC 未完成認證"
            else:
                magic_note = "Magic 缺少可用 PDK，未宣稱 DRC 通過"
            best = exploration.get("best")
            best_note = (
                f"；最佳候選 R={best['resistance_ohm']:g}Ω/C={best['capacitance_f']:g}F"
                if best
                else ""
            )
            summary = {
                "query": query,
                "spec": spec,
                "tools": probe["tools"],
                "layout": layout,
                "simulation": simulation,
                "exploration": exploration,
                "magic": magic,
                "learning": learning,
                "artifacts": all_artifacts,
            }
            summary_artifact = self.adapter.write_text_artifact(
                workspace,
                "experiment_summary",
                json.dumps(summary, ensure_ascii=False, indent=2),
                "experiment-summary",
            )
            all_artifacts.append(summary_artifact)
            summary["artifacts"] = all_artifacts
            result = self.adapter.finalize(workspace, summary)
            result["status"] = status
            result["artifacts"] = all_artifacts
            result["message"] = (
                f"Angela EDA 完成：{', '.join(successful_tools) or '沒有可執行工具'}；"
                f"模擬截止頻率={simulation.get('metrics', {}).get('cutoff_hz')}Hz；"
                f"探索點={exploration.get('successful_count', 0)}；{magic_note}{best_note}；"
                f"產物目錄={workspace.root}"
            )
            return result
        except Exception as exc:
            logger.warning("Angela EDA experiment failed", exc_info=True)
            return {
                "status": "error",
                "message": f"EDA experiment failed: {exc}",
                "diagnostics": [str(exc)],
            }

    async def generate(self, query: str = "", **kwargs: Any) -> Dict[str, Any]:
        return await self.run_experiment(query, sweep=False, **kwargs)

    async def explore(self, query: str = "", **kwargs: Any) -> Dict[str, Any]:
        return await self.run_experiment(query, sweep=True, **kwargs)


__all__ = ["EdaAgent"]
