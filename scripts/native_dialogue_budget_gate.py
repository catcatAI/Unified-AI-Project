#!/usr/bin/env python3
"""純本地對話的預算門禁 — 可中斷、可檢查的演進守門人。

**它守什麼**：`scripts/probe_native_dialogue.py` 量到的「純本地基模（不接任何
外部 LLM）」對話品質——人味分數、鸚鵡捲舌率、亂碼率、QA 機器率、雞同鴨講率，
以及**學習效應**（同一個問題「教之前 → 教之後」的分數差，也就是「多少交談
資料才學會」那個數字）與**穩定度**（兩輪之間的差）。

**預算**：`scripts/native_dialogue_budget.txt`（key = value）定義回合上限、
牆鐘上限與各項門檻。門禁的行為與 `scripts/mypy_budget_gate.py` 同一型：
超標 → exit 1；實際比預算好 → 也要把預算調緊（否則門禁會爛掉），所以
低於預算時預設 exit 1，可用 `--allow-lower` 允許（本地收斂用）。

**中斷與檢查**：量測本身隨時可中斷（每回合前查預算，超了乾淨收束並輸出
partial 結果）；門禁在失敗時會把「哪一項超標、實際值、門檻值」全部印出來，
不需要重跑就能判斷。

**這是臨時門禁**：它守的是一個會被修好的缺陷，拆除理由寫在
`scripts/open_gates.json`（由 `scripts/check_open_gates.py` 驗證）。缺陷修好
之後就拆掉這道門禁——不要讓它變成永久稅。

用法：
    python scripts/native_dialogue_budget_gate.py
    python scripts/native_dialogue_budget_gate.py --report /tmp/nd.json   # 用既有報告裁決
    python scripts/native_dialogue_budget_gate.py --allow-lower
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
BUDGET_FILE = REPO_ROOT / "scripts" / "native_dialogue_budget.txt"
PROBE = REPO_ROOT / "scripts" / "probe_native_dialogue.py"
REGISTRY = REPO_ROOT / "scripts" / "open_gates.json"

# The budget keys and how they are read out of the report.
#   ("min", key) → the value must be ≥ the threshold
#   ("max", key) → the value must be ≤ the threshold
CHECKS: Tuple[Tuple[str, str, str], ...] = (
    ("min", "human_score", "pass1.human_score"),
    ("min", "progress", "progress"),
    ("max", "echo_rate", "pass1.rates.echo"),
    ("max", "artifact_rate", "pass1.rates.artifact"),
    ("max", "qa_machine_rate", "pass1.rates.qa_machine"),
    ("max", "offtopic_rate", "pass1.rates.offtopic"),
    ("max", "abstain_rate", "pass1.rates.abstain"),
    ("max", "empty_rate", "pass1.rates.empty"),
    ("max", "ramble_rate", "pass1.rates.ramble"),
    ("max", "stale_fact_rate", "pass1.rates.stale_fact"),
    # The human-speech standard (the rubric in ai/response/human_speech.py)
    # and the standard set's size — a mean over fewer than 1000 items cannot
    # prove "can speak human language" (the sample may be constrained by the
    # Q&A behaviour itself, or be too simple).
    ("min", "standard_size", "standard_set.size"),
    ("min", "human_speech_pass_rate", "standard_set.pass_rate"),
    ("min", "state_pass_rate", "standard_set.by_kind.state.passed_ratio"),
    ("min", "multi_pass_rate", "standard_set.by_kind.multi.passed_ratio"),
    ("min", "claim_pass_rate", "standard_set.by_kind.claim.passed_ratio"),
    # The first-class "is this intelligence or copied templates?" metric:
    # the share of the answers produced by a *learned* model (the neural
    # retrieval / the statistical core / the neural bridge).
    ("min", "neural_share", "neural_share"),
)


def load_budget() -> Dict[str, float]:
    """The budget file (key = value, '#' comments)."""
    budget: Dict[str, float] = {}
    for raw in BUDGET_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or "=" not in line:
            continue
        key, _, value = line.partition("=")
        try:
            budget[key.strip()] = float(value.strip())
        except ValueError:
            continue
    return budget


def dig(report: dict, path: str) -> float:
    """Read a dotted path out of the report (missing → 0.0).

    A rate is stored as a dict ({"rate":…, "hits":…, "total":…, "ci95":…}) —
    the gate reads the rate itself.
    """
    current: object = report
    for part in path.split("."):
        if not isinstance(current, dict):
            return 0.0
        current = current.get(part)
        if current is None:
            return 0.0
    if isinstance(current, dict):
        current = current.get("rate", 0.0)
    try:
        return float(current)
    except (TypeError, ValueError):
        return 0.0


def removal_reason() -> str:
    """The removal reason of this gate (from the registry)."""
    try:
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except Exception:
        return ""
    for entry in registry.get("gates") or []:
        if entry.get("id") == "native-dialogue-budget":
            return str(entry.get("removal_criterion") or "")
    return ""


def run_probe(report_path: Path, learning: str) -> Tuple[dict, int]:
    """Run the probe and return (report, exit code)."""
    command = [
        sys.executable,
        str(PROBE),
        "--json",
        str(report_path),
        "--learning",
        learning,
    ]
    result = subprocess.run(command, cwd=str(REPO_ROOT), check=False)
    if not report_path.is_file():
        return {}, result.returncode
    return json.loads(report_path.read_text(encoding="utf-8")), result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", dest="report_path", help="judge an existing report JSON")
    parser.add_argument(
        "--allow-lower", action="store_true", help="allow the result to beat the budget"
    )
    parser.add_argument(
        "--learning", choices=("off", "on"), default="off", help="the learning switch"
    )
    parser.add_argument("--json", dest="json_path", help="write the verdict as JSON")
    args = parser.parse_args()

    budget = load_budget()
    if not budget:
        print(f"❌ the budget file is empty or unreadable: {BUDGET_FILE}")
        return 1

    report_path = (
        Path(args.report_path)
        if args.report_path
        else REPO_ROOT / "data" / "native_dialogue_report.json"
    )
    if args.report_path:
        if not report_path.is_file():
            print(f"❌ the report does not exist: {report_path}")
            return 1
        report = json.loads(report_path.read_text(encoding="utf-8"))
    else:
        report, _ = run_probe(report_path, args.learning)

    if not report:
        print("❌ the probe produced no report")
        return 1

    used_budget = report.get("budget") or {}
    violations: List[str] = []
    checks: List[dict] = []

    # The budget consumption itself: the run must stay inside the budget.
    max_turns = budget.get("max_turns")
    max_seconds = budget.get("max_seconds")
    if max_turns is not None and used_budget.get("used_turns", 0) > max_turns:
        violations.append(
            f"the run used {used_budget.get('used_turns')} turns (the budget is {max_turns:.0f})"
        )
    if max_seconds is not None and used_budget.get("used_seconds", 0) > max_seconds:
        violations.append(
            f"the run used {used_budget.get('used_seconds')}s (the budget is {max_seconds:.0f}s)"
        )

    # The measurement itself must be valid and stable: a sample that cannot
    # tell the shapes apart (or whose conclusion flips with the sample size)
    # is not a measurement — the gate must not pass on it.
    validity = report.get("validity") or {}
    if not validity.get("valid", False):
        for problem in validity.get("problems", []) or ["the sample is not valid"]:
            violations.append(f"sample validity: {problem}")
    consistency = report.get("consistency") or {}
    if not consistency.get("consistent", False):
        for item in consistency.get("disagreements", []) or ["the small and the standard disagree"]:
            violations.append(f"sample consistency: {item}")

    for direction, key, path in CHECKS:
        threshold = budget.get(key)
        if threshold is None:
            continue
        actual = dig(report, path)
        ok = actual >= threshold if direction == "min" else actual <= threshold
        checks.append(
            {"key": key, "path": path, "actual": actual, "threshold": threshold, "ok": ok}
        )
        if not ok:
            comparison = "≥" if direction == "min" else "≤"
            violations.append(f"{key}: {actual} (the budget requires {comparison} {threshold})")

    print("純本地對話預算門禁（不接任何外部 LLM）")
    print(
        "  預算消耗：回合 {t}/{tt}　秒數 {s:.1f}/{ss:.0f}".format(
            t=used_budget.get("used_turns", 0),
            tt=budget.get("max_turns", 0),
            s=float(used_budget.get("used_seconds", 0) or 0),
            ss=budget.get("max_seconds", 0),
        )
    )
    for check in checks:
        mark = "✅" if check["ok"] else "❌"
        print(
            f"  {mark} {check['key']}: {check['actual']}（門檻 {check['threshold']}，來源 {check['path']}）"
        )
    if report.get("progress") is not None:
        print(
            f"  學習效應（冷→熱）：{report.get('progress'):+}　穩定度（兩輪差）：{report.get('stability')}"
        )
    standard = report.get("standard_set") or {}
    if standard:
        print(
            f"  標準集 {standard.get('size', 0)} 回合｜人話標準通過 {standard.get('passed', 0)}"
            f"（{standard.get('pass_rate', 0):.1%}）"
        )
    validity = report.get("validity") or {}
    consistency = report.get("consistency") or {}
    print(
        f"  樣本有效性：{'✅' if validity.get('valid') else '❌'}"
        f"（回合 {validity.get('turns', 0)}、不同輸出 {validity.get('distinct_responses', 0)} 種、"
        f"教→問 {validity.get('learning_pairs', 0)} 組）"
    )
    print(
        f"  少量 vs 標準量一致性：{'✅' if consistency.get('consistent') else '❌'}"
        f"（少量 n={((report.get('small_sample') or {}).get('turns', 0))}、"
        f"標準 n={((report.get('standard_sample') or {}).get('turns', 0))}）"
    )

    reason = removal_reason()
    if reason:
        print("  ⏳ 這是臨時門禁，拆除理由：")
        print(f"     {reason}")

    if violations:
        print("  ❌ 超標：")
        for item in violations:
            print(f"    - {item}")
        return 1

    if not args.allow_lower and _has_headroom(budget, checks):
        print("  ⚠️ 實際優於預算——請把門檻調到實測值（門禁只會變緊）；或用 --allow-lower 通過。")
        return 1

    print("  ✅ 通過")
    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(
                {"checks": checks, "violations": violations, "ok": not violations},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return 0


def _has_headroom(budget: Dict[str, float], checks: List[dict]) -> bool:
    """True when every measured value is strictly better than the budget."""
    for check in checks:
        threshold = check["threshold"]
        actual = check["actual"]
        if check["key"] in ("human_score", "progress"):
            if actual <= threshold:
                return False
        else:
            if actual >= threshold:
                return False
    return bool(checks)


if __name__ == "__main__":
    raise SystemExit(main())
