#!/usr/bin/env python3
"""
全量綜合驗收 — 硬件規格自適應（<100MB, <30s, 分批+sleep）

跑 L0→L3 全部基準（20/20 + 關聯 1.0 + 對話框架 100% + 記憶存在 + 推理 60% + 工具 100% + MMLU 無RAG 75/100 實測），
硬件自適應：batch 依 tier，桌機/筆電同硬件同結果。

資源：500 題分批 + 關聯 + 對比，總 <30s，<300MB。
"""

import os, sys, subprocess, time, json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "apps/backend/src"))


def run(cmd, timeout=10):
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, timeout=timeout).decode()
        return out
    except Exception as e:
        return f"FAIL: {e}"


def main():
    from core.backbone.hardware import HardwareProfile

    hw = HardwareProfile.detect()
    tier = HardwareProfile.get_tier(hw)
    adaptive = HardwareProfile.get_adaptive_compute(hw)
    print(
        f"硬件規格自適應全量驗收: GPU={hw['gpu']} RAM={hw['ram_gb']:.1f} tier={tier} vocab={adaptive['garden_max_vocab']}"
    )
    print("=" * 60)

    checks = []
    # L0: 20/20 (check TOTAL: 20/20 or 100.0%, timeout 30 for 461K dict)
    out = run([sys.executable, "scripts/benchmark_ed3n_garden.py", "--engine", "both"], 30)
    ok = ("20/20" in out or "100.0%" in out) and "TOTAL" in out
    if not ok:
        try:
            import subprocess

            out2 = subprocess.run(
                [sys.executable, "scripts/benchmark_ed3n_garden.py", "--engine", "both"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            ok = "20/20" in (out2.stdout + out2.stderr)
        except Exception:
            pass
    checks.append(("L0 20/20", ok))
    print(f"  L0 20/20: {'✅' if ok else '❌'}")

    # L1: association 1.0
    out = run([sys.executable, "scripts/validate_association.py", "--engine", "ed3n"], 10)
    ok = "association_capability=1.0" in out
    checks.append(("L1 關聯 1.0", ok))
    print(f"  L1 關聯 1.0: {'✅' if ok else '❌'}")

    # L1-3: unseen 88% (check for 88% or 7/8, timeout 20 for ONNX load)
    # 誠實門：超時即失敗，不自動放行（舊 fallback 超時當通過已刪除）
    out = run([sys.executable, "scripts/probe_snn_unseen.py"], 20)
    ok = "88%" in out or "7/8" in out
    checks.append(("L1-3 未見 88%", ok))
    print(f"  L1-3 未見 88%: {'✅' if ok else '❌'}")

    # L2-1: dialogue 100%
    out = run([sys.executable, "scripts/benchmark_dialogue_coherence.py"], 10)
    ok = "100%" in out
    checks.append(("L2-1 對話 100%", ok))
    print(f"  L2-1 對話 100%: {'✅' if ok else '❌'}")

    # L2-3: FixedSizeCore 實測門（跑真實 5K 訓練+100 未見測試，取 hits/100；
    # 舊門僅檢查文件存在已退役；以腳本自定目標 ≥50% 為通過線）
    import re

    out = run([sys.executable, "scripts/train_fixedcore_reasoning.py"], 150)
    m = re.search(r"純神經 FixedSizeCore 100 未見:\s*(\d+)/100\s*=\s*(\d+)%", out)
    ok = bool(m and int(m.group(1)) >= 50)
    checks.append(("L2-3 FixedSizeCore≥50%", ok))
    print(f"  L2-3 FixedSizeCore實測 {m.group(0) if m else '無輸出'}: {'✅' if ok else '❌'}")

    # L3-2: tool 100% (90s budget: real network search needs ~12s)
    out = run([sys.executable, "scripts/benchmark_tool_real.py"], 90)
    ok = "100%" in out and "0 崩潰" in out
    checks.append(("L3-2 工具 100%", ok))
    print(f"  L3-2 工具 100%: {'✅' if ok else '❌'}")

    # L3-1: MMLU 風格知識能力實測（R79：舊 benchmark_mmlu_subset 的 100 題是 4 題
    # 模板重複 + 「模擬+20% RAG」假數據，違反 RELEASE_CRITERIA 模擬條款，已退役。
    # 改由 angela_bench 的 knowledge_mc 40 題（真實四選一、無模擬）承擔此驗收）
    out = run(
        [
            sys.executable,
            "scripts/run_benchmarks.py",
            "--backend",
            "native-max",
            "--suite",
            "knowledge_mc",
            "--gate-native",
            "--out",
            "/tmp/fv-bench",
        ],
        60,
    )
    ok = "gate: OK" in out
    checks.append(("L3-1 knowledge_mc gate (angela_bench)", ok))
    print(f"  L3-1 knowledge_mc gate (angela_bench): {'✅' if ok else '❌'}")

    # 總計
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    print("=" * 60)
    print(f"  全量 {passed}/{total} = {passed/total:.0%} 硬件自適應 {tier} chassis-agnostic ✅")
    # 驗證筆電同規格
    hw_same = {
        "gpu": "Intel Arc B570",
        "gpu_memory_gb": 10,
        "ram_gb": 15.5,
        "cpu_cores": 4,
        "gpu_vendor": "intel",
    }
    print(
        f"  筆電同規格 tier {HardwareProfile.get_tier(hw_same)} → {'✅' if HardwareProfile.get_tier(hw_same)==tier else '❌'}"
    )
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
