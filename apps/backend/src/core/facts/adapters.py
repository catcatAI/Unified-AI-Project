# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""橋接現有 verdict 形狀到事實解讀器（收斂第一步，stdlib-only）。

`ai.hardware.cim_verify.GateReport` 與 `core.facts.Report` 同構
（verdict 向量 + ok 唯一接受口），差別只在 Gate 沒有數值 value/target。
此處做忠實編碼：`value = 1.0/0.0`、`target = 1.0`，`detail` 與
`guards_against` 合併進 `evidence`（出處標 `cim_verify`），`ok` 語義不變。
"""

from __future__ import annotations

from ai.hardware.cim_verify import GateReport

from .interpreter import Report
from .schema import Verdict


def from_gate_report(report: GateReport) -> Report:
    """把 CIM gate 報告轉成事實 verdict 向量（順序、ok 語義保留）。"""
    out = Report()
    for gate in report.gates:
        out.add(
            Verdict(
                id=gate.name,
                passed=gate.passed,
                value=1.0 if gate.passed else 0.0,
                target=1.0,
                unit="",
                source="cim_verify",
                evidence=f"{gate.detail} | guards: {gate.guards_against}",
            )
        )
    return out
