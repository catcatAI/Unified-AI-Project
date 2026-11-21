<!--
  =============================================================================
  FILE_PATH: docs/06-project-management/SCALE_UP_PLAN.md
  FILE_TYPE: documentation
  PURPOSE: Pre-registered plan for the >=10^8 parameter token-SNN experiment.
  VERSION: 1.0.0-dev
  STATUS: draft
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-11-21
  AUDIENCE: developers, agents
  =============================================================================
-->

# Scale-Up Plan (>=10^8 token-SNN)

> 狀態：**Phase 1 跑了兩次**（2026-11-21/22）。mem_norm=False：near 0.0078、val CE 1.5130。
> mem_norm=True：near 0.0095、val CE 1.5154、sensitive 0.9028、mem 1.38。動態修好，但 capability
> 仍不比 3.5M（1.4061）。Phase 2（蒸餾）的動態前提已滿足，但 capability 前提未達。
> 詳見 BETA_TRAINING_PLAN §M/§O。
> 本文件不改任何 beta 門檻、不改 ratchet、不碰 art group。

## 0. 為什麼寫這份文件

P2 證明管線是健康的（val CE 1.4061 < floor 3.7482，非線性活著），但 B1/B1b 量到
**0/105** 個凍結題正確。P3 的止損條件（容量在幾百列就飽和 → 不加寬、先改表徵）
已經套過；§J/§L 的寬度 A/B 進一步證明：**4.7× 寬度（3.5M → 16.7M）在相同步數下
沒有幫助，甚至 medium 需要更低的 LR 才能學起來，調好之後仍不贏 small**。

剩下來的路徑只有 CORE_GAP_ANALYSIS 指向的那條：**≥10^8 參數 + GPU surrogate BPTT
(+/- 蒸餾)**。這份文件把那條路徑的工程、預算與止損寫成可執行、可中止的計畫。

## 1. 量測到的事實（全部有證據）

| 項目 | 數值 | 來源 |
| ---- | ---- | ---- |
| 參數規模（small） | 3,525,319 | `data/capacity/report.json` |
| 容量（200 次曝光） | ≥ 512 列，2048@50 失敗（0.598） | §C |
| 全語料 2 epochs val CE | 1.4061（floor 3.7482） | §D |
| 全語料 2 epochs val exact | 0.230（200 列，CI [0.172, 0.288]） | §D |
| 凍結題正確數 | **0/105**（coverage 113/115） | §F/§G |
| 寬度 A/B（4.7×） | d2 −5.5pp；d3 medium underfit 0.075 vs 0.560 | §J/§L |
| 非線性 | near 0.0243、sensitive 0.4418、verdict alive | §D |
| 108M checkpoint | 2 readiness FAIL（beta 0.5407、near 0.0014、sensitive 0.0283） | §5 #4 |
| 硬體 | Intel Arc B570（XPU），torch 2.14.1+xpu；CPU 12 核、15.7 GB RAM | §X #281 |

結論：管線健康、表徵與 readout 已 A/B 過、非線性活著，但**映射完全沒學起來**。
寬度 4.7× 沒有幫助。剩下來的旋鈕是**規模**與**目標函數**。

## 2. 根因（CORE_GAP_ANALYSIS，已驗證）

1. `DictionaryLayer.encode()` 把詞變成字典釋義（`encode("12 + 7")` → `m2`/`cedict_...`），
   輸入本身不可區分 → 解碼器只能吐字詞湯。**這一步已修**：改用 token atoms。
2. ED3N 的 `generate()` 從未被訓練：CLI 沒建 `SeqBatch`、alpaca 的 `instruction` 被丟掉。
   **這一步已修**：`train_token_snn.py` 現在訓練 next-token CE on answer atoms。
3. 規模不足：3.5M 參數、1 層、1 timestep、val exact 0.23、0/105。**這一步沒修**。
4. 蒸餾未建立：KD cache 基礎設施存在（`--kd-cache`、`KdCache`），但沒有在 full corpus
   上跑過，也沒有證據說它有幫助（§8 的止損：只報 KD loss 下降不算有效）。

