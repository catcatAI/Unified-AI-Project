#!/usr/bin/env python3
"""未拆門禁登記簿的驗證器 — 沒有正當、正確的拆除理由，一律拒收。

`scripts/open_gates.json` 只收**將來必須拆掉**的臨時門禁。每條進來之前必須
通過下列檢查（任一不過 → exit 1）：

1. **欄位齊全且非空**：`id`／`script`／`opened`／`owner`／`why_temporary`／
   `removal_criterion`／`ci_step`。
2. **拆除理由必須可驗證**：`removal_criterion` 必須含門檻數字、指令或日期；
   不得含模糊字眼（「之後」「視情況」「待定」「有空」「再說」…）。
3. **為什麼是臨時的必須說得清**：`why_temporary` 必須指出一個「會被修好」的
   缺陷（不得只是「先擋著」）。
4. **檔案必須存在**：`script`／`budget` 指向的檔案要在樹上。
5. **門禁必須真的接在 CI 上**：`ci_step` 的指令必須出現在
   `.github/workflows/ci.yml`——沒接 CI 的登記項是假的。
6. **永久門禁不得進入本簿**：帶 `permanent: true` 的條目直接拒收（永久門禁
   直接住在 CI 設定裡，不需要拆除理由）。

用法：
    python scripts/check_open_gates.py
    python scripts/check_open_gates.py --json out.json
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "scripts" / "open_gates.json"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"

REQUIRED_FIELDS = (
    "id",
    "script",
    "opened",
    "owner",
    "why_temporary",
    "removal_criterion",
    "ci_step",
)

# The wording that makes a removal reason unusable.
VAGUE_MARKERS = (
    "之後",
    "以後",
    "視情況",
    "待定",
    "有空",
    "再說",
    "暫時",
    "先擋",
    "later",
    "eventually",
    "when ready",
    "as needed",
    "someday",
    "tbd",
    "todo",
)

# A removal reason has to name a checkable condition.
MEASURABLE = (
    re.compile(r"\d"),  # a threshold / a count
    re.compile(r"python\s+[a-z0-9_./\-]+\.py", re.IGNORECASE),  # a command
    re.compile(r"pytest\s+", re.IGNORECASE),
    re.compile(r"\d{4}-\d{2}-\d{2}"),  # a date
)


def _load() -> dict:
    try:
        return json.loads(REGISTRY.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"❌ the registry is unreadable: {exc}")


def check_entry(entry: dict, ci_text: str) -> List[str]:
    """The reasons this entry must not be in the registry."""
    problems: List[str] = []
    entry_id = entry.get("id", "<no id>")

    if entry.get("permanent"):
        problems.append(
            f"{entry_id}: a permanent gate must not be in the registry "
            "(it lives in the CI config; there is nothing to remove)"
        )
        return problems

    for field in REQUIRED_FIELDS:
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"{entry_id}: the field {field!r} is missing or empty")

    criterion = str(entry.get("removal_criterion") or "")
    if criterion:
        lowered = criterion.lower()
        for marker in VAGUE_MARKERS:
            if marker in lowered:
                problems.append(
                    f"{entry_id}: the removal reason contains the vague wording "
                    f"{marker!r} — a removal reason must be checkable"
                )
        if not any(pattern.search(criterion) for pattern in MEASURABLE):
            problems.append(
                f"{entry_id}: the removal reason names no checkable condition "
                "(a threshold, a command or a date)"
            )

    why = str(entry.get("why_temporary") or "")
    if why and not re.search(r"缺陷|bug|defect|broken|regression|gap", why, re.IGNORECASE):
        problems.append(
            f"{entry_id}: why_temporary must name the defect the gate guards "
            "(a gate without a fixable defect has no reason to exist)"
        )

    script = str(entry.get("script") or "")
    if script and not (REPO_ROOT / script).is_file():
        problems.append(f"{entry_id}: the script {script!r} does not exist")
    budget = entry.get("budget")
    if budget and not (REPO_ROOT / str(budget)).is_file():
        problems.append(f"{entry_id}: the budget {budget!r} does not exist")

    ci_step = str(entry.get("ci_step") or "")
    if ci_step:
        script_name = Path(script).name if script else ci_step
        if script_name and script_name not in ci_text:
            problems.append(
                f"{entry_id}: the gate is not wired into .github/workflows/ci.yml "
                "(a registered gate that never runs is a lie)"
            )
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", dest="json_path", help="write the verdict as JSON")
    args = parser.parse_args()

    registry = _load()
    gates: List[dict] = registry.get("gates") or []
    ci_text = CI_WORKFLOW.read_text(encoding="utf-8") if CI_WORKFLOW.is_file() else ""

    problems: List[str] = []
    seen_ids: Dict[str, int] = {}
    for entry in gates:
        problems.extend(check_entry(entry, ci_text))
        entry_id = str(entry.get("id"))
        seen_ids[entry_id] = seen_ids.get(entry_id, 0) + 1
    for entry_id, count in seen_ids.items():
        if count > 1:
            problems.append(f"{entry_id}: registered {count} times (the id must be unique)")

    result = {
        "registered": len(gates),
        "ids": [str(g.get("id")) for g in gates],
        "problems": problems,
        "ok": not problems,
    }

    print("未拆門禁登記簿驗證（沒有正當拆除理由者不得入簿）")
    print(f"  登記中的臨時門禁：{len(gates)}")
    for entry in gates:
        print(f"    - {entry.get('id')}")
    if problems:
        print("  ❌ 違規：")
        for item in problems:
            print(f"    - {item}")
    else:
        print("  ✅ 通過：每條都有正當、可驗證的拆除理由")

    if args.json_path:
        Path(args.json_path).write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"  結果已寫入 {args.json_path}")
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
