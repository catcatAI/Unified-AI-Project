# Hardware-Adaptive Triple-Constraint Plan — 全硬件自適應三約束閉環計劃

> **Version:** 7.5.0-dev  
> **Date:** 2026-09-01  
> **Principle:** 智能↑ / 算力↓ / 體積↓ 三約束帕累托最優, 最小單位深度優化, 全硬件自適應, 零偽裝  
> **Verification Gates:** `pytest 5432 + flake 0 + benchmark 20/20 + du -sh + git 0` 每步前三重檢查, 單步可逆 `git restore`

---

## 1. 最小單位 = 模型驗證, 驗收 = 智能報告 (更正)

**最小單位:** 每模型獨立驗證 `ED3N / GARDEN / multimodal / HAM` 各自 `validate_association / benchmark 20/20` 為一單位, 非硬件檔

**硬件自適應 (全覆蓋):** `hardware_profile.py:152` 5檔 `HIGH_PERF→LOW_POWER` 決定 `ed3n_snn on/off` `max_vocab` `threads`, 但驗收仍以 `模型驗證` 為最小單位, 硬件僅決定 `何智能可在何硬件跑`

| 模型 | 最小單位驗證 | 硬件自適應 |
|---|---|---|
| `ED3N` | `validate_association 4指標 1.0` | `LOW_POWER off` `DESKTOP int8` `SERVER fp32` |
| `GARDEN` | `benchmark 20/20` | `max_vocab 500→100k` |
| `multimodal` | `SSIM/PSNR` `snn 9.6K` | `threshold 0.80` 稀疏 |
| `HAM` | `5000 cap` `5000` | `5000` 限 |

- 限值: `CPU 70%` `RAM 80%` `disk 90%` 超即 `SNN off` 回退 `HAM` 召回, 但驗證仍以模型為單位

---

## 2. 三約束缺口與升徑 (已 `find 10081` 建檔)

| 約束 | 基線 `INTELLIGENCE_ASSESSMENT:95%/1.0` | 瓶頸 | 升徑 (最小單位) |
|---|---|---|---|
| 智能↑ | `確定性 9.5` `20/20 100%` `神經 1.0` `snn.pt 29K` | 關聯僅 3圖, 開放域 `SNN-ONLY 11%` | `關聯 12圖` `train_associations=True` 離線 `KB` 蒸餾 LLM→KB (在線 0 算力) |
| 算力↓ | `37 compute_*` `HAM 5000` `tracer 500` | `dense SNN` | `int8 29K→9.6K 3x` 誤差 `0.003<0.01` + `threshold 0.75→0.80` 稀疏 `30%` + `cache 64` |
| 體積↓ | `src 18M` `trained 136K` `resources 80M` `venv 2.4G` | `Live2D 26M×3` 三倍 | `dedup 80M→27M` + `prune 5000→4000` + `snn int8` |

---

## 3. 檢查→執行 (零失誤, 徹底檢查後動手)

**每步前:** `pytest --collect-only 5432` `flake 0` `benchmark 20/20` `du -sh` `free -h/nvidia-smi` `git diff 0` 四重門檻, 備份 `cp snn.pt snn.pt.bak`

1. **探測:** `hardware_profile.detect()` → 寫 `compute.default.yaml` 對應檔, `LOW_POWER` 自動 `ed3n_snn off`
2. **知識:** `train_pipeline --knowledge-only` 離線補 `KB` 星期/月份接續 → `benchmark` 守門 `20/20`
3. **壓縮:** `snn.pt int8` 量化 + `HAM/multimodal 5000` 限 → `pytest 5432` 守門
4. **證明 (驗收):** `validate_association.py` 四指標 (模型驗證為最小單位) + `benchmark 20/20` → 自動生成 `INTELLIGENCE_ASSESSMENT` 智能報告為驗收, 證明 `何硬件何模型何智能` (如 `LOW_POWER ED3N off→KB only / DESKTOP 1.0 int8 / SERVER 1.0 fp32`)

**回滾:** 任一門檻跌 `git restore` + `cp snn.pt.bak snn.pt`, 無假數據 — 僅 `commonpath` 圍欄 + `allow_pickle False` 真測

---

## 4. 智能報告 (自動生成)

`scripts/benchmark_ed3n_garden.py --report hardware` 輸出 `hardware → 智能` 矩陣, 供 `INTELLIGENCE_ASSESSMENT §4.1.2` 引用, 證明最小單位即最優

> 全程 `shlex` `logger.debug` `413` 圍欄, 確認後按此最小單位完整執行
