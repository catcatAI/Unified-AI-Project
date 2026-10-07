# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""事實裁決包：全量事實的單一裁決點（參考解讀器，stdlib-only）。

Python 繼續寫邏輯，裁決只認這裡的輸出。形狀沿
`ai.hardware.cim_verify.GateReport`（ verdict 向量 + ok 唯一接受口）。
"""

from .adapters import from_audit_corrections, from_gate_report, from_sim_verdicts
from .interpreter import (
    Report,
    Verdict,
    adjudicate,
    adjudicate_chain,
    adjudicate_labeled_chain,
    mark_info,
    merge_reports,
    missing_segments,
    stale_facts,
)
from .schema import Compare, Fact

__all__ = [
    "Compare",
    "Fact",
    "Report",
    "Verdict",
    "adjudicate",
    "adjudicate_chain",
    "adjudicate_labeled_chain",
    "from_audit_corrections",
    "from_gate_report",
    "from_sim_verdicts",
    "mark_info",
    "merge_reports",
    "missing_segments",
    "stale_facts",
]
