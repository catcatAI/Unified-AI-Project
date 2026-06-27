# Unified AI Project Documentation

## Structure

- **`00-overview/`** — Project vision, goals, roadmap, glossary (GLOSSARY.md updated 2026-06-25)
- **`02-game-design/`** — Game components, workflow, game-design docs
- **`03-technical-architecture/`** — Architecture, HSP, HAM, AI components, API, testing, security, analysis
- **`04-advanced-concepts/`** — Agent collaboration, meta-formulas (deprecated — package deleted, see Px6), advanced features
- **`05-development/`** — Dev guides, deployment, environment setup, debugging
- **`06-project-management/`** — Plans, status, audit reports
- **`09-archive/`** — Historical/completed/obsolete docs

## Root Files

- **`AGENTS.md`** — 代理開發指南 (構建/測試/代碼規範)
- **`ARCHITECTURE.md`** — System architecture overview (SSOT, 部分過時)
- **`CHANGELOG.md`** — 版本歷史與變更記錄
- **[`QUICK_START.md`](QUICK_START.md)** — Getting started guide (2026-06-25 更新，命令已驗證)
- **`INDEX.md`** — This file
- **`FRAMEWORK_OVERVIEW.md`** — 框架概述 (雙語，含誠實成熟度審計)
- **[`IMPROVEMENT_ROADMAP.md`](06-project-management/IMPROVEMENT_ROADMAP.md)** — **改善路線圖 (新 2026-06-28)** — 修正/修復/更新/迭代/訓練/學習/整理完整計畫，含數據驗證矩陣
- **[`MASTER_TASK_MAP.md`](06-project-management/MASTER_TASK_MAP.md)** — **主任務地圖** — 23份文檔144條索賠的完整來源追蹤，§X 31項 (16 DONE, 14 PENDING, 1 PARTIAL)
- **`COMPREHENSIVE_REPAIR_ROADMAP.md`** — **全面修復路線圖** — 6 階段修復計畫
- **`COMPREHENSIVE_AUDIT_2026-06-25.md`** — **最新全面審計報告**

## Key Active Documents

### Plans (優先閱讀順序)
| 文件 | 說明 |
|------|------|
| **[IMPROVEMENT_ROADMAP.md](06-project-management/IMPROVEMENT_ROADMAP.md)** | **改善路線圖 (2026-06-28)** — 修正/修復/更新/迭代/訓練/學習/整理完整計畫，含數據驗證矩陣與業界比較 |
| **[MASTER_TASK_MAP.md](06-project-management/MASTER_TASK_MAP.md)** | **主任務地圖** — 31項追蹤，含完整成熟度審計，190+ AI類別業界比較 |
| **[FRAMEWORK_OVERVIEW.md](../FRAMEWORK_OVERVIEW.md)** | **框架概述** — 雙語架構導覽，誠實 AI 能力評估 (6.0 with LLM / <0.5 native) |
| **[COMPREHENSIVE_AUDIT_2026-06-25.md](../COMPREHENSIVE_AUDIT_2026-06-25.md)** | **全面審計報告 (2026-06-25)** — 最新全專案審計, 26+發現 |
| **[IDEAL_ARCHITECTURE.md](../IDEAL_ARCHITECTURE.md)** | **理想架構規範** — 16章節定義目標狀態, 目錄結構/路由標準/AI子系統/測試/CI-CD |

所有歷史計畫 (PHASE_REVIEW1-6, COMPREHENSIVE_AUDIT_V1-V3, MASTER_CONSOLIDATED_PLAN 等) 位於 `06-project-management/plans/` 目錄下。

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
- `packages/shared-js/` — Shared JS package (33 files, platform detection)
- `packages/biology-core/` — AngelaDNA core library (voxel body, dynamics)
- `packages/cli/` — CLI tools

---
_Last Updated: 2026-06-28_ | [README.md](../README.md) | [Improvement Roadmap](06-project-management/IMPROVEMENT_ROADMAP.md) | [Master Task Map](06-project-management/MASTER_TASK_MAP.md) | [Framework Overview](FRAMEWORK_OVERVIEW.md) | [Comprehensive Audit 2026-06-25](COMPREHENSIVE_AUDIT_2026-06-25.md)
