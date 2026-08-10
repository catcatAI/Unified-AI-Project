<!--
  =============================================================================
  FILE_HASH: TBD
  FILE_PATH: docs/MD_CONSISTENCY_REVIEW.md
  FILE_TYPE: review
  PURPOSE: 主幹線打印（python -m core.backbone dump）對照 docs/ 全量 MD 的
          一致性審查報告 — 標出『MD 內容對不上主幹線/原始碼』的候選。
  VERSION: 7.5.0-dev
  STATUS: review (awaiting human decision)
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-08-10
  AUDIENCE: maintainers
  =============================================================================
-->

# MD ↔ 主幹線一致性審查報告

> **工具**: `scripts/utils/md_consistency_check.py`。
> **方法**: 對每份非歸檔 MD，抽取 CamelCase / snake_case / 大寫縮寫 token，
> 對照（a）`apps/backend/src` 的檔案 stem + class 名（原始碼存在性）、（b）
> 主幹線實際註冊（module/dictionary/memory/matrix/…，`bb.structure()`）。
> coverage = 命中符號數 / 有意義 token 數。
>
> **原則**: 本報告只列候選，**不自行歸檔**。執行中的計畫 MD（EXECUTION_PLAN、
> REPAIR_ROADMAP、backbone 計畫、本份一致性報告等）一律保留。

## 一、首輪掃描統計

| 指標 | 值 |
|---|---|
| 掃描非歸檔 .md | 若干（docs/ 全量減 09-archive） |
| coverage=0.0（原始碼與 backbone 都查無符號）且 tokens≥5 | **163** |
| coverage=0.0 且 tokens<5（極簡/空洞） | 26 |

coverage=0.0 不代表文檔沒價值——可能是**概念/計畫性**文檔（描述目標而非
現存類）。真正應審查歸檔的是「**描述具體功能但該功能原始碼不存在**」者。

## 二、已確認「功能不存在」的高信度候選（示例）

| 文檔 | 描述的功能 | 原始碼實際狀態 |
|---|---|---|
| `docs/03-technical-architecture/api/multi-llm-api.md` | `/api/llm/*` generate/stream 等 endpoint | `api/v1/endpoints/` 僅 audio/drive/mobile/plugins/trace/vision，**無 /api/llm** |
| `docs/03-technical-architecture/analysis/matrix_driven_autonomy_analysis.md` | 列名 token 查無任何 src class | 待人工核 |
| `docs/04-advanced-concepts/linguistic-immune-system.md` | 「語言免疫系統」概念 | 查無對應 class | 
| `docs/03-technical-architecture/enhanced_fault_tolerance_design.md` | 增強容錯設計 | 查無對應實作符號 |

> 註：`matrix_driven_autonomy_analysis.md` 等**分析類**文檔屬概念設計，未必需歸檔。

## 三、主幹線對照現況

主幹線目前 `python -m core.backbone dump` 打印（伺服器啟動註冊後）：
- core_matrix / modules / memories 會反映 lifespan 註冊的實際單例（ChatService、
  DigitalLife、Lifecycle、Heartbeat、CausalReasoning…）。
- dictionaries / free_matrices 反映 SharedLatentSpace + 遊戲卡片字典等。
- connections 列出每 module 的知名內部接線（`state_matrix`、`memory_bridge` 等）。

**凡 MD「主張某元件接進主幹線」而打印上看不到的**，即係審查/修接線的對象
（對應 `ARCHITECTURE_BACKBONE.md` §11.2 標記 🟡/🔴 的子系統）。

## 四、需要人決策的分類建議

- **A 類（建議歸檔）**: 描述具體 API/功能，但 src 完全無對應符號（如 multi-llm-api）。
- **B 類（保留）**: 概念性/分析性/計畫性文檔（matrix_driven…、enhanced_fault_tolerance…）
  即使 coverage=0.0 也有歷史/規劃價值。
- **C 類（保留且需更新）**: 執行中的計畫 MD（backbone 計畫、REPAIR_ROADMAP 等）。

## 五、下一步

1. 用戶確認 A 類清單。
2. 把 A 類移到 `docs/09-archive/`（保留 git 歷史）。
3. 對 🟡/🔴 元件由 `python -m core.backbone dump` 對照 §11.2 逐項修接線或標記移除。

## 附、完整候選清單（coverage=0.0, tokens≥5）— 由工具產生

執行：
```bash
.venv/bin/python scripts/utils/md_consistency_check.py --threshold 0.001
```
即可重現；本報告上方統計即該輸出摘要。完整 163 條清單不在此重印（由工具單一
來源維護，避免雙源漂移）。