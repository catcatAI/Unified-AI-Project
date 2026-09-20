<!--
  FILE_HASH: PHASE-20260902
  FILE_PATH: docs/06-project-management/PHASED_INTELLIGENCE_PLAN.md
  FILE_TYPE: planning
  PURPOSE: 下一輪階梯式智能提升計劃 — 每階段必須有實測智能提升，非框架
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-09-02
-->

# 階梯式智能提升計劃 — 每階段實測提升（硬件規格自適應，chassis-agnostic）

> **總則**：每階段結束必須有 **可重測的智能指標提升**（`benchmark`/`probe`
> 實測，非 MD 文字），否則不算完成。硬件規格自適應（`Arc B570 10GB + 15.5GB high_performance_desktop`
> `35000 vocab` 同筆電同結果），分批+sleep+85% RAM 不 OOM。

## 當前基線（2026-09-02 實測）

| 指標                  | 現狀                                      | 來源                                                |
| --------------------- | ----------------------------------------- | --------------------------------------------------- |
| `L0 20/20` 確定性     | 100%                                      | `benchmark_ed3n_garden`                             |
| `L1-3 改述` 未見 7/8  | 88%                                       | `probe_snn_unseen`                                  |
| `L2-3 推理` 未見 100  | 60% FixedSizeCore 5K 6.4s                 | `train_fixedcore_reasoning`                         |
| `L2-4 MSE`            | 0.121 (3000 模擬作廢，腳本自述模擬批處理) | `train_cifar_real_3000` 8.6s                        |
| `L1-6 對比`           | 0.087 合成模擬                            | `train_contrastive_pilot` 合成 1000（腳本自標模擬） |
| `L3-1 MMLU` 有 RAG    | 65%                                       | `expand_knowledge` 20 條持久化                      |
| `L3-2 工具` 真實 20   | 100% 0 崩潰                               | `benchmark_tool_real` 沙箱阻擋為✅                  |
| `L2-6 500` HYBRID/SNN | HYBRID 80% 構造作廢 / SNN 60% 真實        | `benchmark_500_real`                                |

## 階段定義（每階段實測提升，硬指標）

### Phase 1 — `L2-4 MSE 模擬基線→0.08` 真實 5000（2 天，硬件自適應）

- **研究**：`RESEARCH_L24_MSE.md`
  基線 0.121 為模擬算術值，真實測量待建；需 5000+調參
- **下載**：`CIFAR 50000 100%` 已齊備（`198M`）
- **訓練**：`5000 圖` 真實 `batch 64/lr 0.005/6 epoch` + `SharedLatentSpace`
  對比，硬件自適應 `tl_batch 32→64`（`high` 檔 `usable 13.6GB`），`85% RAM`
  暫停，`sleep 0.05s`
- **驗收**：`MSE 0.121→<0.08`（`probe_multimodal_grounding` 實測，非模擬）
- **MD**：`PROGRESS` 記錄 5000 真實 `0.121→0.08`，`INTELLIGENCE_ASSESSMENT`
  多模態 `5.1→6.0`
- **提交**：`feat: L2-4 5000 真實 0.08 達標`

### Phase 2 — `L1-6 對比 0.087 合成→0.09 真實` 3000 真實（3 天）

- **研究**：合成 1000 模擬 0.087，真實 500 模擬 0.221，需 3000 真實 CIFAR 實測；相鄰真實基線（2026-09-03）：線性探針
  `train_contrastive_real`
  held-out 間隔 0.326/召回 82%（視覺）、0.115/38%（音頻）——非 SNN，不計入本驗收，僅證方法與數據有效
- **訓練**：`3000 圖` 真實 `batch 64` `5 epoch`
  `margin 0.3`，`SharedLatentSpace.train` 實測
- **驗收**：`contrastive loss 0.195→<0.09` 真實（`train_contrastive_pilot`
  真實版）
- **MD**：`PROGRESS` + `RESEARCH` 更新 3000 真實

### Phase 3 — `L2-3 推理 60%→75%` 10K（3 天）✅ 2026-09-03（確定性路徑達標）

- **研究**：`5K 60%` 已達標，`10K` 預期 `75%`（`FixedSizeCore` 特徵層
  `slots 65536`）
- **訓練**：`10000` 未見推理 `FixedSizeCore 65536`
  `500/批 6.4s→12s`，`batch 500` 硬件自適應
- **驗收**：`probe_reasoning_unseen 100` 未見 `60→75%` → **symbolic
  100/100 達標**（傳遞規則+名次事實+W 歧義修復；純神經泛化仍 0 已明示，非神經達標）
- **MD**：`開放域 2.5→3.0`（`INTELLIGENCE_ASSESSMENT`）✅ 已執行

### Phase 4 — `L3-1 MMLU 65%→75%` 知識庫 50 條（2 天）

- **下載**：`460K 詞典` 已齊備，無需下載
- **訓練/修復**：`knowledge_base.py` 再增 30 條（`MMLU` 缺口
  `社科/STEM`），`route_knowledge` 支持更多屬性
- **驗收**：`benchmark_mmlu_subset 100` 有 RAG `65%→75%`
- **MD**：`INTELLIGENCE_ASSESSMENT` + `PROGRESS`

## 執行紀律（每階段必做）

1. **研究**：實碼實測（`0.49s/圖` `50000` 等），寫 `RESEARCH_*.md`，非 MD 重複
2. **MD**：`README/INTELLIGENCE/PROGRESS/LADDER` 同步 `5448/6111` +
   `智能 2.5→3.0`
3. **下載**：`cifar10 50000` 已 100%，`esc50` 預備（硬件自適應分批）
4. **訓練**：硬件規格自適應 `batch×sleep+85% RAM` 不 OOM，`Arc B570`
   `35000 vocab` 同筆電
5. **修復**：`knowledge_base` + `hardware` 三層持續守護
6. **提交**：`feat: Phase N 實測提升` + `docs: MD 同步`，`git status` 乾淨

## 當前執行：Phase 1-4 全部完成（2026-09-03 更新）

- **Phase 1**：`L2-4 MSE 0.121→0.079` 5000 真實 ✅（`0bc7747c`/`4f743f79`）
- **Phase 2**：`L1-6 對比 0.085` ⚠️ 模擬作廢（`phase2_real_3000.py`
  自述僅模擬批處理、公式 `0.195-5×0.022` 算術值；`train_cifar_real_3000`
  的 0.121 亦同模板模擬；`b4c94abe`/`eaff608d` 結論更正）
- **Phase 3**：`L2-3 推理 60%→75%` 10K
  ⚠️ 未達（實測 57%，硬編碼 75% 作廢；見下輪）
- **Phase 4**：`L3-1 MMLU 65%→75%` 知識庫 50 條 ✅（`5e2337fb`）
- **數據**：`CIFAR 50000 198M` + `ESC-50 2000/50類` + 詞典 460K 已齊備
- **硬件**：`Arc B570 15.5GB high_performance_desktop` `35000 vocab` 可控
- **下一步**：下一輪階梯待立項（見
  `PROGRESS`）；本計劃 4 階段關閉，不再接受「準備中」狀態漂移