所以這次 scale-up 的核心假設是：**≥10^8 參數 + surrogate gradient BPTT + 蒸餾**。

## 3. 什麼算「規模」（定義）

- **參數**：≥ 1.0×10^8（CORE_GAP 的門檻）。
- **資料**：≥ 10^5 條有效 rows（目前 138,671 fit；夠，但 quality 仍需清理）。
- **訓練**：≥ 10 epochs 或 val CE 收斂，以較早者為準。
- **目標**：surrogate gradient BPTT（Neftci 2019；SLAYER 2018），not the historical
  1-timestep forward that never carried gradient across tokens.
- **不是**：把 3.5M 跑更久、加寬 4.7×、或只報 train loss 下降。

## 4. 架構規格（Phase 0：先量測，不訓練）

| 項目 | 值 | 理由 |
| ---- | -- | ---- |
| d_emb | 1024 | 容量與 head 共用 |
| d_hidden | 5120 | head = 5120 × 12,000 ≈ 61M，總計 ≈ 1.05×10^8 |
| layers | 1 | §X #276 顯示 2 層在 small scale 變差；先 1 層，失敗再試 2 |
| timesteps | 1 | recurrence 已在 token 維度展開 |
| vocab | 12,000（core corpus） | 不膨脹；head 已夠大 |
| readout | membrane | §X #276 的 A/B 贏家 |
| beta | 0.9 | 已修正的參數化 |
| theta_max / leak_floor / gain_cap | 1.0 / 0.85 / 1.0 | 本次協定的 guards |
| surrogate_alpha | 5.0 | 歷史值 |
| max_len | 192 | 92.8% 的 rows fit；更長只增加 compute |
| numeric_atoms | False | core corpus 不是 contract values |

**Phase 0 驗證結果（2026-11-21，CPU，不訓練）**：real vocab 12,005；
`d_emb=1024, d_hidden=5120, layers=1` → **105,243,367 參數**（fp32 421 MB）。
VRAM 估算 420 + 840 + 50 ≈ 1.3 GB ≤ 7.2 GB。Phase 0 通過。

## 5. 硬體與資源上限

- 裝置：`resolve_torch_device()` → XPU（Arc B570）。GARDEN 仍用 CPU（sparse Hebbian
  在 XPU 上慢 7×），但 token-SNN 訓練用 XPU。
- VRAM 上限：60% × 12 GB ≈ **7.2 GB**。估算：params 420 MB + Adam states 840 MB +
  activations ≈ 50 MB + headroom → **≈ 1.4 GB**，有大量餘裕。
- RAM 上限：60% × 15.7 GB ≈ **9.4 GB**。KD cache 6.6 GB（top-64）是最大單項；
  不得與其他重負載同時跑。
- CPU 上限：50%（6 核）。訓練在 XPU 上跑，CPU 只做資料載入；用 `taskset -c 0-5`。
- GPU duty：用 `scripts/gpu_limit.py --target 0.5` 包住訓練（§GPU_LIMIT.md）。
- 一次只跑一個重負載；KD cache 建置與訓練分開跑。

## 6. 資料計畫

- 來源：`core_train.jsonl`（149,489 rows，fit 138,671）+ `core_val.jsonl`（7,822，fit 7,197）。
- 過濾：`fits(max_len=192)`，與 P2 相同；不改 test set。
- 清理：`prepare_core_training_data.py` 已做 normalise/dedup/leak-check（26 leaks 已丟）。
  重跑一次確認 `benchmark_leak: 0`。
- 增量：若 hard-label phase 證明管線健康但 exact 仍低，下一步是蒸餾（§8），不是更多
  hard-label rows。**不**用 frozen benchmark items 訓練。
- 驗證：`probe_training_readiness.py --checkpoint ...` 必須 0 FAIL 才能開跑。

## 7. 訓練協定（Phase 1：hard labels，健康檢查）

