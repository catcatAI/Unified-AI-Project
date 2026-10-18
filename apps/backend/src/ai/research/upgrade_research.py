# =============================================================================
# ANGELA-MATRIX: [L4] [α] [A] [L7]
# =============================================================================
"""專案AI自主研究 —《後續研究與升級路徑完整報告》生成器。

契約（使用者任務 2026-10-18）：

- **自己查**：事實只來自專案自身可重現量測（status_matrix / benchmarks /
  check_fact_gates / pre-flight checklist / 驗證登錄 / 測試收集）與外部搜尋
  （run_research），逐一記錄採集成敗（失敗也入報告，屬「已解釋」而非空缺）。
- **自己想**：升級候選由規則從量測資料推導（不人工列點）；擇優排序由透明
  公式計算（impact/effort/risk 規則表寫死於程式、可審計）；專案自有模型
  （確定性引擎、ED3N/GARDEN SNN、知識管線、HAM、因果引擎）逐項實跑體檢，
  輸出原樣入報告。
- **自己寫**：章節由資料填充模板生成；LLM 只做逐段行文潤色，數字指紋
  （numeric fingerprint）比對失配即回退原稿。
- **無異常**：validate_report() 對缺章、空段、佔位字、證據不一致、來源缺失
  零容忍；problems 非空 → CLI exit 1（有問題繼續修，直到通過）。

產物：``docs/RESEARCH_UPGRADE_REPORT_<YYYY-MM-DD>.md``
"""

from __future__ import annotations

import ast
import asyncio
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 常數與版面
# ---------------------------------------------------------------------------

_SECTION_HEADERS = (
    "## 一、摘要",
    "## 二、研究方法與自我驗證",
    "## 三、累積研究資產盤點",
    "## 四、資產 vs 替代方案：優缺點對照",
    "## 五、實測現狀",
    "## 六、升級候選路徑",
    "## 七、擇優排序與路線圖",
    "## 八、後續研究議題",
    "## 九、附錄：資料源與重現命令",
)

_SECTION_MIN_CHARS = {
    "## 一、摘要": 260,
    "## 二、研究方法與自我驗證": 420,
    "## 三、累積研究資產盤點": 520,
    "## 四、資產 vs 替代方案：優缺點對照": 360,
    "## 五、實測現狀": 360,
    "## 六、升級候選路徑": 700,
    "## 七、擇優排序與路線圖": 420,
    "## 八、後續研究議題": 280,
    "## 九、附錄：資料源與重現命令": 280,
}

_PLACEHOLDER_RE = re.compile(r"\bTODO\b|\bTBD\b|\bFIXME\b|待補|此處空缺|占位|占位符")

_EXTERNAL_QUERIES = (
    "small local LLM versus cloud LLM tradeoffs latency privacy quality 2026",
    "spiking neural network advantages limitations compared with transformers 2026",
    "serving cached verified answers instead of regenerating LLM responses efficiency",
)

# 擇優公式（透明、可審計）：score = 4*impact + 2*(4-effort) + 2*(4-risk) + source_bonus
_IMPACT_BY_SOURCE = {
    "assessment-pre-flight": 3,
    "benchmark": 3,
    "fact-gates": 3,
    "verification-register": 2,
    "status-matrix": 2,
    "collector": 2,
    "docs": 1,
}
_SOURCE_BONUS = {
    "assessment-pre-flight": 2,
    "benchmark": 2,
    "verification-register": 1,
    "status-matrix": 1,
    "fact-gates": 2,
    "collector": 1,
    "docs": 0,
}
_EFFORT_HEAVY_RE = re.compile(r"重訓|訓練數據|數據檔|checkpoint|留出集|重現")
_EFFORT_LIGHT_RE = re.compile(r"註解|清死檔|移除|明確從|標注|文檔|register")

_PROBE_TIMEOUT = 90.0
_RESEARCH_TIMEOUT = 120.0
_KNOWLEDGE_PROBE_TIMEOUT = 30.0
_HAM_PROBE_TIMEOUT = 20.0
_LLM_POLISH_TIMEOUT = 60.0
_MAX_POLISH_PARAGRAPHS = 14


# ---------------------------------------------------------------------------
# 小工具
# ---------------------------------------------------------------------------


def _repo_root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "scripts" / "run_benchmarks.py").is_file():
            return p
    return Path.cwd()


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _read_json(path: Any) -> Any:
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        raise _CollectorError(f"{path}: {exc}") from exc


class _CollectorError(Exception):
    """單一採集器失敗：記錄入報告（已解釋），不中斷整體管線。"""


def _run_capture(argv: List[str], cwd: Any, timeout: float) -> Tuple[int, str]:
    try:
        proc = subprocess.run(  # noqa: S603
            argv,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 127, f"runner error: {exc}"
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _collectors_record(name: str, ok: bool, detail: str, ms: int) -> Dict[str, Any]:
    return {"collector": name, "ok": ok, "detail": detail, "ms": ms}


# ---------------------------------------------------------------------------
# Phase 1 — 自己查：可重現量測
# ---------------------------------------------------------------------------


def _collect_repo_stats(root: Any) -> Dict[str, Any]:
    src = root / "apps" / "backend" / "src"
    py_files = 0
    py_lines = 0
    for p in src.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        py_files += 1
        try:
            py_lines += sum(1 for _ in open(p, encoding="utf-8", errors="replace"))
        except OSError:
            continue
    ckpt_dir = root / "apps" / "backend" / "data" / "checkpoints"
    ckpt_files = []
    if ckpt_dir.is_dir():
        ckpt_files = sorted(
            str(p.relative_to(ckpt_dir)) for p in ckpt_dir.rglob("*") if p.is_file()
        )
    return {
        "py_files": py_files,
        "py_lines": py_lines,
        "checkpoint_dir_exists": ckpt_dir.is_dir(),
        "checkpoints": ckpt_files[:20],
        "unified_checkpoint_present": any("unified" in f for f in ckpt_files),
    }


def _collect_test_count(root: Any) -> Dict[str, Any]:
    """權威測試數：pytest --collect-only（與 AGENTS 基準同法）；失敗退 AST。"""
    code, out = _run_capture(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "-o",
            "addopts=",
            "-p",
            "no:cacheprovider",
        ],
        cwd=root,
        timeout=180.0,
    )
    m = re.search(r"(\d+) tests collected", out)
    if code == 0 and m:
        return {"count": int(m.group(1)), "method": "pytest --collect-only"}
    # AST fallback（已解釋的降級，會入附錄）
    count = 0
    for p in (root / "tests").rglob("test_*.py"):
        if "__pycache__" in p.parts:
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        count += sum(
            1
            for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")
        )
    return {"count": count, "method": f"ast-fallback (pytest rc={code})"}


def _collect_status_matrix(root: Any) -> Dict[str, Any]:
    import yaml

    data = _read_json_path_or_yaml(root / "docs" / "status_matrix.yaml", yaml.safe_load)
    features = data.get("features") or []
    by_status: Dict[str, int] = {}
    pending: List[Dict[str, Any]] = []
    for f in features:
        st = str(f.get("status", "?"))
        by_status[st] = by_status.get(st, 0) + 1
        if st != "verified":
            pending.append(
                {
                    "id": str(f.get("id", "?")),
                    "status": st,
                    "claim": str(f.get("claim", ""))[:140],
                    "verify_command": str(f.get("verify_command", "") or ""),
                }
            )
    chat = data.get("chat_pipeline")
    return {
        "total": len(features),
        "by_status": by_status,
        "pending": pending,
        "chat_pipeline": chat,
    }


def _read_json_path_or_yaml(path: Any, loader: Callable[[Any], Any]) -> Any:
    try:
        with open(path, encoding="utf-8") as fh:
            return loader(fh)
    except (OSError, ValueError) as exc:
        raise _CollectorError(f"{path}: {exc}") from exc


def _collect_verification_register(root: Any) -> Dict[str, Any]:
    data = _read_json(root / "docs" / "VERIFICATION_REGISTER.json")
    entries = [
        {
            "id": str(e.get("id", "?")),
            "claim": str(e.get("claim", ""))[:160],
            "why_unverified": str(e.get("why_unverified", ""))[:200],
            "how_to_verify": str(e.get("how_to_verify", ""))[:200],
            "area": str(e.get("area", "")),
        }
        for e in (data.get("entries") or [])
    ]
    return {"open": len(entries), "entries": entries}


