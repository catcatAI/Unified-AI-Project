# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================

"""Audit tests for hardware/edge_card/edge_card_spec.yaml.

The spec is a decision record written before any hardware exists, so these
tests re-derive every committed number (link payload, working-set envelope,
decode bandwidth bound, power envelope) from first principles instead of
trusting the transcribed digits.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

SPEC_PATH = Path(__file__).resolve().parents[2] / "hardware/edge_card/edge_card_spec.yaml"


def _load_spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


# -----------------------------------------------------------------------------
# provenance / housekeeping
# -----------------------------------------------------------------------------
def test_spec_status_and_ownership() -> None:
    spec = _load_spec()

    assert spec["status"] == "draft_awaiting_acceptance_check"
    assert spec["owner"] == "angela"
    assert spec["schema_version"] == "edge-card-spec/1"
    assert spec["current_target"].startswith("L0")


def test_spec_sources_carry_url_and_claim() -> None:
    spec = _load_spec()

    assert spec["sources"], "sources section must not be empty"
    for source_id, source in spec["sources"].items():
        assert source_id.startswith("src_"), source_id
        assert source["what"], source_id
        assert source["url"], source_id
        assert source["type"], source_id


def test_spec_declares_no_prices() -> None:
    spec = _load_spec()

    assert spec["component_selection_policy"]["price_status_default"] == "quote_required"
    assert spec["component_selection_policy"]["do_not_purchase_without_human_approval"] is True
    assert any("no prices" in claim for claim in spec["explicit_non_claims"])
    assert not SPEC_PATH.read_text(encoding="utf-8").count("price_usd")


# -----------------------------------------------------------------------------
# product decision: Gen4 x1 endpoint
# -----------------------------------------------------------------------------
def test_product_decision_locks_gen4_x1() -> None:
    spec = _load_spec()
    host = spec["host_interface"]

    assert spec["product_decision"]["host_link"] == "PCIe-Gen4-x1-endpoint"
    assert host["gen"] == 4.0
    assert host["lanes"] == 1
    assert host["signaling_rate_gbps_per_lane"] == 16
    assert host["payload_encoding"] == "128b/130b"
    assert host["endpoint_mechanism"]["module_speed_cap"] == "gen4"
    assert host["endpoint_mechanism"]["flr"] == "required"
    assert host["endpoint_mechanism"]["msi"] == "required"


def test_pcie_gen4_x1_payload_derivation() -> None:
    host = _load_spec()["host_interface"]

    raw_gbps = host["signaling_rate_gbps_per_lane"] * 128 / 130
    payload_gbs = raw_gbps / 8

    assert round(raw_gbps, 3) == host["payload_gbps_each_direction"] == 15.754
    assert round(payload_gbs, 3) == host["payload_gbs_each_direction"] == 1.969
    assert host["achievable_dma_gbs_each_direction_min"] <= payload_gbs


def test_rejected_orin_nano_records_gen3_reason() -> None:
    spec = _load_spec()
    rejected = {c["id"]: c for c in spec["compute"]["rejected_compute_candidates"]}

    nano = rejected["jetson-orin-nano-8gb"]
    assert "Gen3" in nano["reason"]
    assert "v1.7" in nano["reason"]
    assert nano["source"] == "src_orin_nano_ds"
    assert "fpga-path-agilex-versal" in rejected
    assert "discrete-gpu-low-end" in rejected


# -----------------------------------------------------------------------------
# working set: model + KV + OS must fit module memory
# -----------------------------------------------------------------------------
def test_working_set_arithmetic_and_envelope_fit() -> None:
    envelope = _load_spec()["model_target"]["working_set_gb"]
    kv = envelope["kv_cache_budget_gb"]["value"]
    os_reserve = envelope["os_reserve_gb"]

    e2b = 2.9 + kv + os_reserve
    e4b = 4.5 + kv + os_reserve
    twelve_b = 6.7 + kv + os_reserve

    assert kv == 1.5
    assert round(e2b, 1) == envelope["e2b_q4_0_32k"] == 5.4
    assert round(e4b, 1) == envelope["e4b_q4_0_32k"] == 7.0
    assert round(twelve_b, 1) == envelope["twelve_b_q4_0_32k"] == 9.2

    module_gb = _load_spec()["memory"]["module_lpddr5_gb"]
    assert e2b <= 8 <= module_gb, "E2B Q4_0 must fit even the 8GB floor SKU"
    assert twelve_b <= module_gb, "12B stretch goal must fit the 16GB baseline"


def test_model_target_weights_match_google_table() -> None:
    weights = _load_spec()["model_target"]["primary"]["weights_gb"]

    assert weights == {
        "bf16": 11.4,
        "sfp8": 5.7,
        "q4_0": 2.9,
        "mobile_qat": 1.1,
        "mobile_qat_text_only": 0.84,
    }


# -----------------------------------------------------------------------------
# performance budget: decode is bandwidth-bound
# -----------------------------------------------------------------------------
def test_decode_targets_within_bandwidth_bound() -> None:
    budget = _load_spec()["performance_budget"]
    assumptions = budget["decode_assumptions"]
    targets = budget["decode_tok_s"]

    bw = assumptions["memory_bandwidth_gbs"]
    eff_min, eff_max = assumptions["stream_efficiency_range"]
    assert bw == 102.4
    assert eff_min <= eff_max

    q4_derived = [
        round(bw * eff_min / assumptions["e2b_q4_0_weights_read_gb"], 1),
        round(bw * eff_max / assumptions["e2b_q4_0_weights_read_gb"], 1),
    ]
    mobile_derived = [
        round(bw * eff_min / assumptions["e2b_mobile_weights_read_gb"], 1),
        round(bw * eff_max / assumptions["e2b_mobile_weights_read_gb"], 1),
    ]

    assert q4_derived == targets["derived_e2b_q4_0_range"] == [23.5, 27.7]
    assert mobile_derived == targets["derived_e2b_mobile_range"] == [51.2, 60.5]
    assert targets["target_e2b_q4_0_min"] < q4_derived[0]
    assert targets["target_e2b_mobile_min"] < mobile_derived[0]


def test_host_link_load_time_within_target() -> None:
    host = _load_spec()["host_interface"]
    budget = _load_spec()["performance_budget"]["host_link"]

    load_seconds = 2.9 / host["achievable_dma_gbs_each_direction_min"]
    assert load_seconds <= budget["cold_load_e2b_q4_0_from_host_s_max"]


# -----------------------------------------------------------------------------
# power: slot-only, no auxiliary connector
# -----------------------------------------------------------------------------
def test_power_budget_sums_to_cap_within_slot() -> None:
    power = _load_spec()["power_and_thermal"]
    budget = power["board_budget_w"]

    summed = budget["module_maxn"] + budget["m2_nvme"] + budget["fan"]
    summed += budget["rails_and_conversion_overhead"]

    assert summed == budget["tdp_cap"] == 35
    assert budget["tdp_cap"] <= power["slot_power"]["slot_available_12v_w"] == 75
    assert power["slot_power"]["auxiliary_connector"] == "none"
    assert power["default_mode"] == "25W-MAXN"
    assert power["cooling"] == "single-slot-heatsink-plus-fan"


# -----------------------------------------------------------------------------
# acceptance structure mirrors the task-contract style
# -----------------------------------------------------------------------------
def test_acceptance_levels_cover_l0_through_l4() -> None:
    spec = _load_spec()

    assert spec["acceptance_levels"] == {
        "L0": "specification_and_interface_contract",
        "L1": "software_validation_on_devkit",
        "L2": "carrier_schematic_power_thermal_and_mechanical_analysis",
        "L3": "endpoint_driver_and_host_link_validation",
        "L4": "board_validation_sustained_workload",
    }
    for level in ("L0", "L1", "L2", "L3", "L4"):
        assert spec["acceptance"][level], level


def test_open_items_carry_risk_and_blocking_level() -> None:
    spec = _load_spec()

    assert spec["open_items"], "open risks must be listed, not hidden"
    for item in spec["open_items"]:
        assert item["id"]
        assert item["risk"] in {"low", "medium", "high"}
        assert item["blocks"] in {"L0", "L1", "L2", "L3", "L4"}
        assert item["question"].strip()


# -----------------------------------------------------------------------------
# host-proxy simulation (scripts/sim_edge_card_software.py) evidence
# -----------------------------------------------------------------------------
def test_measured_gguf_file_backs_the_envelope() -> None:
    spec = _load_spec()
    primary = spec["model_target"]["primary"]
    envelope = spec["model_target"]["working_set_gb"]

    file_gb = primary["weights_gb_gguf_measured"]
    assert file_gb == 3.35
    assert file_gb > primary["weights_gb"]["q4_0"], "full GGUF file > table figure"
    measured = file_gb + envelope["kv_cache_budget_gb"]["value"] + envelope["os_reserve_gb"]
    assert round(measured, 2) == envelope["e2b_q4_0_32k_gguf_measured"] == 5.85
    assert measured <= 8, "conservative full-file envelope must fit the 8GB floor SKU"


def test_gguf_file_stream_bound_recomputation() -> None:
    budget = _load_spec()["performance_budget"]
    file_gb = _load_spec()["model_target"]["primary"]["weights_gb_gguf_measured"]
    bw = budget["decode_assumptions"]["memory_bandwidth_gbs"]
    eta_min, eta_max = budget["decode_assumptions"]["stream_efficiency_range"]
    decode = budget["decode_tok_s"]

    low = round(bw * eta_min / file_gb, 1)
    high = round(bw * eta_max / file_gb, 1)
    assert [low, high] == decode["derived_e2b_q4_0_gguf_file_stream_range"] == [16.8, 19.9]
    assert low >= decode["target_e2b_q4_0_min"], "conservative bound must still clear target"
    assert (
        decode["eta_needed_for_target_on_full_file"]
        == round(decode["target_e2b_q4_0_min"] * file_gb / bw, 3)
        == 0.491
    )


def test_host_proxy_simulation_block_is_labelled_and_gated() -> None:
    spec = _load_spec()
    sim = spec["host_proxy_simulation"]

    assert sim["kind"] == "host_proxy_not_l1"
    assert sim["source"].startswith("scripts/sim_edge_card_software.py")
    assert sim["rerun"].startswith(".venv/bin/python scripts/sim_edge_card_software.py")
    assert sim["verdicts"] == {
        "envelope_vs_8gb_floor": "PASS",
        "decode_bound_vs_target_15": "PASS",
        "load_vs_target_5s": "PASS",
    }
    assert sim["measured"]["decode_tok_s"] > 0
    assert sim["measured"]["prefill_tok_s"] > 0
    assert sim["projections"]["envelope_gb"] <= 8
    assert len(sim["caveats"]) >= 3, "proxy limits must be stated, not implied"
    assert any("Orin NX devkit" in c for c in sim["caveats"])


def test_cycle_simulation_block_is_labelled_gated_and_honest() -> None:
    """結構仿真的結論必須自洽，且誠實標示 compute-bound 反證。"""
    spec = _load_spec()
    sim = spec["cycle_simulation"]

    assert sim["kind"] == "structural_discrete_event_not_l1"
    assert sim["rerun"].startswith(".venv/bin/python scripts/sim_edge_card_cycle.py")
    assert sim["checkpoints_hops"] == [16, 100, 1000, 10000]
    measured = sim["measured"]
    assert measured["bottleneck"] == "mac_array", "spec claims a compute-bound card"
    assert measured["utilization"]["mac_array"] >= 0.99
    assert measured["utilization"]["mem_service"] < 0.5
    assert measured["violations"] == 0
    assert measured["replay_identical"] is True
    assert measured["workload_exact"] is True
    # gate must be consistent with the measured number (floor below measurement)
    assert sim["gate"]["min_tok_s"] <= measured["decode_tok_s"]
    # honest refutation of the bandwidth-only decode range
    assert any("derived_e2b_q4_0_range" in refutes["claim"] for refutes in sim["refutes"])
    # ops split must add up to the total per token
    ops = measured["ops_per_token"]
    assert ops["weights"] + ops["attention"] == pytest.approx(ops["total"], rel=1e-3)
    # 沒有任何口徑/配置在 32K 達 15（c1 已被事實作廢，其值也遠低於目標）
    target = spec["performance_budget"]["decode_tok_s"]["target_e2b_q4_0_min"]
    assert measured["decode_tok_s"] < target
    assert sim["sensitivity"]["c1_reading_retired_tok_s"] < target
    # long-run (52k hops) must stay clean and exactly accounted
    long_run = sim["long_run"]
    assert long_run["hops"] >= 50000
    assert long_run["violations"] == 0
    assert long_run["replay_equal_all_checkpoints"] is True
    assert long_run["workload_exact"] is True
    lo, hi = long_run["per_token_ms_range"]
    assert 0 < lo <= hi < 2 * measured["per_token_ms"]


def test_balance_study_answers_memory_pcie_and_cost() -> None:
    """平衡掃描的結論必須可重推：記憶體閒置是結構性的、PCIe 負載過門檻、成本有框。"""
    spec = _load_spec()
    bal = spec["cycle_simulation"]["balance_study"]
    assert bal["source"].endswith("sim_edge_card_sweep.py")
    assert bal["status"] == "candidate_pending_l1_benchmark_and_l2_thermal"

    mem = bal["memory"]
    # 記憶體飽和點遠超任何可購模組 -> 閒置是物理，不是調校失誤
    assert mem["max_real_mode_ops_ns"] == 19  # MAXN GPU 38 dense / 2 ops/MAC
    assert mem["max_real_mode_ops_ns"] < mem["bind_point_ops_ns_32k"]
    assert mem["bind_point_ops_ns_32k"] > 200
    assert mem["real_mode_util_range"][1] < 0.5  # 真模組點連一半都用不到
    probes = mem["probes_mem_util_at_32k"]
    assert probes["r100"] < probes["r150"] < probes["r222_6"] < probes["r445_2"] < 1.0
    # 頻寬天花板與 bind point 一致（roofline = bind ops/ns / ops/token）
    roof = mem["roofline_tok_s_at_32k"]
    assert mem["bind_point_ops_ns_32k"] * 1e9 / roof == pytest.approx(4.218e9, rel=1e-3)

    pc = bal["pcie"]
    assert pc["load_verdict"] == "PASS"
    assert pc["load_s_at_payload"] <= pc["load_budget_s"]
    assert pc["load_s_at_achievable_1_6"] <= pc["load_budget_s"]
    assert pc["decode_util_at_15_tok_s"] < 1e-6  # token stream，非吞吐通道

    meets = bal["meets_target"]
    # 事實關閉：MAC=2 + GPU-only 下，掃描內無任何點達 15；最好點要記帳
    assert meets["any_mode_any_ctx"] == []
    assert "nx16_40w_c2" in meets["best_point"] and "6.77" in meets["best_point"]
    assert "quote" in bal["cost_frame"]


def test_component_review_leverage_and_simulated_numbers() -> None:
    """元件回顧必須把「能提升的」與「不能提升的」都用掃描數字釘死。"""
    spec = _load_spec()
    cr = spec["component_review"]
    target = float(spec["performance_budget"]["decode_tok_s"]["target_e2b_q4_0_min"])
    assert cr["status"] == "candidate_pending_human_approval_and_l2"
    assert cr["rerun"].endswith("sim_edge_card_sweep.py")

    classes = {p["part_class"] for p in cr["standard_parts"]}
    assert {"compute-module", "cooling", "nvme-ssd", "host-link", "power-path"} <= classes
    for part in cr["standard_parts"]:
        assert part.get("source") in spec["sources"], f"未定義來源: {part.get('source')}"
    cooling = next(p for p in cr["standard_parts"] if p["part_class"] == "cooling")
    assert "40W" in cooling["upgrade"] and "unlock" in cooling["upgrade"]
    assert cr["custom_parts"] and cr["layout_review"]
    assert set(cr["layout_review"]) == {
        "vdd_in_feed",
        "pcie_lane",
        "uphy_concurrency",
        "thermal_path",
    }
    for item in cr["custom_parts"]:
        if "source" in item:
            assert item["source"] in spec["sources"]

    # 載入路徑：每條都過 5s，且升級天花板有限（改善空間就是那麼多秒）
    lp = cr["simulation"]["load_paths_s"]
    assert lp["verdict"] == "PASS"
    paths = [
        lp["host_pcie_payload"],
        lp["host_pcie_achievable_1_6"],
        lp["nvme_spec_1_6"],
        lp["nvme_hypothetical_2_4"],
    ]
    assert max(paths) <= lp["budget"]
    assert lp["worst_case"] == pytest.approx(max(paths), abs=0.01)
    assert lp["margin"] == pytest.approx(lp["budget"] - lp["worst_case"], abs=0.01)
    assert lp["margin"] >= 2.8  # 存儲/鏈路升級買不到有意義的時間
    assert lp["nvme_hypothetical_2_4"] < lp["nvme_spec_1_6"]  # 更快裝置更快，但差距有限

    # 功率階梯（GPU-only dense、MAC=2 已證實）：15W < 25W < 40W，且全滅不達 15
    lad = cr["simulation"]["power_ladder_tok_s_at_32k"]
    assert lad["w15_derived"] < lad["w25_default"] < lad["w40_maxn_super"] < target
    # 與已提交的 balance_study 同口徑數字一致（25W/40W 非新測，是同一引擎）
    bal = spec["cycle_simulation"]["balance_study"]
    assert lad["w25_default"] == pytest.approx(bal["real_modes_tok_s"]["nx16_25w_c2"][2])
    assert lad["w40_maxn_super"] == pytest.approx(bal["real_modes_tok_s"]["nx16_40w_c2"][2])

    # 128K：每一點都比 32K 慢，且最好點也不達 15 -> 「能力非速率」的讀法成立
    k128 = cr["simulation"]["ctx_128k_16gb_sku_tok_s"]
    for mode_key in ("w15_derived", "w25_default", "w40_maxn_super"):
        assert k128[mode_key] < lad[mode_key]
    assert max(k128[m] for m in ("w15_derived", "w25_default", "w40_maxn_super")) < target

    meets = cr["simulation"]["meets_target"]
    assert set(meets["at_32k"]) <= set(meets["at_or_below_16k"])
    assert meets["at_32k"] == [] and meets["at_or_below_16k"] == []


def test_compute_tops_split_gpu_dla_and_convention() -> None:
    """模組 TOPS = GPU + DLA 逐項閉合；解碼只認 GPU；MAC=2 口徑有事實出處。

    舊錯（本輪 bug-hunt 抓到）：模組 50/78 被當成可解碼算力——其實含 DLA
    20/40（CNN-only，跑不了 transformer），且 c1 以 1-op/MAC 讀 TOPS——
    NVIDIA 自家 INT8 dense = 2x FP16 dense 反證。此測把修訂釘死。
    """
    spec = _load_spec()
    mod = spec["compute"]["module"]
    sku = spec["compute"]["option_sku"]
    mt, gt, dl = mod["int8_tops"], mod["gpu_tc_int8_tops"], mod["dla_int8_tops_excluded"]

    # 模組口徑 = GPU + DLA，四個數字逐項閉合（16GB，2x NVDLA）
    assert mt["dense_maxn_25w"] == gt["dense_25w_918mhz"] + dl["dense_25w"]
    assert mt["sparse_maxn_25w"] == gt["sparse_25w_918mhz"] + dl["sparse_25w"]
    assert mt["dense_maxn_super_40w"] == gt["dense_maxn_super_1173mhz"] + dl["dense_maxn_super_40w"]
    assert (
        mt["sparse_maxn_super_40w"] == gt["sparse_maxn_super_1173mhz"] + dl["sparse_maxn_super_40w"]
    )

    # 8GB SKU：模組 35/70 = GPU + 1x DLA（10/20）
    smt, sgt = sku["int8_tops"], sku["gpu_tc_int8_tops"]
    sdl = sku["dla_int8_tops_excluded"]
    assert smt["dense_maxn_25w"] == sgt["dense_25w_765mhz"] + sdl["dense_25w"]
    assert smt["sparse_maxn_25w"] == sgt["sparse_25w_765mhz"] + sdl["sparse_25w"]

    # 解碼只用 GPU 份，且嚴格小於模組口徑
    assert mod["decode_usable_dense_tops"] == gt["dense_25w_918mhz"]
    assert gt["dense_25w_918mhz"] < mt["dense_maxn_25w"]
    assert sku["decode_usable_dense_tops"] == sgt["dense_25w_765mhz"]

    # 時脈比例閉合：GPU dense 隨時脈線性（30 @918MHz -> 38 @1173MHz；
    # 同顆 GPU 在 nx8 預設 765MHz = 25）——抓口徑/單位回歸
    assert gt["dense_maxn_super_1173mhz"] == pytest.approx(
        gt["dense_25w_918mhz"] * 1173 / 918, abs=0.5
    )
    assert sgt["dense_25w_765mhz"] == pytest.approx(gt["dense_25w_918mhz"] * 765 / 918, abs=0.5)

    # 口徑結論與 DLA 排除都有事實出處（src 懸空由 test_edge_card_refs 把關）
    assert "MAC=2" in mod["tops_convention"]
    assert "src_jetson_orin_page" in mod["tops_convention"]
    assert gt["source"] in spec["sources"]
    assert dl["source"] in spec["sources"]
    assert "attention" in dl["reason"] and "softmax" in dl["reason"]


def test_spec_top_level_schema_is_complete() -> None:
    """刪除或改名頂層段必須變紅，而不是靜默通過。

    中間條件全列入判定的一半：先保證條件本身存在，再談數值對不對。
    """
    spec = _load_spec()
    required = {
        "schema_version",
        "status",
        "owner",
        "product_decision",
        "compute",
        "host_interface",
        "memory",
        "storage",
        "model_target",
        "performance_budget",
        "power_and_thermal",
        "mechanical",
        "software",
        "acceptance_levels",
        "current_target",
        "acceptance",
        "component_selection_policy",
        "human_approval_required_for",
        "open_items",
        "sources",
        "explicit_non_claims",
        "host_proxy_simulation",
        "cycle_simulation",
        "component_review",
    }
    missing = required - set(spec)
    assert not missing, f"spec 缺頂層段: {sorted(missing)}"
    assert set(spec["acceptance_levels"]) == {"L0", "L1", "L2", "L3", "L4"}
    assert set(spec["host_proxy_simulation"]) >= {
        "kind",
        "date",
        "rerun",
        "source",
        "measured",
        "projections",
        "verdicts",
        "caveats",
    }


def test_spec_declared_paths_exist_on_disk() -> None:
    """spec 寫的路徑必須真實存在；腳本指的 spec 也必須是這一份。"""
    spec = _load_spec()
    repo = SPEC_PATH.parents[2]
    sim = spec["host_proxy_simulation"]
    assert (repo / sim["source"]).is_file(), sim["source"]
    cycle = spec["cycle_simulation"]
    assert (repo / cycle["source"]).is_file(), cycle["source"]
    assert (repo / cycle["engine"]).is_file(), cycle["engine"]
    assert (repo / "hardware/edge_card/edge_card_spec.yaml").resolve() == SPEC_PATH.resolve()


def test_spec_provenance_and_projection_keys_are_complete() -> None:
    """Every measured number must carry its source and recompute cleanly.

    Guards against transcription drift: the GGUF source, the cross-check, the
    envelope-others list, and the simulation projections must all exist and
    agree with the performance budget they were derived from.
    """
    spec = _load_spec()
    primary = spec["model_target"]["primary"]
    budget = spec["performance_budget"]
    sim = spec["host_proxy_simulation"]

    assert primary["weights_gb_source"] == "src_google_gemma_memory"
    assert spec["sources"][primary["weights_gb_source"]]["url"]
    cross = primary["measured_cross_check"]
    assert cross["gguf_q4_k_m_text_gib"] == 2.89
    assert cross["source"] == "src_gemma4_webgpu"
    assert spec["sources"][cross["source"]]["url"]

    others = {item["id"]: item for item in spec["model_target"]["envelope_others"]}
    assert others["google/gemma-4-E4B-it"]["weights_gb_q4_0"] == 4.5
    assert others["gemma-4-12B-and-similar-<=12b-dense"]["weights_gb_q4_0"] == 6.7

    assert spec["sources"]["src_hf_gguf"]["type"] == "manufacturer_artifact"
    assert "huggingface.co" in spec["sources"]["src_hf_gguf"]["url"]

    projections = sim["projections"]
    assert (
        projections["decode_file_stream_bound_tok_s"]
        == budget["decode_tok_s"]["derived_e2b_q4_0_gguf_file_stream_range"]
    )
    assert (
        projections["eta_needed_for_target"]
        == budget["decode_tok_s"]["eta_needed_for_target_on_full_file"]
    )
    assert (
        projections["envelope_gb"]
        == spec["model_target"]["working_set_gb"]["e2b_q4_0_32k_gguf_measured"]
    )
    file_gb = primary["weights_gb_gguf_measured"]
    payload_gbs = spec["host_interface"]["payload_gbs_each_direction"]
    assert projections["load_from_host_s"] == round(file_gb / payload_gbs, 2) == 1.7
