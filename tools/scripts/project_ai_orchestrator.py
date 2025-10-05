#!/usr/bin/env python3
"""
Project AI Orchestrator - 整合式 AI 開發流程自動化工具
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# 配置常量
PROJECT_ROOT = Path(__file__).parent.parent.parent
APPS_BACKEND_DIR = PROJECT_ROOT / "apps" / "backend"
TRAINING_DIR = PROJECT_ROOT / "training"
DOCS_DIR = PROJECT_ROOT / "docs"

# 資料集路徑
DATA_DIR = PROJECT_ROOT / "data"
CONCEPT_DATA_DIR = DATA_DIR / "concept_models"
CONCEPT_DATA_CONFIG = CONCEPT_DATA_DIR / "config.json"
MATH_DATASET_JSON = DATA_DIR / "math_dataset.json"

# 腳本路徑
SCRIPTS_DIR = PROJECT_ROOT / "tools" / "scripts"
PREPARE_CONCEPT_DATA_SCRIPT = SCRIPTS_DIR / "prepare_concept_data.py"
MATH_DATA_GENERATOR = SCRIPTS_DIR / "generate_math_dataset.py"
TRAIN_MODEL_SCRIPT = SCRIPTS_DIR / "train_model.py"
VALIDATE_LINKS_SCRIPT = SCRIPTS_DIR / "validate_docs_links.py"

def run_cmd(cmd: List[str], cwd=None, verbose=False, dry_run=False) -> int:
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

def generate_or_fix_data(needs: Dict[str, bool], math_args: Optional[List[str]] = None, 
                        verbose=False, dry_run=False) -> Dict[str, int]:
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

def run_training(*, preset: Optional[str] = None, resume: bool = False, verbose=False, dry_run=False) -> int:
    if not TRAIN_MODEL_SCRIPT.exists():
        print("[ERROR] 找不到訓練腳本:", TRAIN_MODEL_SCRIPT)
        return 1
    cmd = [sys.executable, str(TRAIN_MODEL_SCRIPT)]
    if preset is not None:
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
        result["json_report_exists"] = True
    if text_report.exists():
        result["text_report_exists"] = True
    return result

def main():
    """主函數"""
    import argparse
    parser = argparse.ArgumentParser(description="Project AI Orchestrator")
    parser.add_argument("--verbose", "-v", action="store_true", help="顯示詳細資訊")
    parser.add_argument("--dry-run", action="store_true", help="僅顯示將執行的命令，不實際執行")
    parser.add_argument("--check-only", action="store_true", help="僅檢查狀態，不執行任何操作")
    parser.add_argument("--math-args", nargs="*", help="傳遞給數學資料生成器的參數")
    
    args = parser.parse_args()
    
    verbose = args.verbose
    dry_run = args.dry_run
    check_only = args.check_only
    math_args = args.math_args
    
    print("🚀 Project AI Orchestrator 啟動")
    print("=" * 50)
    
    # 1. 檢查資料集狀態
    print("\n📊 檢查資料集狀態...")
    data_status = check_datasets(verbose=verbose)
    
    # 2. 決定是否需要資料生成
    print("\n🤔 判斷資料生成需求...")
    needs = decide_data_generation(data_status, verbose=verbose)
    
    # 3. 執行資料生成（除非僅檢查）
    if not check_only:
        print("\n⚙️  執行資料生成...")
        gen_results = generate_or_fix_data(needs, math_args=math_args, verbose=verbose, dry_run=dry_run)
        if any(code != 0 for code in gen_results.values()):
            print("[WARN] 資料生成過程中出現錯誤")
    
    # 4. 檢查模型與訓練狀態
    print("\n🔍 檢查模型與訓練狀態...")
    train_status = check_models_and_training(verbose=verbose)
    
    # 5. 決定是否需要訓練
    print("\n🧠 判斷訓練需求...")
    train_decision = decide_training(data_status, train_status, verbose=verbose)
    
    # 6. 執行訓練（除非僅檢查）
    if not check_only and train_decision["need_train"]:
        print("\n🏋️  執行模型訓練...")
        train_code = run_training(resume=train_decision["can_resume"], verbose=verbose, dry_run=dry_run)
        if train_code != 0:
            print("[ERROR] 訓練過程中出現錯誤")
            return train_code
    
    # 7. 檢查文檔鏈接
    print("\n🔗 檢查文檔鏈接...")
    link_check_result = check_docs_links(verbose=verbose, dry_run=dry_run)
    if not link_check_result["ok"]:
        print("[WARN] 文檔鏈接檢查發現問題")
    
    print("\n✅ Project AI Orchestrator 執行完成")
    return 0

if __name__ == "__main__":
    sys.exit(main())
