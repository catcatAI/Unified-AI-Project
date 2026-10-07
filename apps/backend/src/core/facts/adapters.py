# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""橋接現有 verdict 形狀到事實解讀器（收斂，stdlib-only）。

三套同構形狀在此會合：CIM `GateReport`、卡架構 `audit()` 的 corrections、
edge 卡的 verdicts。前兩者由此適配，第三者原生即 verdict 形狀。
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

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


def from_audit_corrections(corrections: Sequence[Mapping[str, Any]]) -> Report:
    """把架構審計的 corrections 轉成 verdict 向量。

    每條 correction 記為 INFO（出處、嚴重度、重算值全進 evidence，不擋門），
    另立一道 `no_blocking_corrections` 門（blocking 數 <= 0）。於是
    `ok` 恰為「無 blocking 級差異」——審計的本意。
    缺鍵用預設值吞下（severity 預設 material），缺鍵本身不該炸掉審計。
    """
    out = Report()
    blocking = 0
    for item in corrections:
        severity = str(item.get("severity", "material"))
        if severity == "blocking":
            blocking += 1
        out.add(
            Verdict(
                id=str(item.get("id", "unnamed_correction")),
                passed=None,
                value=0.0,
                target=0.0,
                unit="",
                source=str(item.get("source", "card_architecture_audit")),
                evidence=(
                    f"[{severity}] claimed={item.get('claimed', '?')} "
                    f"recomputed={item.get('recomputed', '?')} "
                    f"detail={item.get('detail', '')}"
                ),
            )
        )
    out.add(
        Verdict(
            id="no_blocking_corrections",
            passed=blocking <= 0,
            value=float(blocking),
            target=0.0,
            unit="count",
            source="card_architecture_audit",
            evidence=f"{blocking} blocking corrections",
        )
    )
    return out
