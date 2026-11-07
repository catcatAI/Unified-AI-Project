#!/usr/bin/env python
"""下游問題（第三版）：**這樣學有比較好嗎？**——用連續讀出，三臂增益匹配

前兩版失敗在儀器（§18.2、§19）。§20 量到：把讀出換成膜電位，排名就出現了
（脈衝次數讀出在同樣的權重上完全排不出來）。這一支用那個讀出回答原本的問題。

三臂，**平均增益匹配**，只差在「何時給多少增益」：

* ``neutral``：每次 1.0；
* ``phase``：真振盪器走一整個週期，逐樣本取 ``learning_gain()``；
* ``shuffled``：**同一組增益**、打亂順序（同一個種子）。

``shuffled`` 是關鍵控制組：如果 ``phase`` 只是贏在平均增益，打亂後也會贏；只有
「時機」真的有意義時，``phase`` 才該贏過 ``shuffled``。

量的是 held-out 名次：給 cue，``potential`` 讀出下正確 target 的**分數差**
（margin，連續值，不受脈衝量化影響）與 top-1 命中率。

判詞

* ``phase-beats-matched-mean``：margin 與 top-1 **兩個指標一致**變好，``phase``
  在多數種子上同時贏過 ``neutral`` 與 ``shuffled``，且差距大於種子間散佈；
* ``margin-gain-without-hit-gain``：margin 變好但 top-1 變差——方向相反，**不採計**
  為好處；
* ``timing-does-not-matter-only-gain``：``phase`` 贏 ``neutral`` 但贏不過 ``shuffled``
  ——好處來自平均增益，不是時機；
* ``phase-loses-to-matched-mean``：margin 與 top-1 **都**明顯變差，且多數種子上
  ``phase`` 同時輸給兩個臂——這是負結果，要寫出來，不是「沒差」；
* ``no-downstream-difference``：其餘。

``--task easy`` 是第一版（16 對，中性臂打滿分，比較在天花板上）；
``--task hard``（預設）是候選 48 對、共享噪聲位、lr 0.03，讓中性臂落在約五成。
"""

# =============================================================================
# ANGELA-MATRIX: [L4] [αβγδ] [C] [L0-L11]
# =============================================================================

from __future__ import annotations

import argparse
import importlib.util
import json
import random
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

from ai.garden.snn_core import TensorSNNCore  # noqa: E402
from core.life.al_learning_gate import learning_gain  # noqa: E402
from core.life.al_oscillator import Oscillator, natural_period  # noqa: E402

READOUT_SCRIPT = Path(__file__).with_name("garden_readout_variants.py")


