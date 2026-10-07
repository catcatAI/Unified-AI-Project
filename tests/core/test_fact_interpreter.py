# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""參考解讀器測試：語義單元 + 首條鏈（edge 卡 envelope 經解讀器重裁）。

首條鏈沿用 tests/unit/test_edge_card_spec.py 已驗證的黃金值
（5.85/8、16.8/15、1.7/5），差別在於這裡走解讀器的單一裁決點：
三個事實同時求值、單一 report、可定位到段。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from core.facts import Fact, Report, Verdict, adjudicate, adjudicate_chain

SPEC_PATH = Path(__file__).resolve().parents[2] / "hardware/edge_card/edge_card_spec.yaml"


def _load_spec() -> Any:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


class TestVerdictStatus:
    def test_info_pass_fail_statuses(self) -> None:
        assert Verdict("a", None, 1.0, 2.0).status == "INFO"
        assert Verdict("a", True, 2.0, 1.0).status == "PASS"
        assert Verdict("a", False, 0.0, 1.0).status == "FAIL"

    def test_as_dict_round_trips(self) -> None:
        payload = Verdict("a", False, 0.0, 1.0, "GB", "src", "ev").as_dict()
        assert payload == {
            "id": "a",
            "status": "FAIL",
            "passed": False,
            "value": 0.0,
            "target": 1.0,
            "unit": "GB",
            "source": "src",
            "evidence": "ev",
        }


class TestReportIsTheOnlyGate:
    def test_empty_report_is_not_ok(self) -> None:
        assert Report().ok is False
        assert Report().failed == []

    def test_info_does_not_block(self) -> None:
        report = adjudicate([Fact("i", 1.0, 2.0, "ge", must_pass=False)])
        assert report.ok is True
        assert report.failed == []

    def test_failed_gate_blocks_and_names_itself(self) -> None:
        report = adjudicate(
            [
                Fact("good", 5.0, 1.0, "ge", source="s"),
                Fact("bad", 0.0, 1.0, "ge", evidence="why"),
            ]
        )
        assert report.ok is False
        assert [v.id for v in report.failed] == ["bad"]
        assert report.as_dict()["failed"] == ["bad"]
        text = report.summary()
        assert "[PASS] good" in text
        assert "[FAIL] bad" in text
        assert "BLOCKED" in text

    def test_all_pass_summary(self) -> None:
        report = adjudicate([Fact("a", 2.0, 1.0, "ge")])
        assert "ALL PASS" in report.summary()


class TestComparisons:
    def test_ge_and_le_branches(self) -> None:
        assert adjudicate([Fact("ge", 2.0, 1.0, "ge")]).ok is True
        assert adjudicate([Fact("ge", 0.0, 1.0, "ge")]).ok is False
        assert adjudicate([Fact("le", 1.0, 2.0, "le")]).ok is True
        assert adjudicate([Fact("le", 3.0, 2.0, "le")]).ok is False


class TestFirstChainEdgeCardEnvelope:
    """首條鏈：edge 卡 envelope 三 verdict 經解讀器重裁（數值同 spec 測試）。"""

    def test_envelope_chain_through_the_single_gate(self) -> None:
        spec = _load_spec()
        primary = spec["model_target"]["primary"]
        envelope = spec["model_target"]["working_set_gb"]
        budget = spec["performance_budget"]
        sim = spec["host_proxy_simulation"]

        file_gb = primary["weights_gb_gguf_measured"]
        measured = file_gb + envelope["kv_cache_budget_gb"]["value"] + envelope["os_reserve_gb"]
        bw = budget["decode_assumptions"]["memory_bandwidth_gbs"]
        eta_min, _ = budget["decode_assumptions"]["stream_efficiency_range"]
        decode_low = round(bw * eta_min / file_gb, 1)
        payload_gbs = spec["host_interface"]["payload_gbs_each_direction"]
        load_s = round(file_gb / payload_gbs, 2)

        report = adjudicate(
            [
                Fact(
                    "envelope_vs_8gb_floor",
                    round(measured, 2),
                    8,
                    "le",
                    "GB",
                    "spec.working_set_gb",
                    sim["verdicts"]["envelope_vs_8gb_floor"],
                ),
                Fact(
                    "decode_bound_vs_target_15",
                    decode_low,
                    budget["decode_tok_s"]["target_e2b_q4_0_min"],
                    "ge",
                    "tok/s",
                    "spec.performance_budget",
                    sim["verdicts"]["decode_bound_vs_target_15"],
                ),
                Fact(
                    "load_vs_target_5s",
                    load_s,
                    budget["host_link"]["cold_load_e2b_q4_0_from_host_s_max"],
                    "le",
                    "s",
                    "spec.host_interface",
                    sim["verdicts"]["load_vs_target_5s"],
                ),
            ]
        )
        assert report.ok is True, report.summary()
        assert report.failed == []
        assert [v.id for v in report.verdicts] == [
            "envelope_vs_8gb_floor",
            "decode_bound_vs_target_15",
            "load_vs_target_5s",
        ]

    def test_chain_form_preserves_segment_order(self) -> None:
        report = adjudicate_chain(
            [
                [Fact("seg1", 1.0, 2.0, "le")],
                [Fact("seg2a", 5.0, 1.0, "ge"), Fact("seg2b", 0.0, 9.0, "le")],
            ]
        )
        assert report.ok is True
        assert [v.id for v in report.verdicts] == ["seg1", "seg2a", "seg2b"]

    def test_chain_locates_the_failing_segment(self) -> None:
        report = adjudicate_chain([[Fact("good", 1.0, 2.0, "le")], [Fact("bad", 9.0, 2.0, "le")]])
        assert report.ok is False
        assert [v.id for v in report.failed] == ["bad"]


class TestGateAdapter:
    """CIM GateReport → facts Report：順序與 ok 語義保留，證據帶出處。"""

    def test_mixed_gates_convert_with_evidence(self) -> None:
        from ai.hardware.cim_verify import Gate, GateReport
        from core.facts import from_gate_report

        gates = GateReport()
        gates.add(Gate("drc_clean", "empty extraction", True, "DRC errors = 0"))
        gates.add(Gate("weight_ratio", "inexpressible ratio", False, "worst +5.0%"))
        assert gates.ok is False

        report = from_gate_report(gates)
        assert [v.id for v in report.verdicts] == ["drc_clean", "weight_ratio"]
        assert report.ok is False
        assert [v.id for v in report.failed] == ["weight_ratio"]
        assert "empty extraction" in report.verdicts[0].evidence
        assert report.verdicts[0].source == "cim_verify"

    def test_all_pass_gates_stay_ok(self) -> None:
        from ai.hardware.cim_verify import Gate, GateReport
        from core.facts import from_gate_report

        gates = GateReport()
        gates.add(Gate("a", "x", True, "ok"))
        report = from_gate_report(gates)
        assert report.ok is True
        assert report.as_dict()["failed"] == []
