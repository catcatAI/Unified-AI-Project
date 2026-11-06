#!/usr/bin/env python
"""把六個耦合層級的閘門收成**一個可重跑的命令**（AL 生命證據的總回歸）

每一支 `al_*.py` 都是自己量一件事：節律源、相位→決定、C-param、C-logit、
C-state、C-learn、C-learn 生產接線。它們各自的判準都在自己的檔案裡，但如果
沒有人一次把**全部**跑過，這套「證據」就會隨時間腐爛：改了模型、換了參數、
某個腳本不再 import——而文件還寫著「成立」。

這支做兩件事：

1. 逐層呼叫各閘門的 ``run()``，抽出「判定了什麼、控制組長什麼樣」；
2. 檢查**證據紀律**：每一層都必須回報至少一個控制組／反偽造項。只回報
   「有效應」而沒有控制組的層，不算證據（`no-control`）。

輸出是給人看的一張表。任何一層的期望判詞改變、或控制組消失，總閘門就失敗。
"""

# =============================================================================
# ANGELA-MATRIX: [L3] [αβγδ] [C] [L0-L11]
# =============================================================================

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

# 控制組／反偽造項的命名慣例：名字裡有這些字的檢查，代表它不是在量「有效應」，
# 而是在量「效應不是假的」。
CONTROL_HINTS = (
    "control",
    "identical",
    "untouched",
    "reproducible",
    "not_random",
    "forgery",
    "shuffle",
    "permut",
    "swap",
)


