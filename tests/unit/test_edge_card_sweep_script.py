# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""掃描腳本本身（scripts/sim_edge_card_sweep.py）的結構與算術門。

spec 測試釘靜態數字；本檔釘產生數字的程式：模式表的 ctx 政策
（8GB SKU 止於 32K、16GB 含 128K、15W 標 derived）與載入路徑四條
算式（host payload / host achievable / NVMe spec / 假想更快裝置）。
掃描執行本身由 VERDICT + baseline cross-check 在跑時把關。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/sim_edge_card_sweep.py"


@pytest.fixture(scope="module")
def sweep():
    spec = importlib.util.spec_from_file_location("edge_card_sweep_script", SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_real_modes_carry_per_sku_context_policy(sweep) -> None:
    """8GB SKU 止於 32K（容量），16GB 才有 128K；15W 明標 derived。"""
    modes = sweep.REAL_MODES
    for name, m in modes.items():
        assert {"tops", "conv", "ctxs", "label"} <= set(m)
        assert m["tops"] > 0 and m["conv"] in (1, 2)
        assert 32768 in m["ctxs"]
        if name.startswith("nx8_"):
            assert max(m["ctxs"]) == 32768, f"{name} 不得含 128K"
        if name.startswith("nx16_"):
            assert 131072 in m["ctxs"], f"{name} 缺 128K 能力點"
        if "15w" in name:
            assert "derived" in m["label"], "15W 必須標 derived"
    # 15W 推導 = 25W 檔 x 0.7（spec low_power_profile 的 derate 註記）
    assert modes["nx16_15w_c2"]["tops"] == pytest.approx(modes["nx16_25w_c2"]["tops"] * 0.7)
    assert modes["nx16_15w_c1"]["tops"] == pytest.approx(modes["nx16_25w_c1"]["tops"] * 0.7)


def test_load_paths_arithmetic_and_budget(sweep) -> None:
    """四條載入路徑的算式與 5s 預算：最差仍過，假想裝置有天花板。"""
    fake = {"file_size": 3_349_516_256}
    cfg = sweep.CardConfig()
    lp = sweep.load_paths(fake, cfg)
    assert lp["budget_s"] == 5.0
    assert lp["all_pass"] is True
    assert lp["host_pcie_payload_s"] == pytest.approx(
        fake["file_size"] / cfg.pcie_bytes_per_ns / 1e9, abs=0.01
    )
    assert lp["host_pcie_achievable_s"] == pytest.approx(fake["file_size"] / 1.6 / 1e9, abs=0.01)
    assert lp["nvme_spec_1_6_s"] == pytest.approx(fake["file_size"] / 1.6 / 1e9, abs=0.01)
    assert lp["nvme_hypothetical_2_4_s"] == pytest.approx(fake["file_size"] / 2.4 / 1e9, abs=0.01)
    assert lp["nvme_hypothetical_2_4_s"] < lp["nvme_spec_1_6_s"] < lp["budget_s"]
    assert lp["margin_s"] == pytest.approx(lp["budget_s"] - lp["worst_case_s"], abs=0.01)
    assert lp["worst_case_s"] == pytest.approx(lp["nvme_spec_1_6_s"], abs=0.01)


def test_pcie_analytics_decode_is_category_error(sweep) -> None:
    """解碼 8B/token 走 x1：util 必須近零；載入才是真用到鏈路的地方。"""
    fake = {"file_size": 3_349_516_256}
    pc = sweep.pcie_analytics(fake)
    assert pc["load_pass"] is True
    assert pc["decode_util_at_15"] < 1e-6
    assert pc["load_util_at_payload"] == 1.0  # 載入期間鏈路吃滿


def test_memory_bind_point_above_every_real_mode(sweep) -> None:
    """記憶體綁定点必須高於所有可購模式 -> 掃描才不會出現假的記憶體瓶頸。"""
    gguf = (
        Path.home()
        / ".cache/huggingface/hub/models--google--gemma-4-E2B-it-qat-q4_0-gguf"
        / "snapshots/675cff42a74c774d6cb76f76d8eacb49b48c9b93"
        / "gemma-4-E2B_q4_0-it.gguf"
    )
    if not gguf.is_file():
        pytest.skip("GGUF artifact not present on this machine")
    structure = sweep.read_gguf_structure(gguf)
    bind = sweep.memory_bind_point(structure, sweep.CardConfig(), 32768)
    max_real_ops_ns = max(m["tops"] / m["conv"] for m in sweep.REAL_MODES.values())
    assert bind["ops_ns"] > max_real_ops_ns * 2  # 留兩倍餘裕給未來模組
    assert bind["ops_ns"] == pytest.approx(222.6, rel=0.01)  # spec 記載的 bind point