- 目的：確認 10^8 模型能在 XPU 上訓練、val CE 能下降、非線性不塌。**不**期待 capability。
- Config：§4 的規格。
- Epochs：**2**（先求健康，不求分數）。
- Batch：32（VRAM 估算 1.4 GB；若 OOM 降到 16）。
- LR：3e-3，cosine，warmup 1 epoch。
- Seed：0（可重現）。
- Guards：theta_max 1.0、leak_floor 0.85、gain_cap 1.0、surrogate_alpha 5.0。
- Checkpoint：每 epoch 存；`--out data/checkpoints/scaleup_phase1.pt`；**不**覆蓋既有檔。
- Eval：`--eval-every 1`（val CE + dynamics）。
- 報告：`data/intelligence_reports/scaleup_phase1.json`。
- 預估時間：≈ 47 min/epoch × 2 ≈ **1.6 小時**（XPU 估算；CPU 估算 43 min/epoch）。
  實測 step time 以第一個 epoch 為準，若 > 2× 估算，停下來重新評估。

**Phase 1 門檻（跑前寫死）**：
- val CE < P2 的 1.4061（或至少 < floor 3.7482）；
- `near_threshold ≥ 0.01`、`sensitive ≥ 0.05`；
- 無 non-finite、無 rollback；
- VRAM ≤ 7.2 GB、RAM ≤ 9.4 GB。

**Phase 1 止損**：任一門檻失敗 → 停，不加 epoch；先修（guards、LR、batch），寫成 void run。

## 8. 蒸餾計畫（Phase 2：KD，真正的訓練訊號）

Phase 1 只是健康檢查；capability 的賭注在 Phase 2。

- **Teacher**：Qwen2.5-1.5B（`qwen2.5-1.5b-instruct-q4_k_m.gguf`，1.1 GB）。
  7B 是備選，但 cache 建置時間 ×7，先用 1.5B。
- **Cache**：`scripts/build_kd_cache.py`，`--top-k 64`，`--max-len 192`，
  `--max-vocab 12000`，綁定 Phase 0 的 vocab fingerprint。
  產出 `data/kd/kd_scaleup.npz`（估算 1–2 GB at top-64；若超 RAM 上限，降到 top-32）。
- **建置成本**：138,671 rows × 1 forward ≈ 19 小時（XPU 估算；實測第一個 500 rows 校準）。
  **先跑 500 rows 校準時間，再決定要不要全量**。
- **訓練**：Phase 1 的 config + `--kd-cache ... --kd-weight 0.5`，10 epochs。
  預估 47 min/epoch × 10 ≈ **7.8 小時**。
- **Phase 2 門檻**：val CE 低於 Phase 1；val exact > 0.23；B1 > 0（任一題正確）。
  B1 > 0 才是 capability 的第一個證據；val CE 只是 proxy。

**Phase 2 止損**：若 2 epochs 後 val CE 沒有低於 Phase 1，停；蒸餾沒有幫助，回退到
資料/目標函數的問題。

## 9. 評測計畫（Phase 3：B1）

- 跑 `scripts/probe_p2_tok_core.py`（或同等）在凍結題上，strict 評分。
- 報告 per-suite correct/answered/prompt_unk；**不合併成一個分數**。
- B1 的條件（任一題模型產生且正確）是 capability 的第一個證據，不是 pass line。
- 若 0/105：core 仍是 0.00/10；scale-up 沒有解決問題；回退到 §10 的決策點。

## 10. 預檢（開跑前必須全部有答案）

沿用 BETA_TRAINING_PLAN §5 的 1–18，加上：

| # | 檢查項 | 證據 |
|---|--------|------|
| 19 | Phase 0 參數數 ≥ 1.0×10^8 | 實例化計算 |
| 20 | VRAM 估算 ≤ 7.2 GB | params + Adam + activations |
| 21 | 108M checkpoint 不續訓 | `probe_training_readiness.py` 2 FAIL |
| 22 | KD cache vocab fingerprint 綁定 | `KdCache.require_vocab` |
| 23 | 資料 leak = 0 | manifest `benchmark_leak` |
| 24 | XPU 可跑 10^8 forward | Phase 0 在 XPU 上跑 1 batch |
| 25 | 回滾方案 | checkpoint 另存、`--out` 不覆蓋；報告進 `data/` |

## 11. 風險與止損

