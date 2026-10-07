# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""事實 schema：每個事實帶身份、目標、單位、出處與證據。

事實是數據，不含求值邏輯；求值在 `interpreter.adjudicate`。
`must_pass=False` 的事實只記錄（INFO），不擋門。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional

Compare = Literal["ge", "le"]


@dataclass(frozen=True)
class Fact:
    """一條待裁決的事實。"""

    id: str
    value: float
    target: float
    compare: Compare
    unit: str = ""
    source: str = ""
    evidence: str = ""
    must_pass: bool = True
    extra: Any = None


@dataclass(frozen=True)
class Verdict:
    """一條已裁決的事實。`passed=None` 表 INFO（只記錄，不擋門）。"""

    id: str
    passed: Optional[bool]
    value: float
    target: float
    unit: str = ""
    source: str = ""
    evidence: str = ""

    @property
    def status(self) -> str:
        if self.passed is None:
            return "INFO"
        return "PASS" if self.passed else "FAIL"

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "passed": self.passed,
            "value": self.value,
            "target": self.target,
            "unit": self.unit,
            "source": self.source,
            "evidence": self.evidence,
        }
