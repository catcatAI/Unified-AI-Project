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
        passed: Optional[bool] = fact.value >= fact.target - fact.tol
    elif fact.compare == "le":
        passed = fact.value <= fact.target + fact.tol
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


def merge_reports(*reports: Report) -> Report:
    """合併多個 verdict 向量為單一全倉裁決（gate + audit + edge 三合一）。

    順序即參數順序；空集合回傳空 Report（`ok` 為 False，不謊報全綠）。
    """
    merged = Report()
    for report in reports:
        merged.verdicts.extend(report.verdicts)
    return merged


def missing_segments(report: Report, expected: Sequence[str]) -> List[str]:
    """列出 verdict 向量缺席的鏈段（鏈缺段即判定不完整）。

    呼應「中間條件全列入」：鏈宣告五段、verdict 只有四段時，
    缺的那段就是下一個要補的判定，而不是一句全綠。
    """
    present = {v.segment for v in report.verdicts if v.segment}
    return [seg for seg in expected if seg not in present]


def stale_facts(facts: Sequence[Fact], max_age_days: int, today: str) -> List[str]:
    """列出量測過期的事實 id（量測會腐爛，判新鮮度不判對錯）。

    `today` 與 `measured_at` 皆為 ISO 日期（`YYYY-MM-DD`）；`measured_at`
    為空表未知、不列入；`max_age_days` 為負表不過期檢查。純函數，`today`
    由呼叫方注入以保證確定性。回傳過期 id 清單（空表全新鮮）。
    """
    from datetime import date as _date

    try:
        current = _date.fromisoformat(today)
    except ValueError:
        raise ValueError(f"bad today for staleness check: {today!r}")
    stale: List[str] = []
    for fact in facts:
        if not fact.measured_at:
            continue
        try:
            measured = _date.fromisoformat(fact.measured_at)
        except ValueError:
            stale.append(fact.id)
            continue
        if max_age_days >= 0 and (current - measured).days > max_age_days:
            stale.append(fact.id)
    return stale
