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
4. **種子**：40 個固定（v23 起；v16–v22 是 12 個）；校準掃描用 3 個、選中的候選再用 8 個
   確認（v10 起），三組**兩兩互斥**（v5 起互斥評估種子）。只有 3 個種子的掃描值會系統性偏樂觀
   （實測 +0.055），足以把貼邊的候選誤標成有餘裕；
5. **控制組**：``shuffled``——**同一組增益**打亂順序，分離「平均增益」與「時序」；
6. **判詞**：margin **與** top-1 必須同向；只升 margin 不算贏；
7. **種子穩健性**（v8 起）：``phase-beats-matched-mean``／``phase-loses-to-matched-mean``
   還要在**兩個比較**（對 neutral、對 shuffled）上至少 ``SIGN_TEST_MIN`` 個種子同向
   （40 個種子下是 26 個，單尾二項 p≈0.040），否則降級成
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
import math
import random
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "apps" / "backend" / "src"))

# 版本字串必須跟著量具改：v17 到 v20 的報告在自己的 JSON 裡都寫 v16（檔名是 v17…v20），
# 於是報告說不出自己是哪一版量具產生的。v21 起每次改量具都要同步這一條。
# v23 只改**解析度**，不改門檻：評估種子 12 → 40。理由在 ROADMAP §33 的結尾——12 個種子的
# `se` ≈ 0.03，而判詞要分辨 0.05 的餘裕，這個量具本來就分不出 0.299 與 0.30；逐種子 `sd`
# 0.08–0.12 正是「先調門檻再量」會繞不出去的迴圈。v23 不動 HIT_MARGIN、不動判詞門檻、不動
# 問題，只把同一批量測多跑 28 個種子（同一組固定質數，不是 1000+ 的流水號）。門檻
# `SIGN_TEST_MIN` 由 n 導出（40 → 26，單尾 p≈0.040），所以「多跑種子」不會悄悄放寬判詞。
# v24 新增一個**獨立**的探針（``strength_probe``），不改 12 格階梯的任何門檻與問題：階梯每筆
# 樣本都是 ``{key: 1.0}``，``gate`` 恆等於 1，所以 G1（定點 = target_strength·gate）在階梯上
# 結構上不可能量到——要有東西可量，輸入端必須真的帶強弱。探針預設不跑（``--strength-probe``），
# 因為它答的是另一個問題，不該改變既有報告的內容與成本。
PROTOCOL_VERSION = "al-downstream-v24"
READOUT = "potential"
# 可選的讀出。``direct`` 是 `garden_readout_variants` 裡已有的變體（一步 ``W·a``），不是這支
# 協定新發明的；它不飽和在擴散上，所以是「定點承載強弱，但讀不出」這個結論的對照。
# ``normalized`` 是 `garden_readout_variants._normalized`：每一列先歸一成對 target 的分佈，
# 所以對 cue 的出現頻率不敏感。它是「分級掉一半是頻率尺度、不是學錯」那個說法的直接檢定。
# ``spike_count`` 是**生產路徑**的讀出（`TensorSNNCore.forward`：累積脈衝數 ÷ timesteps）。
# 它原本不在這裡，於是「研究用 membrane potential、生產用 spike count」這兩個名字一直
# 被混著講：`garden_readout_variants` 的判詞（連續讀出在脈衝讀出失敗的閾值上排得出來）
# 因此從來沒有在生產讀出上量過。補進來之後，同一批權重可以三個讀出並排比較。
READOUTS = ("potential", "direct", "normalized", "spike_count")
EPOCHS_MATRIX = (1, 3, 5)
LR_GRID = (0.005, 0.008, 0.01, 0.015, 0.02, 0.03, 0.05)
HIT_RANGE = (0.30, 0.70)
# 校準沿著單調的難度軸「第一個合格就採用」，數學上必然停在邊界上：實測 ``many_to_one``
# 停在 0.306、``hard`` 停在 0.333，兩族都只有 0.006／0.033 的餘裕，比種子噪音還小，換一批
# 種子就掉出範圍（0.299）。所以校準改為優先選「每個 regime 都離上下界至少 0.05」的候選，
# 找不到才退回第一個合格者並標 ``centred: False``。這條餘裕規則是在看到 v8 的 0.299 之後
# 才加的——它會改變「用哪一題」，所以必須寫出來。
HIT_MARGIN = 0.05
# 相位臂均值與中性臂（1.0）的差：實測 3.7e-5，由「每 epoch 走完整週期」決定。這個容差不是控制，
# 只是防止排程被改壞；真正的匹配檢查是同一組增益與不同順序。
GAIN_MATCH_TOL = 0.01
# 40 個固定質數（v23）。刻意跳過 211–241 與 307–349：那是 CALIBRATION_SEEDS 與
# CONFIRMATION_SEEDS 的區間，三組必須兩兩互斥（下面的 assert 會擋）。
SEEDS = (
    11,
    23,
    37,
    41,
    53,
    67,
    79,
    83,
    97,
    101,
    113,
    127,
    131,
    137,
    139,
    149,
    151,
    157,
    163,
    167,
    173,
    179,
    181,
    191,
    193,
    197,
    199,
    251,
    257,
    263,
    269,
    271,
    277,
    281,
    283,
    293,
    401,
    409,
    419,
    421,
)
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
    # 衝突證據的任務族：cue 沒有專屬 token，每個 feature 都對多個 target 有邊。
    #
    # 更正（見 docs/06-project-management/AL_LADDER_ROADMAP.md §53）：這裡原本記「中性臂 ep1/3/5
    # 0.361／0.486／0.500、held-out 0.347／0.486／0.500、遷移與訓練同步」——那組數字是**支持
    # token 別名**的產物，不是中段：stride 寫死 3、`features=12` 時 target 0/4、1/5、2/6、3/7
    # 共用同一組支持 token，命中率卡在 0.5，held-out 也只是継承了同一組 token。修掉別名後，
    # 這一族在 lr 0.008 的中性臂是 0.391／0.406／0.443（真中段），而且 held-out 跟著訓練
    # 走（ep1/3/5 訓練 0.389／0.403／0.486、held-out 0.347／0.389／0.500，差 ≤0.042）——
    # 前提是 `_heldout_pairs` 也用同一個 stride（修一半時它留著 3，held-out 才會掉到 0.167）。
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


def _label_shuffle_baseline(
    family: str, seeds: Sequence[int], readout: Optional[str] = None, epochs: int = 3
) -> Dict[str, float]:
    """隨機標籤訓練：權重統計與真訓練相同，但配對是打亂的。

    這是「這台量具有在量學習嗎」的控制：把 pair 的 target 迴圈位移一位再訓練，若命中率仍落在
    中段，表示任務可靠輸入結構（共用 feature 的共現）解掉，跨臂比較量的就不是學習。若落到亂猜
    附近，表示命中率確實來自學到的 feature→label 對應。
    """
    task = dict(_downstream.TASKS[family])
    true_pairs = _downstream._pairs(task)
    targets = [t for _inputs, t in true_pairs]
    rotated = targets[1:] + targets[:1]
    pairs = [(inputs, label) for (inputs, _t), label in zip(true_pairs, rotated)]
    task = dict(task, pairs=len(pairs))
    hits = []
    heldout = []
    for seed in seeds:
        core = _downstream.TensorSNNCore(
            threshold=float(task["threshold"]), timesteps=_downstream._readouts.TIMESTEPS
        )
        rng = random.Random(seed)
        for _ in range(epochs):
            order = pairs[:]
            rng.shuffle(order)
            for inputs, label in order:
                core.hebbian_update(
                    {key: 1.0 for key in inputs},
                    {label: 1.0},
                    lr=float(task["lr"]),
                    target_strength=_downstream.TARGET_STRENGTH,
                    plasticity=1.0,
                )
        hits.append(
            _downstream._evaluate(core, task, pairs=true_pairs, readout=readout)["hit_rate"]
        )
        heldout.append(
            _downstream._evaluate(
                core, task, pairs=_downstream._heldout_pairs(task), readout=readout
            )["hit_rate"]
        )
    return {
        "train": round(statistics.fmean(hits), 3),
        "heldout": round(statistics.fmean(heldout), 3),
        "chance": round(1.0 / len(set(targets)), 3),
    }


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
    return {"informative": False, "reason": _exhaustion_reason(trials), "trials": trials}


def _exhaustion_reason(trials: Sequence[Dict[str, object]]) -> str:
    """校準找不到候選時，說清楚是「階梯不夠長」還是「這一族根本沒有中段」。

    原本一律寫 ``ladder-exhausted``，但這把兩件事混在一起：

    * ``task-at-ceiling``／``task-at-floor``：**每一級**在 ep1 就頂到 1.0（或塌到 0.0），
      再加階梯也沒用。``hard``／``easy`` 就是這種——每個 cue 都有專屬 token，一次 Hebbian
      就背起來，所以不存在中段。
    * ``ladder-exhausted``：至少有一級在 ep1 落在中段，但撐不到 ep3/ep5（``structured``
      的 lr 0.01 是 ep1/ep3 都 0.583、ep5 升到 0.806）。這種才是可以靠加級數處理的。

    判定只看**第一個量到的 epoch**：``_measure`` 一旦跑出範圍就停，後面的格本來就沒量。

    鍵在記憶體裡是 int、在 JSON 裡是 str（第一次改完就是這樣把 ``hard`` 誤報成
    ``ladder-exhausted``：拿字串鍵去讀 int 鍵，讀不到就退回預設理由）。兩者都接受。
    """
    first_epoch = EPOCHS_MATRIX[0]
    first_hits = [
        float(hits[first_epoch] if first_epoch in hits else hits[str(first_epoch)])  # type: ignore[index]
        for hits in (t["neutral_hit_by_epoch"] for t in trials)  # type: ignore[union-attr]
        if first_epoch in hits or str(first_epoch) in hits
    ]
    if not first_hits:
        return "ladder-exhausted"
    if all(hit >= HIT_RANGE[1] for hit in first_hits):
        return "task-at-ceiling"
    if all(hit <= HIT_RANGE[0] for hit in first_hits):
        return "task-at-floor"
    return "ladder-exhausted"


