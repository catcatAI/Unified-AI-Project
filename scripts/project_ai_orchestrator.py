#!/usr/bin/env python3
"""
Project AI Orchestrator
一鍵協調資料檢查/生成、訓練決策、模型檢查，以及文檔鏈接驗證與自動化流程入口。

安全默認為 dry-run（僅分析與規劃，不執行重任務）。

用法示例：
  python scripts/project_ai_orchestrator.py --dry-run --verbose
  python scripts/project_ai_orchestrator.py --generate-data --check-docs --verbose
  python scripts/project_ai_orchestrator.py --decide-train --run-training --check-docs

步驟：
1) 檢查與驗證資料集（是否存在、是否完整、是否過期）。
2) 視需要生成/修復資料（概念模型、數學模型等）。
3) 檢查模型與訓練系統（是否有現成模型、是否需要繼續/重新訓練）。
4) 視需要執行訓練（支持 resume）。
5) 文檔鏈接驗證與報告（依賴 scripts/validate_doc_links.py 的重定位映射）。

注意：本腳本不直接修改 Markdown；如需批量改鏈接，可另行添加對應腳本或在 validate_doc_links.py 中擴充映射。
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple
import uuid
import hashlib
import shutil
import signal
import time

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
TRAINING_DIR = PROJECT_ROOT / "training"
DOCS_DIR = PROJECT_ROOT / "docs"
APPS_BACKEND_DIR = PROJECT_ROOT / "apps" / "backend"
# 新增狀態與決策資料夾
STATE_DIR = PROJECT_ROOT / "automation_state"
DECISIONS_DIR = PROJECT_ROOT / "automation_reports" / "decisions"

# 常用目標
CONCEPT_DATA_DIR = DATA_DIR / "concept_models_training_data"
CONCEPT_DATA_CONFIG = CONCEPT_DATA_DIR / "data_config.json"
MATH_RAW_DIR = APPS_BACKEND_DIR / "src" / "core" / "tools" / "math_model"
MATH_DATASET_JSON = PROJECT_ROOT / "data" / "raw_datasets" / "arithmetic_train_dataset.json"

VALIDATE_LINKS_SCRIPT = PROJECT_ROOT / "scripts" / "validate_doc_links.py"
PREPARE_CONCEPT_DATA_SCRIPT = PROJECT_ROOT / "tools" / "prepare_concept_models_training_data.py"
MATH_DATA_GENERATOR = MATH_RAW_DIR / "data_generator.py"
TRAIN_MODEL_SCRIPT = TRAINING_DIR / "train_model.py"

REPORTS_DIR = PROJECT_ROOT / "automation_reports"
REPORTS_DIR.mkdir(exist_ok=True)
# 補充：建立狀態與決策目錄
STATE_DIR.mkdir(exist_ok=True)
DECISIONS_DIR.mkdir(parents=True, exist_ok=True)


def run_cmd(cmd, cwd=None, verbose=False, dry_run=False) -> int:
    if verbose:
        print(f"$ {' '.join(cmd)}" + (f"  (cwd={cwd})" if cwd else ""))
    if dry_run:
        return 0
    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None)
    return proc.returncode


def file_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except Exception:
        return 0.0


def _latest_mtime_in_dir(path: Path) -> float:
    latest = 0.0
    if not path.exists():
        return latest
    for p in path.rglob("*"):
        try:
            if p.is_file():
                mt = p.stat().st_mtime
                if mt > latest:
                    latest = mt
        except Exception:
            pass
    return latest


def check_datasets(verbose=False) -> Dict[str, Any]:
    """檢查資料集狀態。"""
    status: Dict[str, Any] = {
        "concept_models": {
            "dir_exists": CONCEPT_DATA_DIR.exists(),
            "config_exists": CONCEPT_DATA_CONFIG.exists(),
            "config_mtime": file_mtime(CONCEPT_DATA_CONFIG),
        },
        "math_model": {
            "dataset_exists": MATH_DATASET_JSON.exists(),
            "dataset_mtime": file_mtime(MATH_DATASET_JSON),
        },
    }
    if verbose:
        print("[DATA] 概念模型資料目錄:", status["concept_models"]) 
        print("[DATA] 數學模型資料:", status["math_model"]) 
    return status


def decide_data_generation(data_status: Dict[str, Any], verbose=False) -> Dict[str, bool]:
    """根據現狀判斷是否需要資料生成/修復。"""
    needs = {
        "concept_models": False,
        "math_model": False,
    }
    cm = data_status.get("concept_models", {})
    if not cm.get("dir_exists") or not cm.get("config_exists"):
        needs["concept_models"] = True
    mm = data_status.get("math_model", {})
    if not mm.get("dataset_exists"):
        needs["math_model"] = True
    if verbose:
        print("[DECIDE] 資料生成需求:", needs)
    return needs


def generate_or_fix_data(needs: Dict[str, bool], *, verbose=False, dry_run=False, math_args: list = None) -> Dict[str, int]:
    """視需要執行資料生成腳本。"""
    results = {"concept_models": 0, "math_model": 0}
    if needs.get("concept_models"):
        if PREPARE_CONCEPT_DATA_SCRIPT.exists():
            code = run_cmd([sys.executable, str(PREPARE_CONCEPT_DATA_SCRIPT)], cwd=PROJECT_ROOT, verbose=verbose, dry_run=dry_run)
            results["concept_models"] = code
        else:
            print("[WARN] 缺少概念模型數據生成腳本:", PREPARE_CONCEPT_DATA_SCRIPT)
            results["concept_models"] = 1
    # 允許當提供了 math_args 時強制觸發數學資料生成（即便 needs["math_model"] 為 False），以支援可選參數透傳的顯式請求
    if needs.get("math_model") or (math_args is not None and len(math_args) > 0):
        if MATH_DATA_GENERATOR.exists():
            cmd = [sys.executable, str(MATH_DATA_GENERATOR)]
            if math_args:
                cmd.extend([str(x) for x in math_args])
            code = run_cmd(cmd, cwd=APPS_BACKEND_DIR, verbose=verbose, dry_run=dry_run)
            results["math_model"] = code
        else:
            print("[WARN] 缺少數學模型數據生成腳本:", MATH_DATA_GENERATOR)
            results["math_model"] = 1
    return results


def check_models_and_training(verbose=False) -> Dict[str, Any]:
    """檢查模型與訓練系統狀態。"""
    models_dir = TRAINING_DIR / "models"
    checkpoints_dir = TRAINING_DIR / "checkpoints"
    status = {
        "train_script_exists": TRAIN_MODEL_SCRIPT.exists(),
        "models_dir_exists": models_dir.exists(),
        "checkpoints_dir_exists": checkpoints_dir.exists(),
        "has_models": any(models_dir.glob("**/*")) if models_dir.exists() else False,
        "has_checkpoints": any(checkpoints_dir.glob("**/*")) if checkpoints_dir.exists() else False,
        "latest_model_mtime": _latest_mtime_in_dir(models_dir),
        "latest_checkpoint_mtime": _latest_mtime_in_dir(checkpoints_dir),
    }
    if verbose:
        print("[TRAIN] 訓練狀態:", status)
    return status


def decide_training(data_status: Dict[str, Any], train_status: Dict[str, Any], verbose=False) -> Dict[str, bool]:
    """根據數據與模型狀態決策是否需要訓練與是否可 resume。"""
    need_train = False
    can_resume = False

    cm_ok = data_status.get("concept_models", {}).get("config_exists")
    mm_ok = data_status.get("math_model", {}).get("dataset_exists")

    data_latest = max(
        data_status.get("concept_models", {}).get("config_mtime", 0.0),
        data_status.get("math_model", {}).get("dataset_mtime", 0.0),
    )
    model_latest = train_status.get("latest_model_mtime", 0.0)

    # 規則：
    # 1) 沒有任何模型且有可用數據 => 需要訓練
    if not train_status.get("has_models") and (cm_ok or mm_ok):
        need_train = True

    # 2) 數據比模型新（可能更新/重生） => 建議重新訓練
    if (cm_ok or mm_ok) and data_latest > 0 and model_latest > 0 and data_latest > model_latest:
        need_train = True

    # 3) 有 checkpoint 則可續訓
    if train_status.get("has_checkpoints"):
        can_resume = True

    if verbose:
        print(f"[DECIDE] need_train={need_train}, can_resume={can_resume}, data_latest={data_latest}, model_latest={model_latest}")
    return {"need_train": need_train, "can_resume": can_resume}


def run_training(*, preset: str = None, resume: bool = False, verbose=False, dry_run=False) -> int:
    if not TRAIN_MODEL_SCRIPT.exists():
        print("[ERROR] 找不到訓練腳本:", TRAIN_MODEL_SCRIPT)
        return 1
    cmd = [sys.executable, str(TRAIN_MODEL_SCRIPT)]
    if preset:
        cmd.extend(["--preset", preset])
    if resume:
        cmd.append("--resume")
    return run_cmd(cmd, cwd=TRAINING_DIR, verbose=verbose, dry_run=dry_run)


def check_docs_links(verbose=False, dry_run=False) -> Dict[str, Any]:
    if not VALIDATE_LINKS_SCRIPT.exists():
        print("[ERROR] 缺少文檔鏈接校驗腳本:", VALIDATE_LINKS_SCRIPT)
        return {"ok": False, "broken": -1}
    json_report = PROJECT_ROOT / "docs_link_check_errors.json"
    text_report = PROJECT_ROOT / "docs_link_check_errors.txt"
    cmd = [sys.executable, str(VALIDATE_LINKS_SCRIPT), "--root", str(DOCS_DIR), "--report-json", str(json_report), "--report-text", str(text_report)]
    if verbose:
        cmd.append("-v")
    code = run_cmd(cmd, cwd=PROJECT_ROOT, verbose=verbose, dry_run=dry_run)
    result = {"ok": code == 0, "json_report": str(json_report), "text_report": str(text_report)}
    if json_report.exists():
        try:
            with open(json_report, "r", encoding="utf-8") as f:
                data = json.load(f)
            result.update({
                "total": data.get("total_links"),
                "broken": data.get("broken_count"),
            })
        except Exception:
            pass
    return result
 

# 新增：載入文檔重定位映射（多來源容錯）
def _load_relocated_links_mapping() -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    # 首選：嘗試從 validate_doc_links.py 模組內取得常見名稱的映射
    try:
        import importlib.util  # 延遲導入以避免全域污染
        spec = importlib.util.spec_from_file_location("validate_doc_links", str(VALIDATE_LINKS_SCRIPT))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            candidates = (
                "RELOCATED_LINKS",
                "RELOCATED",
                "REWRITE_MAP",
                "RELOCATE_MAP",
                "REDIRECT_MAP",
                "LINK_REWRITES",
                "REWRITE_LINKS",
            )
            for name in candidates:
                if hasattr(mod, name):
                    raw = getattr(mod, name)
                    if isinstance(raw, dict):
                        mapping.update({str(k): str(v) for k, v in raw.items()})
    except Exception as e:
        if not mapping:
            print("[WARN] 無法自 validate_doc_links 載入映射:", e)

    # 次選：scripts/doc_link_mapping.json（可由維護者維護）
    json_candidate = PROJECT_ROOT / "scripts" / "doc_link_mapping.json"
    if json_candidate.exists():
        try:
            with open(json_candidate, "r", encoding="utf-8") as f:
                j = json.load(f)
            if isinstance(j, dict):
                mapping.update({str(k): str(v) for k, v in j.items()})
        except Exception as e:
            print("[WARN] 讀取 doc_link_mapping.json 失敗:", e)

    if not mapping:
        print("[INFO] 未發現任何重定位映射，將以空映射繼續（不會對 MD 做變更）")
    return mapping
 
 
def save_run_report(payload: Dict[str, Any]) -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = REPORTS_DIR / f"project_ai_run_{ts}.json"
    # 使用原子寫入避免中斷造成半寫文件
    _atomic_write_text(out, json.dumps(payload, ensure_ascii=False, indent=2))
    print("[REPORT] 已生成:", out)
    return out

 
def _list_markdown_files(root: Path) -> List[Path]:
    return [p for p in root.rglob("*.md") if p.is_file()]

# 新增：可配置範圍掃描 MD 檔案
def _list_markdown_files_with_scope(*, scope: str, custom_dirs: List[str], excludes: List[str]) -> List[Path]:
    roots: List[Path] = []
    if scope == "docs":
        roots = [DOCS_DIR]
    elif scope == "all":
        roots = [PROJECT_ROOT]
    elif scope == "custom":
        for d in custom_dirs:
            d = d.strip()
            if not d:
                continue
            p = (PROJECT_ROOT / d).resolve()
            if p.exists() and p.is_dir():
                roots.append(p)
    else:
        roots = [DOCS_DIR]
    exclude_set = set([e.strip().strip("/") for e in excludes if e.strip()])
    files: List[Path] = []
    for r in roots:
        for p in r.rglob("*.md"):
            if not p.is_file():
                continue
            # 排除規則：若任一父層資料夾名稱在排除清單，則跳過
            skip = False
            for part in p.relative_to(PROJECT_ROOT).parts:
                if part in exclude_set:
                    skip = True
                    break
            if not skip:
                files.append(p)
    return files

# 新增：原子寫入 + 檔案哈希
def _sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _atomic_write_text(path: Path, content: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    os.replace(tmp, path)

# 新增：Checkpoint/Run 狀態管理
from datetime import timezone

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
 
def _run_state_path(state_dir: Path, run_id: str) -> Path:
    return state_dir / f"run_{run_id}.json"

def _load_run_state(state_dir: Path, run_id: str) -> Dict[str, Any]:
    fp = _run_state_path(state_dir, run_id)
    if fp.exists():
        try:
            return json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def _save_run_state(state_dir: Path, run_id: str, state: Dict[str, Any]) -> None:
    fp = _run_state_path(state_dir, run_id)
    fp.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(fp, json.dumps(state, ensure_ascii=False, indent=2))

def _checkpoint(state_dir: Path, run_id: str, step: str, status: str, payload: Dict[str, Any] = None) -> None:
    st = _load_run_state(state_dir, run_id)
    st.setdefault("run_id", run_id)
    st.setdefault("created_at", _now_iso())
    st.setdefault("steps", {})
    st["steps"][step] = {
        "status": status,
        "updated_at": _now_iso(),
        "payload": payload or {}
    }
    _save_run_state(state_dir, run_id, st)

def _step_done(state: Dict[str, Any], step: str) -> bool:
    return state.get("steps", {}).get(step, {}).get("status") == "done"

# 新增：決策資料紀錄
def _decision_log_path(run_id: str) -> Path:
    return DECISIONS_DIR / f"decision_log_{run_id}.jsonl"

def record_decision(run_id: str, decision: Dict[str, Any]) -> None:
    path = _decision_log_path(run_id)
    line = json.dumps({"ts": _now_iso(), **decision}, ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def fix_markdown_links_in_place(mapping: Dict[str, str], *, verbose=False, dry_run=False, files: List[Path] = None) -> Dict[str, Any]:
    """
    以 validate_doc_links 的重定位映射為依據，批量修正 MD 連結目標。
    僅做目標替換，不變動錨點與顯示文本。例如 (old.md) -> (new.md)，(old.md#sec) -> (new.md#sec)
    可傳入 files 覆蓋要處理的檔案清單。
    """
    changes: List[Tuple[str, int]] = []  # (file, replacements)
    if not mapping:
        return {"changed_files": 0, "total_replacements": 0, "detail": []}

    # 來源檔案集合
    if files is None:
        files = _list_markdown_files(DOCS_DIR)
    total_replacements = 0

    def _apply_mapping_to_line(line: str) -> Tuple[str, int]:
        count = 0
        new_line = line
        for old, new in mapping.items():
            for prefix in ["(", "(./"]:
                if prefix + old in new_line:
                    new_line = new_line.replace(prefix + old, prefix + new)
                    count += 1
                if prefix + old + "#" in new_line:
                    new_line = new_line.replace(prefix + old + "#", prefix + new + "#")
                    count += 1
        return new_line, count

    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8")
        except Exception:
            continue
        replaced = 0
        new_lines: List[str] = []
        for line in text.splitlines(keepends=False):
            nl, c = _apply_mapping_to_line(line)
            new_lines.append(nl)
            replaced += c
        if replaced > 0:
            rel = str(fp.relative_to(PROJECT_ROOT))
            changes.append((rel, replaced))
            total_replacements += replaced
            if verbose:
                print(f"[DOCS] {fp}: replacements={replaced}")
            if not dry_run:
                try:
                    # 先備份
                    backup = fp.with_suffix(fp.suffix + ".bak")
                    shutil.copyfile(fp, backup)
                    # 原子寫入
                    _atomic_write_text(fp, "\n".join(new_lines) + "\n")
                except Exception as e:
                    print(f"[WARN] 無法寫入 {fp}: {e}")

    return {"changed_files": len(changes), "total_replacements": total_replacements, "detail": changes}

def main():
    parser = argparse.ArgumentParser(description="Project AI Orchestrator")
    parser.add_argument("--dry-run", action="store_true", help="僅分析規劃，不執行重任務")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--generate-data", action="store_true", help="允許生成/修復資料")
    parser.add_argument("--decide-train", action="store_true", help="根據狀態決策是否需要訓練")
    parser.add_argument("--run-training", action="store_true", help="允許執行訓練")
    parser.add_argument("--preset", type=str, default=None, help="指定訓練預設場景，例如 quick_start / concept_models_training 等")
    parser.add_argument("--resume", action="store_true", help="若可續訓則嘗試加入 --resume")
    parser.add_argument("--check-docs", action="store_true", help="進行文檔鏈接驗證")
    parser.add_argument("--fix-doc-links", action="store_true", help="依據 validate_doc_links 的重定位映射，批量修正 MD 連結目標（可與 --dry-run 搭配預覽）")
    # 數學數據生成器參數透傳（可選，保持相容：未提供則不影響原行為）
    parser.add_argument("--math-mode", type=str, choices=["default", "single"], default=None, help="數學數據生成模式：default 生成 train(JSON)+test(CSV)；single 按參數生成單一資料集")
    parser.add_argument("--math-num-samples", type=int, default=None, help="single 模式下生成樣本數量")
    parser.add_argument("--math-file-format", type=str, choices=["csv", "json"], default=None, help="single 模式輸出格式")
    parser.add_argument("--math-filename-prefix", type=str, default=None, help="single 模式文件名前綴")
    parser.add_argument("--math-output-dir", type=str, default=None, help="輸出目錄（預設為 <project_root>/data/raw_datasets）")
    parser.add_argument("--math-max-digits", type=int, default=None, help="數字最大位數（預設 3）")
    parser.add_argument("--math-seed", type=int, default=None, help="隨機種子（可重現）")
    parser.add_argument("--math-summary-out", type=str, default=None, help="摘要報表 JSON 輸出路徑（可選）")
    # 新增：端到端流程 & 狀態管理
    parser.add_argument("--full-cycle", action="store_true", help="一鍵執行：檢查→生成→決策→(可選訓練)→文檔校驗/修復→報告")
    parser.add_argument("--run-id", type=str, default=None, help="指定本次執行的 run-id（可與 --resume-run 搭配）")
    parser.add_argument("--resume-run", action="store_true", help="若存在已完成部分則繼續，適用於意外中斷續跑")
    parser.add_argument("--state-dir", type=str, default=None, help="狀態存放目錄，預設為 automation_state/")
    # 新增：MD 掃描範圍設定
    parser.add_argument("--md-scope", type=str, default="docs", choices=["docs", "all", "custom"], help="Markdown 掃描範圍")
    parser.add_argument("--md-dirs", type=str, default="", help="自訂掃描根目錄（逗號分隔），在 --md-scope custom 時生效")
    parser.add_argument("--md-excludes", type=str, default=".git,node_modules,build,dist,venv,automation_reports,data", help="排除目錄（逗號分隔）")

    args = parser.parse_args()

    # full-cycle 預設開關
    if args.full_cycle:
        args.generate_data = True
        args.decide_train = True
        args.check_docs = True
        # 訓練是否自動執行遵循使用者是否提供 --run-training，dry-run 則不會跑重任務

    # 初始化 run-id 與狀態
    state_dir = Path(args.state_dir) if args.state_dir else STATE_DIR
    run_id = args.run_id or _default_run_id()
    run_state = _load_run_state(state_dir, run_id) if args.resume_run else {}

    summary: Dict[str, Any] = {
        "dry_run": args.dry_run,
        "run_id": run_id,
        "steps": {}
    }

    # 訊號攔截：確保中斷時寫入 checkpoint
    def _on_sigint(sig, frame):
        try:
            _checkpoint(state_dir, run_id, "__interrupted__", "stopped", {"reason": "SIGINT"})
        finally:
            sys.exit(130)
    try:
        signal.signal(signal.SIGINT, _on_sigint)
    except Exception:
        pass

    # 解析 MD 參數
    md_dirs = [s for s in (args.md_dirs.split(",") if args.md_dirs else []) if s.strip()]
    md_excludes = [s for s in (args.md_excludes.split(",") if args.md_excludes else []) if s.strip()]
    md_files = _list_markdown_files_with_scope(scope=args.md_scope, custom_dirs=md_dirs, excludes=md_excludes)

    # 1) 資料檢查（可續跑）
    if not _step_done(run_state, "data_status"):
        data_status = check_datasets(verbose=args.verbose)
        summary["steps"]["data_status"] = data_status
        _checkpoint(state_dir, run_id, "data_status", "done", data_status)
    else:
        data_status = run_state.get("steps", {}).get("data_status", {}).get("payload", {})
        summary["steps"]["data_status"] = data_status

    # 2) 判斷是否需要資料生成
    if not _step_done(run_state, "data_needs"):
        data_needs = decide_data_generation(data_status, verbose=args.verbose)
        summary["steps"]["data_needs"] = data_needs
        _checkpoint(state_dir, run_id, "data_needs", "done", data_needs)
    else:
        data_needs = run_state.get("steps", {}).get("data_needs", {}).get("payload", {})
        summary["steps"]["data_needs"] = data_needs

    # 3) 視需要生成資料
    if args.generate_data and not _step_done(run_state, "data_generation"):
        # 組裝可選的數學數據生成器參數（未提供則不添加，保持相容）
        math_args = []
        if args.math_mode:
            math_args += ["--mode", args.math_mode]
        if args.math_num_samples is not None:
            math_args += ["--num-samples", str(args.math_num_samples)]
        if args.math_file_format:
            math_args += ["--file-format", args.math_file_format]
        if args.math_filename_prefix:
            math_args += ["--filename-prefix", args.math_filename_prefix]
        if args.math_output_dir:
            math_args += ["--output-dir", args.math_output_dir]
        if args.math_max_digits is not None:
            math_args += ["--max-digits", str(args.math_max_digits)]
        if args.math_seed is not None:
            math_args += ["--seed", str(args.math_seed)]
        if args.math_summary_out:
            math_args += ["--summary-out", args.math_summary_out]
        
        gen_results = generate_or_fix_data(data_needs, verbose=args.verbose, dry_run=args.dry_run, math_args=(math_args or None))
        summary["steps"]["data_generation_results"] = gen_results
        _checkpoint(state_dir, run_id, "data_generation", "done", gen_results)
    elif args.generate_data:
        summary["steps"]["data_generation_results"] = run_state.get("steps", {}).get("data_generation", {}).get("payload", {})

    # 4) 檢查訓練/模型
    if not _step_done(run_state, "train_status"):
        train_status = check_models_and_training(verbose=args.verbose)
        summary["steps"]["train_status"] = train_status
        _checkpoint(state_dir, run_id, "train_status", "done", train_status)
    else:
        train_status = run_state.get("steps", {}).get("train_status", {}).get("payload", {})
        summary["steps"]["train_status"] = train_status

    # 5) 訓練決策
    if args.decide_train and not _step_done(run_state, "train_decision"):
        train_decision = decide_training(data_status, train_status, verbose=args.verbose)
        summary["steps"]["train_decision"] = train_decision
        # 紀錄決策樣本，供未來學習
        record_decision(run_id, {
            "type": "train_decision",
            "context": {"data_status": data_status, "train_status": train_status},
            "decision": train_decision
        })
        _checkpoint(state_dir, run_id, "train_decision", "done", train_decision)
    elif args.decide_train:
        train_decision = run_state.get("steps", {}).get("train_decision", {}).get("payload", {})
        summary["steps"]["train_decision"] = train_decision
    else:
        train_decision = {"need_train": False, "can_resume": False}
        summary["steps"]["train_decision"] = train_decision

    # 6) 視需要執行訓練
    if args.run_training and train_status.get("train_script_exists"):
        if not args.dry_run:
            code = run_training(preset=args.preset, resume=(args.resume and train_decision.get("can_resume", False)), verbose=args.verbose, dry_run=False)
        else:
            code = 0
        summary["steps"]["training_exit_code"] = code
        _checkpoint(state_dir, run_id, "train_run", "done", {"exit_code": code})

    # 7) 文檔鏈接校驗
    if args.check_docs and not _step_done(run_state, "docs_check"):
        docs_result = check_docs_links(verbose=args.verbose, dry_run=args.dry_run)
        summary["steps"]["docs_check"] = docs_result
        _checkpoint(state_dir, run_id, "docs_check", "done", docs_result)
    elif args.check_docs:
        summary["steps"]["docs_check"] = run_state.get("steps", {}).get("docs_check", {}).get("payload", {})

    # 8)（可選）批量修正文檔連結（支援可配置掃描範圍）
    if args.fix_doc_links and not _step_done(run_state, "docs_fix"):
        mapping = _load_relocated_links_mapping()
        if args.verbose:
            print(f"[DOCS] 載入重定位映射 {len(mapping)} 條；掃描 {len(md_files)} 個檔案（scope={args.md_scope}）")
        fix_result = fix_markdown_links_in_place(mapping, verbose=args.verbose, dry_run=args.dry_run, files=md_files)
        summary["steps"]["docs_fix"] = fix_result
        _checkpoint(state_dir, run_id, "docs_fix", "done", fix_result)
    elif args.fix_doc_links:
        summary["steps"]["docs_fix"] = run_state.get("steps", {}).get("docs_fix", {}).get("payload", {})

    # 總結與輸出
    save_run_report(summary)
    if args.verbose:
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    # 返回碼策略：若執行了訓練/數據生成且有非零返回，則非零；否則 0
    exit_code = 0
    gen_exit = summary.get("steps", {}).get("data_generation_results", {})
    if any(v != 0 for v in gen_exit.values() if isinstance(v, int)):
        exit_code = 1
    if summary.get("steps", {}).get("training_exit_code", 0):
        exit_code = summary["steps"]["training_exit_code"]
    return exit_code


if __name__ == "__main__":
    sys.exit(main())