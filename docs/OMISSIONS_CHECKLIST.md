# Unified AI Project — 遺漏清單 (Omissions Checklist)

**版本**: 1.0.0  
**最後更新**: 2026-06-25  
**狀態**: Active  
**目的**: 紀錄專案中所有已知的遺漏、不完整、不一致之處，確保透明化管理

---

## 目錄

1. [認知遺漏 — 我不清楚的區域](#1-認知遺漏--我不清楚的區域)
2. [文件遺漏 — MD 過期/廢棄/不一致](#2-文件遺漏--md-過期廢棄不一致)
3. [任務遺漏 — 修復任務的真實完成度](#3-任務遺漏--修復任務的真實完成度)
4. [Git 遺漏 — 版本控制整潔度](#4-git-遺漏--版本控制整潔度)
5. [安全遺漏](#5-安全遺漏)
6. [配置遺漏](#6-配置遺漏)
7. [程式碼遺漏](#7-程式碼遺漏)
8. [測試遺漏](#8-測試遺漏)
9. [總結與優先級](#9-總結與優先級)

---

## 1. 認知遺漏 — 我不清楚的區域

### 1.1 存在但未深入探索的目錄

| 目錄 | Git 追蹤 | 已知用途 | 未知/風險 |
|------|:--------:|---------|-----------|
| `apps/gemini-os-bridge/` | ✅ 已追蹤 | OS 自動化微服務 | ❓ 程式碼品質未知，文檔覆蓋未知 |
| `apps/pixel-angela/` | ✅ 已追蹤 | PyQt6 像素藝術渲染引擎 | ❓ 是否正常運作？測試覆蓋？ |
| `apps/web-dashboard/` | ✅ 已追蹤 | Next.js Web 儀表板 | ❓ 與 shared-js 整合狀態？ |
| `apps/data/` | ✅ 已追蹤 | 資料儲存 | ❓ 結構未知 |
| `packages/biology-core/` | ✅ 已追蹤 | AngelaDNA 核心庫 | ❓ 程式碼品質未知 |
| `docs/03-technical-architecture/` | ✅ 已追蹤 | 技術架構文檔 (14 子目錄) | ❓ 大量 2026-05 文件，可能已過期 |
| `docs/06-project-management/plans/` | ✅ 已追蹤 | 歷史計劃文檔 (20+ 文件) | ❓ 許多 2026-05/06 計劃，是否廢棄？ |
| `docs/multimodal/` | ✅ 已追蹤 | 多模態文檔 | ❓ 內容未知 |
| `docs/examples/` | ✅ 已追蹤 | 範例文檔 | ❓ 內容未知 |

### 1.2 存在磁碟但未 Git 追蹤的目錄

| 目錄 | 建議處理 |
|------|---------|
| `apps/logs/` | 應加入 `.gitignore`（日誌檔案） |
| `apps/models/` | 應加入 `.gitignore`（訓練模型） |
| `apps/training/` | 應加入 `.gitignore`（訓練資料） |

### 1.3 不清楚的資料夾結構

- `apps/backend/src/ai/` 中有多個子目錄，但 `ai/reasoning/`, `ai/learning/`, `ai/lifecycle/`, `ai/ops/`、`ai/response/`、`ai/meta/` 這些子系統的**實際運作/測試狀態未知**
- `models/` 目錄中的 JSON 文件 (`concept_mapper.json`, `concept_space.json`, 等) 是訓練輸出 artifacts，非原始碼——應明確標記
- `apps/backend/tests/api/v1/endpoints/` 只有一個測試檔案 (`test_drive_integration.py`)——其他 API 端點的測試在哪？

---

## 2. 文件遺漏 — MD 過期/廢棄/不一致

### 2.1 已確認過期的 MD 文件

| 文件 | 問題 | 嚴重度 |
|------|------|:------:|
| `docs/COMPREHENSIVE_AUDIT_2026-06-25.md` | 健康度仍寫 ~55-60%，但實際為 ~85-90% | 🟡 中 |
| `docs/03-technical-architecture/` 多數文件 | 2026-05 撰寫，架構已有大幅變更 | 🟡 中 |
| `docs/06-project-management/plans/*.md` | 多數為 2026-05/06 的歷史計劃，未更新為完成狀態 | 🟢 低 |
| `docs/04-advanced-concepts/` | INDEX.md 已標記為 "deprecated — package deleted" | 🟢 低 |

### 2.2 文件不一致（MD 互相比對）

| 矛盾 | 詳情 |
|------|------|
| AGENTS.md 列 `apps/gemini-os-bridge/` 和 `apps/pixel-angela/` 但無狀態說明 | 已確認存在，但健康度未知 |
| README.md 英文寫 `102 JS/TS`，中文寫 `140 JS/TS`，實際是 `295` | 已修復，但中文版仍有殘留 |
| INDEX.md 未列出 GVV、image generation 端點、shared-js packages | 文件索引不完整 |
| CHANGELOG.md 的 `7.4.0`, `7.3.0`, `7.2.0` 標記為 Internal/Unreleased——AI 自指派版本 | 歷史累積 |

### 2.3 文檔覆蓋缺口

| 缺少的文檔 | 影響 |
|-----------|------|
| 無 `packages/shared-js/README.md` | 開發者不知如何使用共享 JS 套件 |
| 無 `models/README.md` | 不知模型 artifacts 是來源還是產出 |
| 無 `apps/gemini-os-bridge/README.md` | 不知 OS bridge 的功能與 API |
| 無 `docs/ARCHITECTURE.md` 的 GVV 管線說明 | 架構圖缺少 image generation 部分 |

---

## 3. 任務遺漏 — 修復任務的真實完成度

### 3.1 Phase 1 — 架構清理

| 任務 | 聲稱狀態 | 實際驗證 | 差距 |
|------|:--------:|:---------:|------|
| 1.1 聊天端點棄用 | ✅ 完成 | `/angela/chat` 和 `/dialogue` 仍存在但加了 deprecation warning | 正確——預期行為 |
| 1.2 路由命名統一 | ✅ 完成 | `/generate-image` 仍保留（含 deprecation warning，符合路線圖「保留舊路由」策略） | ✅ 正確 — 但未確認新 `/image/generate` 路由是否存在 |
| 1.3 sys.path 移除 | ✅ 完成 | 未驗證 | ❓ |
| 1.4 modules/ 移除 | ✅ 完成 | 目錄已不存在，24 個檔案已刪除並 commit | 正確 |
| 1.5 文檔引用更新 | ✅ 完成 | AGENTS.md、ARCHITECTURE.md 已更新 | 正確 |
| 1.6 PLAN 歸檔 | ✅ 完成 | 4 個 PLAN 文件已從根目錄刪除 | ⚠️ 未歸檔至 `docs/09-archive/`，僅刪除 |
| 1.7 vision 端點棄用 | ✅ 完成 | 未驗證 | ❓ |

### 3.2 Phase 2 — 文檔與配置

| 任務 | 聲稱狀態 | 實際驗證 | 差距 |
|------|:--------:|:---------:|------|
| 2.1 AGENTS.md 更新 | ✅ 完成 | 結構圖、統計已更新 | 正確 |
| 2.2 ARCHITECTURE.md 更新 | ✅ 完成 | 未讀取此文件驗證 | ❓ |
| 2.3 INDEX.md 更新 | ✅ 完成 | 仍有內容缺口（GVV/image generation/shared-js） | ⚠️ 不完整 |
| 2.4 CHANGELOG 更新 | ✅ 完成 | 有 GVV/Phase 4-5 條目 | 正確 |
| 2.5 README.md 更新 | ✅ 完成 | 統計已更新 | 正確 |
| 2.6 CI 修復 | ✅ 完成 | `.github/workflows/ci.yml` 存在 | ❓ 未驗證修正內容 |
| 2.7 IDEAL_ARCHITECTURE.md | ✅ 完成 | 文件存在 | 正確 |

### 3.3 Phase 3 — Stub 實作

| 任務 | 聲稱狀態 | 實際驗證 | 差距 |
|------|:--------:|:---------:|------|
| 3.1 google_drive_handler | ✅ 完成 | 無 pass、無 NotImplementedError | 正確 |
| 3.2 key_generator | ✅ 完成 | 無 pass、無 NotImplementedError | 正確 |
| 3.3 secure_eval | ✅ 完成 | 無 pass、無 NotImplementedError | 正確 |
| 3.4 math_verifier | ✅ 完成 | API 已變更，測試跳過 | ⚠️ API 不相容，測試跳過 |
| 3.5 waiting_scheduler | ✅ 完成 | 未驗證 | ❓ |
| 3.6 ops_routes | ✅ 完成 | 22 tests pass | 正確 |
| 3.7 state_matrix_api | ✅ 完成 | 未驗證 | ❓ |

### 3.4 Phase 4 — JS 共用化

| 任務 | 聲稱狀態 | 實際驗證 | 差距 |
|------|:--------:|:---------:|------|
| 4.1 shared-js 建立 | ✅ 完成 | 33 檔案存在，package.json 存在 | 正確 |
| 4.2-4.3 檔案搬遷 | ✅ 完成 | 0 重複，desktop 7 unique + web 10 unique | 正確 |
| 4.4-4.5 HTML 更新 | ✅ 完成 | 引用已改為 `../../packages/shared-js/js/` | 正確 |
| 4.6 重複移除 | ✅ 完成 | 64 個 JS 重複檔案已刪除並 commit | 正確 |

### 3.5 Phase 5 — 測試增強

| 任務 | 聲稱狀態 | 實際驗證 | 差距 |
|------|:--------:|:---------:|------|
| 5.1 聊天管線重構 | ✅ 完成 | 已 refactor | 正確 |
| 5.2 SessionManager 接入 | ✅ 完成 | 已 wiring | 正確 |
| 5.3 brain_bridge 修復 | ✅ 完成 | 未驗證 | ❓ |
| 5.4 image_generation 測試 | ✅ 完成 | 22 tests | 正確 |
| 5.5 ops_routes 測試 | ✅ 完成 | 22 tests | 正確 |
| 5.6 handlers 測試 | ✅ 完成 | 40 tests | 正確 |
| 5.7 resource bug 修復 | ✅ 完成 | `angela_config.yaml` 已修正 | 正確 |
| 5.8 SessionManager 測試 | ✅ 完成 | 56 tests | 正確 |
| 5.9 跳過測試審計 | ✅ 完成 | 4776 tests / 0 errors / 41 skips | 正確 |

### 3.6 任務完成度總評

- **徹底完成（已驗證）**: Phase 4 (JS sharing), Phase 5 (tests)
- **大部份完成（部分驗證）**: Phase 3 (stubs), Phase 1 (cleanup)
- **未充分驗證 (7 項)**: Phase 1.3 (sys.path), Phase 1.7 (vision endpoint), Phase 2.2 (ARCHITECTURE.md), Phase 2.6 (CI), Phase 3.5 (waiting_scheduler), Phase 3.7 (state_matrix_api), Phase 5.3 (brain_bridge)

---

## 4. Git 遺漏 — 版本控制整潔度

| 問題 | 詳情 | 優先級 |
|------|------|:------:|
| 80+ 過時 git 分支 | 大量 `dependabot/`, `backup-*` 分支未清理 | 🟡 中 |
| `apps/logs/` 未 gitignore | 日誌檔案不該被追蹤 | 🟡 中 |
| `apps/models/` 未 gitignore | 訓練模型不該被追蹤 | 🟡 中 |
| `apps/training/` 未 gitignore | 訓練資料不該被追蹤 | 🟢 低 |
| `models/*.npy` 需 `git rm --cached` | `.gitignore` 已加入但已追蹤的檔案需手動移除 | 🟢 低 |
| `models/*.pt` 需 `git rm --cached` | 同上 | 🟢 低 |
| `scripts/train_learned_repr*.py` 未提交 | GVV 管線原始碼應提交 | 🟢 低 |

---

## 5. 安全遺漏

| 問題 | 詳情 | 優先級 |
|------|------|:------:|
| `.angela_backend.pid` 不被 gitignore | PID 檔案不該被追蹤（已在 `.gitignore` 加入修復） | 🟢 低 |
| `.env` 檔案 | 存在但已正確 gitignore，非風險 | ✅ 安全 |
| `credentials.json` | 已在 `.gitignore` 中 | ✅ 安全 |

---

## 6. 配置遺漏

| 問題 | 詳情 | 優先級 |
|------|------|:------:|
| `pyrightconfig.json` 排除 `packages/` | 整個 packages/ 目錄被排除在類型檢查外 | 🟡 中 |
| `.gitignore` `LAST_MODIFIED: 2026-02-19` | 過時，應更新 | 🟢 低 |

---

## 7. 程式碼遺漏

| 問題 | 詳情 | 優先級 |
|------|------|:------:|
| `apps/gemini-os-bridge/` 程式碼品質未知 | 從未檢查此目錄的程式碼 | 🟡 中 |
| `apps/pixel-angela/` 程式碼品質未知 | 從未檢查此目錄的程式碼 | 🟡 中 |
| `packages/biology-core/` 程式碼品質未知 | 從未檢查此目錄的程式碼 | 🟡 中 |
| `apps/web-dashboard/` 狀態未知 | Next.js 儀表板是否正常運作？ | 🟡 中 |
| 剩餘 6 項未來功能未實作 | Agent Auto-Routing, Frontend Multimodal, AudioService, 等 | 🟢 已知 |

---

## 8. 測試遺漏

| 問題 | 詳情 | 優先級 |
|------|------|:------:|
| `apps/gemini-os-bridge/` 無測試 | 從未看到此目錄的測試 | 🟡 中 |
| `apps/pixel-angela/` 無測試 | 從未看到此目錄的測試 | 🟡 中 |
| `packages/biology-core/` 無測試 | 從未看到此目錄的測試 | 🟡 中 |
| `packages/shared-js/` 無測試 | 共用 JS 套件無自動化測試 | 🟢 低 |
| 41 intentional skips 未確認合理性 | 每個 skip 是否真的有正當理由？ | 🟢 低 |

---

## 9. 總結與優先級

### 🔴 高優先（需立即處理）

| # | 問題 | 類別 |
|---|------|------|
| 1 | INDEX.md 缺少 GVV/image generation/shared-js 引用 | 文件 |
| 2 | `apps/gemini-os-bridge/` 程式碼品質與測試未知 | 程式碼 |
| 3 | `apps/pixel-angela/` 程式碼品質與測試未知 | 程式碼 |

### 🟡 中優先（需安排處理）

| # | 問題 | 類別 |
|---|------|------|
| 4 | COMPREHENSIVE_AUDIT_2026-06-25.md 健康度未更新 | 文件 |
| 5 | 80+ 過時 git 分支未清理 | Git |
| 6 | 6 項 Phase 1/2/3/5 任務未充分驗證 | 任務 |
| 7 | `apps/logs/`, `apps/models/`, `apps/training/` 未 gitignore | Git |
| 8 | pyrightconfig.json 排除 packages/ 目錄 | 配置 |

### 🟢 低優先（可後續處理）

| # | 問題 | 類別 |
|---|------|------|
| 9 | `models/*.npy`, `models/*.pt` 需 `git rm --cached` | Git |
| 10 | `scripts/train_learned_repr*.py` 未提交 | Git |
| 11 | 6 項未來功能未實作 | 功能 |
| 12 | 41 skips 合理性確認 | 測試 |
| 13 | `packages/shared-js/README.md` 不存在 | 文件 |

---

*本清單將隨著修復進展持續更新。最後更新：2026-06-25*
