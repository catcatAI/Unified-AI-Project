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
| **[COMPREHENSIVE_AUDIT_2026-06-25.md](COMPREHENSIVE_AUDIT_2026-06-25.md)** | **全面審計報告 (2026-06-25)** — 最新全專案審計, 涵蓋路由/配置/AI子模組/Desktop App/26+發現 |
| **[IDEAL_ARCHITECTURE.md](IDEAL_ARCHITECTURE.md)** | **理想架構規範** — 16章節定義目標狀態, 目錄結構/路由標準/AI子系統/測試/CI-CD |
| **[REPAIR_ROADMAP.md](REPAIR_ROADMAP.md)** | **修復路線圖** — 6階段修復計畫(P0-P3), 37問題映射40任務, ~28小時至90%健康度 |
| **[COMPREHENSIVE_AUDIT_REPORT.md](06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT.md)** | **全面審計報告 V1 (2026-05-31)** — 6代理審計結果, 原始完成度判定 |
| **[COMPREHENSIVE_AUDIT_REPORT_V2.md](06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT_V2.md)** | **全面審計報告 V2 (2026-06-06, 新)** — H5 衝刺後全量掃描, 3 true stubs, 20 intentional excepts, 132 超長檔案 |
| **[PHASE_REVIEW.md](06-project-management/plans/PHASE_REVIEW.md)** | **階段審查 1 (2026-06-02)** — 首次3代理審計, 10維度深層評分 |
| **[PHASE_REVIEW2.md](06-project-management/plans/PHASE_REVIEW2.md)** | **階段審查 2 (2026-06-03)** — 17會話後追蹤, ~96%綜合, 全域匯入鏈修復 |
| **[MASTER_CONSOLIDATED_PLAN.md](06-project-management/plans/MASTER_CONSOLIDATED_PLAN.md)** | 主執行計畫 — 53項 S/A/B/C 分級, 53/53 完成 |
| **[MASTER_FINALIZATION_PLAN.md](06-project-management/plans/MASTER_FINALIZATION_PLAN.md)** | 最終消滅計畫 — P8-P10 結構改善 + 文檔/測試 |
| **[PHASE6_NEXT_PLAN.md](06-project-management/plans/PHASE6_NEXT_PLAN.md)** | Quality finishing — Plugin, Config handler, Magic number, Stub |
| **[REPAIR_PLAN.md](06-project-management/plans/REPAIR_PLAN.md)** | 修復計畫 — 源碼bug修復 + 測試重構 |
| **[TEST_RESTRUCTURE_PLAN.md](06-project-management/plans/TEST_RESTRUCTURE_PLAN.md)** | 測試層級架構重組 |
| **[CARD_IMPORT_PIPELINE_PLAN.md](06-project-management/plans/CARD_IMPORT_PIPELINE_PLAN.md)** | 卡片導入管線 |
| **[ANGELA_CARD_INTEGRATION_PLAN.md](06-project-management/plans/ANGELA_CARD_INTEGRATION_PLAN.md)** | Card pipeline → ChatService 接線 |
| **[REMAINING_ISSUES_PLAN.md](06-project-management/plans/REMAINING_ISSUES_PLAN.md)** | placeholder 清除、unittest→pytest 遷移 |
| **[CARD_INTEGRATION_PLAN_REVIEW.md](06-project-management/plans/CARD_INTEGRATION_PLAN_REVIEW.md)** | 事前審計：執行前發現 25 問題 |
| **[PHASE_REVIEW3.md](06-project-management/plans/PHASE_REVIEW3.md)** | **階段審查 3 (2026-06-05)** — P0-P2 全部清除後狀態, 10維度判定 |
| **[PHASE_REVIEW4.md](06-project-management/plans/PHASE_REVIEW4.md)** | **階段審查 4 (2026-06-05, v5)** — H5 stub 衝刺, 36/37 stub 實作, 24 空 except 修復, ~62% |
| **[PHASE_REVIEW5.md](06-project-management/plans/PHASE_REVIEW5.md)** | **階段審查 5 (2026-06-06, 新)** — H5 衝刺完成版, 2837+ tests (Phase 3-6 added 162), 0 HIGH 漏洞, 下一階段 H7 路線 |
| **[PLAN_REVIEW.md](06-project-management/plans/PLAN_REVIEW.md)** | **計畫審查** — 跨計畫一致性與完整性審查 |
| **[ANGELA_TRANSLATION_LEARNING_PLAN.md](06-project-management/plans/ANGELA_TRANSLATION_LEARNING_PLAN.md)** | **Angela 翻譯學習計畫** — 多語言翻譯能力建置 |
| **[ED3N_MATURITY_PLAN.md](06-project-management/plans/ED3N_MATURITY_PLAN.md)** | **ED3N 成熟度計畫 (06-06)** — 4階段路線圖, Model Bus, Query Classifier v2 (16 QueryTypes), Training Coordinator |
| **[GARDEN_MODEL_PLAN.md](06-project-management/plans/GARDEN_MODEL_PLAN.md)** | **GARDEN 擴展計畫 (06-06)** — 1GB 輕量級本地模型與五級擴展架構 |
| **[ANGELA_LLM_SNN_ARCHITECTURE_PLAN.md](06-project-management/plans/ANGELA_LLM_SNN_ARCHITECTURE_PLAN.md)** | **ED3N + SNN 架構計畫** — 30+ 現有組件對應 |
| **[ANGELA_CAPABILITY_PLAN.md](06-project-management/plans/ANGELA_CAPABILITY_PLAN.md)** | **Angela 能力補全計畫 v2** — Phase 3-6 完成 (162 new tests, ED3N continuous learning, GARDEN 5-stage pipeline) |
| **[COMPREHENSIVE_AUDIT_V3.md](06-project-management/plans/COMPREHENSIVE_AUDIT_V3.md)** | **全面審計 V3 (06-07)** — ED3N/GARDEN/Model Bus/Router 深度審計, 16 HIGH + 16 MEDIUM 問題, P0-P4 修復計畫 |

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
- `apps/web-live2d-viewer/` — Web-based Live2D model viewer
- `apps/pixel-angela/` — PyQt6 pixel art rendering engine (AngelaDNA voxel body)
- `apps/mobile-app/` — **已移除** (skeleton, 已不包含在專案中)
- `packages/biology-core/` — AngelaDNA core library (voxel body, dynamics)
- `packages/cli/` — CLI tools

