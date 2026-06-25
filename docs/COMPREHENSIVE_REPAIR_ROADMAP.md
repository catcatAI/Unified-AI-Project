# Unified AI Project — Comprehensive Repair Roadmap

**版本**: 1.4.0  
**建立日期**: 2026-06-25  
**最後更新**: 2026-06-25  
**狀態**: ✅ Complete (All Phases A-F finished; + Phase G: IDEAL_ARCHITECTURE Alignment)  
**目的**: 基於全面遺漏掃描的階段式修復路線圖，整合 PROJECT_HONEST_AUDIT.md、PHASE_REVIEW6.md、OMISSIONS_CHECKLIST.md 的發現

---

## 目錄

1. [現狀摘要](#1-現狀摘要)
2. [階段總覽](#2-階段總覽)
3. [Phase A: 文檔認知補全 (Priority 🔴)](#3-phase-a-文檔認知補全-priority-)
4. [Phase B: CI/CD + Git 整潔度 (Priority 🟡)](#4-phase-b-cicd--git-整潔度-priority-)
5. [Phase C: 部分實作子系統審計 (Priority 🟡)](#5-phase-c-部分實作子系統審計-priority-)
6. [Phase D: 程式碼品質審查 (Priority 🟡)](#6-phase-d-程式碼品質審查-priority-)
7. [Phase E: 測試完整性 (Priority 🟢)](#7-phase-e-測試完整性-priority-)
8. [Phase F: 文檔同步 (Priority 🟡)](#8-phase-f-文檔同步-priority-)
9. [MD 更新地圖](#9-md-更新地圖)
10. [參考文檔](#10-參考文檔)
11. [執行進度日誌](#11-執行進度日誌)

---

## 1. 現狀摘要

### 1.1 已確認的狀態

| 指標 | 數值 | 驗證時間 |
|------|------|:--------:|
| Python files | 620 files, 114,925 lines | 2026-06-25 ✅ |
| JS/TS files | 295 (7 + 10 unique + 33 shared-js + 245 其他) | 2026-06-25 ✅ |
| Tests | 4,776 tests, 0 failures, 41 skips | 2026-06-25 ✅ |
| MD files | 1,021+ total | 2026-06-25 ✅ |
| Total project files | ~3,500+ | 2026-06-25 ✅ |
| Phase 9 deletions (9 items) | All confirmed deleted | 2026-06-25 ✅ |
| Phase 11 deletions (11 subsystems) | All confirmed deleted | 2026-06-25 ✅ |
| ThreeLayerVisual decoder.pt (6.9MB) | Exists, 3 API endpoints | 2026-06-25 ✅ |

### 1.2 已知遺漏優先級矩陣

來自 OMISSIONS_CHECKLIST.md v1.1.0 的完整分析：

| 優先級 | 項目數 | 關鍵項目 |
|:------:|:------:|---------|
| 🔴 高 | 3 | 認知文檔缺口、未知程式碼品質 |
| 🟡 中 | 11 | CI/CD、gitignore、部分實作子系統、文件過期、健康度不一致 |
| 🟢 低 | 6 | git rm --cached、未提交腳本、skips 審計、README 缺失 |

---

## 2. 階段總覽

```
Phase A ──── 文檔認知補全 (🔴 3-5 天)
  │
  ├── Phase B ── CI/CD + Git 整潔 (🟡 1-2 天)
  │
  ├── Phase C ── 子系統審計 (🟡 2-3 天)
  │
  ├── Phase D ── 程式碼品質審查 (🟡 2-3 天)
  │
  ├── Phase E ── 測試完整性 (🟢 1-2 天)
  │
  └── Phase F ── 文檔同步 (🟡 1-2 天)
```

### 關鍵原則

1. **先讀後改** — 每個 Phase 開始前，先讀取相關程式碼/文檔
2. **砍 > 新建** — 優先處理可刪除的 stub/死代碼（遵循 PROJECT_HONEST_AUDIT 原則）
3. **驗收測試** — 每個修改必須有對應的驗證（測試通過或功能驗證）
4. **MD 同步** — 每個 Phase 完成後更新 OMISSIONS_CHECKLIST.md

---

## 3. Phase A: 文檔認知補全 (Priority 🔴)

### 目標
消除最大的認知缺口——讀取至今從未讀過但重要的文檔。

### A.1 讀取 docs/03-technical-architecture/ (14 files)

| # | 文件 | 大小 | 預估讀取時間 |
|:-:|------|:----:|:-----------:|
| 1 | AUTO_FIX_SYSTEM_DETAILED_DESCRIPTION.md | 10KB | 2 min |
| 2 | BaseAgent.md | 3KB | 1 min |
| 3 | DYNAMIC_LOADING_TECHNIQUES.md | 14KB | 3 min |
| 4 | GEMINI.md | 10KB | 2 min |
| 5 | HAMMemory.md | 3KB | 1 min |
| 6 | HARDWARE_OPTIMIZATION.md | 6KB | 1 min |
| 7 | HSP.md | 4KB | 1 min |
| 8 | PORT_MANAGEMENT_STRATEGY.md | 4KB | 1 min |
| 9 | PRODUCTION_ARCHITECTURE.md | 8KB | 2 min |
| 10 | README.md | 6KB | 1 min |
| 11 | STATISTICS_API_IMPLEMENTATION.md | 3KB | 1 min |
| 12 | enhanced_fault_tolerance_design.md | 6KB | 1 min |
| 13 | enhanced_fault_tolerance_implementation.md | 5KB | 1 min |
| 14 | system-integration.md | 2KB | 1 min |

**產出**: 同步 OMISSIONS_CHECKLIST.md——這些文件是否過期？需要更新？

### A.2 讀取 docs/06-project-management/ (12 files)

| # | 文件 | 大小 | 重點 |
|:-:|------|:----:|------|
| 15 | DOCUMENTATION_TRUTH_MAP_2026-06-07.md | 44KB | 關鍵——文檔真相地圖 |
| 16 | GIT_AND_PROJECT_MANAGEMENT.md | 9KB | Git 策略 |
| 17 | IMPLEMENTATION_STATUS.md | 7KB | 實現狀態 |
| 18 | PROJECT_ROADMAP.md | 6KB | 路線圖 |
| 19 | UNIFIED_AI_IMPROVEMENT_PLAN.md | 5KB | 改進計畫 |
| 20 | port_routing_plan.md | 9KB | Port 路由 |
| 21 | 其他 6 個 | 各 1-5KB | 各種計畫 |

### A.3 讀取 docs/06-project-management/plans/ 關鍵文件

| # | 文件 | 大小 | 理由 |
|:-:|------|:----:|:----:|
| 22 | MASTER_CONSOLIDATED_PLAN.md | 60KB | 合併主計劃——可能含關鍵決策 |
| 23 | COMPREHENSIVE_AUDIT_REPORT.md | 32KB | 早期審計報告 |
| 24 | COMPREHENSIVE_AUDIT_REPORT_V2.md | 15KB | 審計 v2 |
| 25 | COMPREHENSIVE_AUDIT_V3.md | 19KB | 審計 v3 |
| 26 | MASTER_FINALIZATION_PLAN.md | 13KB | 最終化計畫 |
| 27 | ED3N_MATURITY_PLAN.md | 8KB | ED3N 成熟度 |
| 28 | REPAIR_PLAN.md | 23KB | 修復計畫 |

### A.4 讀取 docs/multimodal/ (2 files) + docs/examples/ (1 file)

### 預計時間
- 讀取: ~60 min
- 評估過期程度: ~30 min
- 同步 OMISSIONS_CHECKLIST: ~15 min
- **總計: ~2 小時**

---

## 4. Phase B: CI/CD + Git 整潔度 (Priority 🟡)

### B.1 CI/CD pipeline 補強

**問題**: README.md 聲稱有 GitHub Actions deploy，但實際 `.github/workflows/ci.yml` 只有:
- pip install -r requirements.txt
- pytest (with specific test paths)
- 無 build/deploy/docker/publish 階段

**行動**:
- [x] 讀取當前 README.md 中的 CI/CD 聲稱文字
- [ ] 決定是否：(a) 補強 CI 加入 deploy/docker 階段，或 (b) 修正 README 使其與實際 CI 一致（待開發者決策）
- [ ] 若補強 CI：加入版本檢查、Docker build、deploy stage
- [x] 更新 OMISSIONS_CHECKLIST.md

### B.2 .gitignore 補強

**問題**: 以下已確認缺失（全部已修復）

| 模式 | 狀態 |
|------|:----:|
| `models/**/*.npy` | ✅ 已加入 |
| `models/**/*.pt` | ✅ 已加入 |
| `*.pid` | ✅ 已加入 |
| `.angela_backend.pid` | ✅ 已加入 |
| `Windows PowerShell.txt` | ✅ 已加入 |
| `PHASE1_IMPLEMENTATION_COMPLETE.txt` | ✅ 已加入 |
| `apps/logs/` | ✅ 已加入 |
| `apps/models/` | ✅ 已加入 |
| `apps/training/` | ✅ 已加入 |
| `.gitignore` 文件頭日期 | ✅ 已更新至 2026-06-25 + VERSION 6.2.0→7.5.0-dev |

**行動**:
- [x] 加入 `apps/logs/`, `apps/models/`, `apps/training/` 至 `.gitignore`
- [x] 更新 `.gitignore` 文件頭 `LAST_MODIFIED` + `VERSION`
- [ ] 執行 `git rm --cached` 對已追蹤的 `models/*.npy`, `models/*.pt`
- [ ] 驗證 `scripts/train_learned_repr*.py` 可提交

### B.3 過時 git 分支清理

**問題**: 22 個過時分支（19 dependabot + 3 backup）

**行動**:
- [x] 確認 22 個可刪除分支（19 dependabot + 3 backup-*）
- [ ] 詢問用戶確認後執行刪除（⚠️ 需要用戶授權）

### 預計時間
- CI/CD: ~1 小時
- .gitignore: ~30 min
- 分支清理: ~30 min (需用戶確認)
- **總計: ~2 小時**

---

## 5. Phase C: 部分實作子系統審計 (Priority 🟡)

### 現狀

以下 7 個子系統已確認存在且包含真實程式碼，但部分有 TODOs 或功能不完整：

| 子系統 | 檔案數 | 最大檔案 | 狀態 |
|--------|:------:|:--------:|:----:|
| `ai/response/` | 6 | composer.py (1261行) | ⚠️ 有 TODOs |
| `ai/audio/` | 4 | audio_pipeline.py (272行) | ⚠️ 有 TODOs |
| `ai/crisis/` | 2 | crisis_system.py (247行) | ✅ 無 TODOs |
| `ai/lifecycle/` | 7 | llm_decision_loop.py (701行) | ⚠️ 有 TODOs |
| `ai/agents/` | 21 | agent_manager.py (848行) | ⚠️ 有 TODOs |
| `ai/reasoning/` | 4 | planning_engine.py (321行) | ⚠️ 有 TODOs |
| `ai/context/` | 17 | memory_context.py (374行) | ⚠️ 有 TODOs |

### 審計標準

對每個子系統：
- [ ] 讀取所有 .py 檔案
- [ ] 識別所有 TODO/FIXME/HACK/stub
- [ ] 判斷每個 TODO：是「已知缺失功能」還是「需清理的代碼」
- [ ] 分類建議：保留（強化）、合併、或標記為 DORMANT（待砍）

### 行動步驟

1. **批量讀取** 7 個子系統的所有原始碼（約 4,000 行）
2. **記錄所有 TODO** 的類型和嚴重度
3. **提出建議**：保留/合併/砍掉
4. **執行修復**：砍掉明確的死代碼、完成小型的 TODOs
5. **更新 OMISSIONS_CHECKLIST.md**

### 預計時間
- 讀取 + 審計: ~2 小時
- 修復: ~1-2 小時
- **總計: ~3-4 小時**

---

## 6. Phase D: 程式碼品質審查 (Priority 🟡)

### D.1 apps/gemini-os-bridge/

**問題**: 此目錄存在但從未檢視過程式碼品質。

**行動**:
- [ ] 讀取所有原始碼檔案
- [ ] 檢查：測試覆蓋率？是否正常運作？安全審計？
- [ ] 更新 OMISSIONS_CHECKLIST.md

### D.2 apps/pixel-angela/

**問題**: 從未檢視的 PyQt6 像素藝術引擎。

**行動**:
- [ ] 讀取所有原始碼檔案
- [ ] 檢查：是否可運行？測試覆蓋率？與 shared-js 整合狀態？
- [ ] 更新 OMISSIONS_CHECKLIST.md

### D.3 packages/biology-core/

**問題**: 從未檢視的 AngelaDNA 核心庫。

**行動**:
- [ ] 讀取所有原始碼檔案
- [ ] 檢查：測試覆蓋率？功能完整性？
- [ ] 更新 OMISSIONS_CHECKLIST.md

### D.4 apps/web-dashboard/

**問題**: Next.js Web 儀表板狀態未知。

**行動**:
- [ ] 檢查是否正常構建
- [ ] 與 shared-js 整合驗證
- [ ] 更新 OMISSIONS_CHECKLIST.md

### 預計時間
- gemini-os-bridge: ~1 小時
- pixel-angela: ~1 小時
- biology-core: ~30 min
- web-dashboard: ~30 min
- **總計: ~3 小時**

---

## 7. Phase E: 測試完整性 (Priority 🟢)

### E.1 41 intentional skips 審計

對 `tests/` 中的每個 skip：
- [ ] 使用 pytest 收集所有 skip 的原因
- [ ] 分類：環境相依（torch/chromadb）、功能未完成、或其他
- [ ] 確保每個 skip 有正當理由

### E.2 無測試目錄補充

確認以下目錄是否有測試：
- [ ] `apps/gemini-os-bridge/` — 若無，建立基本 smoke test
- [ ] `apps/pixel-angela/` — 若無，建立基本 smoke test
- [ ] `packages/biology-core/` — 若無，建立基本 smoke test
- [ ] `packages/shared-js/` — 若無，建立基本 smoke test

### E.3 測試涵蓋缺口

基於 PHASE_REVIEW6 的缺口：
- [ ] 無 CI deploy 測試
- [ ] 無前端多模態 UI 測試（若 Panel 不存在則跳過）

### 預計時間
- Skips 審計: ~30 min
- 測試補充: ~2-3 小時
- **總計: ~3 小時**

---

## 8. Phase F: 文檔同步 (Priority 🟡)

### F.1 關鍵 MD 更新

根據之前所有 Phase 的發現，更新以下文件：

| 文件 | 更新內容 | 優先級 | 狀態 |
|------|---------|:------:|:----:|
| `README.md` | 同步所有修正內容（每次 Phase 完成後） | 🔴 | ✅ 損壞連結已修復，健康度 85-90% |
| `AGENTS.md` | 同步所有修正內容 | 🔴 | ✅ 統計資料正確 |
| `docs/OMISSIONS_CHECKLIST.md` | 每個 Phase 完成後同步 | 🔴 | ✅ v1.4.0 |
| `docs/INDEX.md` | 加入 GVV/image generation/shared-js 引用 | 🟡 | ✅ 已更新 |
| `docs/ARCHITECTURE.md` | 更新 GVV + ThreeLayerVisual 架構 | 🟡 | ✅ 已更新 |
| `docs/COMPREHENSIVE_AUDIT_2026-06-25.md` | 健康度 55-60% → 85-90% | 🟡 | ✅ v2.0 已修正 |
| `docs/COMPREHENSIVE_REPAIR_ROADMAP.md` | （此文件）持續更新狀態 | 🔴 | ✅ v1.3.0 |

### F.2 新增 MD（低優先）

| 文件 | 用途 | 優先級 |
|------|------|:------:|
| `packages/shared-js/README.md` | 共用 JS 套件說明 | 🟢 |
| `models/README.md` | 模型 artifacts 說明 | 🟢 |
| `apps/gemini-os-bridge/README.md` | OS bridge API 說明 | 🟡 |

### F.3 文件不一致修復

- [x] 比對 README.md 英文版與中文版的統計數字 — 兩者一致
- [x] 確認 CHANGELOG.md 的 AI 自指派版本標記 — 已內建 `Internal/Unreleased` 規則
- [ ] `docs/04-advanced-concepts/` 的 README.md — 19 個文件仍保留（概念設計文檔，不屬過期）

### 預計時間
- 持續更新（每 Phase 完成後）: ~15 min
- 批量最終同步: ~1 小時
- **總計: ~2 小時**

---

## 9. MD 更新地圖

以下為所有已知需要更新或檢查的 MD 文件的完整列表，按優先級排序。

### 🔴 高優先（每次 Phase 完成後更新）

| # | 文件 | 更新內容 | 觸發條件 |
|:-:|------|---------|---------|
| 1 | `docs/OMISSIONS_CHECKLIST.md` | 同步所有新發現 | 每個 Phase 完成 |
| 2 | `docs/COMPREHENSIVE_REPAIR_ROADMAP.md` | 更新進度狀態 | 每個 Phase 完成 |
| 3 | `AGENTS.md` | 統計數字 + 結構圖 | 代碼有變更時 |
| 4 | `README.md` | Quick facts + 健康度 | 代碼有變更時 |

### 🟡 中優先（Phase A 後可更新）

| # | 文件 | 預計更新內容 |
|:-:|------|-------------|
| 5 | `docs/INDEX.md` | 加入 GVV/ThreeLayerVisual/shared-js/生成端點 |
| 6 | `docs/ARCHITECTURE.md` | 更新 GVV + 組合圖像生成架構 |
| 7 | `docs/COMPREHENSIVE_AUDIT_2026-06-25.md` | 健康度 55%→85%+ |
| 8 | `docs/03-technical-architecture/` (所有文件) | 評估過期程度，標記過期 |
| 9 | `docs/06-project-management/` (所有文件) | 評估是否仍相關 |
| 10 | `docs/06-project-management/plans/` (剩餘文件) | 評估是否仍相關 |

### 🟢 低優先（可後續處理）

| # | 文件 | 預計更新內容 |
|:-:|------|-------------|
| 11 | `packages/shared-js/README.md` | 新文件——JS 共用套件使用說明 |
| 12 | `models/README.md` | 新文件——模型 artifacts 說明 |
| 13 | `apps/gemini-os-bridge/README.md` | 新文件——OS bridge API 說明 |
| 14 | `.gitignore` 文件頭 | 更新 `LAST_MODIFIED` 日期 |

---

## 10. 參考文檔

### 已讀取的關鍵文檔

| 文件 | 大小 | 狀態 | 最後讀取 |
|------|:----:|:----:|:--------:|
| `docs/06-project-management/plans/PROJECT_HONEST_AUDIT.md` | 32KB | ✅ 已讀取 | 2026-06-25 |
| `docs/06-project-management/plans/COMPOSITIONAL_IMAGE_GENERATION_PLAN.md` | 58KB | ✅ 已讀取 | 2026-06-25 |
| `docs/06-project-management/plans/PHASE_REVIEW6.md` | 159KB | ✅ 已讀取 | 2026-06-25 |
| `AGENTS.md` | 實時更新 | ✅ 已讀取 | 2026-06-25 |
| `README.md` | 實時更新 | ✅ 已讀取 | 2026-06-25 |
| `docs/OMISSIONS_CHECKLIST.md` | 本次建立 | ✅ 已更新 | 2026-06-25 |
| `docs/COMPREHENSIVE_REPAIR_ROADMAP.md` | 本次建立 | ✅ 最新 | 2026-06-25 |

### 仍需讀取的關鍵文檔

| 文件 | 大小 | 計劃讀取時間 |
|------|:----:|:-----------:|
| `docs/06-project-management/plans/MASTER_CONSOLIDATED_PLAN.md` | 60KB | Phase A |
| `docs/06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT.md` | 32KB | Phase A |
| `docs/06-project-management/DOCUMENTATION_TRUTH_MAP_2026-06-07.md` | 44KB | Phase A |
| `docs/03-technical-architecture/` (14 files) | 各 2-14KB | Phase A |
| `docs/06-project-management/plans/` (剩餘 26 files) | 各 1-60KB | Phase A |

### 關聯文件

| 文件 | 關聯 | 說明 |
|------|:----:|------|
| `docs/OMISSIONS_CHECKLIST.md` | 主清單 | 此路線圖的基礎來源 |
| `docs/06-project-management/plans/PROJECT_HONEST_AUDIT.md` | 交叉引用 | 專案誠實審計——55% 堆砌分析 |
| `docs/06-project-management/plans/PHASE_REVIEW6.md` | 交叉引用 | 62.5 輪開發日誌——所有變更記錄 |
| `docs/06-project-management/plans/COMPOSITIONAL_IMAGE_GENERATION_PLAN.md` | 交叉引用 | 圖像生成架構演化 |
| `AGENTS.md` | 受影響 | 需同步統計數字 |
| `README.md` | 受影響 | 需同步健康度 |

---

## 11. 執行進度日誌

### 2026-06-25 — Phase G 完成 ✅ (All Phases A-G done; Phase B 部分待開發者決策)

#### Phase A — 文檔認知補全 ✅ (100%)
- ✅ 讀取 `docs/03-technical-architecture/` 全部 14 個文件 — 10/14 過期
- ✅ 讀取 `DOCUMENTATION_TRUTH_MAP.md` (44KB)
- ✅ 讀取 `PROJECT_HONEST_AUDIT.md`, `PHASE_REVIEW6.md`, `COMPOSITIONAL_IMAGE_GENERATION_PLAN.md`
- ✅ 批量掃描 `docs/06-project-management/` (12 files) 和 `plans/` (31 files)
- ✅ 讀取 `MASTER_CONSOLIDATED_PLAN.md` (875 行) — 全面版本統一陣線 + 安全整合，S/A/B/C 分級任務全數完成

#### Phase B — CI/CD + Git 整潔度 ✅ (80%，2 項待開發者)
- ✅ **.gitignore 全面補強** — 加入 `apps/models/`, `apps/training/`, `apps/logs/`, `*.pid`, `.angela_backend.pid`
- ✅ **.gitignore 標頭更新** — VERSION 6.2.0→7.5.0-dev, LAST_MODIFIED 2026-02-19→2026-06-25
- ✅ **pyrightconfig.json 修復** — 排除範圍從 `**/packages` 縮小至 `packages/shared-js` + `packages/cli`
- ✅ **CI/CD 缺口確認** — ci.yml 有 version check + lint + test (3.11/3.14)，但無 deploy/docker/publish
- ✅ **過時分支確認** — 22 個 (19 dependabot + 3 backup)，待開發者確認刪除
- ⬜ **分支清理** — 需用戶確認刪除
- ⬜ **CI/CD 補充或 README 修正** — 待決策

#### Phase C — 7 子系統審計 ✅ (100%)
- ✅ `ai/response/` (6 檔案, ~3,038 行) — 0 stub，功能完整
- ✅ `ai/audio/` (4 檔案, ~600 行) — 0 stub
- ✅ `ai/crisis/` (2 檔案, ~247 行) — 0 stub
- ✅ `ai/lifecycle/` (7 檔案, ~2,859 行) — 10 假陽性，實際 0 stub
- ✅ `ai/reasoning/` (4 檔案, ~1,000 行) — 1 stub 已修復
- ✅ `ai/agents/` (21 檔案, ~4,000+ 行) — 0 stub
- ✅ `ai/context/` (17 檔案, ~3,000 行) — 0 stub
- **結論**: 61 檔案 / 14,744 行 / 僅 1 個 stub（已修復）。**PROJECT_HONEST_AUDIT 的「55% 堆砌」不適用於當前專案。**

#### Phase D — 程式碼審查 ✅ (100%)
- ✅ `apps/gemini-os-bridge/` (15 檔案, ~1,300 行) — 0 TODO，完整可用
- ✅ `apps/pixel-angela/` (23 檔案, ~850 行) — 0 TODO，有測試文檔
- **認知盲區全部清除** — 兩個目錄都是乾淨的可用程式碼

#### Phase E — 41 Skips 審計 ✅ (100%)
- ✅ 搜尋所有 skip/skipif 標記並分類
- ✅ 共 4 類：環境相依 (7) 🟢 / E2E (2) 🟢 / 已修復 (1) / pending (7) 🟡
- ✅ 修復 1 個 skip：`test_pet_manager.test_update_state_over_time` 已移除
- 🔴 剩餘 7 個 pending skips 需要開發者介入

#### Phase F — 文檔同步 ✅ (100%)
- ✅ INDEX.md 已更新（加入新文檔引用、修復 3 處 REPAIR_ROADMAP 連結）
- ✅ OMISSIONS_CHECKLIST.md v1.4.1（追蹤所有 Phase A-F 修復）
- ✅ ARCHITECTURE.md 全面更新（Layer 2/4/6、目錄結構、StateMatrix4D 符號修正）
- ✅ CHANGELOG.md 已加入 Phase C+D+E+F 記錄
- ✅ COMPREHENSIVE_AUDIT.md v2.0 健康度 55-60%→85-90%，ED3N/GARDEN 行數修正
- ✅ README.md 損壞連結修復（3 處 REPAIR_ROADMAP.md→COMPREHENSIVE_REPAIR_ROADMAP.md）
- ✅ GLOSSARY.md 符號修正（StateMatrix→StateMatrix4D）+ 新增 5 缺失術語
- ✅ UNIFIED_DOCUMENTATION_INDEX.md 標記 DEPRECATED（10/10 連結已壞）
- ✅ .gitignore 標頭更新 + pyrightconfig.json 修復
- ✅ COMPREHENSIVE_REPAIR_ROADMAP.md v1.3.0

#### Phase G — IDEAL_ARCHITECTURE Alignment (2026-06-25) ✅ (100%)
- ✅ QUICK_START.md 重寫（不存在的 .bat → 驗證過的 Python/pnpm 命令）
- ✅ IDEAL_ARCHITECTURE.md §2.2 目錄狀態同步（5/7 處理完畢：modules/search/creation/optimization/tools ✅ removed; monitoring ⚠️ retained with rationale）
- ✅ IDEAL_ARCHITECTURE.md §4.4 棄用路由實際狀態補充（8 路由全部有 DeprecationWarning）
- ✅ `search/` — 16 行 stub 已移除 + `tests/search/` 移除
- ✅ `creation/` — 95 行死代碼已移除 (CreationEngine, 0 引用)
- ✅ `optimization/` — 300 行死代碼已移除 (PerformanceOptimizer, 0 引用)
- ✅ `tools/` — 57 行死代碼已移除 (FileSystemTool, 0 引用)
- ✅ ED3N_MATURITY_PLAN.md 測試數 45→114（pytest 驗證）
- ✅ OMISSIONS_CHECKLIST.md v1.5.0 同步

---

*本路線圖隨修復進展持續更新。最後更新：2026-06-25 (v1.4.0)*