def _sign_test_minimum(seeds: int, alpha: float = 0.05) -> int:
    """單尾二項檢定：n 個種子至少要幾個同向，才算不是擲硬幣。

    門檻一律由 n 導出，不寫死：P(X>=9|12,0.5)=0.073、P(X>=10|12,0.5)=0.019，所以 n=12 是 10；
    P(X>=25|40,0.5)=0.077、P(X>=26|40,0.5)=0.040，所以 n=40 是 26。加種子而門檻不動，判詞會變鬆。
    """
    from math import comb

    for need in range(seeds // 2, seeds + 1):
        tail = sum(comb(seeds, k) for k in range(need, seeds + 1)) / 2**seeds
        if tail <= alpha:
            return need
    return seeds


SIGN_TEST_MIN = _sign_test_minimum(len(SEEDS))


def _gains_matched(
    phase_gains: Sequence[float], shuffled_gains: Sequence[float], neutral_gain: float = 1.0
) -> Dict[str, object]:
    """增益匹配要檢查「分佈」，不是「均值」。

    排程每個 epoch 剛好走完一個週期，所以相位臂均值實測 1.0000369（差 3.7e-5），任何 0.01 以上
    的均值容差**都不可能失敗**——一個不可能失敗的閘門不是控制。真正有力量的是：打亂臂與相位臂
    有同一組增益（打亂只換順序）、且順序確實不同（否則 shuffled 只是 phase 的複本）。相位臂的
    散佈（0.4–1.6）本身也是混淆：對 ``neutral`` 的比較同時混了「時序」與「每步增益有大小」，
    只有對 ``shuffled`` 才隔離時序。
    """
    mean_delta = statistics.fmean(phase_gains) - neutral_gain
    return {
        "mean_delta": round(mean_delta, 6),
        "phase_gain_sd": round(statistics.pstdev(phase_gains), 4),
        "phase_gain_min": round(min(phase_gains), 4),
        "phase_gain_max": round(max(phase_gains), 4),
        # 打亂臂必須是同一組增益的**不同順序**：同分佈（否則兩臂的「量」不同）且順序不同
        # （否則 shuffled 只是 phase 的複本，兩臂比較等於自己比自己）。
        "multiset_match": sorted(phase_gains) == sorted(shuffled_gains),
        "order_differs": list(phase_gains) != list(shuffled_gains),
    }


def _paired_stats(
    rows: Dict[str, List[Dict[str, float]]], a: str, b: str, key: str
) -> Dict[str, float]:
    """配對差：同一個種子上的 a − b。只有配對才看得出「差多少」，逐種子勝負只看方向。"""
    diffs = [x[key] - y[key] for x, y in zip(rows[a], rows[b])]
    mean = statistics.fmean(diffs)
    sd = statistics.stdev(diffs) if len(diffs) > 1 else 0.0
    se = sd / len(diffs) ** 0.5 if diffs else 0.0
    return {
        "mean": round(mean, 5),
        "sd": round(sd, 5),
        "se": round(se, 5),
        "ci95_half_width": round(1.96 * se, 5),
        "wins": sum(1 for d in diffs if d > 0),
        "n": len(diffs),
    }


def _min_detectable_delta(sigma: float, n: int, need: int, power: float = 0.8) -> float | None:
    """符號檢定在 n 個種子、σ 這個散佈下，能偵測到的最小差（power 0.8）。

    「沒有差別」不等於「差別是 0」：``SIGN_TEST_MIN`` 要求 n 個種子裡至少 ``need`` 個同向，
    而每個種子「同向」的機率是 Φ(δ/σ)。所以要在觀測到的 σ 上算出這個門檻能達到的最小 δ——
    低於它的效果本來就偵測不到，判詞不該假裝分辨得出來。
    """
    if sigma <= 0 or n <= 0:
        return None

    def hit_prob(mu: float) -> float:
        p = 0.5 * (1.0 + math.erf((mu / sigma) / math.sqrt(2.0)))
        return sum(math.comb(n, k) * p**k * (1 - p) ** (n - k) for k in range(need, n + 1))

    lo, hi = 0.0, 4.0 * sigma
    if hit_prob(hi) < power:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if hit_prob(mid) < power:
            lo = mid
        else:
            hi = mid
    return round(hi, 3)


def _seed_robust(verdict: str, seed_wins: Dict[str, int]) -> Tuple[str, str | None]:
    """平均差要在種子上站得住，才算機制有效（或有害）。

    均值差 0.05 可能來自 12:0，也可能是 7:5；後者不是「時序有用」，只是擲硬幣。
    所以 ``phase-beats-matched-mean`` 與 ``phase-loses-to-matched-mean`` 都要求在
    兩個比較上至少 ``_sign_test_minimum(n)`` 個種子同向，否則降級。

    門檻不能是常數：把種子從 12 加到 40 卻仍要求 10 個同向，判詞會變鬆。
    """
    seeds = seed_wins["seeds"]
    need = _sign_test_minimum(int(seeds))
    over_neutral = seed_wins["phase_over_neutral_hit"]
    over_shuffled = seed_wins["phase_over_shuffled_hit"]
    if verdict == "phase-beats-matched-mean":
        if min(over_neutral, over_shuffled) >= need:
            return verdict, None
        return "timing-does-not-matter-only-gain", (
            f"seed-robustness failed: phase>neutral {over_neutral}/{seeds}, "
            f"phase>shuffled {over_shuffled}/{seeds}, need {need}/{seeds}"
        )
    if verdict == HARM:
        under_neutral = seeds - over_neutral
        under_shuffled = seeds - over_shuffled
        if min(under_neutral, under_shuffled) >= need:
            return verdict, None
        return "no-downstream-difference", (
            f"harm not seed-robust: phase<neutral {under_neutral}/{seeds}, "
            f"phase<shuffled {under_shuffled}/{seeds}, need {need}/{seeds}"
        )
    return verdict, None


def evaluate_cell(
    family: str,
    calibration: Dict[str, object],
    epochs: int,
    readout: Optional[str] = None,
    seeds: Optional[Sequence[int]] = None,
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
    seeds = tuple(seeds) if seeds else SEEDS
    need = _sign_test_minimum(len(seeds))
    for seed in seeds:
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

    # 逐種子勝負：均值差可能是 7:5 也可能是 12:0，判詞本身看不出來。
    def wins(a: str, b: str, key: str) -> int:
        return sum(1 for x, y in zip(rows[a], rows[b]) if x[key] > y[key])

    seed_wins = {
        "seeds": len(seeds),
        "sign_test_min": need,
        "phase_over_neutral_margin": wins("phase", "neutral", "margin"),
        "phase_over_neutral_hit": wins("phase", "neutral", "hit_rate"),
        "phase_over_shuffled_margin": wins("phase", "shuffled", "margin"),
        "phase_over_shuffled_hit": wins("phase", "shuffled", "hit_rate"),
    }
    paired = {
        f"phase_vs_{other}_hit": _paired_stats(rows, "phase", other, "hit_rate")
        for other in ("neutral", "shuffled")
    }
    for other in ("neutral", "shuffled"):
        paired[f"phase_vs_{other}_margin"] = _paired_stats(rows, "phase", other, "margin")
    # 這台量具在這個格子上能分辨多小的差：σ 來自配對差的散佈。
    mde = _min_detectable_delta(paired["phase_vs_neutral_hit"]["sd"], len(seeds), need)
    # 判詞的 margin 尺度：``gain`` 對 ``pstdev(neutral margins)``。這個尺度把「種子難度」也
    # 算進雜訊（未配對），而且沒有除以 √n，所以它比配對差的標準誤大很多倍——差多少倍會隨
    # 族而變（conflict 的種子難度變異大、m2o 幾乎沒有），於是「同一個門檻」在不同格上其實
    # 鬆緊不同。把兩個尺度都寫出來，讓判詞可以被重算。
    neutral_margins = [row["margin"] for row in rows["neutral"]]
    paired_margin = paired["phase_vs_neutral_margin"]
    margin_gate = {
        "yardstick": round(statistics.pstdev(neutral_margins), 6),
        "gain": round(paired_margin["mean"], 6),
        "paired_sd": paired_margin["sd"],
        "paired_se": paired_margin["se"],
        "gain_over_se": (
            round(abs(paired_margin["mean"]) / paired_margin["se"], 2)
            if paired_margin["se"]
            else None
        ),
        # 門檻要求 |gain| > yardstick；換成「幾個配對標準誤」才看得出它多嚴。
        "yardstick_over_se": (
            round(statistics.pstdev(neutral_margins) / paired_margin["se"], 2)
            if paired_margin["se"]
            else None
        ),
    }
    # 「held-out 在亂猜」原本用 ``2 / len(targets)``：係數 2 沒有來源，也不看 held-out 有幾條。
    # 改成二項散佈上界 ``p + 2·√(p(1−p)/m)``（m = held-out pair 數）：m 越大，允許的超出越小。
    chance = 1 / len(targets)
    chance_upper = chance + 2 * math.sqrt(chance * (1 - chance) / len(held))

    # 增益匹配：均值容差不可能失敗（排程恰好走完整週期），所以真正有力量的是分佈與順序。
    match = _gains_matched(phase_gains, shuffled)
    matched = (
        bool(match["multiset_match"])
        and bool(match["order_differs"])
        and abs(float(match["mean_delta"])) <= GAIN_MATCH_TOL
    )
    raw_verdict = _downstream._verdict(rows, need=need) if matched else "gain-not-matched"
    verdict, downgrade = _seed_robust(raw_verdict, seed_wins)

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
        "heldout_chance": round(chance, 3),
        "heldout_chance_upper": round(chance_upper, 3),
        "heldout_pairs": len(held),
        "heldout_at_chance": all(
            statistics.fmean(heldout[name]) <= chance_upper for name in heldout
        ),
        "heldout_at_chance_by_arm": {
            name: statistics.fmean(heldout[name]) <= chance_upper for name in heldout
        },
        "gain_matched": bool(matched),
        "gain_match": match,
        "margin_gate": margin_gate,
        "seed_wins": seed_wins,
        "paired": paired,
        "detectable_hit_delta": mde,
        "raw_verdict": raw_verdict,
        "downgrade": downgrade,
        "verdict": verdict,
    }


# ---------------------------------------------------------------------------
# G1 的下游探針：強弱進到權重裡之後，讀出有沒有看見？
# ---------------------------------------------------------------------------
# WHY 這一段不在 12 格階梯裡：階梯量的是「時機」（phase vs shuffled），而它每一筆樣本都是
# `{key: 1.0}` / `{label: 1.0}`，`gate` 恆等於 1，所以 G1（定點 = target_strength·gate）在階梯上
# **結構上不可能**有任何效果——不管規則怎麼改，每個配對都停在同一個 0.35。這是上一輪
# (G1) 修正的限制，寫在 CHANGELOG 但沒有量具。要讓「強弱」有東西可量，輸入端必須真的帶強弱。
#
# 這裡用「出現次數」當強弱來源（真實語料的共現頻率就是這樣分佈的：常見關聯多次、罕見一次），
# 四個臂**共用同一條訓練流**（同樣的配對、同樣的順序、同樣的長度），只改信心怎麼進
# ``hebbian_update``：
#   flat    信心 1.0、plasticity 1.0         —— 舊規則的輸入（定點人人相同）
#   graded  信心 = tier/3、plasticity 1.0    —— G1：強弱進到**定點**
#   matched 同一組信心打散到別的樣本上        —— 控制：信心分佈相同、對應關係毁掉
#   speed   信心 1.0、plasticity = tier/3    —— 舊語意：強弱只當**速率**
# 判準只比 ``graded`` 與 ``matched``：前者測「對應關係」，後者測「剛好有些信心值比較小」。
STRENGTH_TIERS = (1, 3)
STRENGTH_EPOCHS = 3
STRENGTH_TIER_SEED = 20261110  # 固定：哪個配對屬於哪一層不能隨評估種子改
# 收斂區要另一批設定：ep3 的權重離定點還很遠（實測強層 0.065，收斂後 0.22），那個區域量到的
# 是累積速率—四個臂拉的節點都在同一個量級，「定點帶強弱」與「速率帶強弱」分不開。只有接近
# 定點才分得開，所以收斂區單獨一跑，且只需要前 12 個種子（每一下都貴 13 倍）。
STRENGTH_EQUILIBRIUM_EPOCHS = 40
STRENGTH_EQUILIBRIUM_SEEDS = 12
# 收斂區的判準：graded 的「弱/強 權重比」必須比 flat 低至少這麼多。實測 flat 0.84、speed 0.62、
# graded 0.41，所以 0.15 的分界落在「速率造成的差」與「定點造成的差」之間。
STRENGTH_MIN_RATIO_DROP = 0.15
# 權重要算得上「照 tier 排序」：Spearman 中位以上、且兩層平均差至少 0.02（實測 flat 的兩層差
# 來自 decay 不平衡，量級 0.005–0.02，所以門檻必須高於它才分得開「定點真的有差」）。
STRENGTH_MIN_SPEARMAN = 0.5
STRENGTH_MIN_GAP = 0.02


def _ranks(values: Sequence[float]) -> List[float]:
    """平均名次（同分共用名次），給 Spearman 用；不引進 scipy。"""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        shared = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = shared
        i = j + 1
    return ranks


def _spearman(xs: Sequence[float], ys: Sequence[float]) -> Optional[float]:
    """秩相關；任一側完全沒有散佈時回 ``None``（同分全平不是「完美相關」）。"""
    if len(xs) != len(ys) or len(xs) < 3:
        return None
    rx, ry = _ranks(xs), _ranks(ys)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else None


def _pair_weight(core: object, inputs: Sequence[str], target: str) -> Optional[float]:
    """這個配對在權重矩陣上的平均權重（cue token → target）。"""
    idx = getattr(core, "_key_to_idx", {})
    matrix = getattr(core, "_W", None)
    j = idx.get(target)
    if matrix is None or j is None:
        return None
    values = []
    for key in inputs:
        i = idx.get(key)
        if i is None:
            continue
        cell = matrix[i, j]
        values.append(float(cell.item() if hasattr(cell, "item") else cell))
    return statistics.fmean(values) if values else None


def _attribution(pairs: Sequence[Tuple[List[str], str]], tiers: Sequence[int]) -> Dict[str, object]:
    """這個族的權重比量具到底在讀誰的格子（純設計量，不訓練）。

    WHY 需要這一格：``_pair_weight`` 讀的是 (cue token → target) 的**平均權重**，並把它當成「這個
    配對的權重」。但那只在某個格子只被一個配對寫過時才成立。`conflict` 是 96 個 cue 共用 8 個
    target、每個 target 被 6 強 + 6 弱寫入，於是每一個格子平均有 10.4 個寫入者、95% 的格子混了
    兩個 tier——讀出來的比例必然趨近 1，跟 G1 學到什麼無關。把那種數字叫 ``fixed-point-inert``
    是對模型的宣稱，而量具根本分不出「不帶強弱」與「十個寫入者被平均掉」。

    所以判詞從此要帶著這個比例一起講：只有 ``single_tier_fraction == 1.0`` 時，比值才能不帶註記。
    """
    writers: Dict[Tuple[str, str], Dict[int, int]] = {}
    for (inputs, target), tier in zip(pairs, tiers):
        for token in inputs:
            cell = writers.setdefault((token, target), {})
            cell[tier] = cell.get(tier, 0) + 1
    reads = 0
    single = 0
    total_writers = 0
    for (inputs, target), _tier in zip(pairs, tiers):
        for token in inputs:
            cell = writers[(token, target)]
            reads += 1
            total_writers += sum(cell.values())
            if len(cell) == 1:
                single += 1
    return {
        "reads": reads,
        "single_tier_fraction": round(single / reads, 3) if reads else 0.0,
        "writers_per_cell": round(total_writers / reads, 2) if reads else 0.0,
    }


def _caveated(verdict: str, attribution: Dict[str, object]) -> str:
    """判詞帶著量具的污染度：分不出乾淨與混合的族，就不准講成乾淨的結論。"""
    fraction = float(attribution["single_tier_fraction"])  # type: ignore[arg-type]
    if fraction >= 1.0:
        return verdict
    return f"{verdict} (cells-shared {fraction:g})"


def _tier_of_pairs(pairs: Sequence[Tuple[List[str], str]]) -> List[int]:
    """把配對分層：一半強（tier 3）、一半弱（tier 1），用固定種子打散，不跟 target 分組共振。"""
    count = len(pairs)
    strong = set(random.Random(STRENGTH_TIER_SEED).sample(range(count), count // 2))
    return [STRENGTH_TIERS[1] if i in strong else STRENGTH_TIERS[0] for i in range(count)]


def _strength_stream(
    pairs: Sequence[Tuple[List[str], str]], tiers: Sequence[int], seed: int, epochs: int
) -> List[int]:
    """訓練流：每個配對按 tier 重複，逐 epoch 打亂；回傳的每一項是配對索引。"""
    stream = [i for i, tier in enumerate(tiers) for _ in range(tier)]
    rng = random.Random(seed * 6151 + 17)
    out: List[int] = []
    for _ in range(epochs):
        order = stream[:]
        rng.shuffle(order)
        out.extend(order)
    return out


def _rank_credit(out: Dict[str, float], targets: Sequence[str], target: str) -> float:
    """正確 target 名次的信用（reciprocal rank）：第 1 名 1.0、第 2 名 0.5、第 3 名 0.33……

    WHY 需要第三種指標：§46–§48 試過的三種讀出都只看勝負或絕對尺度——top-1 把「差一點」
    與「完全沒有」算成一樣（`conflict` 的 0.420 對隨機 0.125 明明活著，卻說不出好壞），而
    `margin` 是「與最強對手的分數差」，換讀出就換尺度，且它與 top-1 會給相反答案。名次對
    尺度不變、且保留「差一點」與「差很多」的差別，所以它是唯一能回答「強弱有沒有被放到
    正確的關聯上、只是不夠強」的既有量具。

    並列時算贏過我們（保守）：只在嚴格大於時才降名次，免得並列被當成證據。
    """
    correct = out.get(target)
    if correct is None:
        return 0.0
    # ``>=``：並列要算贏過我們，否則「什麼都沒學到、全部打平」會被讀成完美的第 1 名。
    better = sum(
        1
        for label in targets
        if label != target and out.get(label) is not None and float(out[label]) >= float(correct)
    )
    return 1.0 / (1.0 + better)


def _rank_credit_mean(
    core: Any,
    pairs: Sequence[Tuple[List[str], str]],
    targets: Sequence[str],
    tiers: Optional[Sequence[int]] = None,
    readout: Optional[str] = None,
) -> Dict[str, float]:
    """名次信用，**按層分開**（與 `_evaluate` 同一批配對、同一個讀出）。

    WHY 不能只看全體平均：``graded`` 的設計就是讓弱層的權重比強層小，所以把兩層平均起來
    等於用「有沒有把弱層當強層」去評分——那會讓 ``graded`` 看起來比把一切都當一樣的
    ``flat`` 差。實測 `conflict` 在 ``normalized``、ep40：全體平均 graded 0.679 對 matched
    0.744（40/0 種子都像「graded 較差」），而那個差全部來自被刻意壓低的弱層。這裡跟 §50
    同型：量具只能在它的前提成立的那一層講話，所以判詞只看強層。
    """
    use_readout = readout or READOUT
    per_tier: Dict[int, List[float]] = {}
    credits: List[float] = []
    for index, (inputs, target) in enumerate(pairs):
        out = _downstream._readouts._forward(core, {key: 1.0 for key in inputs}, use_readout)
        credit = _rank_credit(out, targets, target)
        credits.append(credit)
        if tiers is not None:
            per_tier.setdefault(int(tiers[index]), []).append(credit)
    strong = per_tier.get(max(STRENGTH_TIERS), [])
    weak = per_tier.get(min(STRENGTH_TIERS), [])
    return {
        "all": statistics.fmean(credits) if credits else 0.0,
        "strong": statistics.fmean(strong) if strong else 0.0,
        "weak": statistics.fmean(weak) if weak else 0.0,
    }


def _hit_rates_by_tier(
    core: Any,
    pairs: Sequence[Tuple[List[str], str]],
    targets: Sequence[str],
    tiers: Sequence[int],
    readout: Optional[str] = None,
) -> Dict[str, float]:
    """把命中率**按層拆開**：弱層是「學得慢」還是「永遠贏不了」，全體平均分不出來。

    WHY 非拆不可：``graded`` 的弱層定點本來就低（``0.35×conf``），所以全體命中率同時混著
    「弱層那一半掉了多少」與「強層有沒有被拖累」兩件事。實測 `many_to_one`（lr 0.005、
    40 種子、``direct``）``graded`` 全體 0.514 對 ``flat`` 0.698——那個 0.514 可能是弱層
    全輸，也可能是兩層各退一點，而這兩種解釋要的修法完全不同（前者要改終點，後者要改
    訓練量）。

    與 `_rank_credit_mean` 同一批配對、同一個讀出、同一種分層，只是把「第幾名」換成
    「有沒有贏」，所以兩者的分層可以直接對照。
    """
    use_readout = readout or READOUT
    per_tier: Dict[int, List[int]] = {}
    hits = 0
    for index, (inputs, target) in enumerate(pairs):
        out = _downstream._readouts._forward(core, {key: 1.0 for key in inputs}, use_readout)
        _, hit = _downstream._score(out, targets, target)
        hits += int(hit)
        per_tier.setdefault(int(tiers[index]), []).append(int(hit))
    strong = per_tier.get(max(STRENGTH_TIERS), [])
    weak = per_tier.get(min(STRENGTH_TIERS), [])
    return {
        "hit_rate": hits / len(pairs) if pairs else 0.0,
        "hit_strong": statistics.fmean(strong) if strong else 0.0,
        "hit_weak": statistics.fmean(weak) if weak else 0.0,
    }


def _run_strength_arm(
    task: Dict[str, object],
    pairs: Sequence[Tuple[List[str], str]],
    tiers: Sequence[int],
    stream: Sequence[int],
    confidences: Sequence[float],
    seed: int,
    arm: str,
    readout: str = READOUT,
) -> Dict[str, float]:
    """同一條流、同一個種子，只改信心與 plasticity 怎麼進來。

    ``readout`` 決定這批權重要怎麼讀：``potential``（16 步擴散，會把連通分量填平）或
    ``direct``（一步 ``W·a``，只吃直接關聯，不飽和在擴散上）。同一批權重、不同讀出，
    就是「塌的是讀出還是學到的東西」那個問題。
    """
    core = _downstream.TensorSNNCore(
        threshold=float(task["threshold"]),  # type: ignore[arg-type]
        timesteps=_downstream._readouts.TIMESTEPS,
    )
    top = float(max(STRENGTH_TIERS))
    for pair_index, conf in zip(stream, confidences):
        inputs, target = pairs[pair_index]
        tier = tiers[pair_index]
        graded = tier / top
        # 信心只放一側（target）：`_hebbian_patch` 的 gate 是**兩側**信心的乘積，兩邊都放
        # 等於把同一個信心算兩次（gate = conf²、定點 0.35·conf² = 1/9），而 `speed` 臂只放
        # 一次（plasticity = conf、gate = 1）。兩個臂要分的是「強弱住在終點還是速率」，
        # 注入量不同就混進第三個變因，所以先把它對齊。
        #
        # 對齊之後（20 種子、direct、`many_to_one` lr 0.005、命中率按層拆開）：ep1 兩臂每一層
        # 都相同到三位小數（0.648／0.036）——注入速率確實一樣了，分歧從 ep3 才開始，因為終點
        # 一個是 0.35、一個是 0.35·c。`graded` 的弱層因此有兩件事同時成立：ep1–ep10 停在亂猜
        # （0.029–0.040，亂猜 1/24 = 0.042），ep10–ep40 才爬到 0.398；`speed` 走同一條流是
        # 0.036 → 0.173 → 0.329 → 0.983（flat 1.000）。算術上未飽和時增量 ∝ c²（速率與終點
        # 各帶一次 conf）對 ∝ c，所以弱層權重固定是 1 : 3 : 9（graded : speed : flat），棘輪
        # `TestGradedWeakTierAccumulatesAtConfSquared` 釘住這個比值。
        core.hebbian_update(
            {key: 1.0 for key in inputs},
            {target: (conf if arm in ("graded", "matched") else 1.0)},
            lr=float(task["lr"]),  # type: ignore[arg-type]
            target_strength=_downstream.TARGET_STRENGTH,
            plasticity=(graded if arm == "speed" else 1.0),
        )
    weights = [_pair_weight(core, inputs, target) for inputs, target in pairs]
    usable = [(t, w) for t, w in zip(tiers, weights) if w is not None]
    strong = [w for t, w in usable if t == STRENGTH_TIERS[1]]
    weak = [w for t, w in usable if t == STRENGTH_TIERS[0]]
    rho = _spearman([float(t) for t, _ in usable], [float(w) for _, w in usable])
    evaluated = _downstream._evaluate(
        core, dict(task, pairs=len(pairs)), pairs=pairs, readout=readout
    )
    tiered = _hit_rates_by_tier(
        core, pairs, _downstream._candidate_targets(pairs), tiers, readout=readout
    )
    rank_credit = _rank_credit_mean(
        core, pairs, _downstream._candidate_targets(pairs), tiers=tiers, readout=readout
    )
    return {
        "readout": readout,
        "spearman": round(rho, 3) if rho is not None else None,
        "tier_gap": (
            round(statistics.fmean(strong) - statistics.fmean(weak), 5) if strong and weak else 0.0
        ),
        "weight_strong": round(statistics.fmean(strong), 5) if strong else 0.0,
        "weight_weak": round(statistics.fmean(weak), 5) if weak else 0.0,
        "distinct_levels": len({round(w, 3) for _, w in usable}),
        "hit_rate": round(evaluated["hit_rate"], 3),
        # 同一次訓練、同一批配對，只是把命中率按層拆開（見 `_hit_rates_by_tier`）。
        "hit_strong": round(tiered["hit_strong"], 3),
        "hit_weak": round(tiered["hit_weak"], 3),
        "margin": round(evaluated["margin"], 5),
        "rank_credit": round(rank_credit["all"], 5),
        # 判詞只看強層：那裡才是「強弱沒有綁在對的關聯上」這個宣稱的適用範圍。
        "rank_credit_strong": round(rank_credit["strong"], 5),
        "rank_credit_weak": round(rank_credit["weak"], 5),
    }


def strength_probe(
    family: str,
    calibration: Dict[str, object],
    readout: Optional[str] = None,
    seeds: Optional[Sequence[int]] = None,
    epochs: int = STRENGTH_EPOCHS,
) -> Dict[str, object]:
    """強弱（出現次數）有沒有進到權重，以及讀出看不看得見。

    四個臂共用同一條訓練流與同一個種子，所以任何差異都只能來自「信心怎麼進 update」。

    ``readout`` 不固定成 ``potential``：v24 量到的兩難就是「讀出有訊號的區域還沒走到定點、
    定點看得見的區域讀出已經飽和」，所以讀出本身就是待測變因之一——換讀出要能改變結論，
    否則「讀出飽和」只是猜測。預設仍舊是 ``potential``。
    """
    use_readout = readout or READOUT
    assert use_readout in READOUTS, f"unknown readout {use_readout!r}"
    task = _task(family, calibration["step"], float(calibration["lr"]))  # type: ignore[arg-type]
    pairs = _downstream._pairs(task)
    tiers = _tier_of_pairs(pairs)
    use_seeds = tuple(seeds) if seeds else SEEDS
    arms = ("flat", "graded", "matched", "speed")
    rows: Dict[str, List[Dict[str, float]]] = {name: [] for name in arms}
    for seed in use_seeds:
        stream = _strength_stream(pairs, tiers, seed, epochs)
        graded_conf = tuple(tiers[i] / float(max(STRENGTH_TIERS)) for i in stream)
        matched_conf = list(graded_conf)
        random.Random(seed * 104729 + 7).shuffle(matched_conf)
        confidences = {
            "flat": [1.0] * len(stream),
            "graded": list(graded_conf),
            "matched": matched_conf,
            "speed": [1.0] * len(stream),
        }
        for arm in arms:
            rows[arm].append(
                _run_strength_arm(
                    task, pairs, tiers, stream, confidences[arm], seed, arm, readout=use_readout
                )
            )

    need = _sign_test_minimum(len(use_seeds))
    gaps = {arm: [row["tier_gap"] for row in rows[arm]] for arm in arms}
    ordered = sum(1 for a, b in zip(gaps["graded"], gaps["matched"]) if a > b)
    attribution = _attribution(pairs, tiers)
    hits_better = sum(
        1 for a, b in zip(rows["graded"], rows["matched"]) if a["hit_rate"] > b["hit_rate"]
    )
    hits_worse = sum(
        1 for a, b in zip(rows["graded"], rows["matched"]) if a["hit_rate"] < b["hit_rate"]
    )
    summary = {
        arm: {
            "spearman_mean": (
                round(
                    statistics.fmean(r["spearman"] for r in rows[arm] if r["spearman"] is not None),
                    3,
                )
                if any(r["spearman"] is not None for r in rows[arm])
                else None
            ),
            "tier_gap_mean": round(statistics.fmean(gaps[arm]), 5),
            "tier_gap_sd": round(statistics.stdev(gaps[arm]), 5) if len(gaps[arm]) > 1 else 0.0,
            "weight_strong_mean": round(statistics.fmean(r["weight_strong"] for r in rows[arm]), 5),
            "weight_weak_mean": round(statistics.fmean(r["weight_weak"] for r in rows[arm]), 5),
            "distinct_levels_min": min(int(r["distinct_levels"]) for r in rows[arm]),
            "hit_rate_mean": round(statistics.fmean(r["hit_rate"] for r in rows[arm]), 3),
            "margin_mean": round(statistics.fmean(r["margin"] for r in rows[arm]), 5),
            "rank_credit_mean": round(statistics.fmean(r["rank_credit"] for r in rows[arm]), 4),
            "rank_credit_strong_mean": round(
                statistics.fmean(r["rank_credit_strong"] for r in rows[arm]), 4
            ),
            "rank_credit_weak_mean": round(
                statistics.fmean(r["rank_credit_weak"] for r in rows[arm]), 4
            ),
        }
        for arm in arms
    }
    graded = summary["graded"]
    ordering = (
        "ordering-carries-across-tiers"
        if (
            (graded["spearman_mean"] or 0.0) >= STRENGTH_MIN_SPEARMAN
            and graded["tier_gap_mean"] >= STRENGTH_MIN_GAP
            and ordered >= need
        )
        else "ordering-not-separated-from-distribution"
    )
    readout = _readout_verdict(hits_better, hits_worse, need)
    # 判詞的比較對象是**強層**信用：平均會懲罰分級本身（見 ``_rank_credit_mean``），
    # 而宣稱是「強弱綁在對的關聯上」，所以要看強層有沒有排前面。
    rank_better = sum(
        1
        for a, b in zip(rows["graded"], rows["matched"])
        if a["rank_credit_strong"] > b["rank_credit_strong"]
    )
    rank_worse = sum(
        1
        for a, b in zip(rows["graded"], rows["matched"])
        if a["rank_credit_strong"] < b["rank_credit_strong"]
    )
    # ``matched`` 這個控制臂還有效嗎？它把 tier 與信心的綁定打散，而更新規則是「拉向
    # ``target_strength × gate``（gate＝兩個信心的乘積）」，所以它只會把每條配對的終點抹平——
    # 行為上很接近另一個 ``flat``。實測 `conflict`/`direct`/ep40（40 種子）：`matched` 對 `flat`
    # 命中 10/13（門檻 26，無差），而 `graded` 對 `flat` 命中 1/29、名次 0/40、margin 0/40
    # （全顯著）。也就是說「輸給打散控制臂」跟「輸給均勻權重」是同一件事，不能拿前者當獨立證據。
    # 所以這裡多存一組不依賴 `matched` 的比較，讓判詞可以兩個控制臂都報。
    flat_better = sum(
        1 for a, b in zip(rows["graded"], rows["flat"]) if a["hit_rate"] > b["hit_rate"]
    )
    flat_worse = sum(
        1 for a, b in zip(rows["graded"], rows["flat"]) if a["hit_rate"] < b["hit_rate"]
    )
    control_better = sum(
        1 for a, b in zip(rows["matched"], rows["flat"]) if a["hit_rate"] > b["hit_rate"]
    )
    control_worse = sum(
        1 for a, b in zip(rows["matched"], rows["flat"]) if a["hit_rate"] < b["hit_rate"]
    )
    return {
        "family": family,
        "epochs": epochs,
        "readout": use_readout,
        # 任務參數要跟著讀出一起記：換讀出必須重跑校準，而校準會挑不同的 ``lr``／``step``。
        # 少了這兩個數字，「讀出差異」會偷偷混到「任務參數差異」裡。
        "lr": round(float(task["lr"]), 4),  # type: ignore[arg-type]
        "stream_length": len(_strength_stream(pairs, tiers, 11, epochs)),
        "pairs": len(pairs),
        "tiers": {str(t): tiers.count(t) for t in sorted(set(tiers))},
        "attribution": _attribution(pairs, tiers),
        "seeds": len(use_seeds),
        "sign_test_min": need,
        "arms": summary,
        "graded_over_matched_tier_gap": ordered,
        "graded_over_matched_hit": hits_better,
        "graded_under_matched_hit": hits_worse,
        # 排序判詞也建在 ``_pair_weight`` 上，所以同樣要帶著污染度；命中率的那一句不必（它不讀格子）。
        "ordering_verdict": _caveated(ordering, attribution),
        "readout_verdict": readout,
        # 名次信用對尺度不變、也不讀格子，所以它跟「讀出看不看得見」是**不同的問題**：
        # ``readout_verdict`` 問「graded 有沒有比控制臂多命中」，這裡問「正確 target 是不是
        # 排得更前」——後者就是 §48 說「三種讀出都回答不了」的那個問題。
        "rank_verdict": _rank_verdict(
            rank_better,
            rank_worse,
            need,
            _rank_interpretable(
                float(graded["hit_rate_mean"]), float(summary["matched"]["hit_rate_mean"])
            ),
        ),
        "graded_over_matched_rank": rank_better,
        "graded_under_matched_rank": rank_worse,
        # 第二條控制比較（不依賴 `matched`）：分級對「均勻權重」的淨值。
        "contrast_verdict": _readout_verdict(flat_better, flat_worse, need),
        "graded_over_flat_hit": flat_better,
        "graded_under_flat_hit": flat_worse,
        # 控制臂自己的體檢：`matched` 跟 `flat` 分不開時，任何「輸給控制臂」都等於
        # "輸給均勻權重"，不能算成獨立證據。
        "control_verdict": _control_verdict(control_better, control_worse, need),
    }


def _control_verdict(better: int, worse: int, need: int) -> str:
    """`matched` 控制臂還分得出來嗎？

    ``matched`` 只打散 tier 與信心的綁定，不動訓練流（流本身就按 tier 重複），所以它保留「強配對
    看三次」這件事，只把信心換成隨機。在這個更新規則下（拉向 ``target_strength × gate``），隨機信心
    的期望值對每條配對都一樣，於是它變成「幅度較低的均勻權重」，也就是第二個 ``flat``。

    這件事必須自己回報，否則「分級輸給控制臂」會被誤讀成「分級輸給隨機的 tier 綁定」，實際上兩者
    是同一句話。
    """
    if better >= need and better > worse:
        return "control-arm-better-than-flat"
    if worse >= need and worse > better:
        return "control-arm-worse-than-flat"
    return "control-arm-indistinguishable-from-flat"


def _readout_verdict(better: int, worse: int, need: int) -> str:
    """方向要分開講：贏過控制與輪給控制是相反的結論，把它們都叫「有效」就不算量了。

    ``need`` 由種子數導出（``_sign_test_minimum``），所以多跑種子不會放寬判詞。
    """
    if better >= need and better > worse:
        return "readout-better"
    if worse >= need and worse > better:
        return "readout-worse"
    return "readout-no-difference"


def strength_equilibrium(
    family: str,
    calibration: Dict[str, object],
    seeds: Optional[Sequence[int]] = None,
    epochs: int = STRENGTH_EQUILIBRIUM_EPOCHS,
    readout: Optional[str] = None,
) -> Dict[str, object]:
    """収斂區的同一組比較：只看兩層的權重比，不看 top-1。

    WHY 需要這一跑：``strength_probe`` 在 ep3 量到的權重離定點還很遠（實測強層 0.065，収斂後
    0.22），那個區域四臂拉的節點都在同一個量級——「定點帶強弱」與「速率帶強弱」在瞬態分不開。
    接近定點時才分開：flat 的弱/強 比 0.84（純粋是 decay 不平衡造成的）、speed 0.62（慢的更少
    累積）、graded 0.41（定點本身就是 T·gate）。

    top-1 在這個區域已經不能用：讀出在大量權重下飽和（實測 ep20 起 flat 也是 0.000），所以
    這裡只報權重比，不報命中率——量不到的不假裝量到。
    """
    use_readout = readout or READOUT
    assert use_readout in READOUTS, f"unknown readout {use_readout!r}"
    using = tuple(seeds) if seeds else tuple(SEEDS[:STRENGTH_EQUILIBRIUM_SEEDS])
    if set(using) & set(CALIBRATION_SEEDS):
        raise ValueError("equilibrium seeds must not include calibration seeds")
    task = _task(family, calibration["step"], float(calibration["lr"]))  # type: ignore[arg-type]
    pairs = _downstream._pairs(task)
    tiers = _tier_of_pairs(pairs)
    arms = ("flat", "graded", "matched", "speed")
    rows: Dict[str, List[Dict[str, float]]] = {name: [] for name in arms}
    for seed in using:
        stream = _strength_stream(pairs, tiers, seed, epochs)
        matched_conf = [tiers[i] / float(max(STRENGTH_TIERS)) for i in stream]
        random.Random(seed * 104729 + 7).shuffle(matched_conf)
        confidences = {
            "flat": [1.0] * len(stream),
            "graded": [tiers[i] / float(max(STRENGTH_TIERS)) for i in stream],
            "matched": matched_conf,
            "speed": [1.0] * len(stream),
        }
        for arm in arms:
            rows[arm].append(
                _run_strength_arm(
                    task, pairs, tiers, stream, confidences[arm], seed, arm, readout=use_readout
                )
            )

    def ratio(row: Dict[str, float]) -> float:
        strong = row["weight_strong"] or 0.0
        return row["weight_weak"] / strong if strong else 0.0

    summary = {
        arm: {
            "weak_over_strong_mean": round(statistics.fmean(ratio(r) for r in rows[arm]), 3),
            "weak_over_strong_sd": (
                round(statistics.stdev(ratio(r) for r in rows[arm]), 3)
                if len(rows[arm]) > 1
                else 0.0
            ),
            "weight_strong_mean": round(statistics.fmean(r["weight_strong"] for r in rows[arm]), 5),
            "weight_weak_mean": round(statistics.fmean(r["weight_weak"] for r in rows[arm]), 5),
            # 定點區的 top-1：在 ``potential`` 下這個數字全部是 0.000（飽和），在 ``direct`` 下
            # 才有內容——兩者要一起看，「讀出死了」才不是一句無法反駁的話。
            "hit_rate_mean": round(statistics.fmean(r["hit_rate"] for r in rows[arm]), 3),
        }
        for arm in arms
    }
    need = _sign_test_minimum(len(using))
    attribution = _attribution(pairs, tiers)
    graded_below_flat = sum(1 for g, f in zip(rows["graded"], rows["flat"]) if ratio(g) < ratio(f))
    graded_below_matched = sum(
        1 for g, m in zip(rows["graded"], rows["matched"]) if ratio(g) < ratio(m)
    )
    drop = summary["flat"]["weak_over_strong_mean"] - summary["graded"]["weak_over_strong_mean"]
    reaches = (
        drop >= STRENGTH_MIN_RATIO_DROP and min(graded_below_flat, graded_below_matched) >= need
    )
    hits_better = sum(
        1 for g, m in zip(rows["graded"], rows["matched"]) if g["hit_rate"] > m["hit_rate"]
    )
    hits_worse = sum(
        1 for g, m in zip(rows["graded"], rows["matched"]) if g["hit_rate"] < m["hit_rate"]
    )
    return {
        "family": family,
        "epochs": epochs,
        "readout": use_readout,
        "lr": round(float(task["lr"]), 4),  # type: ignore[arg-type]
        # 定點區的 top-1 是否分得開：這一格就是「讀出飽和」假設的拷問。
        "graded_over_matched_hit": hits_better,
        "graded_under_matched_hit": hits_worse,
        "readout_verdict": _readout_verdict(hits_better, hits_worse, need),
        "seeds": len(using),
        "sign_test_min": need,
        "arms": summary,
        "ratio_drop_vs_flat": round(drop, 3),
        "graded_below_flat": graded_below_flat,
        "graded_below_matched": graded_below_matched,
        "attribution": attribution,
        "verdict": _caveated(
            "fixed-point-carries-strength" if reaches else "fixed-point-inert", attribution
        ),
    }


# ---------------------------------------------------------------------------
# G1 的第三種量法：同一個 cue 底下的兩個 target 競爭
# ---------------------------------------------------------------------------
# WHY 又一套：上面三族都是「一個 cue 對一個 target」，所以唯一的問法就是 top-1。但 §46 的擴散
# 把它壓平、§47 的絕對值讓它偏、§48 的歸一化把它整個抹掉——三種讀出壞在不同地方，共同點是
# 只看勝負、不看分佈。分佈敏感的問法不能跨配對比（絕對值只能跨配對比，一歸一化就沒了），
# 只能在**同一個 cue 內部**比：給每個 cue 兩個 target，強的那個信心高、弱的那個信心低，
# 問「強的排在弱的前面嗎」。同一個 cue 的兩個分數同乘一個正數不會改變順序，所以這個量法
# 對頻率完全免疫，歸一化讀出也保得住它。
#
# 為了讓信心是**唯一**的強弱來源，每個配對每輪只出現一次（不是按 tier 重複）。否則「出現
# 次數」本身就會把強的那個寫得更重，四個臂都靠重複次數得分，測到的就不是定點而是頻率。
# flat 因此必然是打平（兩個 target 被寫入同樣多次），這正好是「這個量法不是白送」的證據。
AMBIGUOUS_CUES = 24
AMBIGUOUS_EPOCHS = 40
AMBIGUOUS_SEEDS = 12
# 「強排在弱前面」要算成立：平均勝率至少這麼多，而且贏過控制臂的種子數要過符號檢定。
AMBIGUOUS_MIN_WINS = 0.75


def _ambiguous_design() -> List[Tuple[List[str], str, str]]:
    """每個 cue 共用同一組輸入 token、指向兩個不同的 target（強／弱）。"""
    design: List[Tuple[List[str], str, str]] = []
    for i in range(AMBIGUOUS_CUES):
        design.append(
            ([f"cue{i:02d}", f"n{i % 3}", "shared"], f"t{2 * i:02d}", f"t{2 * i + 1:02d}")
        )
    return design


def _ambiguous_stream(count: int, seed: int, epochs: int) -> List[int]:
    """每個配對每輪恰好一次；每一項是配對索引（偶數強、奇數弱）。"""
    rng = random.Random(seed * 7907 + 13)
    base = list(range(count))
    out: List[int] = []
    for _ in range(epochs):
        order = base[:]
        rng.shuffle(order)
        out.extend(order)
    return out


def _run_within_cue_arm(
    pairs: Sequence[Tuple[List[str], str]],
    tiers: Sequence[int],
    stream: Sequence[int],
    confidences: Sequence[float],
    arm: str,
    readout: str,
    lr: float,
) -> Dict[str, object]:
    """同一條流、同一組配對，只改信心怎麼進來；回傳「強排在弱前面」的逐 cue 結果。"""
    core = _downstream.TensorSNNCore(threshold=0.25, timesteps=_downstream._readouts.TIMESTEPS)
    top = float(max(STRENGTH_TIERS))
    for pair_index, conf in zip(stream, confidences):
        inputs, target = pairs[pair_index]
        tier = tiers[pair_index]
        core.hebbian_update(
            {key: (conf if arm in ("graded", "matched") else 1.0) for key in inputs},
            {target: (conf if arm in ("graded", "matched") else 1.0)},
            lr=lr,
            target_strength=_downstream.TARGET_STRENGTH,
            plasticity=(tier / top if arm == "speed" else 1.0),
        )
    wins, ties, margins = 0, 0, []
    for inputs, strong, weak in _ambiguous_design():
        out = _downstream._readouts._forward(core, {key: 1.0 for key in inputs}, readout)
        hi, lo = out.get(strong), out.get(weak)
        if hi is None or lo is None:
            continue
        margins.append(float(hi) - float(lo))
        if float(hi) == float(lo):
            ties += 1
        elif float(hi) > float(lo):
            wins += 1
    cues = len(margins)
    return {
        "win_rate": round(wins / cues, 3) if cues else 0.0,
        "wins": wins,
        "ties": ties,
        "cues": cues,
        "margin_mean": round(statistics.fmean(margins), 5) if margins else 0.0,
    }


def within_cue_probe(
    readout: Optional[str] = None,
    seeds: Optional[Sequence[int]] = None,
    epochs: int = AMBIGUOUS_EPOCHS,
    lr: float = 0.015,
) -> Dict[str, object]:
    """強弱是不是真的被綁在**對的關聯**上（而不是剛好有些權重比較小）。

    判準只看 ``graded`` 對 ``matched``：後者的信心分佈完全相同，只是被打散到別的配對，所以
    差異只能來自「信心有沒有落在正確的關聯上」。``flat`` 是下界（兩個 target 被寫入同樣多次，
    應該打平），``speed`` 把強弱放在速率而非定點，用來分開兩種語意。
    """
    use_readout = readout or READOUT
    assert use_readout in READOUTS, f"unknown readout {use_readout!r}"
    using = tuple(seeds) if seeds else tuple(SEEDS[:AMBIGUOUS_SEEDS])
    design = _ambiguous_design()
    pairs: List[Tuple[List[str], str]] = []
    tiers: List[int] = []
    for inputs, strong, weak in design:
        pairs.append((inputs, strong))
        tiers.append(STRENGTH_TIERS[1])
        pairs.append((inputs, weak))
        tiers.append(STRENGTH_TIERS[0])
    arms = ("flat", "graded", "matched", "speed")
    top = float(max(STRENGTH_TIERS))
    rows: Dict[str, List[Dict[str, object]]] = {name: [] for name in arms}
    for seed in using:
        stream = _ambiguous_stream(len(pairs), seed, epochs)
        graded_conf = [tiers[i] / top for i in stream]
        matched_conf = list(graded_conf)
        random.Random(seed * 104729 + 7).shuffle(matched_conf)
        confidences = {
            "flat": [1.0] * len(stream),
            "graded": graded_conf,
            "matched": matched_conf,
            "speed": [1.0] * len(stream),
        }
        for arm in arms:
            rows[arm].append(
                _run_within_cue_arm(pairs, tiers, stream, confidences[arm], arm, use_readout, lr)
            )

    need = _sign_test_minimum(len(using))
    rates = {arm: [float(r["win_rate"]) for r in rows[arm]] for arm in arms}
    better = sum(1 for g, m in zip(rates["graded"], rates["matched"]) if g > m)
    worse = sum(1 for g, m in zip(rates["graded"], rates["matched"]) if g < m)
    graded_mean = statistics.fmean(rates["graded"])
    anchored = graded_mean >= AMBIGUOUS_MIN_WINS and better >= need and better > worse
    return {
        "family": "ambiguous",
        "epochs": epochs,
        "readout": use_readout,
        "lr": lr,
        "cues": len(design),
        "seeds": len(using),
        "sign_test_min": need,
        "arms": {
            arm: {
                "win_rate_mean": round(statistics.fmean(rates[arm]), 3),
                "win_rate_sd": (
                    round(statistics.stdev(rates[arm]), 3) if len(rates[arm]) > 1 else 0.0
                ),
                "tie_mean": round(statistics.fmean(float(r["ties"]) for r in rows[arm]), 2),
                "margin_mean": round(
                    statistics.fmean(float(r["margin_mean"]) for r in rows[arm]), 5
                ),
            }
            for arm in arms
        },
        "graded_over_matched": better,
        "graded_under_matched": worse,
        "verdict": (
            "within-cue-strength-anchored" if anchored else "within-cue-strength-not-anchored"
        ),
    }


def _rank_interpretable(graded_hit: float, matched_hit: float) -> bool:
    """讀出還活著嗎——死讀出上的名次一律不准講話。

    WHY 必須擋：ep40 的 ``potential`` 讀出是擴散飽和後的死讀出（四臂 top-1 全 0.0），可是名次
    信用在那裡**不是 0**：實測 `hard` graded 0.0135 對 matched 0.2281（鈕 40/0）、
    `many_to_one` 0.0451 對 0.0069（39/1）——兩個方向都出現，而且都在四臂命中率全 0 的格子上。
    那不是機制，是「連正確 target 都點不出來時」的勝負排列。若讓它講話，它會開始製造
    「graded 比較好」與「graded 比較壞」兩種相反的假宣稱。

    界是絕對下限而不是新門檻：0.0 就是「完全點不出正確答案」。而且必須**兩臂都**點得出來：
    第一版寫成 ``max(...) > 0``，於是 `hard`/`potential`/ep40（graded 0.0、matched 0.2030）
    没被擋下，還報了 ``favours-matched`` 40/0。要被評的那個臂自己都拿不到正確答案時，它的
    名次只是「所有東西都贏過我」，不是排序資訊；那一句話要由 ``readout_verdict`` 去講。
    """
    return min(graded_hit, matched_hit) > 0.0


def _rank_verdict(better: int, worse: int, need: int, interpretable: bool = True) -> str:
    """名次的方向也要分開講，且用同一個由種子數導出的門檻（不另外挑門檻）。

    ``need`` 從種子數算出來，所以這條也繼承「多跑種子不會放寬判詞」。死讀出上則回
    ``rank-credit-readout-degenerate``：空白不能冒充「沒問題」。
    """
    if not interpretable:
        return "rank-credit-readout-degenerate"
    if better >= need and better > worse:
        return "rank-credit-favours-graded"
    if worse >= need and worse > better:
        return "rank-credit-favours-matched"
    return "rank-credit-no-difference"


def strength_report(
    family: str,
    calibration: Dict[str, object],
    seeds: Optional[Sequence[int]] = None,
    readout: Optional[str] = None,
) -> Dict[str, object]:
    """瞬態（讀出還活著）＋収斂區（定點看得到）兩段合起來看。

    兩段必須一起報：只跑瞬態得到「四臂差不多」會誤判成「強弱沒用」，實際上是「還沒走到定點」；
    只跑収斂則會把已經飽和的 top-1（0.000）誤讀成「強弱有害」。
    """
    transient = strength_probe(
        family, calibration, readout=readout, seeds=seeds, epochs=STRENGTH_EPOCHS
    )
    plateau = strength_equilibrium(family, calibration, readout=readout)
    return {
        "family": family,
        "readout": transient["readout"],
        "transient": transient,
        "equilibrium": plateau,
        # 兩句都要留下來：「定點有沒有带強弱」與「讀出看不看得見」是兩個獨立問題，拿其中
        # 一句當結論會把「還沒走到定點」或「讀出已經飽和」誤讀成機制的成敗。
        "weights_verdict": plateau["verdict"],
        "ordering_verdict": transient["ordering_verdict"],
        # 讀出的兩難要靠兩格一起講：瞬態有訊號但還沒走到定點，定點區在 potential 下又全 0。
        # 把兩者分開報，才不會用一邊的失敗冒充另一邊的。
        "readout_verdict": transient["readout_verdict"],
        "equilibrium_readout_verdict": plateau["readout_verdict"],
        # 名次信用只看排序、不看格子，所以不帶污染度註記；它回答的是 top-1 回答不了的問題。
        "rank_verdict": transient["rank_verdict"],
    }


NO_BENEFIT = (
    "no-downstream-difference",
    "margin-gain-without-hit-gain",
    # top-1 變好但 margin 沒過散布門檻，且贏不過同散佈的 shuffled：好處來自「增益有大有小」，
    # 不是時機。算「機制（時機）沒有好處」。
    "hit-gain-without-margin-gain",
    "timing-does-not-matter-only-gain",
    "phase-loses-to-matched-mean",
)
HARM = "phase-loses-to-matched-mean"


# 結構上量不到中段的族。這裡的「量不到」不是「沒差」，而是「這一族的設計讓 top-1 讀出
# 不可能有中段」：每 cue 一個專屬 token ⇒ ep1 就是 1.000，跨 epoch 沒有可比較的區間。
# 它們不是被偷偷丟掉，而是具名列出：報告會帶 ``unmeasured`` 欄位，判詞也會擋住
# 「新增一族、它量不到、但整體判詞照樣下結論」這種情況（見 overall_verdict）。
# v23 除名 `hard`：40 個種子下它在 ep1/3/5 三格全部可下結論（12 個種子時 ep1 的 neutral
# 是 0.333 且 sd=0，看起來像「ep1 即天花板」其實是解析度不足）。登記簿必須兩邊都會響——
# 量不到沒登記會擋判詞，登記了卻量到就是過期，`_stale_registrations()` 會讓官方跑法 exit 1。
UNMEASURED_FAMILIES: Dict[str, str] = {
    "structured": "ep1 完全遷移、ep3 起電位壓成同分（margin=0）→ 讀出崩成 0，沒有中段",
}
# 棘輪：量不到的族數只能減不能增（要新增必須同時上調預算並寫出結構原因）。
UNMEASURED_BUDGET_FILE = Path(__file__).with_name("al_unmeasured_budget.txt")


def _unmeasured_budget() -> int:
    """允許「結構上量不到」的族數；讀不到檔案時回 0（fail-closed）。"""
    try:
        return int(UNMEASURED_BUDGET_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 0


def _stale_registrations(
    cells: Sequence[Dict[str, object]], registered: Optional[Dict[str, str]] = None
) -> List[str]:
    """登記為「量不到」、但這次每一格都量到的族＝登記簿過期。

    方向很重要：上一版的門只擋「量不到卻沒登記」，於是登記簿只會長、不會消——`hard` 在
    12 個種子下看起來量不到，40 個種子下三格全部可下結論，登記卻會繼續留著冒充「未知」。
    過期登記比漏登記安全（偏保守），但它同樣是「文件說的話與量測不一致」，所以同樣要響。
    """
    registered = UNMEASURED_FAMILIES if registered is None else registered
    totals: Dict[str, List[int]] = {}
    for cell in cells:
        family = str(cell["family"])
        bucket = totals.setdefault(family, [0, 0])
        bucket[1] += 1
        if cell["informative"]:
            bucket[0] += 1
    return sorted(
        name
        for name in registered
        if name in totals and totals[name][1] > 0 and totals[name][0] == totals[name][1]
    )


def overall_verdict(cells: Sequence[Dict[str, object]], unregistered: Sequence[str] = ()) -> str:
    # 先擋「有一族量不到，而它不在登記簿裡」：那時任何整體判詞都是在拿沒有證據的格子
    # 冒充結論（未爆彈就是這樣留下來的）。
    if unregistered:
        return "unmeasured-unregistered"
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


def run(
    readout: Optional[str] = None,
    seeds: Optional[Sequence[int]] = None,
    families: Optional[Sequence[str]] = None,
    strength: bool = False,
    within_cue: bool = False,
) -> Dict[str, object]:
    cells: List[Dict[str, object]] = []
    probes: List[Dict[str, object]] = []
    use_seeds = tuple(seeds) if seeds else SEEDS
    if set(use_seeds) & set(CALIBRATION_SEEDS):
        raise ValueError("evaluation seeds must not include calibration seeds")
    use_families = tuple(families) if families else tuple(FAMILIES)
    for family in use_families:
        # 每族只校準一次：step 與 lr 固定，epochs 這條軸才只改訓練量。
        calibration = calibrate_family(family, readout=readout)
        for epochs in EPOCHS_MATRIX:
            if not calibration["informative"]:
                cells.append(
                    {
                        "family": family,
                        "epochs": epochs,
                        "informative": False,
                        "reason": calibration.get("reason", "ladder-exhausted"),
                        "calibration": calibration,
                    }
                )
                continue
            cell = evaluate_cell(family, calibration, epochs, readout=readout, seeds=use_seeds)
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
        # 強弱探針只在這一族校準成功時才有意義（校準失敗＝連基準都量不到）。
        if strength and calibration["informative"]:
            probe = strength_report(family, calibration, seeds=use_seeds, readout=readout)
            probes.append(probe)
            t = probe["transient"]
            e = probe["equilibrium"]
            print(
                f"strength {family:<12} ep{STRENGTH_EPOCHS} (readout {probe['readout']}) "
                f"graded rho {t['arms']['graded']['spearman_mean']} "
                f"hit {t['arms']['graded']['hit_rate_mean']} vs matched "
                f"{t['arms']['matched']['hit_rate_mean']} "
                f"(G>M {t['graded_over_matched_hit']}/{t['seeds']}, "
                f"G<M {t['graded_under_matched_hit']}/{t['seeds']}) "
                f"-> {t['ordering_verdict']}/{t['readout_verdict']}"
            )
            print(
                f"strength {family:<12} ep{STRENGTH_EQUILIBRIUM_EPOCHS} (plateau) "
                f"weak/strong flat {e['arms']['flat']['weak_over_strong_mean']} "
                f"graded {e['arms']['graded']['weak_over_strong_mean']} "
                f"matched {e['arms']['matched']['weak_over_strong_mean']} "
                f"speed {e['arms']['speed']['weak_over_strong_mean']} "
                f"| drop {e['ratio_drop_vs_flat']} "
                f"| G<F {e['graded_below_flat']}/{e['seeds']} "
                f"G<M {e['graded_below_matched']}/{e['seeds']} -> {e['verdict']}"
            )
            print(
                f"strength {family:<12} ep{STRENGTH_EQUILIBRIUM_EPOCHS} (top-1, "
                f"{e['readout']}) flat {e['arms']['flat']['hit_rate_mean']} "
                f"graded {e['arms']['graded']['hit_rate_mean']} "
                f"matched {e['arms']['matched']['hit_rate_mean']} "
                f"speed {e['arms']['speed']['hit_rate_mean']} "
                f"(G>M {e['graded_over_matched_hit']}/{e['seeds']}, "
                f"G<M {e['graded_under_matched_hit']}/{e['seeds']}) "
                f"-> {e['readout_verdict']}"
            )

    # 哪些族沒有產出可下結論的格、以及為什麼；未登記的族會讓整體判詞變成
    # ``unmeasured-unregistered``，不再讓它們安靜地從判詞裡消失。
    unmeasured = sorted({str(cell["family"]) for cell in cells if not cell["informative"]})
    unmeasured_reasons = {
        name: UNMEASURED_FAMILIES.get(name, "unregistered（新族量不到就必須登記）")
        for name in unmeasured
    }
    unregistered = [name for name in unmeasured if name not in UNMEASURED_FAMILIES]
    stale = _stale_registrations(cells)
    for name in stale:
        print(
            f"STALE REGISTRATION: {name} 登記為量不到，但這次每一格都可下結論 "
            f"→ 從 UNMEASURED_FAMILIES 除名並下調 scripts/al_unmeasured_budget.txt"
        )

    # 量具本身的控制：同一批輸入、打亂的標籤。若這段也拿到中段，跨臂比較量的是輸入結構。
    controls = {
        family: _label_shuffle_baseline(family, CALIBRATION_SEEDS, readout=readout)
        for family in use_families
    }
    for name, control in controls.items():
        print(
            f"control {name:<12} label-shuffle train {control['train']} "
            f"held-out {control['heldout']} (chance {control['chance']})"
        )

    result: Dict[str, object] = {
        "protocol": PROTOCOL_VERSION,
        "readout": readout or READOUT,
        "controls": controls,
        "epochs_matrix": list(EPOCHS_MATRIX),
        "lr_grid": list(LR_GRID),
        "hit_range": list(HIT_RANGE),
        "families": {name: steps for name, steps in FAMILIES.items() if name in use_families},
        "seeds": list(use_seeds),
        "sign_test_min": _sign_test_minimum(len(use_seeds)),
        "unmeasured": unmeasured_reasons,
        "unregistered_unmeasured": unregistered,
        "stale_unmeasured": stale,
        "cells": cells,
        "verdict": overall_verdict(cells, unregistered),
    }
    # 同 cue 內競爭跟族無關（它自己一套設計），所以只跑一次，而且跟 ``strength`` 共用一個
    # 判詞——不然「定點有帶強弱但綁錯關聯」這種情況會從跨族判詞裡消失。
    within = (
        within_cue_probe(readout=readout, seeds=use_seeds[:AMBIGUOUS_SEEDS]) if within_cue else None
    )
    if within is not None:
        result["within_cue"] = within
    if strength or within is not None:
        if strength:
            result["strength_probe"] = probes
        result["strength_verdict"] = _strength_verdict(probes, within)
    return result


def _strength_verdict(
    probes: Sequence[Dict[str, object]], within: Optional[Dict[str, object]] = None
) -> str:
    """跨族判詞：兩個問題分開講；只有不一致的族才退成「依 regime 而定」。

    一致性的負結果也是結論（所有族都「定點沒帶強弱」或「讀出看不見」），不能模糊成「沒差」。
    """
    if not probes:
        base = "no-strength-probe"
        tail = f"/{within['verdict']}" if within else ""
        return f"{base}{tail}"
    weights = {str(p["weights_verdict"]) for p in probes}
    ordering = {str(p["ordering_verdict"]) for p in probes}
    readout = {str(p["readout_verdict"]) for p in probes}
    w = weights.pop() if len(weights) == 1 else "weights-regime-dependent"
    o = ordering.pop() if len(ordering) == 1 else "ordering-regime-dependent"
    r = readout.pop() if len(readout) == 1 else "readout-regime-dependent"
    # 第三句只有真的量到才加：沒跑就不能用空白冒充「沒問題」。
    verdict = f"{w}/{o}/{r}" + (f"/{within['verdict']}" if within else "")
    # 名次信用也只在每一族都量到時才組成：它是「排序」那個問題，跟 weights／ordering 不同格。
    ranks = {str(p["rank_verdict"]) for p in probes if "rank_verdict" in p}
    if ranks and len(ranks) == 1 and all("rank_verdict" in p for p in probes):
        verdict = f"{verdict}/{ranks.pop()}"
    return verdict


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path)
    # 讀出：預設仍是 ``potential``（16 步擴散，既有報告要能重現）。``direct`` 是一步
    # ``W · a``，不會被擴散壓平；切過去等於重新基線，所有格子都要重跑重報。
    ap.add_argument("--readout", choices=READOUTS, default=READOUT)
    # 種子可以加，但門檻要跟著 n 走（``_sign_test_minimum``）——否則 40 個種子仍只要求 10 個
    # 同向，判詞會悄悄變鬆。校準種子永不參與評估。
    ap.add_argument("--seeds", type=int, default=len(SEEDS))
    ap.add_argument("--families", default=",".join(FAMILIES))
    # 強弱探針：問「出現次數造成的強弱有沒有進到權重、讀出看不看得見」。預設不跑，因為它
    # 問的不是時機（階梯的問題），而且會多出 4 臂 × 種子 的訓練成本。
    ap.add_argument("--strength-probe", action="store_true")
    # 同 cue 內競爭：問「強弱有沒有綁在對的關聯上」。它不屬於任何既有族（每族都是一個 cue 對
    # 一個 target，只有 top-1 可問），所以自己一套設計，也自己一個開關。
    ap.add_argument("--within-cue", action="store_true")
    args = ap.parse_args(argv)

    seed_list = tuple(SEEDS) + tuple(s for s in range(1000, 1000 + max(0, args.seeds - len(SEEDS))))
    result = run(
        readout=args.readout,
        seeds=seed_list[: args.seeds],
        families=[f for f in args.families.split(",") if f],
        strength=args.strength_probe,
        within_cue=args.within_cue,
    )
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
            f"| MDE {body['detectable_hit_delta']} "
            f"| P>N {body['seed_wins']['phase_over_neutral_hit']}/{body['seed_wins']['seeds']} "
            f"P>S {body['seed_wins']['phase_over_shuffled_hit']}/{body['seed_wins']['seeds']}  "
            f"-> {body['verdict']}"
        )
    print(f"verdict: {result['verdict']}")
    if result.get("strength_verdict"):
        print(f"strength verdict: {result['strength_verdict']}")
    if result.get("within_cue"):
        within = result["within_cue"]
        assert isinstance(within, dict)
        arms = within["arms"]  # type: ignore[index]
        print(
            f"within-cue {within['readout']}: "
            + " ".join(
                f"{k} {arms[k]['win_rate_mean']}" for k in ("flat", "graded", "matched", "speed")
            )
            + f" | G>M {within['graded_over_matched']} G<M {within['graded_under_matched']}"
            f" need {within['sign_test_min']} -> {within['verdict']}"
        )

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"report: {args.json}")
    # 登記簿過期就 exit 1：報告照寫（證據不能丟），但這一輪不算通過——否則「量得到卻
    # 仍登記為量不到」會跟「量不到卻沒登記」一樣，安安靜靜地活過每一次重跑。
    if result["stale_unmeasured"]:
        print(
            "registry is stale: "
            + ", ".join(result["stale_unmeasured"])
            + " —— 除名後重跑（登記數只能降，見 scripts/al_unmeasured_budget.txt）"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