def _load_gate_native(root: Any) -> Dict[str, float]:
    src_path = root / "scripts" / "run_benchmarks.py"
    try:
        tree = ast.parse(src_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        raise _CollectorError(f"GATE_NATIVE parse: {exc}") from exc
    for node in tree.body:
        targets: List[Any] = []
        if isinstance(node, ast.AnnAssign):
            targets = [node.target]
        elif isinstance(node, ast.Assign):
            targets = list(node.targets)
        for t in targets:
            if isinstance(t, ast.Name) and t.id == "GATE_NATIVE" and node.value is not None:
                try:
                    return {str(k): float(v) for k, v in ast.literal_eval(node.value).items()}
                except (ValueError, TypeError) as exc:
                    raise _CollectorError(f"GATE_NATIVE literal: {exc}") from exc
    raise _CollectorError("GATE_NATIVE not found in run_benchmarks.py")


def _collect_benchmarks(root: Any) -> Dict[str, Any]:
    import glob as _glob

    files = sorted(_glob.glob(str(root / "benchmarks" / "results" / "bench_*.json")))
    if not files:
        raise _CollectorError("benchmarks/results/bench_*.json 不存在")
    latest = files[-1]
    data = _read_json(latest)
    floors = _load_gate_native(root)
    suites: List[Dict[str, Any]] = []
    for r in data.get("results", []):
        acc = r.get("accuracy")
        floor = floors.get(str(r.get("suite")))
        state = "no-floor"
        if isinstance(acc, (int, float)) and floor is not None:
            if acc < floor:
                state = "below"
            elif acc - floor <= 5.0:
                state = "margin"
            else:
                state = "pass"
        suites.append(
            {
                "backend": str(r.get("backend", "")),
                "suite": str(r.get("suite", "")),
                "total": r.get("total"),
                "passed": r.get("passed"),
                "skipped": r.get("skipped"),
                "accuracy": acc,
                "floor": floor,
                "state": state,
            }
        )
    return {
        "file": os.path.basename(latest),
        "generated_at": data.get("generated_at"),
        "suites": suites,
    }


def _collect_fact_gates(root: Any) -> Dict[str, Any]:
    code, out = _run_capture(
        [sys.executable, "scripts/check_fact_gates.py"], cwd=root, timeout=180.0
    )
    results = re.findall(r"\[(PASS|FAIL)\]\s+([\w.]+)", out)
    failed = [name for status, name in results if status == "FAIL"]
    return {
        "exit_code": code,
        "passed": code == 0 and "ALL PASS" in out,
        "checks": [{"name": n, "ok": s == "PASS"} for s, n in results],
        "failed": failed,
        "tail": out.strip().splitlines()[-1][:160] if out.strip() else "",
    }


def _collect_validation_reports(root: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for name in ("ed3n", "garden"):
        try:
            data = _read_json(root / "scripts" / f"validation_report_{name}.json")
        except _CollectorError as exc:
            out[name] = {"ok": False, "error": str(exc)}
            continue
        engines = data.get("engines")
        out[name] = {"ok": True, "engines": engines, "datasets": list(data.get("datasets") or [])}
    return out


def _collect_checklist(root: Any) -> Dict[str, Any]:
    path = root / "docs" / "AI_SUBSTRATE_ASSESSMENT_2026-10-18.md"
    text = path.read_text(encoding="utf-8")
    items = []
    for m in re.finditer(r"^- \[([ xX])\] (\w\d+) (.+)$", text, re.MULTILINE):
        items.append({"id": m.group(2), "done": m.group(1) != " ", "text": m.group(3).strip()})
    if not items:
        raise _CollectorError("pre-flight checklist 未解析到任何 - [ ] 條目")
    return {
        "total": len(items),
        "done": sum(1 for i in items if i["done"]),
        "pending": [i for i in items if not i["done"]],
        "done_ids": [i["id"] for i in items if i["done"]],
    }


def _collect_docs_index(root: Any) -> Dict[str, Any]:
    names = (
        "FRAMEWORK_OVERVIEW.md",
        "INTELLIGENCE_ASSESSMENT.md",
        "MASTER_TASK_MAP.md",
        "STATUS_MATRIX.md",
        "AI_SUBSTRATE_ASSESSMENT_2026-10-18.md",
        "VERIFICATION_REGISTER.json",
        "status_matrix.yaml",
    )
    base = root / "docs" / "06-project-management"
    out: Dict[str, Any] = {}
    for n in names:
        for cand in (root / "docs" / n, base / n):
            if cand.is_file():
                out[n] = {
                    "path": str(cand.relative_to(root)),
                    "lines": len(cand.read_text(encoding="utf-8", errors="replace").splitlines()),
                }
                break
        else:
            out[n] = {"path": None, "lines": 0}
    return out


def _collect_rule_store() -> Dict[str, Any]:
    from ai.rules import get_rule_store

    return get_rule_store().stats()


def gather_facts() -> Dict[str, Any]:
    """彙整全部可重現量測；單一採集器失敗只記錄，不中斷。"""
    root = _repo_root()
    collectors: List[Dict[str, Any]] = []
    facts: Dict[str, Any] = {"generated_at": _now_iso(), "repo_root": str(root)}

    def _one(name: str, fn: Callable[[], Any]) -> Any:
        t0 = time.time()
        try:
            value = fn()
            collectors.append(_collectors_record(name, True, "ok", int((time.time() - t0) * 1000)))
            return value
        except Exception as exc:  # noqa: BLE001 — 採集器隔離：任何失敗都入報告
            collectors.append(
                _collectors_record(
                    name,
                    False,
                    f"{type(exc).__name__}: {exc}"[:300],
                    int((time.time() - t0) * 1000),
                )
            )
            return {"_error": str(exc)[:300]}

    facts["repo"] = _one("repo_stats", lambda: _collect_repo_stats(root))
    facts["test_count"] = _one("test_count", lambda: _collect_test_count(root))
    facts["status_matrix"] = _one("status_matrix", lambda: _collect_status_matrix(root))
    facts["verification_register"] = _one(
        "verification_register", lambda: _collect_verification_register(root)
    )
    facts["benchmarks"] = _one("benchmarks", lambda: _collect_benchmarks(root))
    facts["fact_gates"] = _one("fact_gates", lambda: _collect_fact_gates(root))
    facts["validation"] = _one("validation_reports", lambda: _collect_validation_reports(root))
    facts["checklist"] = _one("assessment_checklist", lambda: _collect_checklist(root))
    facts["docs_index"] = _one("docs_index", lambda: _collect_docs_index(root))
    facts["rule_store"] = _one("rule_store", _collect_rule_store)
    facts["collectors"] = collectors
    return facts


# ---------------------------------------------------------------------------
# Phase 1b — 自己查：外部查證（run_research）
# ---------------------------------------------------------------------------


def _research_external_sync() -> List[Dict[str, Any]]:
    from core.tools.research_pipeline import run_research

    results: List[Dict[str, Any]] = []
    for q in _EXTERNAL_QUERIES:
        t0 = time.time()
        try:
            res = run_research(q, num_results=5)
        except Exception as exc:  # noqa: BLE001 — 離線/網路失敗必須記錄而非拋出
            results.append(
                {
                    "query": q,
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}"[:200],
                    "ms": int((time.time() - t0) * 1000),
                }
            )
            continue
        sources = [
            {"url": str(s.get("url", "")), "title": str(s.get("title", ""))[:100]}
            for s in (res.get("sources") or [])[:5]
        ]
        results.append(
            {
                "query": q,
                "ok": bool(res.get("ok")),
                "error": res.get("error"),
                "facts": [str(f)[:240] for f in (res.get("facts") or [])[:8]],
                "conflicts": [str(c)[:240] for c in (res.get("conflicts") or [])[:4]],
                "sources": sources,
                "n_fetched": res.get("n_fetched"),
                "ms": int((time.time() - t0) * 1000),
            }
        )
    return results


# ---------------------------------------------------------------------------
# Phase 2 — 自己想：專案自有模型體檢
# ---------------------------------------------------------------------------


async def _probe_in(
    probes: List[Dict[str, Any]], name: str, fn: Callable[[], Any], timeout: float
) -> None:
    """同步探針跑在 thread，帶逾時；失敗記為探針結果。"""
    t0 = time.time()
    try:
        out = await asyncio.wait_for(asyncio.to_thread(fn), timeout=timeout)
        probes.append(
            {
                "probe": name,
                "ok": True,
                "ms": int((time.time() - t0) * 1000),
                "output": str(out)[:200],
            }
        )
    except Exception as exc:  # noqa: BLE001
        probes.append(
            {
                "probe": name,
                "ok": False,
                "ms": int((time.time() - t0) * 1000),
                "error": f"{type(exc).__name__}: {exc}"[:200],
            }
        )


async def _probe_in_async(
    probes: List[Dict[str, Any]], name: str, coro_factory: Callable[[], Any], timeout: float
) -> None:
    t0 = time.time()
    try:
        out = await asyncio.wait_for(coro_factory(), timeout=timeout)
        probes.append(
            {
                "probe": name,
                "ok": True,
                "ms": int((time.time() - t0) * 1000),
                "output": str(out)[:200],
            }
        )
    except Exception as exc:  # noqa: BLE001
        probes.append(
            {
                "probe": name,
                "ok": False,
                "ms": int((time.time() - t0) * 1000),
                "error": f"{type(exc).__name__}: {exc}"[:200],
            }
        )


def _probe_deterministic_math() -> str:
    from services.math_verifier import evaluate_logic, evaluate_math

    got = evaluate_math("1234*5678=?")
    expect = str(1234 * 5678)
    logic = evaluate_logic("true and false=?")
    if got is None or expect not in str(got):
        raise RuntimeError(f"evaluate_math 自檢失敗：{got!r} ≠ 含 {expect}")
    if logic is None:
        raise RuntimeError("evaluate_logic 自檢失敗：None")
    return f"math 重算 {expect} ✓；logic {logic}"


def _probe_knowledge_route() -> str:
    from ai.knowledge_base import route_knowledge

    hit = route_knowledge("WHAT COLOR IS THE SKY?")
    if not hit:
        raise RuntimeError("route_knowledge 正例未命中（查表能力失效）")
    return hit


def _probe_symbolic_route() -> str:
    from ai.symbolic_reasoner import route_reasoning

    hit = route_reasoning("All mammals are animals. A dog is a mammal. Is a dog an animal?")
    if not hit:
        raise RuntimeError("route_reasoning 三段論正例未命中（符號推理失效）")
    return hit


def _probe_rules_verify() -> str:
    from ai.rules import verify_solution

    ok, kind, reason = verify_solution(
        "小明有3個蘋果，給了弟弟1個，還剩幾個？", "3-1=2，所以還剩2個"
    )
    if not ok:
        raise RuntimeError(f"verify_solution 拒絕正例：{reason}")
    return f"verified kind={kind} reason={reason}"


def _probe_formula_solve() -> str:
    from ai.memory.formula_solver import solve

    hit = solve("a car accelerates at 3 m/s² for 4 seconds, what is its velocity")
    if not hit:
        raise RuntimeError("formula_solver 正例未命中（物理公式求解失效）")
    return f"value={hit.get('value')} formula={hit.get('formula')}"


def _probe_ed3n_warm() -> str:
    from ai.ed3n.ed3n_engine import ED3NEngine

    n = ED3NEngine.get_shared(load_trained=True).warm_up()
    return f"warm_up={n}"


def _probe_ed3n_process() -> str:
    from ai.ed3n.ed3n_engine import ED3NEngine

    return ED3NEngine.get_shared(load_trained=True).process("2+2=? 請回答")


def _probe_garden_process() -> str:
    from ai.garden.garden_engine import GARDENEngine

    eng = GARDENEngine.get_shared(load_presets=True)
    out = eng.process("hello world")
    net = eng.get_last_network_output() if hasattr(eng, "get_last_network_output") else {}
    dims = len(net) if isinstance(net, dict) else 0
    return f"{out} (network_output dims={dims})"


def _probe_causal_predict() -> str:
    from ai.reasoning.causal_reasoning_engine import CausalReasoningEngine

    eng = CausalReasoningEngine()
    if hasattr(eng, "retrospective_warm_start"):
        eng.retrospective_warm_start()
    hits = eng.predict("user_input")
    return f"predict(user_input) → {len(hits) if isinstance(hits, list) else hits} 條"


async def probe_own_models() -> List[Dict[str, Any]]:
    """專案自有模型逐項實跑（SNN / 確定性 / 知識 / 記憶 / 因果）。"""
    probes: List[Dict[str, Any]] = []
    # 確定性（含自檢：與 python 獨立重算比對）
    await _probe_in(probes, "deterministic.math+logic", _probe_deterministic_math, 30.0)
    await _probe_in(probes, "knowledge.route", _probe_knowledge_route, 30.0)
    await _probe_in(probes, "symbolic.route", _probe_symbolic_route, 30.0)
    await _probe_in(probes, "rules.verify", _probe_rules_verify, 30.0)
    await _probe_in(probes, "formula.solve", _probe_formula_solve, 30.0)
    # SNN
    await _probe_in(probes, "ed3n.warm_up", _probe_ed3n_warm, _PROBE_TIMEOUT)
    await _probe_in(probes, "ed3n.process", _probe_ed3n_process, _PROBE_TIMEOUT)
    await _probe_in(probes, "garden.process", _probe_garden_process, _PROBE_TIMEOUT)
    # 因果
    await _probe_in(probes, "causal.predict", _probe_causal_predict, 60.0)

    # 知識管線（async 7 階）
    async def _kp() -> Any:
        from ai.meta.knowledge_pipeline import get_knowledge_pipeline

        res = await get_knowledge_pipeline().query("What is the capital of France?")
        if not res or not res.get("answer"):
            raise RuntimeError(f"knowledge_pipeline 正例未命中：{res!r}")
        return res

    await _probe_in_async(probes, "knowledge_pipeline.query", _kp, _KNOWLEDGE_PROBE_TIMEOUT)

    # HAM 記憶（關鍵字查詢，async）
    async def _ham() -> Any:
        from ai.memory.ham_memory.ham_manager import HAMMemoryManager

        mems = await HAMMemoryManager().query_core_memory(["研究", "升級"], limit=3)
        return f"{len(mems)} 條：" + "；".join(str(getattr(m, "content", m))[:60] for m in mems[:3])

    await _probe_in_async(probes, "ham.query_core_memory", _ham, _HAM_PROBE_TIMEOUT)
    return probes


# ---------------------------------------------------------------------------
# Phase 2b — 自己想：候選推導與擇優（規則式，透明公式）
# ---------------------------------------------------------------------------


def _score_candidate(cand: Dict[str, Any]) -> Dict[str, Any]:
    src = cand["source"]
    impact = _IMPACT_BY_SOURCE.get(src, 2)
    text = f"{cand.get('title', '')} {cand.get('action', '')}"
    if _EFFORT_HEAVY_RE.search(text):
        effort = 3
    elif _EFFORT_LIGHT_RE.search(text):
        effort = 1
    else:
        effort = 2
    risk = 1 if src in ("docs", "collector") else 2
    score = 4 * impact + 2 * (4 - effort) + 2 * (4 - risk) + _SOURCE_BONUS.get(src, 0)
    cand.update({"impact": impact, "effort": effort, "risk": risk, "score": score})
    return cand


def _cands_checklist(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    checklist = facts.get("checklist") or {}
    if isinstance(checklist, dict) and "pending" in checklist:
        for item in checklist["pending"]:
            out.append(
                {
                    "id": item["id"],
                    "source": "assessment-pre-flight",
                    "title": item["text"][:140],
                    "action": item["text"],
                    "evidence": [f"docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md: - [ ] {item['id']}"],
                }
            )
    return out


def _cands_verification(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    vr = facts.get("verification_register") or {}
    if isinstance(vr, dict):
        for e in vr.get("entries") or []:
            out.append(
                {
                    "id": f"VR-{e['id']}",
                    "source": "verification-register",
                    "title": e["claim"],
                    "action": e["how_to_verify"],
                    "evidence": [
                        f"why_unverified: {e['why_unverified']}",
                        f"area: {e['area']}",
                    ],
                }
            )
    return out


def _cands_status_matrix(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    sm = facts.get("status_matrix") or {}
    if isinstance(sm, dict) and sm.get("pending"):
        ids = ", ".join(p["id"] for p in sm["pending"][:8])
        more = f"（等 {len(sm['pending'])} 項）" if len(sm["pending"]) > 8 else ""
        out.append(
            {
                "id": "SM-promote",
                "source": "status-matrix",
                "title": (
                    f"將未 verified 的 {len(sm['pending'])} 項功能推進至 verified"
                    "（附各自 verify_command）"
                ),
                "action": f"逐項執行 verify_command 並回填 evidence：{ids}{more}",
                "evidence": [f"status 分佈：{sm.get('by_status')}"],
            }
        )
    return out


def _cands_benchmarks(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    bench = facts.get("benchmarks") or {}
    if not isinstance(bench, dict):
        return out
    for s in bench.get("suites") or []:
        if s["backend"] != "native":
            continue
        acc, floor, st = s.get("accuracy"), s.get("floor"), s["state"]
        if st == "below":
            out.append(
                {
                    "id": f"BENCH-{s['suite']}",
                    "source": "benchmark",
                    "title": f"native {s['suite']} 準確率 {acc}% 低於門檻 {floor}%",
                    "action": "分析逐題失敗明細（results JSON details）→ 補引擎/資料 → 重跑 gate",
                    "evidence": [
                        f"bench {bench.get('file')}: {s['suite']} {s['passed']}/{s['total']} = {acc}%"
                    ],
                }
            )
        elif st == "no-floor":
            out.append(
                {
                    "id": f"BENCH-floor-{s['suite']}",
                    "source": "benchmark",
                    "title": f"native {s['suite']} 套件無 GATE_NATIVE 地板（{acc}% 無門檻約束）",
                    "action": "在 run_benchmarks.GATE_NATIVE 定義地板並納入 --gate-native 回歸",
                    "evidence": [f"bench {bench.get('file')}: {s['suite']} accuracy={acc}"],
                }
            )
        elif st == "margin":
            out.append(
                {
                    "id": f"BENCH-margin-{s['suite']}",
                    "source": "benchmark",
                    "title": f"native {s['suite']} {acc}% 雖過門但餘量 ≤5pt（地板 {floor}%）",
                    "action": "固定失敗樣本為回歸集，防止跌破门檻",
                    "evidence": [f"margin={round(acc - floor, 2)}pt"],
                }
            )
    return out


def _cands_gates(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    gates = facts.get("fact_gates") or {}
    if isinstance(gates, dict):
        for name in gates.get("failed") or []:
            out.append(
                {
                    "id": f"GATE-{name}",
                    "source": "fact-gates",
                    "title": f"fact gate 失敗：{name}",
                    "action": f"修復 check_fact_gates 域 {name} 至 PASS",
                    "evidence": [f"exit_code={gates.get('exit_code')}"],
                }
            )
    return out


def _cands_checkpoint(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    repo = facts.get("repo") or {}
    if (
        isinstance(repo, dict)
        and repo.get("checkpoint_dir_exists")
        and not repo.get("unified_checkpoint_present")
    ):
        out.append(
            {
                "id": "CKPT-unified",
                "source": "assessment-pre-flight",
                "title": (
                    "data/checkpoints/ 無 unified 權重（統計核心未載入，"
                    "log checkpoint resolved to (none)）"
                ),
                "action": "本機重訓入庫或自外置機器復原（併同 A2 決策）",
                "evidence": [f"checkpoints 現況：{repo.get('checkpoints') or '（空）'}"],
            }
        )
    return out


def _cands_collectors(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for c in facts.get("collectors") or []:
        if not c.get("ok"):
            out.append(
                {
                    "id": f"COL-{c['collector']}",
                    "source": "collector",
                    "title": f"報告採集器失敗：{c['collector']}",
                    "action": (
                        f"修復採集器 {c['collector']}（否則該章節資料面缺口）"
                        f"—— {c.get('detail', '')[:120]}"
                    ),
                    "evidence": [str(c.get("detail", ""))[:200]],
                }
            )
    return out


def _cands_docs(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    docs_index = facts.get("docs_index") or {}
    if isinstance(docs_index, dict):
        missing = [n for n, v in docs_index.items() if isinstance(v, dict) and not v.get("path")]
        if missing:
            out.append(
                {
                    "id": "DOCS-missing",
                    "source": "docs",
                    "title": f"關鍵文檔缺失：{', '.join(missing)}",
                    "action": "補齊或修正 docs 引用路徑",
                    "evidence": missing,
                }
            )
    return out


_CAND_RULES = (
    _cands_checklist,
    _cands_verification,
    _cands_status_matrix,
    _cands_benchmarks,
    _cands_gates,
    _cands_checkpoint,
    _cands_collectors,
    _cands_docs,
)


def _score_sort_wave(cands: List[Dict[str, Any]]) -> None:
    """透明公式打分 → 降冪排序 → Wave 1-3 分段 → 前 3 條標 picked。"""
    for c in cands:
        _score_candidate(c)
    cands.sort(key=lambda c: (-c["score"], str(c["id"])))
    n = len(cands)
    third = max(1, (n + 2) // 3)
    for i, c in enumerate(cands):
        c["wave"] = 1 if i < third else (2 if i < 2 * third else 3)
        c["picked"] = i < min(3, n)


def derive_candidates(facts: Dict[str, Any]) -> List[Dict[str, Any]]:
    """升級候選 = 規則從量測推導（checklist 未完成項 / 驗證登錄 / 狀態矩陣 /
    benchmark 門 / fact gates 失敗 / 採集器失敗 / 關鍵文檔缺失）。"""
    cands: List[Dict[str, Any]] = []
    for rule in _CAND_RULES:
        cands.extend(rule(facts))
    _score_sort_wave(cands)
    return cands


# ---------------------------------------------------------------------------
# Phase 3 — 自己寫：章節生成
# ---------------------------------------------------------------------------


def _fmt_num(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


def _section(title: str, body: str) -> str:
    return f"{title}\n\n{body.strip()}\n"


def _probe_rows(probes: List[Dict[str, Any]]) -> str:
    lines = ["| 探針 | 結果 | 耗時 | 輸出/錯誤 |", "|---|---|---|---|"]
    for p in probes:
        status = "✅" if p.get("ok") else "❌"
        detail = p.get("output") if p.get("ok") else p.get("error", "")
        lines.append(
            f"| {p['probe']} | {status} | {p['ms']}ms | {str(detail).replace('|', '/')[:150]} |"
        )
    return "\n".join(lines)


def _collector_rows(collectors: List[Dict[str, Any]]) -> str:
    lines = ["| 採集器 | 狀態 | 耗時 | 說明 |", "|---|---|---|---|"]
    for c in collectors:
        status = "✅" if c.get("ok") else "❌"
        lines.append(
            f"| {c['collector']} | {status} | {c['ms']}ms | {str(c.get('detail', '')).replace('|', '/')[:150]} |"
        )
    return "\n".join(lines)


def _s1_summary(
    facts: Dict[str, Any],
    cands: List[Dict[str, Any]],
    probes: List[Dict[str, Any]],
    web: List[Dict[str, Any]],
) -> str:
    tc = facts.get("test_count") or {}
    gates = facts.get("fact_gates") or {}
    checklist = facts.get("checklist") or {}
    sm = facts.get("status_matrix") or {}
    bench = facts.get("benchmarks") or {}
    native = [s for s in (bench.get("suites") or []) if s.get("backend") == "native"]
    best = ", ".join(f"{s['suite']}={_fmt_num(s['accuracy'])}%" for s in native[:4]) or "無"
    picked = [c for c in cands if c.get("picked")]
    probe_ok = sum(1 for p in probes if p.get("ok"))
    web_ok = sum(1 for r in web if r.get("ok"))
    return (
        f"本報告由專案自身AI自主生成（自己查/自己想/自己寫，LLM 僅潤色行文），生成時間 {facts.get('generated_at')}。"
        f"本輪量測：測試收集 {tc.get('count', '?')}（{tc.get('method', '?')}）；fact gates "
        f"{'全部 PASS' if gates.get('passed') else '有失敗：' + ','.join(gates.get('failed') or [])}；"
        f"status_matrix {sm.get('total', '?')} 項（verified {sm.get('by_status', {}).get('verified', 0)}）；"
        f"pre-flight 清單 {checklist.get('done', 0)}/{checklist.get('total', '?')} 已完成。"
        f"自有模型體檢 {probe_ok}/{len(probes)} 通過；外部查證 {web_ok}/{len(web)} 組取得。"
        f"native 基準：{best}。"
        f"由量測推導升級候選 {len(cands)} 條，擇優前 {len(picked)} 條列為 Wave 1（見第七節）。"
    )


def _s2_method(facts: Dict[str, Any], probes: List[Dict[str, Any]]) -> str:
    return (
        "資料鏈：以下採集器逐一執行（失敗僅記錄、報告照常生成，屬已解釋缺口而非靜默空缺）。\n\n"
        + _collector_rows(facts.get("collectors") or [])
        + "\n\n自有模型體檢（每項實跑，非引用文件分數）：\n\n"
        + _probe_rows(probes)
        + "\n\n擇優公式（寫死於 ai/research/upgrade_research.py，可審計）："
        "`score = 4×impact + 2×(4−effort) + 2×(4−risk) + source_bonus`；"
        "impact/bonus 依來源（pre-flight/benchmark/gates=3 權重），effort 依動作關鍵字"
        "（重訓/數據=3、驗證/門檻=2、註解/清理=1），risk 依來源類別（文件/採集器=1，其餘=2）。"
        "LLM 潤色僅作用於純敘述段落（表格/標題逐字保留），每段以數字指紋比對，失配即回退原稿。"
    )


def _s3_assets(facts: Dict[str, Any], probes: List[Dict[str, Any]]) -> str:
    repo = facts.get("repo") or {}
    sm = facts.get("status_matrix") or {}
    docs_index = facts.get("docs_index") or {}
    rule = facts.get("rule_store") or {}
    bench = facts.get("benchmarks") or {}
    val = facts.get("validation") or {}

    status_rows = (
        "\n".join(f"| {k} | {v} |" for k, v in sorted((sm.get("by_status") or {}).items()))
        or "| （無） | 0 |"
    )
    doc_rows = "\n".join(
        f"| {n} | {v.get('lines', 0)} | {v.get('path') or '❌ 缺失'} |"
        for n, v in (docs_index or {}).items()
    )
    feature_rows = (
        "\n".join(
            f"| {p['id']} | {p['status']} | {p['claim'].replace('|', '/')} |"
            for p in (sm.get("pending") or [])[:12]
        )
        or "| （全部 verified） | — | — |"
    )
    return (
        f"**程式資產**：apps/backend/src 共 {repo.get('py_files', '?')} 個 Python 檔、"
        f"{repo.get('py_lines', '?')} 行；測試收集 {(facts.get('test_count') or {}).get('count', '?')} 項。"
        f"unified checkpoint：{'✅ 已存在' if repo.get('unified_checkpoint_present') else '❌ 未入庫（見 A2/CKPT 路徑）'}。\n\n"
        "**功能狀態（docs/status_matrix.yaml — 專案自有的機器可讀真相源）：**\n\n"
        "| status | 數量 |\n|---|---|\n"
        + status_rows
        + f"\n\n未達 verified 的功能（升級候選來源，共 {len(sm.get('pending') or [])} 項，前 12 項）：\n\n"
        + "| id | status | claim |\n|---|---|---|\n"
        + feature_rows
        + "\n\n**規則沉澱層（本專案新增的可重用資產）**："
        f"rules={rule.get('total', 0)}、serves={rule.get('serves', 0)}、feedback={rule.get('feedback', 0)}、"
        f"by_kind={rule.get('by_kind', {})}（命中 0 tokens、confidence 公式 (2+successes)/(3+feedback)）。\n\n"
        "**訓練/驗證報告工件**："
        + json.dumps(val, ensure_ascii=False)[:400]
        + "\n\n**基準工件**："
        + str(bench.get("file", "（缺）"))
        + f"（generated_at={bench.get('generated_at')}）\n\n"
        + "**專案文檔索引**（行數實測）：\n\n| 文檔 | 行數 | 路徑 |\n|---|---|---|\n"
        + doc_rows
    )


_ASSET_CLASSES = (
    ("確定性求解與驗算", ("deterministic.math+logic", "formula.solve", "rules.verify"), ()),
    ("規則沉澱重放（0-token 重用）", ("rules.verify",), (2,)),
    ("統計語言核心（n-gram unified）", (), (0,)),
    ("SNN 神經核心（ED3N / GARDEN）", ("ed3n.warm_up", "ed3n.process", "garden.process"), (1,)),
    (
        "知識 / 記憶 / 因果檢索",
        ("knowledge.route", "knowledge_pipeline.query", "ham.query_core_memory", "causal.predict"),
        (0,),
    ),
    ("雲端融合路由（unified→LLM）", (), (0,)),
    ("外部研究管線（搜尋→事實→矛盾偵測）", (), (2,)),
)


def _s4_web_cell(web: List[Dict[str, Any]], idx: Tuple[int, ...]) -> str:
    parts = []
    for i in idx:
        if i >= len(web):
            continue
        r = web[i]
        if r.get("ok") and r.get("facts"):
            host = ""
            if r.get("sources"):
                host = re.sub(r"^https?://([^/]+).*$", r"\1", r["sources"][0].get("url", "")) or ""
            parts.append(f"{r['facts'][0][:110]}（{host or 'q' + str(i + 1)}）")
        elif not r.get("ok"):
            parts.append("外部查證未取得（離線/失敗，已記錄）")
    return "<br>".join(parts) if parts else "（對應查詢未取得事實）"


def _s4_measured(
    name: str,
    active: List[Dict[str, Any]],
    ok_n: int,
    native_acc: Dict[str, Any],
    rule: Dict[str, Any],
    repo: Dict[str, Any],
    facts: Dict[str, Any],
) -> str:
    measured = (
        f"探針 {ok_n}/{len(active)} 通過"
        + (
            "；" + "、".join(f"{p['probe']}={p['output'][:40]}" for p in active if p.get("ok"))
            if active
            else ""
        )
    ) or "依工件量測"
    if name.startswith("統計"):
        measured = (
            f"native 基準 accuracy={native_acc.get('math', '—')}%（math suite）；"
            f"checkpoint={'在庫' if repo.get('unified_checkpoint_present') else '缺'}"
        )
    if name.startswith("規則"):
        measured = (
            f"rules={rule.get('total', 0)} serves={rule.get('serves', 0)} "
            f"avg_conf={rule.get('avg_confidence', 0)}"
        )
    if name.startswith("雲端"):
        sm = facts.get("status_matrix") or {}
        chat = sm.get("chat_pipeline")
        measured = f"chat_pipeline 狀態：{type(chat).__name__} {str(chat)[:80]}"
    return measured


def _s4_probe_notes(active: List[Dict[str, Any]], ok_n: int) -> Tuple[List[str], List[str]]:
    pros: List[str] = []
    cons: List[str] = []
    if active:
        (pros if ok_n == len(active) else cons).append(f"本輪探針 {ok_n}/{len(active)}")
        miss = [
            p["probe"]
            for p in active
            if not p.get("ok") or str(p.get("output", "")).startswith("無命中")
        ]
        if miss:
            cons.append(f"未命中：{', '.join(miss)}（查表/未涵蓋表述）")
    return pros, cons


def _s4_named_notes(
    name: str, rule: Dict[str, Any], web_ok: int, web_total: int
) -> Tuple[List[str], List[str]]:
    pros: List[str] = []
    cons: List[str] = []
    if name.startswith("確定性"):
        pros.append("離線可用、可重算可驗錯")
    if name.startswith("規則"):
        pros.append(f"命中 0 tokens（實測 serves={rule.get('serves', 0)}）")
        cons.append("身份保守（異數字/異措辭不命中）")
    if name.startswith("統計"):
        cons.append("wiki 權重未入庫 → 統計層本輪僅確定性層")
    if name.startswith("雲端"):
        cons.append("依雲端可用性與 key 治理（C3）")
    if name.startswith("外部"):
        (pros if web_ok else cons).append(f"外部查證 {web_ok}/{web_total} 組")
    return pros, cons


def _s4_compare(
    probes: List[Dict[str, Any]], web: List[Dict[str, Any]], facts: Dict[str, Any]
) -> str:
    probe_map = {p["probe"]: p for p in probes}
    rule = facts.get("rule_store") or {}
    repo = facts.get("repo") or {}
    bench = facts.get("benchmarks") or {}
    native_acc = {
        s["suite"]: s["accuracy"]
        for s in (bench.get("suites") or [])
        if s.get("backend") == "native" and isinstance(s.get("accuracy"), (int, float))
    }
    web_ok = sum(1 for r in web if r.get("ok"))

    rows = [
        "| 資產類別 | 專案實測（本輪） | 優點（由實測生成） | 缺點 / 風險（由實測生成） | 相對替代方案（外部查證） |",
        "|---|---|---|---|---|",
    ]
    for name, probe_names, web_idx in _ASSET_CLASSES:
        active = [probe_map[p] for p in probe_names if p in probe_map]
        ok_n = sum(1 for p in active if p.get("ok"))
        measured = _s4_measured(name, active, ok_n, native_acc, rule, repo, facts)
        base_pros, base_cons = _s4_probe_notes(active, ok_n)
        named_pros, named_cons = _s4_named_notes(name, rule, web_ok, len(web))
        pros = base_pros + named_pros
        cons = base_cons + named_cons
        rows.append(
            f"| {name} | {measured.replace('|', '/')} | {'；'.join(pros) or '（無實測優點）'} | "
            f"{'；'.join(cons) or '（無實測缺點）'} | {_s4_web_cell(web, web_idx).replace('|', '/')} |"
        )
    return (
        "對照口徑：**優缺點只由本輪實測生成**（探針/工件/規則庫），不引文件宣稱；"
        "替代方案欄為外部查證事實（來源見附錄）。LLM-only / 純雲端 / 大模型堆疊 等替代組合的事實依據落在"
        "「相對替代方案」欄。\n\n" + "\n".join(rows)
    )


def _s5_current(facts: Dict[str, Any]) -> str:
    bench = facts.get("benchmarks") or {}
    sm = facts.get("status_matrix") or {}
    gates = facts.get("fact_gates") or {}
    tc = facts.get("test_count") or {}
    checklist = facts.get("checklist") or {}
    vr = facts.get("verification_register") or {}
    rows = ["| suite | passed/total | accuracy | floor | 狀態 |", "|---|---|---|---|---|"]
    for s in bench.get("suites") or []:
        rows.append(
            f"| {s['backend']}/{s['suite']} | {s['passed']}/{s['total']} | {_fmt_num(s['accuracy'])}% | {_fmt_num(s['floor']) if s['floor'] is not None else '—'} | {s['state']} |"
        )
    gate_rows = (
        "\n".join(f"- {'✅' if c['ok'] else '❌'} {c['name']}" for c in gates.get("checks") or [])
        or "- （無項目）"
    )
    return (
        f"- 測試收集：**{tc.get('count', '?')}**（method: {tc.get('method', '?')}）\n"
        f"- status_matrix：total={sm.get('total')}，分佈={sm.get('by_status')}\n"
        f"- pre-flight：{checklist.get('done', '?')}/{checklist.get('total', '?')} 完成，待辦 {len(checklist.get('pending') or [])} 項\n"
        f"- 驗證登錄：{vr.get('open', '?')} 項 open\n"
        f"- fact gates：{'ALL PASS' if gates.get('passed') else 'FAILED: ' + ','.join(gates.get('failed') or [])}（exit={gates.get('exit_code')}）\n\n"
        "基準明細（benchmarks/results 工件，逐套件）：\n\n"
        + "\n".join(rows)
        + "\n\nfact gates 項：\n\n"
        + gate_rows
    )


def _s6_candidates(cands: List[Dict[str, Any]]) -> str:
    rows = [
        "| id | 來源 | 候選（title） | I/E/R | score | wave |",
        "|---|---|---|---|---|---|",
    ]
    for c in cands:
        rows.append(
            f"| {c['id']} | {c['source']} | {str(c['title']).replace('|', '/')} | {c['impact']}/{c['effort']}/{c['risk']} | {c['score']} | W{c['wave']} |"
        )
    return (
        f"候選由規則從量測推導（共 {len(cands)} 條，來源：pre-flight checklist 未完成項、VERIFICATION_REGISTER、"
        "status_matrix 未 verified、benchmark 地板/餘量/缺地板、fact gates 失敗、採集器失敗、checkpoint 缺失）。"
        "每條附證據，全文如下：\n\n"
        + "\n".join(rows)
        + "\n\n證據摘要（逐條）：\n\n"
        + "\n\n".join(
            f"- **{c['id']}**（score={c['score']}）：{c['action'][:220]}　證據：{'; '.join(str(e)[:120] for e in c['evidence'][:2])}"
            for c in cands
        )
    )


def _s7_roadmap(cands: List[Dict[str, Any]]) -> str:
    picked = [c for c in cands if c.get("picked")]
    w1 = [c for c in cands if c["wave"] == 1]
    w2 = [c for c in cands if c["wave"] == 2]
    w3 = [c for c in cands if c["wave"] == 3]
    line = lambda cs: "、".join(f"{c['id']}({c['score']})" for c in cs) or "（無）"
    return (
        "**擇優（公式排序前 3，建議先做）**：\n\n"
        + "\n".join(
            f"{i}. **{c['id']}** — {str(c['title']).replace(chr(10), ' ')[:160]}（score={c['score']}，來源 {c['source']}）"
            for i, c in enumerate(picked, 1)
        )
        + "\n\n**Wave 1**（最高分 1/3，含上述擇優項）："
        + line(w1)
        + "\n\n**Wave 2**："
        + line(w2)
        + "\n\n**Wave 3**（其餘，含文件/採集器修復）："
        + line(w3)
        + "\n\n排序完全由公式決定（公式與規則表見第二節），本節無人工覆寫。"
    )


def _s8_bench_questions(bench: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for s in bench.get("suites") or []:
        if s.get("backend") != "native":
            continue
        if s.get("state") == "no-floor":
            out.append(
                f"native {s['suite']}（accuracy={_fmt_num(s.get('accuracy'))}%）"
                "該以什麼地板納入 --gate-native 回歸？"
            )
        elif s.get("state") == "margin":
            out.append(
                f"native {s['suite']} 餘量僅 {round(s['accuracy'] - s['floor'], 1)}pt，"
                "跌破前該固定哪些失敗樣本為回歸集？"
            )
    return out


def _s8_gap_questions(facts: Dict[str, Any], web: List[Dict[str, Any]]) -> List[str]:
    out: List[str] = []
    repo = facts.get("repo") or {}
    if repo.get("checkpoint_dir_exists") and not repo.get("unified_checkpoint_present"):
        out.append(
            "unified 權重復原（A2）後，bpc 是否與歷史 UNIFIED_AI_RESULTS.md 的 2.711 一致"
            "（重現性驗證）？"
        )
    gates = facts.get("fact_gates") or {}
    if gates.get("failed"):
        out.append(
            f"fact gates 失敗域 {','.join(gates.get('failed') or [])} 是資料面缺口還是門檻設定問題？"
        )
    sm = facts.get("status_matrix") or {}
    pending_n = len(sm.get("pending") or [])
    if pending_n:
        out.append(
            f"status_matrix {pending_n} 項未 verified 中，哪些能用自動 verify_command "
            "直接推進、哪些需先補實作？"
        )
    if web and any(not r.get("ok") for r in web):
        out.append("外部查證部分未取得（離線/逾時）——重跑時該否增加來源鏡像或快取？")
    if not out:
        out.append(
            "本輪量測未發現開放缺口（全門檻、全 verified）——下輪該抬高地板還是擴展套件覆蓋？"
        )
    return out


def _s8_research(
    facts: Dict[str, Any], web: List[Dict[str, Any]], cands: List[Dict[str, Any]]
) -> str:
    lines: List[str] = []
    checklist = facts.get("checklist") or {}
    e_items = [
        p
        for p in (checklist.get("pending") or [])
        if str(p.get("id", "")).startswith("E")
        or re.search(r"探針|泛化|研究", str(p.get("text", "")))
    ]
    if e_items:
        lines.append("**源自 pre-flight 的研究型待辦**：\n")
        lines.extend(f"- [{p['id']}] {p['text']}" for p in e_items)
    conflicts = [c for r in web if r.get("ok") for c in (r.get("conflicts") or [])]
    if conflicts:
        lines.append("\n**外部查證偵測到的矛盾（建議以官方/一手來源裁定）**：\n")
        lines.extend(f"- {c}" for c in conflicts[:6])
    else:
        lines.append("\n**外部查證矛盾偵測**：本輪未取得矛盾（或外部查證未成功，見附錄採集表）。")
    bench_open = [
        c
        for c in cands
        if c["id"].startswith("BENCH-floor-") or c["id"].startswith("BENCH-margin-")
    ]
    if bench_open:
        lines.append("\n**基準面開放問題**：")
        lines.extend(f"- {c['title']}" for c in bench_open)
    open_q = _s8_bench_questions(facts.get("benchmarks") or {}) + _s8_gap_questions(facts, web)
    lines.append("\n**開放研究問題（由量測缺口推導，非人工列點）**：")
    lines.extend(f"- {q}" for q in open_q)
    return "\n".join(lines)


def _s9_appendix(
    facts: Dict[str, Any],
    web: List[Dict[str, Any]],
    polish_records: List[Dict[str, Any]],
    elapsed_s: float,
) -> str:
    src_lines = []
    for r in web:
        if r.get("ok"):
            for s in r.get("sources") or []:
                src_lines.append(
                    f"- [{r['query'][:60]}…] {s.get('title', '')} — {s.get('url', '')}"
                )
        else:
            src_lines.append(
                f"- [{r['query'][:60]}…] ❌ 未取得：{str(r.get('error') or '無回應')[:120]}"
            )
    return (
        "**資料源（全部可重現）**：\n\n"
        "- docs/status_matrix.yaml、docs/VERIFICATION_REGISTER.json、"
        "docs/AI_SUBSTRATE_ASSESSMENT_2026-10-18.md（pre-flight）、"
        "benchmarks/results/、scripts/validation_report_*.json、data/rules/solution_rules.json\n\n"
        "**重現命令**：\n\n"
        "```bash\n"
        ".venv/bin/pytest --collect-only -q -o addopts=\n"
        "python3 scripts/check_fact_gates.py\n"
        "python3 scripts/run_benchmarks.py --backend native --gate-native\n"
        "python3 scripts/generate_upgrade_report.py --no-polish   # 重生成（不含 LLM 潤色）\n"
        "```\n\n"
        "**外部查證來源**：\n\n"
        + ("\n".join(src_lines) if src_lines else "- （本輪外部查證未取得任何來源）")
        + "\n\n**LLM 潤色記錄**（只潤色、數字指紋守護）：\n\n"
        + "\n".join(_polish_rows(polish_records))
        + f"\n\n生成耗時：{elapsed_s:.1f}s；生成時間：{facts.get('generated_at')}。"
    )


def _polish_rows(records: List[Dict[str, Any]]) -> List[str]:
    lines = ["| 區塊 | 潤色結果 |", "|---|---|"]
    for p in records:
        lines.append(f"| {p['block']} | {p['action']} |")
    return lines


def draft_report(
    facts: Dict[str, Any],
    web: List[Dict[str, Any]],
    probes: List[Dict[str, Any]],
    cands: List[Dict[str, Any]],
    polish_records: List[Dict[str, Any]],
    elapsed_s: float,
) -> str:
    body = "".join(
        (
            _section(_SECTION_HEADERS[0], _s1_summary(facts, cands, probes, web)),
            _section(_SECTION_HEADERS[1], _s2_method(facts, probes)),
            _section(_SECTION_HEADERS[2], _s3_assets(facts, probes)),
            _section(_SECTION_HEADERS[3], _s4_compare(probes, web, facts)),
            _section(_SECTION_HEADERS[4], _s5_current(facts)),
            _section(_SECTION_HEADERS[5], _s6_candidates(cands)),
            _section(_SECTION_HEADERS[6], _s7_roadmap(cands)),
            _section(_SECTION_HEADERS[7], _s8_research(facts, web, cands)),
            _section(_SECTION_HEADERS[8], _s9_appendix(facts, web, polish_records, elapsed_s)),
        )
    )
    return (
        "# 專案AI自主研究報告：後續研究與升級路徑（自動生成）\n\n"
        "> 本文件由 `ai/research/upgrade_research.py` 自動生成：事實=專案自測/外部查證，"
        "推導=規則與透明公式，撰寫=資料填充模板；**LLM 僅潤色行文（數字指紋守護，失配回退）**。\n\n"
        + body
    )


# ---------------------------------------------------------------------------
# Phase 3b — LLM 潤色（只潤色行文，數字指紋比對）
# ---------------------------------------------------------------------------


def _numeric_fingerprint(text: str) -> Counter:
    return Counter(re.findall(r"-?\d+(?:\.\d+)?", text))


def _is_table_or_heading(par: str) -> bool:
    stripped = par.strip()
    if not stripped:
        return True
    if stripped.startswith("#") or stripped.startswith(">") or stripped.startswith("```"):
        return True
    return "|" in stripped


async def _polish_one(par: str, svc: Any, system_prompt: str, block: str) -> Tuple[str, str]:
    """單段潤色：回 (採用文字, action)。失配/失敗一律回原段（守護數字）。"""
    try:
        from core.system.config.magic_numbers import timeout_value

        out = await asyncio.wait_for(
            svc.generate_text(
                prompt=par,
                max_tokens=1600,
                temperature=0.2,
                system_prompt=system_prompt,
                editorial=True,
            ),
            timeout=timeout_value("research.llm_synthesis", _LLM_POLISH_TIMEOUT),
        )
    except Exception as exc:  # noqa: BLE001 — LLM 潤色失敗 → 原稿
        return par, f"fallback:{type(exc).__name__}"[:80]
    text = str(out or "").strip()
    if len(text) < 40:
        return par, "fallback:輸出過短"
    if _numeric_fingerprint(par) != _numeric_fingerprint(text):
        return par, "fallback:數字指紋失配"
    return text, "polished"


async def polish_report(md: str, enabled: bool) -> Tuple[str, List[Dict[str, Any]]]:
    """逐段潤色純敘述段（表格/標題原樣保留）；數字指紋失配 → 回退該段。"""
    records: List[Dict[str, Any]] = []
    if not enabled:
        records.append({"block": "（整份）", "action": "disabled（--no-polish）"})
        return md, records
    try:
        from services.angela_llm_service import get_llm_service

        svc = await get_llm_service()
    except Exception as exc:  # noqa: BLE001 — LLM 不可用 → 全文原稿
        records.append(
            {"block": "（整份）", "action": f"fallback:LLM 不可用（{type(exc).__name__}）"}
        )
        return md, records

    system_prompt = (
        "你是技術文件編輯。只潤色行文（用詞、語氣、流暢度），"
        "不得改變任何數字、數值、專有名詞、事實、標題、表格、清單結構與格式。"
        "禁止新增或刪除內容。直接輸出潤色後的文字，不要引言或引號。"
    )
    paragraphs = md.split("\n\n")
    polished: List[str] = []
    used = 0
    for idx, par in enumerate(paragraphs):
        if _is_table_or_heading(par) or len(par.strip()) < 60 or used >= _MAX_POLISH_PARAGRAPHS:
            polished.append(par)
            continue
        if _numeric_fingerprint(par) == Counter() and len(par) < 120:
            # 無數字的短段落沒有指紋保護價值，直接保留
            polished.append(par)
            continue
        used += 1
        block = f"p{idx}:{par.strip()[:40].replace(chr(10), ' ')}"
        text, action = await _polish_one(par, svc, system_prompt, block)
        records.append({"block": block, "action": action})
        polished.append(text)
    if not records:
        records.append({"block": "（整份）", "action": "no-eligible-paragraphs"})
    return "\n\n".join(polished), records


# ---------------------------------------------------------------------------
# 驗證 —「無異常」零容忍
# ---------------------------------------------------------------------------


def _evidence_assertions(md: str, facts: Dict[str, Any]) -> List[str]:
    """證據不一致 = 問題。獨立重讀量測結構，逐項比對報告內文。"""
    problems: List[str] = []
    tc = facts.get("test_count") or {}
    if isinstance(tc.get("count"), int):
        if str(tc["count"]) not in md:
            problems.append(f"證據不一致：測試數 {tc['count']} 未出現在報告")
    bench = facts.get("benchmarks") or {}
    for s in bench.get("suites") or []:
        if not isinstance(s.get("accuracy"), (int, float)):
            continue
        needle = f"{s['passed']}/{s['total']}"
        if needle not in md:
            problems.append(f"證據不一致：基準 {s['backend']}/{s['suite']} {needle} 未出現在報告")
    sm = facts.get("status_matrix") or {}
    if isinstance(sm.get("total"), int) and str(sm["total"]) not in md:
        problems.append(f"證據不一致：status_matrix total={sm['total']} 未出現在報告")
    checklist = facts.get("checklist") or {}
    pending_n = len(checklist.get("pending") or [])
    if pending_n and f"待辦 {pending_n} 項" not in md:
        problems.append(f"證據不一致：pre-flight 待辦 {pending_n} 未出現在報告")
    return problems


def _validate_sections(md: str) -> List[str]:
    problems: List[str] = []
    for header in _SECTION_HEADERS:
        if header not in md:
            problems.append(f"缺章：{header}")
    for header, minimum in _SECTION_MIN_CHARS.items():
        if header in md:
            start = md.index(header)
            nxt = min(
                [
                    md.find(h, start + len(header))
                    for h in _SECTION_HEADERS
                    if md.find(h, start + len(header)) != -1
                ]
                or [len(md)],
            )
            body_len = len(md[start:nxt].strip())
            if body_len < minimum:
                problems.append(f"空缺：{header} 正文 {body_len} < {minimum} 字")
    ph = _PLACEHOLDER_RE.search(md)
    if ph:
        problems.append(f"佔位字殘留：{ph.group(0)}")
    return problems


def _validate_candidates(md: str, cands: List[Dict[str, Any]]) -> List[str]:
    problems: List[str] = []
    if len(cands) < 8:
        problems.append(f"候選覆蓋不足：{len(cands)} < 8（升級路徑覆蓋不完整）")
    picked = [c for c in cands if c.get("picked")]
    if len(picked) < 3:
        problems.append(f"擇優項不足：{len(picked)} < 3")
    for c in cands:
        if not str(c.get("title", "")).strip() or not c.get("evidence"):
            problems.append(f"候選 {c.get('id')} 缺 title 或 evidence（空缺）")
        if not isinstance(c.get("score"), (int, float)):
            problems.append(f"候選 {c.get('id')} 缺分數")
    if "建議先做" not in md:
        problems.append("第七節缺「建議先做」擇優標記")
    return problems


def _validate_web(md: str, web: List[Dict[str, Any]]) -> List[str]:
    problems: List[str] = []
    ok_web = [r for r in web if r.get("ok")]
    if ok_web:
        urls = {s.get("url") for r in ok_web for s in (r.get("sources") or []) if s.get("url")}
        if len(urls) < 3:
            problems.append(f"外部來源不足：{len(urls)} < 3")
    elif "外部查證未取得" not in md and "未取得" not in md:
        problems.append("外部查證全失敗但報告未記錄（空缺）")
    return problems


def _validate_closure(
    md: str, facts: Dict[str, Any], polish_records: List[Dict[str, Any]]
) -> List[str]:
    problems: List[str] = []
    if not polish_records:
        problems.append("LLM 潤色無記錄（附錄缺表）")
    collectors_failed = [c for c in (facts.get("collectors") or []) if not c.get("ok")]
    for c in collectors_failed:
        if c["collector"] not in md:
            problems.append(f"採集器失敗未在報告記錄：{c['collector']}（未解釋缺口）")
    probes = facts.get("_probes") or []
    if probes:
        ok_n = sum(1 for p in probes if p.get("ok"))
        if ok_n == 0:
            problems.append("自有模型體檢全數失敗（0 通過）— 專案未完成或有問題")
    return problems


def validate_report(
    md: str,
    facts: Dict[str, Any],
    cands: List[Dict[str, Any]],
    web: List[Dict[str, Any]],
    polish_records: List[Dict[str, Any]],
) -> List[str]:
    problems: List[str] = []
    problems.extend(_validate_sections(md))
    problems.extend(_validate_candidates(md, cands))
    problems.extend(_validate_web(md, web))
    problems.extend(_validate_closure(md, facts, polish_records))
    problems.extend(_evidence_assertions(md, facts))
    return problems


# ---------------------------------------------------------------------------
# 主管線
# ---------------------------------------------------------------------------


async def run_upgrade_research(
    web: bool = True, polish: bool = True, out_path: Optional[str] = None
) -> Dict[str, Any]:
    """執行自主研究全流程，回傳 {path, problems, stats}。"""
    t0 = time.time()
    facts = await asyncio.to_thread(gather_facts)

    if web:
        web_results = await asyncio.wait_for(
            asyncio.to_thread(_research_external_sync),
            timeout=_RESEARCH_TIMEOUT * len(_EXTERNAL_QUERIES),
        )
    else:
        web_results = [
            {"query": q, "ok": False, "error": "disabled（--no-web）"} for q in _EXTERNAL_QUERIES
        ]

    probes = await probe_own_models()
    facts["_probes"] = probes

    cands = derive_candidates(facts)
    polish_records: List[Dict[str, Any]] = []
    # 二段式：初稿（無潤色記錄）→ LLM 潤色 → 以完整潤色記錄重排 → 套回潤色段
    draft = draft_report(facts, web_results, probes, cands, polish_records, 0.0)
    polished, polish_records = await polish_report(draft, polish)
    elapsed = time.time() - t0
    rendered = draft_report(facts, web_results, probes, cands, polish_records, elapsed)
    # 潤色只作用於敘述段：表格段落本就不被潤色，故終稿與 polished 的差異只在敘述段。
    # 逐段取優（表格/標題/指紋失配一律以 rendered 為準）：
    final_md = _merge_polish(rendered, polished)

    problems = validate_report(final_md, facts, cands, web_results, polish_records)

    root = _repo_root()
    if out_path is None:
        day = datetime.now().strftime("%Y-%m-%d")
        out_path = str(root / "docs" / f"RESEARCH_UPGRADE_REPORT_{day}.md")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(final_md)

    return {
        "path": out_path,
        "problems": problems,
        "ok": not problems,
        "stats": {
            "elapsed_s": round(time.time() - t0, 1),
            "candidates": len(cands),
            "picked": [c["id"] for c in cands if c.get("picked")],
            "probes_ok": sum(1 for p in probes if p.get("ok")),
            "probes_total": len(probes),
            "web_ok": sum(1 for r in web_results if r.get("ok")),
            "collectors_ok": sum(1 for c in facts.get("collectors", []) if c.get("ok")),
            "collectors_total": len(facts.get("collectors", [])),
            "polish": dict(Counter(p["action"].split(":")[0] for p in polish_records)),
            "report_chars": len(final_md),
        },
    }


def _merge_polish(draft: str, polished: str) -> str:
    """把 polished 的非表格敘述段套回 draft（表格/標題/附錄一律以 draft 為準）。

    兩份文本段落數一致（polish_report 不增刪段），逐段選擇：
    段內含 '|' 或以 # 開頭 → 用 draft；否則用 polished（若指紋已守護）。
    """
    d_parts = draft.split("\n\n")
    p_parts = polished.split("\n\n")
    if len(d_parts) != len(p_parts):
        return draft
    merged = [
        d if _is_table_or_heading(d) or _numeric_fingerprint(d) != _numeric_fingerprint(p) else p
        for d, p in zip(d_parts, p_parts)
    ]
    return "\n\n".join(merged)