---

## Recent Plans & Reports

| 文件 | 說明 |
|------|------|
| **[COMPREHENSIVE_AUDIT_2026-06-25.md](COMPREHENSIVE_AUDIT_2026-06-25.md)** | **最新全面審計報告 (2026-06-25)** — 全專案審計, 涵蓋26+發現 |
| **[IDEAL_ARCHITECTURE.md](IDEAL_ARCHITECTURE.md)** | **理想架構規範** — 專案應有的理想狀態目標架構 |
| **[REPAIR_ROADMAP.md](REPAIR_ROADMAP.md)** | **修復路線圖** — 階段性修復計畫，使實際接近理想 |

---
_Last Updated: 2026-06-25_ | [README.md](../README.md) | [Comprehensive Audit 2026-06-25](COMPREHENSIVE_AUDIT_2026-06-25.md) | [IDEAL_ARCHITECTURE](IDEAL_ARCHITECTURE.md) | [REPAIR_ROADMAP](REPAIR_ROADMAP.md) | [Comprehensive Audit V1](06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT.md) | [Comprehensive Audit V2](06-project-management/plans/COMPREHENSIVE_AUDIT_REPORT_V2.md) | [Comprehensive Audit V3](06-project-management/plans/COMPREHENSIVE_AUDIT_V3.md) | [Phase Review 1](06-project-management/plans/PHASE_REVIEW.md) | [Phase Review 2](06-project-management/plans/PHASE_REVIEW2.md) | [Phase Review 3](06-project-management/plans/PHASE_REVIEW3.md) | [Phase Review 4](06-project-management/plans/PHASE_REVIEW4.md) | [Phase Review 5](06-project-management/plans/PHASE_REVIEW5.md)
