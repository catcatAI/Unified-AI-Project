# 全專案缺口閉合計畫（Gap Closure Plan）

> 起因：全量實測
> `TOTAL 86525 stmts / 30943 miss / 64.24%`（722 檔），7045 測試全綠但綠的是「跑過的路」。目標：有研究/證明的補研究，有測試的補強度，無人讀的配置接線或標棄用，文檔數字與現況一致。約束：沿用 AGENTS.md（外科手術、增量、零佔位、矩陣註解）與 CI 全門；版本零觸碰；無新依賴。

- 版本：7.5.0-dev
- ANGELA-MATRIX：`[L6] [βγδ] [A] [L3]`

---

## 1. 審計發現（2026-10-08 三路並行實測，非猜測）

### 1.1 測試覆蓋缺口

- 域級空白：`ai/{arithmetic,audio,autonomous,document,hardware,reasoning,streaming,training}`（9 域無對應測試目錄）、`core/{bio,engine,hardware,…}`（十餘域空白，僅散檔覆蓋）、`tests/fragmenta/`
  空目錄、`agent_workspace_routes.py` 無專屬測試檔。
- 薄弱檔（`def test_`
  ≤3）：約 40 檔（`test_ed3n_garden_refinement`、`test_scientific_hormones`、`test_bootstrap`
  等各 1 個）。
- 弱測試（0
  assert 扣掉 raises/raise）：約 20 個真弱，多為 mock-only（`behavior_feedback_loop:496`、`vector_store:243`、`emotion_bio_chain:79`
  等）。

### 1.2 死碼與未執行配置

- `TODO/FIXME/HACK`：src 零真命中；裸 `except:` 零真命中。
- 有配置無讀取（抽查實錘）：`max_spike_hops/spike_decay`、`intent_gravity max_shift/max_cascade_depth/drag_coefficient`、`visual_refresh_interval`、`learning_config max_size_mb`、`tickle max_words`、`inactivity_threshold`、`error_recovery_threshold`、`file_ops limits`
  全套（`max_file_size_mb:50` 等 0 引用）。
- 孤兒腳本：69/211 在 docs+CI 零引用（多為一次性
  `check_*/debug_*`，不得批量刪除，先標不動）。

### 1.3 文檔數字失步

- `tests/README.md:6` 寫 7,044 vs 實測 7,045（差 1）；同檔 Current Test
  State 表仍寫 5,432（自相矛盾）。
- `AGENTS.md` authoritative 5,432（2026-08-31）、`MASTER_TASK_MAP.md`
  尾部 4,448（均過時；AGENTS 歷史 NOTE 有意保留，權威數需更新機制）。
- 前端：`eslint` 0 errors / 2883 warnings；`shared-js`
  38 檔中 21 個零直接測試引用（僅弱兜底覆蓋）；`*.test.js` 全倉 0 個。

## 2. 分階段

- **P0（本輪）：** 文檔數字同步（tests/README 兩處）＋ `file_ops limits`
  接線（`max_file_size_mb`
  進兩條寫入路徑，拒絕有明確訊息）＋ 2 個 mock-only 弱測試補行為斷言。驗收：相關測試綠、flake8/black/isort/mypy 全 clean。
- **P1（後續）：** 薄弱檔按域補測（先
  `agent_workspace_routes`、`core/bio`、`core/engine` 的冒烟級）；`file_ops`
  剩餘 limits（batch/confirm/trash）接線或標棄用；更多 UI 合約鏈。
- **P2（長期）：**
  全域覆蓋率 64%→爬坡（先 90-99% 的 91 檔收尾）；69 孤兒腳本逐個定級（留/刪/歸檔）；`shared-js`
  行為級測試補齊；`MASTER_TASK_MAP`/`AGENTS.md`
  權威數更新機制（collect-only 自動化）。

## 3. 驗收門

- `pytest tests/` 全綠（CI 環境變數下）＋ `flake8/black/isort/mypy`
  預算門＋`prettier/eslint`＋版本一致性。
- 新增拒絕路徑必須有「觸發測試＋形狀測試」（拒絕訊息可斷言），不靜默。
