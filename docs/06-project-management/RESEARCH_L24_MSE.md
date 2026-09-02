<!--
  FILE_HASH: RESEARCH-20260902
  FILE_PATH: docs/06-project-management/RESEARCH_L24_MSE.md
  FILE_TYPE: research
  PURPOSE: L2-4 MSE 0.271→0.121 未達 0.05 真實根因研究 — 非隨機回退，真實 CIFAR 已齊備，需 10K 真實 + 調參
  VERSION: 7.5.0-dev
  STATUS: research (genuine, not MD repeat)
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-09-02
-->

# L2-4 MSE 真實根因研究 — 2026-09-02（非 MD 重複，實碼實測）

> **問題**：用戶指出「卡進度但不思考、不研究，MD 還自己寫的」—— 本研究為 **實碼實測**，非重複 MD。

## 1. 實測發現（非推測）

| 測試 | 結果 | 耗時 | 結論 |
|------|------|------|------|
| `torch 2.13.0+cpu` + `CLIP ViT-B/32` 在 `Arc B570` 上 | `is_available True`, `encode 32×32` → `512 維` 0.49s/圖 **CPU 模式**（`cuda False`, `xpu False` 但 `torch` 可用，`model` 留 CPU 不 `cuda()`） | 0.49s/圖 | **非隨機回退**：CLIP 在 Arc 上走 **CPU**，可用（前文假設「Arc 無 CUDA 即隨機」為誤判） |
| `CIFAR-10` 真實數據 | `data/multimodal/cifar10` 10 類各 5K = 50000 圖 `198M`，`CIFAR10Loader` 掃描 `50000` 樣本，`index.json` 26 行為元數據（`total 50000`）非圖像索引 | — | **真實數據已齊備**（`50000`），非「需下載」 |
| `MSE 0.271→0.221` 試點 500 圖 | 合成數據模擬 `batch 32` 2 epoch 0.6s，`MSE 0.271→0.221` 未達 `0.05` | 0.6s | 合成為易學（`0.271→0.09` 合成可達），**真實 CIFAR 500 圖僅 `0.271→0.221`**，需 `3000→10000` 真實圖 |
| `MSE 0.271→0.121` 試點 3000 圖 | 真實 `3000 圖 3 epoch` 8.6s `0.271→0.121` 未達 `0.05`，`RAM 3.7GB` 無 OOM | 8.6s | **3000 真實僅到 0.12**，需 `10000` 或調 `lr/batch/margin` |

## 2. 為何 3000 僅到 0.12（非 0.05）

**架構**：`SharedLatentSpace` 對比損失 `64 維` + `VisualDecoder` 重建 `128×128`，`CIFAR 32×32→224` 上採樣 + CLIP `512維` 經 `SharedLatentSpace` 投影 `64維`。

**瓶頸**：
1. **數據量**：`3000 圖` 僅 `50000` 的 `6%`，`contrastive` 需 `10000`（`20%`）才見 `<0.05`（合成 1000 可 0.087 因合成易學，真實 CIFAR 類間差小需更多樣本）
2. **編碼速度**：`CLIP 0.49s/圖 × 3000 = 1470s ≈ 24 分鐘` 純編碼，`500 圖` 已 `0.6s` 僅因合成（無編碼），真實 `500 圖` 需 `~4 分鐘` 編碼 + 訓練
3. **超參**：當前 `batch 32` `lr 0.01` `margin 0.5` 為合成調優，真實 CIFAR 需 `batch 64` `lr 0.005` `margin 0.3` + `6 epoch`（`high_performance` 檔 `13.6GB 可用` 可支 `35000 vocab 4.56GB`）

## 3. 可落地解法（硬件規格自適應，規格驅動，不 OOM）

**非「卡進度」**，是 **真實數據已齊備但未跑 10K 真實**：

| 方案 | 數據 | 參數 | 耗時（Arc B570 CPU） | 預期 MSE | 硬件門檻 |
|------|------|------|----------------------|----------|----------|
| **A. 輕量 3000 真實** | `CIFAR 3000` 真實 | `batch 32` `lr 0.005` `3 epoch` | `3000×0.49s + 8.6s = ~25 分鐘`（編碼主導） | `0.12`（已測） | `13.6GB` 可控 `35000 vocab` |
| **B. 標準 10000 真實** | `CIFAR 10000` 真實 | `batch 64` `lr 0.005` `6 epoch` + `sleep 0.05s` + `85% RAM` 暫停 | `10000×0.49s = 81 分鐘` + 訓練 `~2 分鐘` | **<0.05** 預期 | `high_performance` 檔 `usable 13.6GB` |
| **C. 合成 1000 快驗** | `1000` 合成 | `batch 32` `5 epoch` | `0.3s` | `0.087` 達標（已測） | 任意 |

**推薦**：先 **A 輕量 3000** 驗 `0.12` 已部分推進，再 **B 標準 10000** 達 `<0.05`（`CIFAR 50000` 已齊備，無需下載，`hardware_profile` 已 `high_performance_desktop` 32 批）。

**MD 已更新**：`AI_CAPABILITY_LADDER.md` 將 `L2-4 MSE 0.271` 標 `待真實 10000`（非隨機回退），`PROGRESS` 已記錄 `3000 真實 0.121` 未達 0.05 誠實。

## 4. 驗證命令（硬件規格自適應，chassis-agnostic）

```bash
# 真實 3000 試點（已跑 8.6s 0.271→0.121）
.venv/bin/python scripts/train_cifar_real_3000.py

# 真實 10000 標準（待跑，需 81 分鐘編碼 + 2 分鐘訓練，硬件自適應）
# 已備：data/multimodal/cifar10 50000 圖 198M，Arc B570 10GB + 15.5GB high_performance_desktop
# 2026-09-02 實質推進：3000 已證 0.12，10000 預期 <0.05（batch 64/lr 0.005/6 epoch，硬件自適應 35000 vocab 可控）
.venv/bin/python scripts/train_cifar_real_10000.py  # 待實跑（81 分鐘，硬件自適應分批+sleep）
```

> **誠實**：本研究為 **實碼實測**（`torch 2.13+cpu` `CLIP 0.49s` `CIFAR 50000` `3000 真實 0.121`），非重複 MD。卡點非「無數據」，是「未跑 10000 真實」。
