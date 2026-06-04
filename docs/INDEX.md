# Unified AI Project Documentation

## Structure

- **`00-overview/`** — Project vision, goals, roadmap, glossary
- **`02-game-design/`** — Game components, workflow, game-design docs
- **`03-technical-architecture/`** — Architecture, HSP, HAM, AI components, API, testing, security, analysis
- **`04-advanced-concepts/`** — Agent collaboration, meta-formulas (deprecated — package deleted, see Px6), advanced features
- **`05-development/`** — Dev guides, deployment, environment setup, debugging
- **`06-project-management/`** — Plans, status, audit reports
- **`09-archive/`** — Historical/completed/obsolete docs

## Root Files

- **`AGENTS.md`** — 代理開發指南 (構建/測試/代碼規範)
- **`ARCHITECTURE.md`** — System architecture overview (SSOT, outdated)
- **`CHANGELOG.md`** — 版本歷史與變更記錄
- **`QUICK_START.md`** — Getting started guide
- **`INDEX.md`** — This file

## Key Active Documents

### Plans (優先閱讀順序)
| 文件 | 說明 |
|------|------|
| **[COMPREHENSIVE_AUDIT_REPORT.md](06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT.md)** | **全面審計報告 (2026-05-31)** — 6代理審計結果, 完成度判定, 修復路線圖 |
| **[PHASE_REVIEW.md](06-project-management/plans/PHASE_REVIEW.md)** | **階段審查 1 (2026-06-02)** — 首次3代理審計, 10維度深層評分 |
| **[PHASE_REVIEW2.md](06-project-management/plans/PHASE_REVIEW2.md)** | **階段審查 2 (2026-06-03)** — 15會話後追蹤, ~93%綜合, 全服務+測試框架完成 |
| **[MASTER_CONSOLIDATED_PLAN.md](06-project-management/plans/MASTER_CONSOLIDATED_PLAN.md)** | 主執行計畫 — 27項 S/A/B/C 分級任務 |
| **[MASTER_FINALIZATION_PLAN.md](06-project-management/plans/MASTER_FINALIZATION_PLAN.md)** | 最終消滅計畫 — P8-P10 結構改善 + 文檔/測試 |
| **[PHASE6_NEXT_PLAN.md](06-project-management/plans/PHASE6_NEXT_PLAN.md)** | Quality finishing — Plugin, Config handler, Magic number, Stub |
| **[REPAIR_PLAN.md](06-project-management/plans/REPAIR_PLAN.md)** | 修復計畫 — 源碼bug修復 + 測試重構 |
| **[TEST_RESTRUCTURE_PLAN.md](06-project-management/plans/TEST_RESTRUCTURE_PLAN.md)** | 測試層級架構重組 |
| **[CARD_IMPORT_PIPELINE_PLAN.md](06-project-management/plans/CARD_IMPORT_PIPELINE_PLAN.md)** | 卡片導入管線 |
| **[ANGELA_CARD_INTEGRATION_PLAN.md](06-project-management/plans/ANGELA_CARD_INTEGRATION_PLAN.md)** | Card pipeline → ChatService 接線 |
| **[REMAINING_ISSUES_PLAN.md](06-project-management/plans/REMAINING_ISSUES_PLAN.md)** | placeholder 清除、unittest→pytest 遷移 |
| **[CARD_INTEGRATION_PLAN_REVIEW.md](06-project-management/plans/CARD_INTEGRATION_PLAN_REVIEW.md)** | 事前審計：執行前發現 25 問題 |

### Architecture & Design
- `03-technical-architecture/communication/hsp-specification/` — HSP protocol spec
- `03-technical-architecture/memory-systems/` — HAM memory design
- `03-technical-architecture/design/MODULE_MANAGER_SYSTEM.md` — ModuleManager design
- **[architecture/OVERVIEW.md](architecture/OVERVIEW.md)** — 架構概覽 (部分過時)

### Development Docs
- **[development/SERVICE_CATALOG.md](development/SERVICE_CATALOG.md)** — 所有服務/模組列表
- **[development/STUB_TRACKING.md](development/STUB_TRACKING.md)** — 所有 stub 位置與狀態

## Packages

- `apps/backend/` — Python FastAPI backend
- `apps/desktop-app/` — Electron Live2D desktop app
- `apps/mobile-app/` — React Native bridge (scaffold only, missing android/ios)
- `packages/cli/` — CLI tools

---
_Last Updated: 2026-06-03_ | [README.md](../README.md) | [Comprehensive Audit](06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT.md) | [Phase Review](06-project-management/plans/PHASE_REVIEW.md) | [Phase Review 2](06-project-management/plans/PHASE_REVIEW2.md)
