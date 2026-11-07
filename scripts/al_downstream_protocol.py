#!/usr/bin/env python
"""固定評分協定 v3：相位調制到底有沒有用？（跨 regime × 任務族）

v2 只跑兩個 regime、一個任務族，結論是 `regime-dependent-no-claim`。v3 的改動是
**增加獨立維度**，不是再調參數：

* regime 矩陣擴成 epochs ∈ {1, 3, 5}；
* 任務族擴成兩個、干擾結構不同：
  - ``hard``：所有 cue 共用一個噪聲位，每 cue 有自己的 token；
  - ``many_to_one``：兩個 cue 共用同一個 target（干擾真的存在，但答案仍可學）。

協定（寫死在常數裡，不從命令列給）

1. **讀出**：膜電位（§20：脈衝次數在同權重下無鑑別力）；
2. **調制頻率**：每個 epoch 走完一個振盪週期（v6 起）；``epochs`` 只改變訓練量，
   不改變每樣本拿到的相位速度；
3. **難度校準**：每個任務族沿固定階梯 × lr 格點，取第一個讓**中性臂** top-1 落在
   [0.30, 0.70] 的組合；校準不到就整族標 ``uninformative``（天花板與地板都不算證據）。
   v7 起**每族只校準一次**，且候選組合必須讓 ``EPOCHS_MATRIX`` 裡**每一個** regime 的中性臂
   都落在 [0.30, 0.70]；某格若仍跑出範圍就標 ``neutral-out-of-range``，而不是換一個更簡單
   的任務重校（見下）；
4. **種子**：12 個固定；校準掃描用 3 個、選中的候選再用 8 個確認（v10 起），三組**兩兩互斥**
   （v5 起互斥評估種子）。只有 3 個種子的掃描值會系統性偏樂觀（實測 +0.055），足以把貼邊的
   候選誤標成有餘裕；
5. **控制組**：``shuffled``——**同一組增益**打亂順序，分離「平均增益」與「時序」；
6. **判詞**：margin **與** top-1 必須同向；只升 margin 不算贏；
7. **種子穩健性**（v8 起）：``phase-beats-matched-mean``／``phase-loses-to-matched-mean``
   還要在**兩個比較**（對 neutral、對 shuffled）上至少 ``SIGN_TEST_MIN`` 個種子同向
   （12 個種子下是 10 個，單尾二項 p≈0.019），否則降級成
   ``timing-does-not-matter-only-gain``／``no-downstream-difference``。均值差 0.05 可能
   來自 12:0，也可能是 7:5，只看均值會把擲硬幣當成機制。

v7 修的是**混淆**：v6 及以前，難度階梯是逐格校準的，於是 ``epochs`` 這一軸同時換掉了
任務難度與任務大小——實測 ``hard`` 的 ep1 落在 48 pair／3 噪聲位，ep3/ep5 落在 96 pair／
2 噪聲位；``many_to_one`` 的 ep1 用 target_group 12，ep3/ep5 用 24。跨 epoch 的比較因此
不是「只多訓練幾輪」。v7 每族只校準一次，候選組合必須讓**每個** regime 的中性臂都在
[0.30, 0.70]（只在校準那一格看是不夠的：在 ep1 校準出來的任務到了 ep5 會飽和到 1.0），
之後 step 與 lr 都固定，``epochs`` 只改訓練量；跑出範圍的格標成不可下結論，而不是換題。

v11 修的是**根**：``_train`` 與 ``_evaluate`` 用的是同一批 pair，所以報告裡的 ``hit_rate`` 一直是
訓練集命中率，不是 held-out。實測中性臂 ep1 0.52 → ep3 0.96 → ep5 1.00，而同一批權重在同規則、
沒訓練過的 cue 上，所有種子、所有 epoch 都是 0.062（3/48，等於亂猜）。也就是說：下游量到的差別
只能是「記得多快」，這個模型根本沒有遷移可言。v11 把 ``heldout_hit_rate_mean`` 與
``heldout_at_chance`` 寫進每一格，讓這件事每次重跑都會自己現形。

v12 加一族人造任務 ``structured``：每個 target 一個共用的 feature token，訓練與 held-out 的
cue 都帶，所以 held-out 終於有意義。實測它 ep1 就完全遷移（訓練集與 held-out 都 1.000），但
ep3 起所有 target 的電位壓成同分（margin 恰 0.0000），top-1 崩成 0.000——``epochs`` 在這模型
上不是學習曲線，是「先學會、再壓平」。

v9 修的是**校準貼邊**：沿著單調的難度軸「第一個合格就採用」，必然停在界內第一點——實測
``many_to_one`` 停在 0.306（餘裕 0.006）、``hard`` 停在 0.333（餘裕 0.033），兩族都是換一批
種子就會跨出界外的距離。v9 優先選每個 regime 都離上下界至少 ``HIT_MARGIN``=0.05 的候選，
找不到才退回第一個合格者並標 ``centred: False``。這條規則同樣是看到 v8 的 0.299 之後才寫
的，而且它會改變「用哪一題」，所以結果必須整個重跑重報，不能只拿它去救那一格。

v8 是**在看到 v7 的數字之後**才加的規則，必須這樣標記：v7 修好混淆後，``hard`` ep5 出現
``phase-beats-matched-mean``（top-1 0.701 vs shuffled 0.653 vs neutral 0.573），但逐種子
看是 phase>neutral 11/12、phase>shuffled **7/12**——對 shuffled 的優勢是擲硬幣。v8 因此
要求兩個比較都至少 10/12 同向（單尾二項 p≈0.019）才給出方向性判詞，否則降級。這條規則
只會**撤掉**判詞、不會生出判詞，所以即使它是事後加入的，偏誤方向是保守的。

v4 只是**修儀器**：候選 label 由 pair 索引拼字串改成由任務的目標 label 集決定。
多對一任務裡一個 label 對應多個 pair，索引拼法會讓半數 pair 的 rivals 全空
（直接判 miss，命中率硬性截在 0.5），另一半把自己的 label 當對手。v3 的
``many_to_one`` 全部數字因此作廢，必須重跑。

整體判詞

* ``insufficient-informative-regimes``：可下結論的格 < 2；
* ``mechanism-benefit-consistent``：所有可下結論的格都是 `phase-beats-matched-mean`；
* ``no-mechanism-benefit-consistent``：所有格都沒贏過 neutral；
* ``mechanism-harm-consistent``：所有可下結論的格都是 `phase-loses-to-matched-mean`；
* ``regime-dependent-no-claim``：其餘（方向不一致）。
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

PROTOCOL_VERSION = "al-downstream-v14"
READOUT = "potential"
EPOCHS_MATRIX = (1, 3, 5)
LR_GRID = (0.005, 0.008, 0.01, 0.015, 0.02, 0.03, 0.05)
HIT_RANGE = (0.30, 0.70)
# 校準沿著單調的難度軸「第一個合格就採用」，數學上必然停在邊界上：實測 ``many_to_one``
# 停在 0.306、``hard`` 停在 0.333，兩族都只有 0.006／0.033 的餘裕，比種子噪音還小，換一批
# 種子就掉出範圍（0.299）。所以校準改為優先選「每個 regime 都離上下界至少 0.05」的候選，
# 找不到才退回第一個合格者並標 ``centred: False``。這條餘裕規則是在看到 v8 的 0.299 之後
# 才加的——它會改變「用哪一題」，所以必須寫出來。
HIT_MARGIN = 0.05
SEEDS = (11, 23, 37, 41, 53, 67, 79, 83, 97, 101, 113, 127)
# 校準種子必須與評估種子**互斥**：共用種子等於先看答案再出題，被校準到 [0.30, 0.70]
# 的中性臂會在評估時被同一批種子稍微優待（v4 及以前就是這樣）。
CALIBRATION_SEEDS = (211, 223, 241)
# 掃描用 3 個種子太省：實測同一題目在掃描種子上是 0.361，在評估種子上是 0.306——系統性
# 偏樂觀 0.055，剛好把「貼邊」誤標成「有餘裕」。所以選中的候選要再用一組較大的、與前兩組
# 都互斥的種子確認一次；``centred`` 與報告裡的校準命中率都用確認值，不用掃描值。
CONFIRMATION_SEEDS = (307, 311, 313, 317, 331, 337, 347, 349)

# 難度階梯：每個任務族由易到難，第一個校準得動的就採用。
FAMILIES: Dict[str, List[Dict[str, object]]] = {
    "hard": [
        {"pairs": 48, "noise_bits": 3, "shared": True},
        # 72/2 是為了讓「同一題目在 ep1 不低於 0.30、ep5 不高於 0.70」有機會成立而加的
        # 一級。原本 48/3 到 96/2 跳太大：前者 ep5 飽和到 1.0，後者 ep1 只有 0.24。
        {"pairs": 72, "noise_bits": 2, "shared": True},
        {"pairs": 96, "noise_bits": 2, "shared": True},
        {"pairs": 144, "noise_bits": 1, "shared": True},
    ],
    # 衝突證據的任務族：cue 沒有專屬 token，每個 feature 都對多個 target 有邊。實測
    # 96 pair／12 feature／5 token／2 個支持證據／8 個 target／lr 0.01 時，中性臂在
    # ep1/3/5 是 0.361／0.486／0.500，held-out 是 0.347／0.486／0.500（亂猜 0.125）——
    # 中段存在，而且遷移與訓練同步，不是背誦。
    "conflict": [
        {
            "pairs": 96,
            "features": 12,
            "cue_tokens": 5,
            "support": 2,
            "target_group": 8,
        },
        {
            "pairs": 96,
            "features": 16,
            "cue_tokens": 5,
            "support": 2,
            "target_group": 8,
        },
        {
            "pairs": 96,
            "features": 12,
            "cue_tokens": 4,
            "support": 1,
            "target_group": 8,
        },
        {
            "pairs": 192,
            "features": 16,
            "cue_tokens": 5,
            "support": 1,
            "target_group": 8,
        },
    ],
    # 共用判別特徵的任務族：每個 target 一個 feature token，訓練與 held-out 的 cue 都帶。
    # 這一族存在的目的是讓 held-out 有意義；實測它在 ep1 就能完全遷移（train 與 held-out
    # 都 1.000），但 ep3 起所有 target 的電位壓成同分、margin 恰為 0，top-1 崩成 0。
    "structured": [
        {"pairs": 48, "noise_bits": 3, "shared": True, "target_group": 12, "feature_token": True},
        {"pairs": 96, "noise_bits": 3, "shared": True, "target_group": 12, "feature_token": True},
        {"pairs": 192, "noise_bits": 2, "shared": True, "target_group": 12, "feature_token": True},
    ],
    "many_to_one": [
        {"pairs": 48, "noise_bits": 3, "shared": True, "target_group": 24},
        {"pairs": 48, "noise_bits": 3, "shared": True, "target_group": 18},
        {"pairs": 48, "noise_bits": 3, "shared": True, "target_group": 12},
        # 72p/group 12 是同一組目標配對、只是資料量多一級（實測 ep1 0.361 vs 0.306）。沒有
        # 這一級，group 12 只剩 0.306 這種貼著下界的候選，換一批種子就掉到 0.299。
        {"pairs": 72, "noise_bits": 3, "shared": True, "target_group": 12},
        {"pairs": 96, "noise_bits": 2, "shared": True, "target_group": 24},
    ],
}

DOWNSTREAM_SCRIPT = Path(__file__).with_name("al_c_learn_downstream.py")


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_downstream = _load("al_c_learn_downstream", DOWNSTREAM_SCRIPT)

assert READOUT == "potential", "the protocol fixes the readout; change it here deliberately"
assert not set(CALIBRATION_SEEDS) & set(SEEDS), "calibration seeds must not leak into evaluation"


def _task(family: str, step: Dict[str, object], lr: float) -> Dict[str, object]:
    base = dict(_downstream.TASKS["hard"] if family == "hard" else _downstream.TASKS[family])
    base.update(step)
    base["lr"] = lr
    return base


def _measure(task: Dict[str, object], seeds, readout: Optional[str] = None) -> Dict[int, float]:
    """每個 regime 的中性臂命中率；中途跑出 [0.30, 0.70] 就停止（後面的格沒量到）。"""
    pairs = int(task["pairs"])  # type: ignore[arg-type]
    hits_by_epoch: Dict[int, float] = {}
    for epochs in EPOCHS_MATRIX:
        hits = []
        for seed in seeds:
            core = _downstream._train([1.0] * (pairs * epochs), seed, task, epochs)
            hits.append(_downstream._evaluate(core, task, readout=readout)["hit_rate"])
        mean_hit = statistics.fmean(hits)
        hits_by_epoch[epochs] = round(mean_hit, 3)
        if not HIT_RANGE[0] <= mean_hit <= HIT_RANGE[1]:
            break
    return hits_by_epoch


def _is_centred(hits_by_epoch: Dict[int, float]) -> bool:
    """每個 regime 都離上下界至少 ``HIT_MARGIN``（且每一格都量過）。"""
    if len(hits_by_epoch) != len(EPOCHS_MATRIX):
        return False
    return all(
        HIT_RANGE[0] + HIT_MARGIN <= hit <= HIT_RANGE[1] - HIT_MARGIN
        for hit in hits_by_epoch.values()
    )


def calibrate_family(family: str, readout: Optional[str] = None) -> Dict[str, object]:
    """挑一個在**所有** regime 都讓中性臂落在中段的 step 與 lr。

    逐格校準會讓難度階梯隨 ``epochs`` 移動，把「多訓練幾輪」變成「換一題更簡單的」。
    但固定在校準訓練量上也不夠：在 ep1 校準出來的任務，到了 ep5 常常已經飽和（實測中性臂
    top-1 0.986／1.0），於是這條軸只剩一格能用。所以候選組合必須**每一個** regime 都落在
    [0.30, 0.70]；找不到就整族標 ``uninformative``——寧可承認這族測不出東西，也不要換題。

    另外優先選「離邊界至少 ``HIT_MARGIN``」的候選：第一個合格者總是貼著邊界（實測 0.306／
    0.333），而校準只有 ``CALIBRATION_SEEDS`` 三個種子，估出來的餘裕和噪音同量級。找不到有
    餘裕的候選才退回第一個合格者（``centred: False``），不因為沒餘裕就宣稱這族測不出東西。
    """
    trials: List[Dict[str, object]] = []
    fallback: Dict[str, object] | None = None
    for step in FAMILIES[family]:
        for lr in LR_GRID:
            task = _task(family, step, lr)
            hits_by_epoch = _measure(task, CALIBRATION_SEEDS, readout=readout)
            in_range = len(hits_by_epoch) == len(EPOCHS_MATRIX) and all(
                HIT_RANGE[0] <= hit <= HIT_RANGE[1] for hit in hits_by_epoch.values()
            )
            entry = dict(step)
            entry.update(lr=lr, neutral_hit_by_epoch=hits_by_epoch, in_range_everywhere=in_range)
            trials.append(entry)
            if not in_range:
                continue
            confirmed = _measure(task, CONFIRMATION_SEEDS, readout=readout)
            candidate: Dict[str, object] = {
                "informative": True,
                "step": dict(step),
                "lr": lr,
                "neutral_hit_by_epoch": {str(epoch): hit for epoch, hit in confirmed.items()},
                "scan_hit_by_epoch": {str(epoch): hit for epoch, hit in hits_by_epoch.items()},
                "centred": _is_centred(confirmed),
                "trials": trials,
            }
            if candidate["centred"]:
                return candidate
            if fallback is None:
                fallback = candidate
    if fallback is not None:
        return fallback
    return {"informative": False, "trials": trials}


def _sign_test_minimum(seeds: int, alpha: float = 0.05) -> int:
    """單尾二項檢定：12 個種子至少要幾個同向，才算不是擲硬幣。

    P(X>=9|12,0.5)=0.073，P(X>=10|12,0.5)=0.019，所以 12 個種子的門檻是 10。
    """
    from math import comb

    for need in range(seeds // 2, seeds + 1):
        tail = sum(comb(seeds, k) for k in range(need, seeds + 1)) / 2**seeds
        if tail <= alpha:
            return need
    return seeds


SIGN_TEST_MIN = _sign_test_minimum(len(SEEDS))


def _seed_robust(verdict: str, seed_wins: Dict[str, int]) -> Tuple[str, str | None]:
    """平均差要在種子上站得住，才算機制有效（或有害）。

    均值差 0.05 可能來自 12:0，也可能是 7:5；後者不是「時序有用」，只是擲硬幣。
    所以 ``phase-beats-matched-mean`` 與 ``phase-loses-to-matched-mean`` 都要求在
    兩個比較上至少 ``SIGN_TEST_MIN`` 個種子同向，否則降級。
    """
    seeds = seed_wins["seeds"]
    over_neutral = seed_wins["phase_over_neutral_hit"]
    over_shuffled = seed_wins["phase_over_shuffled_hit"]
    if verdict == "phase-beats-matched-mean":
        if min(over_neutral, over_shuffled) >= SIGN_TEST_MIN:
            return verdict, None
        return "timing-does-not-matter-only-gain", (
            f"seed-robustness failed: phase>neutral {over_neutral}/{seeds}, "
            f"phase>shuffled {over_shuffled}/{seeds}, need {SIGN_TEST_MIN}/{seeds}"
        )
    if verdict == HARM:
        under_neutral = seeds - over_neutral
        under_shuffled = seeds - over_shuffled
        if min(under_neutral, under_shuffled) >= SIGN_TEST_MIN:
            return verdict, None
        return "no-downstream-difference", (
            f"harm not seed-robust: phase<neutral {under_neutral}/{seeds}, "
            f"phase<shuffled {under_shuffled}/{seeds}, need {SIGN_TEST_MIN}/{seeds}"
        )
    return verdict, None


def evaluate_cell(
    family: str, calibration: Dict[str, object], epochs: int, readout: Optional[str] = None
) -> Dict[str, object]:
    task = _task(family, calibration["step"], float(calibration["lr"]))  # type: ignore[arg-type]
    pairs = int(task["pairs"])  # type: ignore[arg-type]
    period = _downstream.natural_period()
    # 每個 epoch 一個週期：不同 epochs 之間的「每樣本相位速度」相同，否則
    # 「訓練量」與「調制頻率」是同一個開關，兩種解釋分不開。
    phase_gains = _downstream._schedule(period, pairs * epochs, step_per_period=pairs)

    # 沒訓練過的 cue：這是「學會」與「記得」的分界。訓練與評估原本共用同一批 pair，
    # 所以這裡的 hit_rate 只說明背得多快；沒訓練過的 cue 上還剩下多少，才是遷移。
    held = _downstream._heldout_pairs(task)
    targets = _downstream._candidate_targets(_downstream._pairs(task))

    rows: Dict[str, List[Dict[str, float]]] = {"neutral": [], "phase": [], "shuffled": []}
    heldout: Dict[str, List[float]] = {"neutral": [], "phase": [], "shuffled": []}
    for seed in SEEDS:
        shuffled = phase_gains[:]
        random.Random(seed * 7919).shuffle(shuffled)
        arms = {"neutral": [1.0] * (pairs * epochs), "phase": phase_gains, "shuffled": shuffled}
        for name, gains in arms.items():
            core = _downstream._train(gains, seed, task, epochs)
            rows[name].append(_downstream._evaluate(core, task, readout=readout))
            heldout[name].append(
                _downstream._evaluate(core, task, held, readout=readout)["hit_rate"]
            )

    gains = {
        "neutral": 1.0,
        "phase": statistics.fmean(phase_gains),
        "shuffled": statistics.fmean(phase_gains),
    }

    # 逐種子勝負：12 個種子的平均差可能是 7:5 也可能是 12:0，判詞本身看不出來。
    def wins(a: str, b: str, key: str) -> int:
        return sum(1 for x, y in zip(rows[a], rows[b]) if x[key] > y[key])

    seed_wins = {
        "seeds": len(SEEDS),
        "phase_over_neutral_margin": wins("phase", "neutral", "margin"),
        "phase_over_neutral_hit": wins("phase", "neutral", "hit_rate"),
        "phase_over_shuffled_margin": wins("phase", "shuffled", "margin"),
        "phase_over_shuffled_hit": wins("phase", "shuffled", "hit_rate"),
    }
    raw_verdict = (
        _downstream._verdict(rows)
        if abs(gains["phase"] - gains["neutral"]) <= 0.05
        else "gain-not-matched"
    )
    verdict, downgrade = _seed_robust(raw_verdict, seed_wins)
    matched = abs(gains["phase"] - gains["neutral"]) <= 0.05
    return {
        "family": family,
        "task": {key: value for key, value in task.items() if key != "threshold"},
        "epochs": epochs,
        "arms": {
            name: {
                "margin_mean": round(statistics.fmean(r["margin"] for r in rows[name]), 5),
                "hit_rate_mean": round(statistics.fmean(r["hit_rate"] for r in rows[name]), 3),
                # 逐種子離散度：同一題目的中性臂在 12 個評估種子上 0.299、在 8 個確認種子上
                # 0.406、在 3 個掃描種子上 0.306——不同種子組的均值差到 0.107。沒有這個數字，
                # 就分不出「這格真的有差」和「這一組種子剛好偏」。
                "hit_rate_sd": round(statistics.stdev(r["hit_rate"] for r in rows[name]), 3),
                "hit_rate_se": round(
                    statistics.stdev(r["hit_rate"] for r in rows[name]) / len(rows[name]) ** 0.5, 3
                ),
                "hit_rate_min": round(min(r["hit_rate"] for r in rows[name]), 3),
                "hit_rate_max": round(max(r["hit_rate"] for r in rows[name]), 3),
                "heldout_hit_rate_mean": round(statistics.fmean(heldout[name]), 3),
                "heldout_hit_rate_sd": round(statistics.stdev(heldout[name]), 3),
                "gain_mean": round(gains[name], 4),
            }
            for name in rows
        },
        "heldout_chance": round(1 / len(targets), 3),
        "heldout_at_chance": all(
            statistics.fmean(heldout[name]) <= 2 / len(targets) for name in heldout
        ),
        "gain_matched": bool(matched),
        "seed_wins": seed_wins,
        "raw_verdict": raw_verdict,
        "downgrade": downgrade,
        "verdict": verdict,
    }


NO_BENEFIT = (
    "no-downstream-difference",
    "margin-gain-without-hit-gain",
    "timing-does-not-matter-only-gain",
    "phase-loses-to-matched-mean",
)
HARM = "phase-loses-to-matched-mean"


def overall_verdict(cells: Sequence[Dict[str, object]]) -> str:
    informative = [cell for cell in cells if cell["informative"]]
    if len(informative) < 2:
        return "insufficient-informative-regimes"
    verdicts = [cell["cell"]["verdict"] for cell in informative]  # type: ignore[index]
    if all(v == "phase-beats-matched-mean" for v in verdicts):
        return "mechanism-benefit-consistent"
    if all(v == HARM for v in verdicts):
        # 一致的負結果也是一種結論；不能只因為方向是負的就退回「沒差」。
        return "mechanism-harm-consistent"
    if all(v in NO_BENEFIT for v in verdicts):
        return "no-mechanism-benefit-consistent"
    return "regime-dependent-no-claim"


def run(readout: Optional[str] = None) -> Dict[str, object]:
    cells: List[Dict[str, object]] = []
    for family in FAMILIES:
        # 每族只校準一次：step 與 lr 固定，epochs 這條軸才只改訓練量。
        calibration = calibrate_family(family, readout=readout)
        for epochs in EPOCHS_MATRIX:
            if not calibration["informative"]:
                cells.append(
                    {
                        "family": family,
                        "epochs": epochs,
                        "informative": False,
                        "reason": "ladder-exhausted",
                        "calibration": calibration,
                    }
                )
                continue
            cell = evaluate_cell(family, calibration, epochs, readout=readout)
            neutral_hit = float(cell["arms"]["neutral"]["hit_rate_mean"])  # type: ignore[index]
            in_range = HIT_RANGE[0] <= neutral_hit <= HIT_RANGE[1]
            margin = min(neutral_hit - HIT_RANGE[0], HIT_RANGE[1] - neutral_hit)
            cells.append(
                {
                    "family": family,
                    "epochs": epochs,
                    "informative": in_range,
                    "reason": None if in_range else "neutral-out-of-range",
                    "calibration": calibration,
                    "cell": cell,
                    "neutral_margin": round(margin, 3),
                    "thin_margin": in_range and margin < HIT_MARGIN,
                }
            )

    return {
        "protocol": PROTOCOL_VERSION,
        "readout": readout or READOUT,
        "epochs_matrix": list(EPOCHS_MATRIX),
        "lr_grid": list(LR_GRID),
        "hit_range": list(HIT_RANGE),
        "families": {name: steps for name, steps in FAMILIES.items()},
        "seeds": list(SEEDS),
        "cells": cells,
        "verdict": overall_verdict(cells),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path)
    # 讀出：預設仍是 ``potential``（16 步擴散，既有報告要能重現）。``direct`` 是一步
    # ``W · a``，不會被擴散壓平；切過去等於重新基線，所有格子都要重跑重報。
    ap.add_argument("--readout", choices=("potential", "direct"), default=READOUT)
    args = ap.parse_args(argv)

    result = run(readout=args.readout)
    print(f"protocol: {result['protocol']}  readout {result['readout']}")
    for cell in result["cells"]:  # type: ignore[union-attr]
        cal = cell["calibration"]
        if not cell["informative"]:
            if cell.get("reason") == "neutral-out-of-range":
                arms = cell["cell"]["arms"]  # type: ignore[index]
                print(
                    f"{cell['family']:<12} ep{cell['epochs']}: OUT OF RANGE "
                    f"(neutral top-1 {arms['neutral']['hit_rate_mean']}, "
                    f"step {cal['step']}, lr {cal['lr']})"
                )
                continue
            tops = ", ".join(
                f"{t.get('pairs')}p/{t.get('noise_bits')}b@{t['lr']}: "
                f"{t.get('neutral_hit_by_epoch')}"
                for t in cal["trials"][-3:]  # type: ignore[index]
            )
            print(f"{cell['family']:<12} ep{cell['epochs']}: UNINFORMATIVE (…{tops})")
            continue
        body = cell["cell"]
        arms = body["arms"]
        print(
            f"{cell['family']:<12} ep{cell['epochs']}: lr {body['task'].get('lr')} "
            f"neutral top-1 {cal['neutral_hit_by_epoch'].get(str(cell['epochs']))}  "
            f"N {arms['neutral']['margin_mean']:+.5f}/{arms['neutral']['hit_rate_mean']}  "
            f"P {arms['phase']['margin_mean']:+.5f}/{arms['phase']['hit_rate_mean']}  "
            f"S {arms['shuffled']['margin_mean']:+.5f}/{arms['shuffled']['hit_rate_mean']}  "
            f"| P>N {body['seed_wins']['phase_over_neutral_hit']}/{body['seed_wins']['seeds']} "
            f"P>S {body['seed_wins']['phase_over_shuffled_hit']}/{body['seed_wins']['seeds']}  "
            f"-> {body['verdict']}"
        )
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