def _load(module_name: str):
    path = SCRIPTS / f"{module_name}.py"
    spec = importlib.util.spec_from_file_location(f"al_gate_{module_name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _check_controls(checks: Dict[str, object]) -> List[Tuple[str, bool]]:
    """把「控制組」挑出來。布林直接看值；dict 看裡面的 ``passed`` / ``ok``。"""
    found: List[Tuple[str, bool]] = []
    for name, value in checks.items():
        lowered = name.lower()
        if not any(hint in lowered for hint in CONTROL_HINTS):
            continue
        if isinstance(value, bool):
            found.append((name, value))
        elif isinstance(value, dict):
            for key in ("passed", "ok", "identical"):
                if key in value:
                    found.append((f"{name}.{key}", bool(value[key])))
                    break
    return found


def _forgery_controls(forgeries: Dict[str, object]) -> List[Tuple[str, bool]]:
    """偽造品必須**失敗**（passed=False）才算控制成立。"""
    found: List[Tuple[str, bool]] = []
    for name, value in forgeries.items():
        if isinstance(value, dict) and "passed" in value:
            found.append((f"forgery:{name} fails", not bool(value["passed"])))
        elif isinstance(value, bool):
            found.append((f"forgery:{name} fails", not value))
    return found


def _evaluate(name: str, result: Dict[str, object], expected: str) -> Dict[str, object]:
    """把一支腳本的結果壓成 (passed, verdict, controls, headline)。"""
    verdict = str(result.get("verdict", "")) if "verdict" in result else ""
    controls: List[Tuple[str, bool]] = []

    checks = result.get("checks")
    if isinstance(checks, dict):
        controls.extend(_check_controls(checks))
        flat = [v for v in checks.values() if isinstance(v, bool)]
        checks_ok = all(flat) if flat else True
    else:
        checks_ok = True

    forgeries = result.get("forgeries")
    if isinstance(forgeries, dict):
        controls.extend(_forgery_controls(forgeries))

    # 電源循環那支沒有 `checks`：它的控制組是兩個偽造誤差必須遠大於真誤差。
    if "forgery_hold_error" in result and "forgery_reset_error" in result:
        controls.append(("forgery:hold error ≫ real", float(result["forgery_hold_error"]) > 1e-6))
        controls.append(("forgery:reset error ≫ real", float(result["forgery_reset_error"]) > 1e-6))

    if "admissible" in result:
        passed = bool(result["admissible"])
    elif "main_ok" in result:
        passed = bool(result["main_ok"]) and bool(result.get("forgeries_all_fail", False))
    elif "passed" in result:
        passed = bool(result["passed"])
    else:
        # 有幾支只在 main() 裡把 checks 全部 AND 起來，沒有回傳 admissible。
        # 那就照同樣的規則在這裡算，而不是預設失敗。
        passed = checks_ok
    if not checks_ok:
        passed = False

    if expected and verdict != expected:
        passed = False

    # 證據紀律：沒有控制組回報的層，不算證據。
    if not controls:
        passed = False
        discipline = "no-control"
    elif not all(ok for _, ok in controls):
        passed = False
        discipline = "control-failed"
    else:
        discipline = "ok"

    headline = _headline(result)
    return {
        "rung": name,
        "module": result.get("kind", name),
        "verdict": verdict or "(no verdict)",
        "expected": expected,
        "passed": bool(passed),
        "discipline": discipline,
        "headline": headline,
        "controls": [{"name": n, "ok": ok} for n, ok in controls],
    }


def _headline(result: Dict[str, object]) -> str:
    """一層一句話：挑一個最有辨識度的數字。"""
    if "error" in result and "gap_seconds" in result:
        return f"restart gap {result['gap_seconds']}s, error {float(result['error']):.1e}"
    if "natural_period_s" in result:
        return f"natural period {result['natural_period_s']}s"
    if "kl_max" in result:
        return f"max KL {result['kl_max']}"
    if "weight_spread" in result:
        return f"weight spread {result['weight_spread']}"
    if "crossover_spread" in result:
        return f"crossover spread {result['crossover_spread']}"
    if "single_path" in result and isinstance(result["single_path"], dict):
        return f"ΔW {result['single_path'].get('max_weight_delta'):.6f}"
    for key in ("explained_variance", "explained", "rho", "r"):
        if key in result:
            return f"{key} {result[key]}"
    return "—"


def _run_rung(
    name: str, module: str, expected: str, kwargs: Dict[str, object]
) -> Dict[str, object]:
    try:
        mod = _load(module)
        result = mod.run(**kwargs)
    except Exception as exc:  # noqa: BLE001 - 一層壞掉不能帶走整張表
        return {
            "rung": name,
            "module": module,
            "verdict": f"error: {type(exc).__name__}: {exc}",
            "expected": expected,
            "passed": False,
            "discipline": "error",
            "headline": "—",
            "controls": [],
        }
    return _evaluate(name, result, expected)


RUNGS: Sequence[Tuple[str, str, str, Dict[str, object]]] = (
    ("rhythm-source", "al_rhythm_source", "self-rhythm-admissible", {"seconds": 120.0}),
    ("power-cycle", "al_power_cycle", "", {"seconds": 3.1}),
    ("phase-effect", "al_phase_effect", "phase-affects-decision", {}),
    ("c-param", "al_c_param", "generation-params-modulated", {}),
    ("c-logit", "al_c_logit", "phase-reaches-logits", {}),
    ("c-state", "al_c_state", "phase-changes-internal-dynamics", {}),
    ("c-learn", "al_c_learn", "phase-decides-what-gets-kept", {}),
    ("c-learn-wired", "al_c_learn_wired", "phase-reaches-learning-in-production", {}),
)


def run(only: Optional[Sequence[str]] = None) -> Dict[str, object]:
    wanted = set(only) if only else None
    rows: List[Dict[str, object]] = []
    for name, module, expected, kwargs in RUNGS:
        if wanted is not None and name not in wanted:
            continue
        started = time.time()
        row = _run_rung(name, module, expected, kwargs)
        row["seconds"] = round(time.time() - started, 1)
        rows.append(row)

    failed = [row["rung"] for row in rows if not row["passed"]]
    admissible = bool(rows) and not failed
    return {
        "kind": "al_evidence_gate",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "rows": rows,
        "failed": failed,
        "admissible": admissible,
        "verdict": "all-rungs-admissible" if admissible else "evidence-incomplete",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", nargs="*", default=None, help="只跑這幾層")
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    result = run(args.only)
    for row in result["rows"]:  # type: ignore[index]
        mark = "ok  " if row["passed"] else "FAIL"
        print(
            f"{mark} {row['rung']:<16} {row['verdict']:<40} "
            f"controls={len(row['controls'])} {row['seconds']}s  {row['headline']}"
        )
        if not row["passed"]:
            print(f"     discipline: {row['discipline']}")
            for control in row["controls"]:
                if not control["ok"]:
                    print(f"     control failed: {control['name']}")
    print(f"verdict: {result['verdict']}  failed={result['failed']}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"report: {args.json}")
    return 0 if result["admissible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
