# 專案總整頓計畫（PROJECT_CLEANUP_PLAN）

> 狀態：**✅ 全部完成（2026-08-24）**
> 執行驗證：全專案測試掃描 —
> tests/ai 2,101 passed、core/services 1,611、integration 40、api/services/unit/utils
> 1,177（刪除已死 provider 測試後）、security/fragmenta/data/tools 59、
> mcp/models/shared/game/desktop 121、api 140。**合計 ~5,250 passed, 0 failed**。
> 提交：b26456ba（主清理）、3e6317f5（provider 測試移除）
> 日期：2026-08-23
> 觸發：用戶指正「是不是把 AI 模型當整個專案了？」——全量審計證實：
> canonical 引擎（unified_engine）獨享近期全部開發，而三個前身引擎、
> 其 providers、測試、腳本、README 仍活著且互相矛盾。

---

## 0. 審計結論摘要

| 類別 | 發現 |
|---|---|
| 重複引擎 | three_axis（零生產引用）、ed3n（19+ 檔引用、仍在 fallback 鏈）、garden（config 停用但 chat_service 開機仍建構） |
| providers | `providers/ed3n.py`/`garden.py` 計畫早已寫明刪除但未執行 |
| checkpoint | symlink 正確，但 `data_config.py` 被繞過——3 套路徑解析並存，4 處 CWD 相對路徑 |
| config | `standard/compute.default.yaml` 是 stale 副本（§263 定 system/ 為正典）；root configs 雙腦 |
| 測試 | garden/ed3n 套件 489 collect 且 ed3n 已有 7 fail（靜默腐爛）；three_axis 44 pass 測試零生產呼叫者的引擎 |
| 文檔矛盾 | README 仍宣傳 ED3N+GARDEN 為原生 AI、隻字未提 unified_engine；ENGINE.md §8.4 的污染數字未標記被 RESULTS.md 撤回；THREE_AXIS_*.md 自稱藍圖 vs 總綱判死 |
| scripts | train_unified vs train_pipeline(84KB) vs ~15 個 near-duplicate 實驗腳本 |
| zzz | 149 行對話紀錄被 REFACTOR_PLAN 引用為設計依據卻是 untracked 的根目錄裸檔 |

---

## 1. 執行清單（按槓桿排序）

### A. 刪 three_axis（零風險）
- 刪 `apps/backend/src/ai/three_axis/`
- 刪 `scripts/train_three_axis.py`、`scripts/prepare_three_axis_datasets.py`
- 刪 `tests/ai/test_three_axis_*.py`（44 tests，測的是零呼叫者）

### B. providers 收斂
- 刪 `services/llm/providers/{ed3n,garden}.py`
- registry enum 移除對應項
- `llm.default.yaml` fallback chain 改 `unified-1g → ollama-llama3`

### C. chat_service 撤除開機建構（誠實邊界）
- `chat_service.initialize()` 不再建 ED3N/GARDEN engine
- ed3n/garden 模組**保留**（multimodal adapter 等 19 檔仍依賴），但降級為
  「關聯/多模態子系統」——文字推理一律 unified
- 後續真刪需先拆 multimodal_ed3n_adapter（另案）

### D. 文檔同步
- README：AI 架構段改為 unified_engine 為核心、ED3N/GARDEN 標為關聯子系統
- ENGINE.md §8.4 污染數字加「已被 RESULTS.md 撤回」標頭
- NEXT.md baseline 表改引乾淨值
- THREE_AXIS_SCALEUP.md 標頭歸檔說明

### E. 路徑統一
- 全部改走 `core/data_config.get_*_dir()`
- 刪 `apps/backend/src/path_config.py`（指向無人使用的 layout）
- 修 4 處 CWD 相對路徑（multimodal_state_persistence / error_recovery /
  grounded_learning_manager / providers）
- wiki 語料移出 checkpoints/unified/ → `ZX/raw_datasets/corpus/`

### F. configs + zzz
- 刪 `apps/backend/configs/standard/compute.default.yaml`（stale 副本）
- `configs/standard/backbone.default.yaml` 移至 backend configs 或標 deprecated
- `zzz` → `docs/03-technical-architecture/design/DESIGN_NOTES_fixed_core.md`
  + REFACTOR_PLAN 引用更新

### G. checkpoint/scripts 清理
- 刪 11 個過時 npz（保留 full_train + 三語 128k）
- 歸檔 ~20 個 dead trainers 至 `scripts/_archive/`

---

## 2. 驗收

- `pnpm dev:backend` 可啟動、unified 路由優先
- 全量 pytest：legacy 套件移除後剩餘全過
- grep 無 `train_three_axis|providers.ed3n|providers.garden|path_config` 殘留
- README/MD 數字一致（2.403 乾淨基準口徑）