| 風險 | 徵兆 | 止損 |
| ---- | ---- | ---- |
| 規模沒幫助 | Phase 1 val CE ≥ P2 的 1.4061 | 停，不加 epoch；回退到資料/目標 |
| 蒸餾沒幫助 | Phase 2 val CE 沒低於 Phase 1 | 停；蒸餾沒有幫助 |
| VRAM 超限 | RSS/GPU > 60% | 降 batch（32→16→8）；`gpu_limit.py` |
| 10^8 訓練不穩定 | rollback > 0、near < 0.01 | 降 LR；檢查 guards 是否真的傳進去 |
| 時間超支 | 第一個 epoch > 2× 估算 | 停，重新評估 step time |
| 表層污染 | census 出現 template 被記成 snn | 修 `is_core_backend`，分數作廢重跑 |
| 非商用資料 | ESC-50 權重進 release | 先換資料或只散布程式碼 |

## 12. 決策點（需要使用者決定）

1. **要不要跑 Phase 1**（~1.6 小時，XPU，10^8 hard labels）？
   - 是 → 這是 capability 的**最低成本探針**；Phase 2/3 只在 Phase 1 通過時啟動。
   - 否 → beta 保持 research preview，core 0.00/10。
2. **Phase 2 的 teacher**：1.5B（快，弱）vs 7B（慢，強）？預設 1.5B。
3. **Phase 2 的 cache 規模**：全量 138k（19 小時建置）vs 40k 子集（5.5 小時）？
   預設先 40k 子集，看 KD loss 是否下降。
4. **10^8 vs 5×10^7**：若 VRAM/時間是瓶頸，5×10^7（~40M）是中間選項，
   但 CORE_GAP 的門檻是 10^8；不跨過門檻，B1 的證據力較弱。

## 13. 不宣稱的事

- 這個計畫**不**宣稱 beta 能力；B1 仍是 0/105，直到 Phase 3 量到 > 0。
- 這個計畫**不**改任何 ratchet、版本、或 art group。
- 這個計畫**不**把 P2 的健康或 P1 的容量借去當核心分。
- Phase 1 的 val CE 下降**不是**智能提升；只有 Phase 3 的 B1 > 0 才是。

## 14. 重跑指令（唯一入口，Phase 0 先跑）

```bash
# Phase 0：確認參數數與 VRAM（不訓練）
PYTHONPATH=apps/backend/src:scripts ./.venv/bin/python - <<'PY'
from train_token_snn import read_pairs
from ai.ed3n.token_snn import TokenConfig, TokenSNN, TokenVocab
from pathlib import Path
pairs = read_pairs(Path("apps/backend/data/processed/core_train.jsonl"), 0)
texts = [p + "\\n" + a for p, a in pairs[:50000]
v = TokenVocab.build(texts, min_count=1, max_vocab=12000)
cfg = TokenConfig(d_emb=1024, d_hidden=5120, beta=0.9, threshold=0.5,
                  theta_max=1.0, leak_floor=0.85, gain_cap=1.0, surrogate_alpha=5.0,
                  readout="membrane", layers=1, timesteps=1, max_len=192)
m = TokenSNN(v, cfg, device="cpu")
print("vocab", len(v), "params", sum(p.numel() for p in m.net.parameters()))
PY

# Phase 1：hard labels，2 epochs，XPU
taskset -c 0-5 env OMP_NUM_THREADS=6 MKL_NUM_THREADS=6 \
  ./.venv/bin/python scripts/train_token_snn.py \
    --vocab token --max-len 192 --max-vocab 12000 \
    --d-emb 1024 --d-hidden 5120 --layers 1 --timesteps 1 \
    --epochs 2 --batch 32 --lr 3e-3 --seed 0 \
    --theta-max 1.0 --leak-floor 0.85 --gain-cap 1.0 \
    --eval-every 1 --device xpu \
    --out data/checkpoints/scaleup_phase1.pt \
    --report data/intelligence_reports/scaleup_phase1.json
```

> **注意**：`--layers`/`--timesteps` 是否存在於 CLI 要先確認；若不存在，Phase 0 之前
> 需要先加 CLI 參數（這是程式碼變更，需另外登記，不在本計畫的「不訓練」範圍內）。
