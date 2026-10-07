# =============================================================================
# ANGELA-MATRIX: [L6] [βγδ] [A] [L3]
# =============================================================================
"""參考解讀器：全量求值，輸出 verdict 向量（短路是 bug，不是優化）。

語義 v1（凍結於 FACT_INTERPRETER_AND_CHAIN_ADJUDICATION_PLAN.md §3.2）：
- `must_pass` 事實按 `compare`（ge/le）求值；`must_pass=False` 記 INFO。
- `Report.ok` 為唯一的接受口：非空且所有 must_pass 皆 PASS。
- `adjudicate_chain` 串聯多段（如 UI 五段），任一段 FAIL 即定位到段。
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import List, Mapping, Optional, Sequence

from .schema import Fact, Verdict


@dataclass
class Report:
    verdicts: List[Verdict] = field(default_factory=list)

    def add(self, verdict: Verdict) -> None:
        self.verdicts.append(verdict)

    @property
    def ok(self) -> bool:
        """唯一的接受口：非空且所有 must_pass 皆 PASS（INFO 不擋門）。"""
        if not self.verdicts:
            return False
        return all(v.passed is not False for v in self.verdicts)

    @property
    def failed(self) -> List[Verdict]:
        return [v for v in self.verdicts if v.passed is False]

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "verdicts": [v.as_dict() for v in self.verdicts],
            "failed": [v.id for v in self.failed],
        }

    def summary(self) -> str:
        lines = []
        for v in self.verdicts:
            lines.append(f"  [{v.status}] {v.id}: {v.value} {v.unit} vs {v.target}")
            if v.passed is False:
                lines.append(f"         evidence: {v.evidence or v.source}")
        lines.append(f"  => {'ALL PASS' if self.ok else 'BLOCKED'}")
        return "\n".join(lines)


def _evaluate(fact: Fact) -> Verdict:
    if not fact.must_pass:
        return Verdict(
            id=fact.id,
            passed=None,
            value=fact.value,
            target=fact.target,
            unit=fact.unit,
            source=fact.source,
            evidence=fact.evidence,
        )
    if fact.compare == "ge":
        passed: Optional[bool] = fact.value >= fact.target
    elif fact.compare == "le":
        passed = fact.value <= fact.target
    else:
        raise ValueError(f"unknown compare for fact {fact.id!r}: {fact.compare!r}")
    return Verdict(
        id=fact.id,
        passed=passed,
        value=fact.value,
        target=fact.target,
        unit=fact.unit,
        source=fact.source,
        evidence=fact.evidence,
    )


def adjudicate(facts: Sequence[Fact]) -> Report:
    """同時裁決所有事實（不短路），回傳 verdict 向量。"""
    report = Report()
    for fact in facts:
        report.add(_evaluate(fact))
    return report


def adjudicate_chain(segments: Sequence[Sequence[Fact]]) -> Report:
    """串聯多段事實鏈（如 UI 五段）， verdict 保留段順序以便定位。"""
    report = Report()
    for facts in segments:
        for fact in facts:
            report.add(_evaluate(fact))
    return report


def adjudicate_labeled_chain(segments: Mapping[str, Sequence[Fact]]) -> Report:
    """帶段標籤的鏈式裁決：失敗段直接讀 `verdict.segment` 定位。

    Mapping 保持插入順序，verdict 順序與段展開順序一致。
    """
    report = Report()
    for label, facts in segments.items():
        for fact in facts:
            verdict = _evaluate(fact)
            report.add(replace(verdict, segment=label))
    return report


def mark_info(fact: Fact) -> Fact:
    """把事實降為 INFO（只記錄，不擋門）：衝突時保守方當 gate、另一方經此降級。

    如 full-file 保守 bound 當門、active-weights 樂觀 bound 記 INFO。
    """
    return replace(fact, must_pass=False)