def _load_readouts():
    spec = importlib.util.spec_from_file_location("garden_readout_variants", READOUT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {READOUT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_readouts = _load_readouts()

EPOCHS = 1
TARGET_STRENGTH = 0.35
SEEDS = (11, 23, 37, 41, 53, 67)

# 第一版任務（16 對、lr 0.05）讓中性臂打滿分，margin 的比較是在天花板上做的。
# 難版：候選變多、共享噪聲位、學習率調低到中性臂只有一半左右。
TASKS: Dict[str, Dict[str, object]] = {
    "easy": {"pairs": 16, "noise_bits": 3, "shared": False, "lr": 0.05, "threshold": 0.25},
    "hard": {"pairs": 48, "noise_bits": 3, "shared": True, "lr": 0.03, "threshold": 0.25},
    # 第二個任務族：真正互相競爭的 cue —— 每 group 個 cue 共用一個主 token，
    # 只能靠各自的專屬 token 分辨。干擾結構不同於 hard（hard 是全體共用一個噪聲位）。
    # 多對一：兩個 cue 共用同一個 target。干擾真的存在（同一列由兩組 cue 累積），
    # 但答案仍然可學 —— 這才是「干擾結構不同、難度可校準」的第二族。
    "many_to_one": {
        "pairs": 48,
        "noise_bits": 3,
        "shared": True,
        "target_group": 24,
        "lr": 0.03,
        "threshold": 0.25,
    },
}
DEFAULT_TASK = "hard"


def _pairs(task: Dict[str, object]) -> List[Tuple[List[str], str]]:
    """每個 cue 有自己的 token，加噪聲位；難版讓所有 cue 共用一個 ``shared`` 位。"""
    count = int(task["pairs"])  # type: ignore[arg-type]
    bits = int(task["noise_bits"])  # type: ignore[arg-type]
    pairs: List[Tuple[List[str], str]] = []
    for i in range(count):
        cue = [f"cue{i:02d}"]
        if task["shared"]:
            cue += [f"n{i % bits}", "shared"]
        else:
            cue += [f"n{(i * 7 + j) % bits}" for j in range(bits)]
        target = f"t{i % int(task.get('target_group') or count):02d}"
        pairs.append((cue, target))
    return pairs


def _schedule(period: float, n: int, step_per_period: Optional[int] = None) -> List[float]:
    """逐樣本取增益；``step_per_period`` 決定「每幾個樣本走完一個週期」。

    預設是整段 ``n`` 個樣本走完一個週期。多輪訓練時必須另外指定，否則週期會隨
    ``epochs`` 一起被拉長（5 輪 = 相位前進慢 5 倍），「訓練量」與「調制頻率」就綁在
    同一個開關上，兩種解釋分不開。
    """
    osc = Oscillator()
    osc.step(period * 3.0)
    gains: List[float] = []
    dt = period / (step_per_period or n)
    for _ in range(n):
        osc.step(dt)
        gains.append(learning_gain(osc.activation).gain)
    return gains


def _train(
    gains: Sequence[float], seed: int, task: Dict[str, object], epochs: int = EPOCHS
) -> TensorSNNCore:
    core = TensorSNNCore(threshold=float(task["threshold"]), timesteps=_readouts.TIMESTEPS)  # type: ignore[arg-type]
    rng = random.Random(seed)
    pairs = _pairs(task)
    for _ in range(epochs):
        order = pairs[:]
        rng.shuffle(order)
        for (inputs, target), gain in zip(order, gains):
            core.hebbian_update(
                {key: 1.0 for key in inputs},
                {target: 1.0},
                lr=float(task["lr"]),  # type: ignore[arg-type]
                target_strength=TARGET_STRENGTH,
                plasticity=gain,
            )
    return core


def _candidate_targets(pairs: Sequence[Tuple[List[str], str]]) -> List[str]:
    """任務的目標 label 集（去重、保序）。"""
    seen: List[str] = []
    for _, target in pairs:
        if target not in seen:
            seen.append(target)
    return seen


def _score(out: Dict[str, float], targets: Sequence[str], target: str) -> Tuple[float, bool]:
    """正確 target 對「其他候選 label」最佳值的差，以及是否 top-1。

    候選集必須由**目標 label** 決定，不能由 pair 索引拼字串。多對一任務裡一個
    label 對應多個 pair：用索引拼 ``t{i:02d}`` 時，索引超過 label 數的 pair 抓到的
    全是 ``None``（rivals 空 → 直接判 miss，命中率被硬性截在半數），而 label 相同
    的另一個 pair 從來沒被排除，真要比到也會同分。兩者都會讓「學得好不好」看起來
    比實際差。
    """
    correct = out.get(target)
    rivals = [out[label] for label in targets if label != target and label in out]
    if correct is None or not rivals:
        return 0.0, False
    best = max(rivals)
    return correct - best, correct > best


def _evaluate(core: TensorSNNCore, task: Dict[str, object]) -> Dict[str, float]:
    hits, margins = 0, []
    pairs = _pairs(task)
    targets = _candidate_targets(pairs)
    for inputs, target in pairs:
        out = _readouts._forward(core, {key: 1.0 for key in inputs}, "potential")
        margin, hit = _score(out, targets, target)
        margins.append(margin)
        hits += int(hit)
    return {"hit_rate": hits / len(pairs), "margin": statistics.fmean(margins)}


def _verdict(rows: Dict[str, List[Dict[str, float]]]) -> str:
    """兩個指標都要看：margin 上升但 top-1 下降不是「贏」。"""
    phase = [row["margin"] for row in rows["phase"]]
    neutral = [row["margin"] for row in rows["neutral"]]
    shuffled = [row["margin"] for row in rows["shuffled"]]
    spread = statistics.pstdev(neutral)
    margin_gain = statistics.fmean(phase) - statistics.fmean(neutral)
    beats_shuffled = statistics.fmean(phase) - statistics.fmean(shuffled)
    hit_phase = statistics.fmean(row["hit_rate"] for row in rows["phase"])
    hit_neutral = statistics.fmean(row["hit_rate"] for row in rows["neutral"])
    beats_both = sum(1 for p, n, s in zip(phase, neutral, shuffled) if p > n and p > s)

    if margin_gain <= spread:
        # 「沒有好處」與「明顯有害」是兩件事。原本一律回報 no-downstream-difference，
        # 等於把一個可信的負結果寫成「沒差」——那會讓後面的結論少掉一個反例。
        losers = sum(1 for p, n, s in zip(phase, neutral, shuffled) if p < n and p < s)
        if (
            margin_gain < -spread
            and hit_phase < hit_neutral
            and beats_shuffled < -spread
            and losers > len(phase) / 2
        ):
            return "phase-loses-to-matched-mean"
        return "no-downstream-difference"
    if hit_phase < hit_neutral:
        # margin 變好但打中的變少：方向相反，不能算贏
        return "margin-gain-without-hit-gain"
    if beats_shuffled <= spread:
        return "timing-does-not-matter-only-gain"
    if beats_both > len(phase) / 2:
        return "phase-beats-matched-mean"
    return "no-downstream-difference"


def run(
    seeds: Sequence[int] = SEEDS, task_name: str = DEFAULT_TASK, epochs: int = EPOCHS
) -> Dict[str, object]:
    task = TASKS[task_name]
    period = natural_period()
    n_samples = int(task["pairs"]) * epochs  # type: ignore[arg-type]
    # 每個 epoch 走完一個週期：每樣本的相位前進速度與 epochs 無關。
    phase_gains = _schedule(period, n_samples, step_per_period=int(task["pairs"]))  # type: ignore[arg-type]

    rows: Dict[str, List[Dict[str, float]]] = {"neutral": [], "phase": [], "shuffled": []}
    gain_means: Dict[str, float] = {}
    for seed in seeds:
        shuffled = phase_gains[:]
        random.Random(seed * 7919).shuffle(shuffled)
        arms = {"neutral": [1.0] * n_samples, "phase": phase_gains, "shuffled": shuffled}
        for name, gains in arms.items():
            rows[name].append(_evaluate(_train(gains, seed, task, epochs), task))
            gain_means.setdefault(name, statistics.fmean(gains))

    summary = {
        name: {
            "margin_mean": round(statistics.fmean(r["margin"] for r in rows[name]), 5),
            "hit_rate_mean": round(statistics.fmean(r["hit_rate"] for r in rows[name]), 3),
            "gain_mean": round(gain_means[name], 4),
        }
        for name in rows
    }
    matched = abs(gain_means["phase"] - gain_means["neutral"]) <= 0.05

    return {
        "task": task_name,
        "task_params": dict(task),
        "period_s": round(period, 3),
        "epochs": epochs,
        "seeds": list(seeds),
        "arms": summary,
        "gain_matched": bool(matched),
        "per_seed_margin": {name: [round(r["margin"], 5) for r in rows[name]] for name in rows},
        "per_seed_hit_rate": {name: [round(r["hit_rate"], 3) for r in rows[name]] for name in rows},
        "verdict": _verdict(rows) if matched else "gain-not-matched",
    }


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", choices=sorted(TASKS), default=DEFAULT_TASK)
    ap.add_argument(
        "--epochs",
        type=int,
        default=EPOCHS,
        help="訓練輪數：1 是一次性學習，5 以上會讓權重飽和到 Oja 上限",
    )
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)

    result = run(task_name=args.task, epochs=args.epochs)
    print(f"task: {args.task} {result['task_params']}")
    for name, arm in result["arms"].items():  # type: ignore[union-attr]
        print(
            f"{name:<9} margin {arm['margin_mean']:+.5f}  hit {arm['hit_rate_mean']:.3f}  "
            f"gain {arm['gain_mean']:.3f}"
        )
    print(f"per-seed margin {result['per_seed_margin']}")
    print(f"verdict: {result['verdict']}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"report: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
