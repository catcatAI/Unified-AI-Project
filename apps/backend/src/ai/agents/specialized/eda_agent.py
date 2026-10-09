# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

"""Angela's sandboxed EDA experiment agent."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
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
                "description": "讀取 AI 計算卡決策包與待驗證項目",
                "version": "0.1.0",
            },
            {
                "name": "cim_strip_reference",
                "capability_id": "cim_strip_reference",
                "description": "以實測單元電流推導 CIM strip 的線性度、功耗、能耗與面積",
                "version": "0.1.0",
            },
            {
                "name": "cim_spice_verify",
                "capability_id": "cim_spice_verify",
                "description": "用 ngspice 重跑 strip 權重響應，證偽或證實凍結包聲稱的 1:2:4:8",
                "version": "0.1.0",
            },
            {
                "name": "cim_dot_product_verify",
                "capability_id": "cim_dot_product_verify",
                "description": "以實測單元電流跑真實 int8 矩陣向量乘，確認陣列真的會算",
                "version": "0.1.0",
            },
            {
                "name": "cim_extracted_netlist_sim",
                "capability_id": "cim_extracted_netlist_sim",
                "description": "模擬萃取後的版圖 netlist，確認畫出來的矽真的會算",
                "version": "0.1.0",
            },
            {
                "name": "cim_single_die_experiment",
                "capability_id": "cim_single_die_experiment",
                "description": "以實測陣列密度複查單 die 容量，取代凍結包聲稱的 0.42um2/cell",
                "version": "0.1.0",
            },
            {
                "name": "card_architecture_audit",
                "capability_id": "card_architecture_audit",
                "description": "用實測 sky130 製程數據重算卡級架構摘要的每個數字並標出修正",
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
            / "hardware/assemblies/wip/ai_compute_card/angela_interface_freeze_packet.yaml"
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

    async def verify_cim_weight_response(self) -> Dict[str, Any]:
        """Check the strip weight-response claim instead of trusting it.

        The freeze packet asserts that current-summed addition is exact and that
        weights scale 1:2:4:8. This recomputes that from the measured fixture and,
        when a sky130 model library is installed, re-derives it with ngspice so a
        future cell change that breaks linearity fails loudly rather than
        silently inheriting an old pass.
        """
        from ai.hardware.cim_strip_reference import (
            WEIGHT_RESPONSE_MEASUREMENT,
            evaluate_weight_response,
            simulate_weight_response,
        )

        declared = WEIGHT_RESPONSE_MEASUREMENT
        cells = [int(value) for value in declared["cells_per_bin"]]
        measured: Dict[str, float] = {"idle": float(declared["word_0000_a"])}
        for index, (count, current) in enumerate(zip(cells, declared["single_hot_currents_a"])):
            measured[f"bin{index}"] = float(current)
            measured[f"bin{index}_cells"] = float(count)
        measured["all_hot"] = float(declared["word_1111_sum_a"])
        static = evaluate_weight_response(measured)
        static["source"] = "bundled_measurement_fixture"
        static["fixture"] = declared["fixture"]

        run_directory: Optional[Path] = None
        if self.adapter.enabled:
            workspace = self.adapter.create_workspace("cim_spice")
            run_directory = workspace.root
        if run_directory is None:
            skipped = {"status": "skipped", "reason": "eda_disabled"}
            simulator: Dict[str, Any] = skipped
            reduced: Dict[str, Any] = skipped
        else:
            simulator = await simulate_weight_response(run_directory)
            reduced = await self._simulate_reduced_rail_weight_response(run_directory)

        agreed = simulator.get("status") in {"pass", "skipped"}
        reduced_agreed = reduced.get("status") in {"pass", "skipped"}
        static_ok = static.get("status") == "pass"
        # An absent simulator is not evidence against the claim, but a
        # measurement that actually fails is.
        reduced_failed = reduced.get("status") == "fail"
        return {
            "status": ("verified" if static_ok and not reduced_failed else "failed"),
            "static_check": static,
            "simulator_cross_check": simulator,
            "simulator_agrees_with_fixture": agreed,
            "reduced_rail_cross_check": reduced,
            "reduced_rail_agrees_with_model": reduced_agreed,
            "note": (
                "the current fixture measures an exact parallel-cell response; "
                "the superseded first fixture is retained in the model so the "
                "fixed defect stays quantified instead of being forgotten"
            ),
            "reduced_rail_note": (
                "identical parallel cells add by construction in SPICE, so this "
                "re-check establishes that the cell still conducts a usable, "
                "ratio-preserving current at the design operating point; it does "
                "not cover mismatch, corners or the sense chain"
            ),
        }

    async def _simulate_reduced_rail_weight_response(self, run_directory: Path) -> Dict[str, Any]:
        """Re-run the weight response at the model's recommended operating point.

        The recorded fixture measurement was taken at 1.8V, which is the drafted
        rail the design intends to leave. Re-checking at the recommended point
        answers the open question "does the same 1:2:4:8 hold where we will
        actually run" instead of assuming the 1.8V result carries over.
        """
        from ai.hardware.cim_strip_reference import (
            CimStripReferenceModel,
            simulate_weight_response,
        )

        point = CimStripReferenceModel().recommended_design().get("design_point")
        if not point:
            return {"status": "skipped", "reason": "no_recommended_design_point"}
        vds_v = float(point["array_vds_v"])
        vgs_v = float(point["input_vgs_max_v"])
        result = await simulate_weight_response(
            run_directory / f"reduced_rail_{vds_v:g}v_{vgs_v:g}v",
            vds_v=vds_v,
            vgs_v=vgs_v,
        )
        result["array_vds_v"] = vds_v
        result["input_vgs_max_v"] = vgs_v
        return result

    async def run_cim_strip_experiment(
        self,
        array_vds_v: Optional[float] = None,
        input_vgs_max_v: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Run the measured current-mode CIM strip model for the current process.

        This is the counterpart to ``run_ai_card_reference_experiment``: that one
        models the digital end-state card, this one models the current-process
        CIM strip that the freeze packet proposes, using real measured cell
        currents so the power budget is derived rather than assumed.
        """
        if not self.adapter.enabled:
            return {
                "status": "unavailable",
                "message": "EDA integration is disabled by configuration",
                "diagnostics": ["eda.enabled=false"],
            }
        try:
            from ai.hardware.cim_strip_reference import CimStripConfig, CimStripReferenceModel

            overrides: Dict[str, Any] = {}
            if array_vds_v is not None:
                overrides["array_vds_v"] = float(array_vds_v)
            if input_vgs_max_v is not None:
                overrides["input_vgs_max_v"] = float(input_vgs_max_v)
            config = CimStripConfig(**overrides)
            model = CimStripReferenceModel(config)
            experiment = model.run()
            verification = await self.verify_cim_weight_response()

            workspace = self.adapter.create_workspace("cim_strip")
            artifact = self.adapter.write_text_artifact(
                workspace,
                "cim_strip_result",
                json.dumps(experiment, ensure_ascii=False, indent=2),
                "cim-strip-episode",
            )
            verification_artifact = self.adapter.write_text_artifact(
                workspace,
                "cim_weight_response_verification",
                json.dumps(verification, ensure_ascii=False, indent=2),
                "cim-weight-response-verification",
            )
            learning = await self._record_learning_episode(
                workflow="cim_strip",
                parameters={
                    "array_vds_v": config.array_vds_v,
                    "input_vgs_max_v": config.input_vgs_max_v,
                    "dies_per_package": config.dies_per_package,
                    "strips_per_die": config.strips_per_die,
                    "end_state_figures_used": False,
                },
                tools=self.adapter.config.get("tools", {}),
                results={"cim_strip": experiment, "weight_response": verification},
                artifacts=[artifact, verification_artifact],
                workspace=workspace,
            )
            all_artifacts = [artifact, verification_artifact]
            learning_artifact = learning.pop("artifact", None)
            if learning_artifact:
                all_artifacts.append(learning_artifact)

            blockers = list(experiment.get("blockers", []))
            gates = experiment.get("gate_summary", {})
            recommended = experiment.get("recommended_design", {})
            point = recommended.get("design_point")
            design_note = (
                "；可行現行製程設計點："
                f"陣列軌 {point['array_vds_v']}V／輸入擺幅 {point['input_vgs_max_v']}V／"
                f"感測窗 {point['sense_time_s'] * 1e9:.0f}ns → "
                f"{point['energy_pj_per_mac']:.3f}pJ/MAC、整卡 {point['card_power_w']:.1f}W、"
                f"{point['resolution_bits']:.1f} bit 雜訊解析度"
                if point
                else "；尚未找到通過全部閘門的現行製程設計點"
            )
            summary = {
                "status": "blocked" if blockers else "gates_passed",
                "tool": "cim_strip",
                "result": experiment,
                "weight_response_verification": verification,
                "learning": learning,
                "artifacts": all_artifacts,
                "research_summary": {
                    "gate_summary": gates,
                    "blockers": blockers,
                    "warnings": list(experiment.get("warnings", [])),
                    "recommended_design_point": point,
                    "recommended_design_sensitivity": {
                        "sense_time": recommended.get("sense_time_sensitivity"),
                        "sense_chain_power": recommended.get("sense_chain_power_sensitivity"),
                    },
                    "next_owner": "angela",
                    "completion_claim_allowed": False,
                },
                "message": (
                    f"CIM strip current-process 模型：線性度="
                    f"{'通過' if gates.get('weight_linearity_passed') else '未通過'}，"
                    f"單封裝功耗="
                    f"{experiment['power_envelope']['scenarios'][0]['package_power_w']:.1f}W，"
                    f"{config.packages_per_card} 封裝整卡="
                    f"{experiment['power_envelope']['scenarios'][0]['card_power_w']:.0f}W"
                    f"（預算 {config.board_power_budget_w:.0f}W 的 "
                    f"{experiment['power_envelope']['card_fills_board_budget_x']:.2f} 倍），"
                    f"能耗="
                    f"{experiment['published_comparison']['modelled_energy_pj_per_mac']:.0f}pJ/MAC，"
                    f"阻塞={len(blockers)} 項"
                    f"{design_note}；"
                    "目前不可宣稱最終架構已定案。"
                ),
            }
            result = self.adapter.finalize(workspace, summary)
            result["status"] = summary["status"]
            result["message"] = summary["message"]
            result["artifacts"] = all_artifacts
            return result
        except Exception as exc:
            logger.warning("CIM strip experiment failed", exc_info=True)
            return {
                "status": "error",
                "message": f"CIM strip experiment failed: {exc}",
                "diagnostics": [str(exc)],
            }

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
            pending_decisions = packet.get("pending_decisions", [])
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
                    "path": "hardware/assemblies/wip/ai_compute_card/angela_interface_freeze_packet.yaml",
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
                    f"待驗決策={len(pending_decisions)} 項；"
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

    async def run_cim_dot_product_experiment(
        self,
        cases: int = 6,
        strips: int = 4,
        slots: int = 6,
        array_vds_v: float = 0.3,
        input_vgs_v: float = 1.0,
        seed: int = 20260927,
    ) -> Dict[str, Any]:
        """Run real int8 matrix-vector cases through the array and check the answers.

        This is the check that the cell *computes*, as opposed to merely having
        the right current ratios. A weight is realised by its binary bits, so the
        spine current divided by the single-cell current must equal the exact
        integer dot product, with no fitting and no tolerance to hide behind.
        """
        if not self.adapter.enabled:
            return {
                "status": "unavailable",
                "message": "EDA integration is disabled by configuration",
                "diagnostics": ["eda.enabled=false"],
            }
        try:
            import random

            from ai.hardware.cim_strip_reference import (
                DotProductVector,
                run_functional_dot_product_test,
            )

            if cases < 1 or strips < 1 or slots < 1:
                raise ValueError("cases, strips and slots must be positive")
            rnd = random.Random(seed)
            vectors = [
                DotProductVector(
                    input_bits=(1, 1, 0, 0, 1, 0),
                    strip_weights=(
                        (1, 2, 4, 8, 16, 32),
                        (255, 0, 0, 0, 0, 0),
                        (0, 0, 0, 0, 0, 1),
                        (128, 64, 32, 16, 8, 4),
                    )[:strips],
                    label="hand_checked",
                )
            ]
            for index in range(cases - 1):
                vectors.append(
                    DotProductVector(
                        input_bits=tuple(rnd.randint(0, 1) for _ in range(slots)),
                        strip_weights=tuple(
                            tuple(rnd.randint(0, 255) for _ in range(slots)) for _ in range(strips)
                        ),
                        label=f"random_{index}",
                    )
                )
            workspace = self.adapter.create_workspace("cim_dot_product")
            result = await run_functional_dot_product_test(
                workspace.root,
                vectors,
                array_vds_v=array_vds_v,
                input_vgs_v=input_vgs_v,
            )
            artifact = self.adapter.write_text_artifact(
                workspace,
                "cim_dot_product_result",
                json.dumps(result, ensure_ascii=False, indent=2),
                "cim-dot-product-episode",
            )
            status = result.get("status", "error")
            summary = {
                "status": status,
                "tool": "cim_dot_product",
                "result": result,
                "artifacts": [artifact],
                "message": (
                    f"CIM int8 矩陣向量乘驗證：{result.get('cases_passed', 0)}/"
                    f"{result.get('case_count', 0)} 案例通過，"
                    f"模擬單元數 {result.get('total_cell_count', 0)}，"
                    f"陣列軌 {array_vds_v}V／輸入擺幅 {input_vgs_v}V。"
                    if result.get("cases")
                    else f"CIM 點積驗證未執行：{result.get('reason', status)}"
                ),
            }
            finalized = self.adapter.finalize(workspace, summary)
            finalized["status"] = status
            finalized["message"] = summary["message"]
            finalized["artifacts"] = [artifact]
            return finalized
        except Exception as exc:
            logger.warning("CIM dot product experiment failed", exc_info=True)
            return {
                "status": "error",
                "message": f"CIM dot product experiment failed: {exc}",
                "diagnostics": [str(exc)],
            }

    async def run_cim_single_die_experiment(
        self,
        weight_bits: int = 4,
        slots: int = 2,
        die_area_mm2: Optional[float] = None,
        array_fraction: float = 0.65,
        simulate_extracted: bool = False,
    ) -> Dict[str, Any]:
        """Re-ask the single-die capacity question against a measured cell area.

        The interface-freeze packet sized 1 MB of int8 weights at 0.42 um2 per
        cell, which is its bare device rectangle with no contacts, no spacing and
        no routing. This lays the array out again, tiles ``slots`` strips so the
        area is measured on an array rather than on one block's edge margin, and
        re-derives the capacity table from the density it measured. The packet's
        figure is kept in the report so the correction stays a visible diff, and
        the single-die verdict is re-asked instead of inherited.
        """
        if not self.adapter.enabled:
            return {
                "status": "unavailable",
                "message": "EDA integration is disabled by configuration",
                "diagnostics": ["eda.enabled=false"],
            }
        try:
            from ai.hardware.card_architecture_audit import ANALOG_CIM_DENSITY
            from ai.hardware.cim_strip_reference import (
                MEASUREMENT_PROVENANCE,
                MIN_CHARACTERISED_NFET_W_UM,
                CimStripConfig,
                find_sky130_model_library,
            )
            from ai.hardware.cim_toolchain import MODEL_LIBRARY
            from ai.hardware.cim_verify import verify_weights
            from ai.hardware.cim_weight_strip import (
                WeightStripGeometry,
                build_strip,
                extract,
                spine_topology,
                tile_strips,
            )

            if not 2 <= weight_bits <= 8:
                raise ValueError("weight_bits must be in [2, 8]")
            if slots < 1:
                raise ValueError("slots must be positive")
            config = CimStripConfig()
            area_budget_mm2 = float(die_area_mm2 or config.die_area_budget_mm2)

            bins = tuple(1 << bit for bit in range(weight_bits))
            strip = build_strip(WeightStripGeometry(columns=weight_bits, weight_bins=bins))
            tile = tile_strips(strip, slots)
            workspace = self.adapter.create_workspace("cim_single_die")
            run = extract(tile, workspace.root)
            expected = int(tile["transistors_total"])
            drc_errors = run.get("drc_errors")
            extracted = run.get("extracted")
            if run.get("status") == "skipped":
                layout_status = "skipped"
            elif run.get("status") == "ok" and drc_errors == 0 and extracted == expected:
                layout_status = "ok"
            else:
                layout_status = "failed"
            spice_path = workspace.root / "strip.spice"
            layout_verification = {
                "status": layout_status,
                "reason": run.get("reason"),
                "drc_errors": drc_errors,
                "extracted_transistors": extracted,
                "expected_transistors": expected,
                "spine_topology": spine_topology(spice_path) if spice_path.is_file() else {},
                "tile_copies": slots,
                "tile_cells": expected,
                "tile_width_um": round(float(tile["width_um"]), 3),
                "tile_height_um": round(float(tile["height_um"]), 3),
                "tile_um2_per_cell": round(float(tile["um2_per_transistor"]), 4),
            }

            claimed_cell_um2 = float(config.cell_footprint_um2)
            measured_cell_um2 = float(tile["um2_per_transistor"])
            drafted_cell_w_um = float(MEASUREMENT_PROVENANCE["cell_w_um"])
            bare_device_um2 = drafted_cell_w_um * float(MEASUREMENT_PROVENANCE["cell_l_um"])
            dense_um2 = float(ANALOG_CIM_DENSITY.um2_per_element)
            density_findings = {
                "measured_um2_per_cell": round(measured_cell_um2, 4),
                "measured_on": (
                    f"{slots} DRC-checked strip(s), {expected} extracted cells, "
                    f"{weight_bits}-bit weight columns"
                ),
                "claimed_um2_per_cell": claimed_cell_um2,
                "claim_source": "freeze packet area model (CimStripConfig.cell_footprint_um2)",
                "measured_over_claimed_x": round(measured_cell_um2 / claimed_cell_um2, 3),
                "bare_device_wl_um2": round(bare_device_um2, 4),
                "measured_over_bare_device_x": round(measured_cell_um2 / bare_device_um2, 2),
                "dense_array_um2_per_cell": dense_um2,
                "dense_array_provenance": ANALOG_CIM_DENSITY.provenance,
                "dense_array_measured_here": ANALOG_CIM_DENSITY.measured_in_this_repository,
                "pdk_min_characterised_w_um": MIN_CHARACTERISED_NFET_W_UM,
                "drafted_cell_w_um": drafted_cell_w_um,
                "pdk_covers_drafted_cell": drafted_cell_w_um >= MIN_CHARACTERISED_NFET_W_UM,
                "note": (
                    f"the packet's {claimed_cell_um2:.2f} um2 per cell is its bare "
                    f"device W*L figure, while the device rectangle itself is "
                    f"{bare_device_um2:.3f} um2 and the cell actually laid out, "
                    f"DRC-checked and extracted here measures {measured_cell_um2:.2f} um2 "
                    f"({measured_cell_um2 / claimed_cell_um2:.1f}x the claim) once "
                    "contacts, spacing and routing exist; the PDK additionally only "
                    f"characterises the nfet down to W={MIN_CHARACTERISED_NFET_W_UM}um, "
                    f"above the {drafted_cell_w_um}um cell drafted here, so the drawn "
                    "cell has no characterised model"
                ),
            }

            cells_per_weight = int(config.cells_per_weight_max)

            def capacity_kb(area_mm2_value: float, density_um2: float) -> float:
                cells = area_mm2_value * 1.0e6 * array_fraction / density_um2
                return cells / cells_per_weight / 1024.0

            def array_area_mm2(weight_mb: float, density_um2: float) -> float:
                weights = weight_mb * 1024.0 * 1024.0
                return weights * cells_per_weight * density_um2 / 1.0e6

            die_areas = (1.5, 4.0, 9.0, 25.0, 100.0)
            single_die_sizing = {
                "density_um2_per_cell_used": round(measured_cell_um2, 4),
                "density_source": "measured here on the DRC-checked array tile",
                "cells_per_weight": cells_per_weight,
                "cells_per_weight_model": (
                    "the packet's own bit-serial model, so the only thing that "
                    "changed against the packet is the measured density"
                ),
                "array_fraction": array_fraction,
                "array_fraction_is_an_assumption": True,
                "capacity": {
                    "die_area_mm2": area_budget_mm2,
                    "weight_capacity_kb": round(capacity_kb(area_budget_mm2, measured_cell_um2), 2),
                    "weight_capacity_mb": round(
                        capacity_kb(area_budget_mm2, measured_cell_um2) / 1024.0, 4
                    ),
                },
                "capacity_kb_by_die_area_mm2": {
                    f"{area:g}": round(capacity_kb(area, measured_cell_um2), 2)
                    for area in die_areas
                },
                "array_area_mm2_required_for": {
                    "weights_1mb": round(array_area_mm2(1.0, measured_cell_um2), 2),
                    "weights_16mb": round(array_area_mm2(16.0, measured_cell_um2), 2),
                },
                "best_case_with_dense_array_mm2_required_for": {
                    "weights_1mb": round(array_area_mm2(1.0, dense_um2), 2),
                    "weights_16mb": round(array_area_mm2(16.0, dense_um2), 2),
                    "density_um2_per_cell": dense_um2,
                },
                "single_die_verdict": (
                    f"1 MB of int8 weights needs about "
                    f"{array_area_mm2(1.0, measured_cell_um2):.1f} mm2 of array at the "
                    f"density measured here and "
                    f"{array_area_mm2(16.0, measured_cell_um2):.0f} mm2 for the 16 MB "
                    f"working set, so neither fits a {area_budget_mm2:g} mm2 die; even at "
                    f"the densest array this repository has measured ({dense_um2} um2 per "
                    f"cell) the 1 MB figure is "
                    f"{array_area_mm2(1.0, dense_um2):.1f} mm2 of array alone, before "
                    "the sense chain, sequencer, pad ring and power grid are placed, so "
                    "the co-package is not optional scope"
                ),
            }

            simulation: Dict[str, Any] = {"status": "not_requested"}
            if simulate_extracted:
                library = MODEL_LIBRARY if MODEL_LIBRARY.is_file() else None
                if library is None:
                    library = find_sky130_model_library()
                if library is None:
                    simulation = {
                        "status": "skipped",
                        "reason": "sky130_model_library_not_found",
                    }
                else:
                    sim_directory = workspace.root / "single_strip"
                    sim_spice_path = spice_path
                    if slots > 1:
                        # Every copy of the tile is identical, so one strip is the
                        # whole weight-ratio gate and the tiled netlist would
                        # otherwise mix several copies into one ratio test.
                        sim_directory.mkdir(parents=True, exist_ok=True)
                        extract(strip, sim_directory)
                        sim_spice_path = sim_directory / "strip.spice"
                    if not sim_spice_path.is_file():
                        simulation = {
                            "status": "skipped",
                            "reason": "extracted_netlist_missing",
                        }
                    else:
                        report = verify_weights(
                            sim_spice_path.read_text(encoding="utf-8", errors="replace"),
                            bins,
                            library,
                        )
                        simulation = {
                            "status": "pass" if report.ok else "fail",
                            "weights": report.as_dict(),
                            "model_library": str(library),
                            "note": (
                                "the weight-ratio gate runs on one strip: the tile's "
                                "copies are identical by construction"
                            ),
                        }

            if layout_status == "ok":
                status = "verified"
            elif layout_status == "skipped":
                status = "layout_skipped"
            else:
                status = "layout_failed"
            message = (
                f"CIM 單 die 面積複查：實測 {measured_cell_um2:.2f} um2/cell、"
                f"凍結包聲稱 {claimed_cell_um2:.2f} um2/cell"
                f"（{measured_cell_um2 / claimed_cell_um2:.1f} 倍）；"
                f"{weight_bits}-bit 權重 × {slots} 條 strip tile："
                f"DRC={drc_errors}、萃取 {extracted}/{expected} 顆；"
                f"依實測密度 1MB int8 權重需 "
                f"{array_area_mm2(1.0, measured_cell_um2):.1f}mm2、16MB 需 "
                f"{array_area_mm2(16.0, measured_cell_um2):.0f}mm2，"
                f"{area_budget_mm2:g}mm2 die 僅容納 "
                f"{capacity_kb(area_budget_mm2, measured_cell_um2):.1f}KB；"
                f"PDK 僅保證 W>={MIN_CHARACTERISED_NFET_W_UM}um，草稿 cell 為 "
                f"{drafted_cell_w_um}um；不可宣稱單 die 可達成容量目標。"
            )
            report_payload = {
                "schema_version": "cim-single-die/1",
                "owner": "angela",
                "weight_bits": weight_bits,
                "slots": slots,
                "layout_verification": layout_verification,
                "density_findings": density_findings,
                "single_die_sizing": single_die_sizing,
                "extracted_simulation": simulation,
                "completion_claim_allowed": False,
            }
            artifact = self.adapter.write_text_artifact(
                workspace,
                "cim_single_die_result",
                json.dumps(report_payload, ensure_ascii=False, indent=2),
                "cim-single-die-episode",
            )
            learning = await self._record_learning_episode(
                workflow="cim_single_die",
                parameters={
                    "weight_bits": weight_bits,
                    "slots": slots,
                    "die_area_mm2": area_budget_mm2,
                    "array_fraction": array_fraction,
                    "measured_um2_per_cell": round(measured_cell_um2, 4),
                },
                tools=self.adapter.config.get("tools", {}),
                results={
                    "layout_verification": layout_verification,
                    "density_findings": density_findings,
                    "single_die_sizing": single_die_sizing,
                },
                artifacts=[artifact],
                workspace=workspace,
            )
            artifacts = [artifact]
            learning_artifact = learning.pop("artifact", None)
            if learning_artifact:
                artifacts.append(learning_artifact)
            summary = {
                "status": status,
                "tool": "cim_single_die",
                "result": report_payload,
                "learning": learning,
                "artifacts": artifacts,
                "message": message,
            }
            finalized = self.adapter.finalize(workspace, summary)
            finalized["status"] = status
            finalized["message"] = message
            finalized["artifacts"] = artifacts
            return finalized
        except Exception as exc:
            logger.warning("CIM single-die experiment failed", exc_info=True)
            return {
                "status": "error",
                "message": f"CIM single-die experiment failed: {exc}",
                "diagnostics": [str(exc)],
            }

    async def run_card_architecture_audit(self) -> Dict[str, Any]:
        """Re-derive a card architecture summary against measured process data.

        Claims about throughput, L1 capacity and power are only worth as much as
        the assumptions under them, so this recomputes each one and reports the
        density it used, flagging the ones that rest on literature rather than on
        anything measured in this repository.
        """
        try:
            from ai.hardware.card_architecture_audit import audit

            report = audit()
            blocking = [item for item in report["corrections"] if item["severity"] == "blocking"]
            material = [item for item in report["corrections"] if item["severity"] == "material"]
            recomputed = report["recomputed"]
            message = (
                f"卡級架構審計：阻斷 {len(blocking)} 項／待補 {len(material)} 項。"
                f"權重串流需 "
                f"{recomputed['weight_streaming']['required_weight_bandwidth_gbs'] / 1000:.2f}"
                f" TB/s、最佳路徑僅 "
                f"{recomputed['weight_streaming']['best_available_gbs'] / 1000:.3f} TB/s"
                f"（差 {recomputed['weight_streaming']['shortfall_x']:.0f} 倍）；"
                f"L1 僅容納模型的 "
                f"{recomputed['weight_streaming']['l1_resident_fraction'] * 100:.0f}%，"
                f"要常駐需 "
                f"{recomputed['l1_residency']['per_die_capacity_mb']:.0f}MB/die"
                f"（現為 {recomputed['l1_residency']['claimed_l1_mb_per_die']:.1f}MB）；"
                f"單 die 算力需每 bit-plane 約 "
                f"{recomputed['sense_amplifier_budget']['required_parallel_sense_amps_per_plane']:.0f}"
                f" 顆感測放大器；"
                f"die 面積 {recomputed['die_area']['total_area_mm2_per_die']:.0f}mm2 "
                f"（其中 L1 與控制器的密度來自文獻，非本專案實測）。"
            )
            return {
                "status": "corrected" if blocking else "no_blocking_findings",
                "tool": "card_architecture_audit",
                "result": report,
                "blocking_finding_count": len(blocking),
                "material_finding_count": len(material),
                "completion_claim_allowed": False,
                "message": message,
            }
        except Exception as exc:
            logger.warning("Card architecture audit failed", exc_info=True)
            return {
                "status": "error",
                "message": f"Card architecture audit failed: {exc}",
                "diagnostics": [str(exc)],
            }


__all__ = ["EdaAgent"]
