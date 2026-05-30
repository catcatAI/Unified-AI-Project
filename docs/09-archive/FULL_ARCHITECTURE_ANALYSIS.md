# Angela AI — 全量架構設計圖譜與多維一致性分析

> **分析日期**: 2026-05-25（2026-05-30 歸檔 — 本文件作為歷史快照保留，不反映重構後的 codebase）  
> **項目版本**: v6.5.0-dev (代碼) / v6.2.0 (VERSION 文件) / v6.1.0 (config)  
> **分析範圍**: 全部 apps/ backend / desktop-app / mobile-app / packages / tests / CI  
> **方法**: Git 歷史 → 淺層結構 → 中層模塊 → 深層算法，逐層檢查一致性

---

## 目錄

1. [版本演化全景圖 (Git 深度溯源)](#1-版本演化全景圖-git-深度溯源)
   - [版本號歷史完整溯源](#11-版本號歷史完整溯源)
   - [版本號變更的 Git 精確時間線](#12-版本號變更的-git-精確時間線)
   - [版本號矛盾根源分析](#13-版本號矛盾根源分析)
   - [Git 分支拓撲 (精簡)](#14-git-分支拓撲-精簡)
   - [Git 提交統計](#15-git-提交統計按時間分組)
   - [演化大事記](#16-演化大事記完整版)
   - [各組件正確子版本號分析](#17-各組件正確子版本號分析)
2. [全量架構文字設計圖](#2-全量架構文字設計圖)
3. [淺層檢查 — 目錄結構與模塊邊界](#3-淺層檢查)
4. [中層檢查 — 模塊間依賴與數據流](#4-中層檢查)
5. [深層檢查 — 核心算法與理論公式](#5-深層檢查)
6. [一致性綜合評分表](#6-一致性綜合評分表)
7. [關鍵發現與矛盾點](#7-關鍵發現與矛盾點)
8. [改進建議](#8-改進建議)

---

## 1. 版本演化全景圖 (Git 深度溯源)

### 1.1 版本號歷史完整溯源

> 本節基於 Git 從第一個 commit (`ddb266946`) 到 HEAD 的**完整提交歷史**，逐個 commit 追蹤每一個版本號變更的**精確時刻、變更內容、變更理由**。

#### 版本號存在位置清單 (完整枚舉)

通過對整個代碼庫的全面掃描，以下 **13 個位置** 聲明了版本號：

| # | 文件路徑 | 字段 | 當前值 | 首次出現 commit | 最後更新 commit | 最後更新理由 |
|---|---------|------|--------|----------------|----------------|------------|
| 1 | `package.json` | `version` | **6.5.0-dev** | `ddb266946` (0.1.0) | `45c63d3af` | AI agent "Fix and update" — 無明確理由 |
| 2 | `apps/desktop-app/electron_app/package.json` | `version` | **6.5.0-dev** | `34de65d0c` (1.0.0) | `af7f03a80` | 與根 package.json 同步 |
| 3 | `apps/mobile-app/package.json` | `version` | **6.5.0-dev** | `2c1816e0` (6.2.0) | `af7f03a80` | 與根 package.json 同步 |
| 4 | `apps/backend/src/core/version.py` | `CURRENT_VERSION` | **6.5.0-dev** | `bcb01db3c` (6.2.0) | `af7f03a80` | 與 package.json 同步 |
| 5 | `VERSION` (根目錄文件) | 純文字 | **6.2.0** | `b29441e74` (6.2.0) | **從未更新** | 創建後被遺忘 |
| 6 | `config/angela_config.json` | `version` | **6.1.0** | `b29441e74` (6.1.0) | **從未更新** | 創建後被遺忘 |
| 7 | `apps/backend/src/core/__init__.py` | docstring | **6.2.0** | `bcb01db3c` | **從未更新** | 初始化後未被修改 |
| 8 | `CHANGELOG.md` | section headers | **6.2.2 ~ 7.4.0** | `0e803d64` (v7.x) | `9819d95f5` (v6.2.2) | 見下方詳細分析 |
| 9 | `packages/cli/__init__.py` | `__version__` | **1.1.0** | `037851ee` | — | 獨立於主項目的 CLI 版本 |
| 10 | `packages/biology-core/package.json` | `version` | **1.0.0** | 初始提交 | — | 獨立包版本 |
| 11 | `docs/README_v6.2.0_FINAL.md` | title | **v6.2.0** | — | — | 靜態文檔快照 |
| 12 | `reports/` (~20 個報告文件) | 文件名/內容 | **v6.2.0 ~ v6.2.3** | — | — | 歷史審計報告 |
| 13 | `test_results/api_comprehensive_test_results.json` | `version` | **6.0.4** | — | — | API 測試結果快照 |

---

### 1.2 版本號變更的 Git 精確時間線

以下按照 **Git commit 時間順序**，列出每次版本號變更：

#### 階段 1: 初始創建期 (2024, 0.1.0)

```
commit ddb266946 — Initial commit
  package.json:    "version": "0.1.0"
  pyproject.toml:  version = "0.1.0"
  
理由: 項目最初由 MikoAI + Fragmenta 合併而成，0.1.0 是標準的"初始開發版本"標記
```

```
後續 ~100+ commits 保持 "0.1.0" 不變 (約 2024 ~ 2025-08)
  這期間 package.json 從未被修改過 version 字段
  
理由: 項目處於早期快速迭代階段，無人管理版本號
```

#### 階段 2: Desktop App 獨立版本 (2026-02-04, 1.0.0)

```
commit 34de65d0c — Session 3: Desktop Application Complete Implementation
  apps/desktop-app/electron_app/package.json: "version": "1.0.0"
  
理由: Electron 桌面應用首次獲得獨立版本號，標記為"完整實現"
```

```
commit 83238b593 — chore: remove old desktop app
  根 package.json 仍然是 "0.1.0"
  
理由: 清理舊桌面應用代碼，版本號未受影響
```

#### 階段 3: 第一次大版本跳躍 (2026-02-05 ~ 02-07, 0.1.0 → 6.2.0)

```
commit 494f277bf (2025-11-08) — 重構開始前
  根 package.json 仍然是 "0.1.0"
  但 pyproject.toml 已被改為 version = "0.1.0" (與 package.json 分離)
```

關鍵跳躍發生在提交 `dcb539009` (Phase 4) 到 `b29441e74` (Add audit docs) 之間：

```
commit dcb539009 — Phase 4 - Node version alignment and Electron build path
  根 package.json:     "version": "6.2.0"     ← 從 0.1.0 直接跳到 6.2.0
  desktop electron:    "version": "6.2.0"
  其他子包也同步到 6.2.0

理由分析:
  這不是正常的語義化版本遞增 (0.1.0 → 0.2.0 → ... → 6.2.0)
  而是直接從 0.1.0 跳躍到 6.2.0，跳過了 5 個主版本號
  理由推測: CHANGELOG 中列出了 0.1.0 → 6.0.0 之間的所有"歷史版本"
  (v1.0.0 ~ v6.0.0) 作為回溯性記錄，但實際 Git 歷史中並不存在這些版本號的提交
  即: v1.0~v6.0 是**回溯性虛擬版本**，從未被正式 tag 或寫入代碼
```

```
commit b29441e74 — Add audit docs; update backend, desktop & agents
  VERSION 文件: 首次創建，內容為 "6.2.0"     ← 與 package.json 同步
  config/angela_config.json: 首次出現，version = "6.1.0"  ← 比 VERSION 落後 0.1
  core/version.py: 首次創建 (commit bcb01db3c)，VersionInfo(6,2,0,STABLE)

版本矛盾根源 #1:
  VERSION 文件與 config/angela_config.json 在同一 commit 中創建
  但 VERSION = 6.2.0，config = 6.1.0
  這是版本號散亂的**第一個根源**
  理由: 創建時就沒有統一
```

#### 階段 4: CHANGELOG v7.x 時期 (2026-05-09, 7.2.0~7.4.0)

```
這是整個版本歷史中最關鍵的矛盾點。

commit 0e803d64 (2026-05-09 09:09) 
  feat: implement autonomous spatial gravity, adaptive memory contexts, intent-driven
  mouse navigation, and loss-based gait evolution engines.
  
  這個 commit 創建了 CHANGELOG.md，寫入了:
  ## [7.4.0] - 2026-05-09  ← 置頂 (最新)
  ## [7.3.0] - 2026-05-09
  ## [7.2.0] - 2026-05-09
  ## [7.1.1] - 2026-02-13    ← 在 v6.2.0 之後 (日期在前的在新版)

  但!!! 這個 commit 並沒有修改 package.json 或任何其他版本文件
  根 package.json 此時仍然是 "6.2.0"

commit 253aa8ff (2026-05-09 02:19)  ← 時間更早
  feat: implement autonomous core components including self-introspection, art learning,
  and action execution systems
  也在 CHANGELOG.md 中添加了內容 (v7.3.0)

commit cbe75f61d (2026-05-09 01:22)  ← 時間最早
  feat: integrate native spatial math engine and intent-based coordinate gravity system
  for 4D state matrix synchronization
  也在 CHANGELOG.md 中添加了內容 (v7.2.0)

版本矛盾根源 #2:
  CHANGELOG 聲稱這是 v7.2.0 ~ v7.4.0 的發布
  但: 1) 沒有對應的 git tag (只有一個 v6.0.0 tag)
      2) package.json 沒有更新到 v7.x
      3) 代碼庫中沒有任何文件標記為 v7.x
      4) v7.1.1 的日期 2026-02-13 實際上是 v6.2.0 的時代
  
  結論: v7.x 是 AI agent 在自動生成 CHANGELOG 時**憑空賦予的版本號**
        它描述的功能 (Spatial AI, Intent Gravity) 確實在代碼中實現了
        但版本號從未被正式批准或寫入源代碼文件
```

#### 階段 5: 版本回溯 (2026-05-16, 7.x → 6.2.2)

```
commit 9819d95f5 (2026-05-16) — Fix and update
  這是一個 AI agent 的自動提交
  
  在 CHANGELOG.md 的頂部插入了:
  ## [6.2.2] - 2026-05-16
  
  效果: v6.2.2 被放在了 v7.x 條目的前面
        CHANGELOG 從此變成了: 6.2.2 (最新) → 7.4.0 → 7.3.0 → 7.2.0 → ...

  理由: agent 試圖"修復"版本號矛盾，但方式是在 v7.x 前面加一個 v6.x 條目
        這實際上製造了更混亂的局面 — 版本號在 CHANGELOG 中**非單調遞增**
```

#### 階段 6: 6.2.1 → 6.5.0-dev (2026-05-21 ~ 05-25)

```
commit c39bc4009 (2026-05-21) — Fix and update
  根 package.json: "version": "6.2.1"   ← 從 6.2.0 小版本遞增
  理由不明 (沒有任何與 6.2.1 對應的 CHANGELOG 條目)

commit ff316973b (2026-05-11) — Fix (時間標籤混亂，實際在 c39bc4009 之前)
  根 package.json: "version": "6.2.1"   ← AI agent 設置
  同時 desktop-app 和 mobile-app 也被改為 6.2.1

commit af7f03a80 (2026-05-24) — Fix and update
  根 package.json:     "version": "6.5.0-dev"    ← 從 6.2.1 → 6.5.0 (跳躍 0.3)
  desktop electron:    "version": "6.5.0-dev"
  mobile:              "version": "6.5.0-dev"
  core/version.py:     VersionInfo(6,5,0,DEV)   ← 與 package.json 同步

  這是 CURRENT HEAD 的版本狀態

理由分析: 6.2.1 → 6.5.0-dev 跳躍 0.3 個 minor
  推測理由: 1) 開發階段從 STABLE 改為 DEV
           2) minor 從 2 跳到 5 是因為中間有 3 個隱式版本 (6.3, 6.4, 6.5)
           3) 但沒有任何提交記錄對應這些版本
  這不是標準的 semver 行為
```

---

### 1.3 版本號矛盾根源分析

#### 所有版本號位置與其 Git 溯源

| 位置 | 當前值 | Git 首次出現 | Git 最後更新 | 從未更新天數 | 偏差方向 |
|------|--------|-------------|-------------|-------------|---------|
| `package.json` | **6.5.0-dev** | `ddb266946` (0.1.0) | `45c63d3af` (2026-05-25) | 0 天 (最新) | 基準 |
| `core/version.py` | **6.5.0-dev** | `bcb01db3c` (6.2.0) | `af7f03a80` (2026-05-24) | 1 天 | ✅ 一致 |
| `desktop-app/package.json` | **6.5.0-dev** | `34de65d0c` (1.0.0) | `af7f03a80` (2026-05-24) | 1 天 | ✅ 一致 |
| `mobile-app/package.json` | **6.5.0-dev** | `2c1816e0` (6.2.0) | `af7f03a80` (2026-05-24) | 1 天 | ✅ 一致 |
| **`VERSION` 文件** | **6.2.0** | `b29441e74` (2026-02-07) | **從未更新** | **107 天** | ❌ 落後 3 minor |
| **`config/angela_config.json`** | **6.1.0** | `b29441e74` (2026-02-07) | **從未更新** | **107 天** | ❌ 落後 4 minor |
| **`core/__init__.py` docstring** | **6.2.0** | `bcb01db3c` (2026-02-22) | **從未更新** | **92 天** | ❌ 落後 3 minor |
| **`CHANGELOG.md` v7.x** | **7.2.0~7.4.0** | `0e803d64` (2026-05-09) | — | — | ❌ 超前 1 major |
| **`CHANGELOG.md` v6.2.2** | **6.2.2** | `9819d95f5` (2026-05-16) | — | — | ❌ 落後 3 minor |

#### v7.x 之謎 — 完整解讀

```
CHANGELOG 中的 v7.x 不是"真正的發布版本"
而是 AI agent 在 CHANGELOG 生成時使用的內部工作版本號

證據鏈:
  1. Git tag: 只有 v6.0.0 和 AI 兩個 tag，無任何 v7.x tag
  2. package.json: 從未被設置為 v7.x
  3. code: 沒有任何源代碼文件聲明 v7.x
  4. 時間矛盾: v7.1.1 的日期是 2026-02-13，但此時所有版本文件都還是 v6.2.0
  5. 引入方式: CHANGELOG 在 2026-05-09 首次創建時直接寫入 v7.x
     說明這是回溯性文檔，不是版本遞增的結果

真實情況:
  項目在 2026-02-07 ~ 2026-05-09 之間完成了 Spatial AI 等重大功能
  AI agent 在彙總 CHANGELOG 時給這些功能分配了 v7.x 的版本號
  但項目管理人/後續 agent 決定回歸 v6.x 主線
  原因可能是: v7.0 從未正式發布，不能跳過
```

#### CHANGELOG vs 真實版本對照表

| CHANGELOG 版本 | CHANGELOG 日期 | 真實代碼版本 (當時) | 功能 | 一致性 |
|---------------|---------------|-------------------|------|--------|
| [0.1.0] | 2024-XX-XX | 0.1.0 | Genesis Merge | ✅ 一致 |
| [1.0.0] | 2024-XX-XX | 0.1.0 (未更新) | Initial Release | ❌ 回溯撰寫 |
| [2.0.0] | 2025-XX-XX | 0.1.0 (未更新) | Cross-Platform | ❌ 回溯撰寫 |
| [3.0.0] | 2025-XX-XX | 0.1.0 (未更新) | Advanced AI | ❌ 回溯撰寫 |
| [4.0.0] | 2025-XX-XX | 0.1.0 (未更新) | Desktop Integration | ❌ 回溯撰寫 |
| [5.0.0] | 2025-XX-XX | 0.1.0 (未更新) | Live2D Integration | ❌ 回溯撰寫 |
| [6.0.0] | 2026-01-XX | 0.1.0 → 6.2.0 | A/B/C Security | ⚠️ 跳躍式 |
| [6.1.0] | 2026-02-05 | 6.2.0 | Phase 12 Restoration | ❌ 日期矛盾 |
| [6.2.0] | 2026-02-07 | 6.2.0 | Phase 14 Complete | ✅ 一致 |
| [7.1.1] | 2026-02-13 | 6.2.0 | Resource Analysis | ❌ v7 回溯 |
| [7.2.0] | 2026-05-09 | 6.2.0 → 6.2.1 | Spatial Math Engine | ❌ v7 回溯 |
| [7.3.0] | 2026-05-09 | 6.2.0 → 6.2.1 | Coordinate AI | ❌ v7 回溯 |
| [7.4.0] | 2026-05-09 | 6.2.0 → 6.2.1 | Spatial Gravity | ❌ v7 回溯 |
| [6.2.2] | 2026-05-16 | 6.2.1 → 6.5.0-dev | Session Manager | ⚠️ 壓在 v7 上 |

#### 散亂根源總結

```
根源 1: 創建時不一致 (2026-02-07)
  commit b29441e74 同時創建了 VERSION (6.2.0) 和 config (6.1.0)
  兩者從第一天起就差 0.1

根源 2: 文件被遺忘 (2026-02-07 至今)
  VERSION 文件: 107 天未更新
  config/angela_config.json: 107 天未更新
  core/__init__.py docstring: 92 天未更新

根源 3: AI Agent 自由創作 (2026-05-09)
  CHANGELOG 首次創建時使用了 v7.x
  這是未經人工審核的 AI 生成內容

根源 4: 版本跳躍無規範 (多次)
  0.1.0 → 6.2.0 (跳 6 個 major)
  6.2.1 → 6.5.0-dev (跳 0.3 minor)
  從未有過 6.3.0, 6.4.0 的發布

根源 5: 無版本管理流程
  沒有版本發布檢查清單
  沒有 CI 版本一致性檢查
  版本號由不同 AI agent 在不同時間隨機修改
```

### 1.4 Git 分支拓撲 (精簡)

```
v0.1.0 ──────────────────────────────────────────────→ v6.2.0 ──→ v6.2.1 ──→ v6.5.0-dev (HEAD)
  │                                                      ↑            ↑            ↑
  │  回溯性CHANGELOG v1.0~v5.0 (從未寫入代碼)            │            │            │
  │  (僅存在於文檔中，Git 中無對應版本文件)                │            │            │
  │                                                      │            │            │
  └──── AI agent 創作 v7.x CHANGELOG (2026-05-09) ──────┼───── 合併到主線 ────────┤
       ↑ 這些功能確實存在於代碼中                         │                        │
       ↑ 但版本號是 agent 自行分配的                      回溯: v6.2.2 壓在       │
                                                         v7.x 前面 (2026-05-16)  │
                                                                                   │
                                                         最終統一為 6.5.0-dev      │
                                                         (2026-05-24~25)
```

### 1.5 Git 提交統計 (按時間分組)

| 時期 | 提交模式 | 代表 Branch | 關鍵變更 | 版本狀態 |
|------|---------|------------|---------|---------|
| **2024 H2 — Genesis** (~10 commits) | `Initial commit`, `1` | `master` | MikoAI + Fragmenta 初始合併 | 0.1.0 (從未變更) |
| **2025 H1 — Monorepo** (~30 commits) | `feat(structure):`, `feat(backend):`, `feat(desktop):` | `main` | pnpm monorepo 遷移 | 0.1.0 (從未變更) |
| **2025 H2 — HSP Protocol** (~60 commits) | `feat(hsp):`, `fix(hsp):`, `feat(FragmentaOrchestrator):` | `feature/*` | MQTT 協議 | 0.1.0 (從未變更) |
| **2026 Q1 — AI Engine** (~100 commits) | `feat: implement`, `refactor:`, `fix:` | `main` | HAM Memory、Agent System | 0.1.0 → 6.2.0 (跳躍) |
| **2026 Q2 — Spatial AI** (~50 commits) | `feat: spatial`, `feat: coordinate AI` | `main` | 8D State Matrix、Intent Gravity | 6.2.0 (v7 僅存在 CHANGELOG) |
| **2026-05 — 收斂期** (~30 commits) | `Fix and update`, `chore(backup):` | `main` | 版本統一、配置快照 | 6.2.1 → 6.5.0-dev |

### 1.6 演化大事記 (完整版)

```
2024                     2025 H1                   2025 H2                    2026 Q1                        2026-05-09              2026-05-25
│                        │                        │                          │                              │                       │
Genesis Merge            Monorepo                 HSP Protocol               AI Engine                     Spatial AI              Current Dev
MikoAI+Fragmenta         pnpm workspace           MQTT + Service            HAM Memory +                  8D State Matrix         版本統一到
                         Backend/FastAPI          Discovery +               10 Agents + LIS                Intent Gravity          6.5.0-dev
                         Desktop/Electron         Fragmenta                 + AVIS                         + Spatial Math
                         CLI/Python               Orchestrator
│                        │                        │                          │                              │                       │
├────────────────────────┼────────────────────────┼──────────────────────────┼──────────────────────────────┼───────────────────────┤
v0.1.0                   v0.1.0                   v0.1.0                    0.1.0 → 6.2.0                 6.2.0 → 6.2.1           6.5.0-dev
(真實)                   (真實)                   (真實)                    (跳躍式更新)                   (agent 寫 v7 CHANGELOG)  (最終收斂)
                                                                             VERSION 文件創建 (6.2.0)      agent 加 6.2.2 條目
                                                                             config 創建 (6.1.0)
```

---

### 1.7 各組件正確子版本號分析

> 以下基於實際代碼功能完整度、獨立於任何現有版本號，為每個組件重新計算正確的 semver。
>
> **原則**: 非 lockstep — 每個組件依自身功能成熟度獨立定版。
> MAJOR = 架構質變/breaking change, MINOR = 新功能集合, PATCH = 修復, -dev = 存在已知不一致

#### ① apps/backend (Python FastAPI) → **7.5.0-dev**

這是整個專案的核心，503 個 Python 源文件、34 個 core/ 子包、40 個 ai/ 子系統。

| 版本里程碑 | 代碼證據 | 功能說明 | breaking? |
|-----------|---------|---------|-----------|
| v7.0 | `core/security/*`, 三鑰體系, `SignedCommunicationMiddleware` | A/B/C 安全架構 — 打破 v5 以前所有安全模型 | ✅ 是 |
| v7.1 | `ai/memory/ham_memory/`, `ai/agents/*` (10 agents) | HAM 分層記憶 + 多 Agent 系統 | ❌ |
| v7.2 | `state_matrix.py` shunting-yard + RPN executor | 原生空間數學引擎 (純幾何算術，脫離 LLM) | ❌ |
| v7.3 | 8 軸 `compute_coordinate()`, `art_learning_system.py` spatial aesthetic | 原生坐標 AI + 美感空間推理 | ❌ |
| v7.4 | `apply_intent_gravity()`, `apply_inter_dimensional_drag()`, `retrieve_by_spatial_proximity()` | 意圖重力 + 維度拖拽 + 空間記憶 | ❌ |
| **v7.5** | `services/connection_session.py`, 各種修復 | **Session 握手協議 (超出 v7.4 的功能)** | ❌ |

**當前錯誤標記對照**:
| 文件 | 當前值 | 正確值 | 錯誤分析 |
|------|--------|--------|---------|
| `pyproject.toml` | 0.1.0 | **7.5.0-dev** | 從 monorepo 遷移 (`e32cfe31b`, 2025-03) 後從未更新，已過期約 **15 個月** |
| `setup.py` | 0.1.0 | **7.5.0-dev** | 同上 |
| `package.json` (backend/) | 1.0.0 | **7.5.0-dev** | 單獨的 pnpm workspace 文件，被遺忘 |
| `core/version.py` | 6.5.0-dev | **7.5.0-dev** | MAJOR 少 1 — 忽視了 Spatial AI 帶來的架構質變 |
| `core/__init__.py` | 6.2.0 | **7.5.0-dev** | docstring 未更新 (92 天) |

---

#### ② apps/desktop-app (Electron) → **4.1.0-dev**

Desktop 是**後端的客戶端**，它不實現 Spatial AI / HAM / HSP，它實現的是**桌面寵物互動 + Live2D 渲染 + 通訊層**。37 個 JS 模塊、一個 1566 行的 main process。

| 版本里程碑 | 代碼證據 | 功能說明 | breaking? |
|-----------|---------|---------|-----------|
| v1.0 | `main.js` Electron shell, 基本 window | frameless + transparent + always-on-top 桌面窗口 | — |
| v2.0 | `live2d-cubism-wrapper.js` (1426 行), Cubism SDK 5 R5 | Live2D: 7 表情, 10 動作, 物理模擬 (頭髮/衣物) | ✅ 新渲染引擎 |
| v3.0 | `tray-manager.js`, `desktop-presence.js`, autostart | 系統托盤 + 自動啟動 + 桌面空間感知 + 壁紙整合 | ❌ |
| v4.0 | `security-manager.js`, Key C, `state-matrix.js` | 安全層 (Key C 加密) + 4D 情緒狀態矩陣同步 | ✅ 安全架構 |
| **v4.1** | `backend-websocket.js` session handshake, IPC 重構 | **Session 協議 + 移除 auto-reconnect + 修復多重 client_id** | ❌ |

**為什麼是 4.x 而不是 7.x？** Desktop 的 v4 (security) 約等於 backend 的 v6 水平。Backend v7 的 Spatial AI 完全在服務器端，desktop 只是被動顯示 state matrix 的結果，不涉及自身的架構質變。

**當前錯誤標記**: `electron_app/package.json` → `6.5.0-dev` ❌ — 盲目跟隨根 package.json，非自身功能反映。降級到 4.1.0-dev 才是真實狀態。

---

#### ③ apps/mobile-app (React Native) → **1.2.0-dev**

Mobile 是**最不成熟的組件**。只有 **3 個源文件**：`App.js` (828 行)、`src/api/client.js` (131 行)、`src/security/encryption.js` (212 行)。無 Live2D、無 WebSocket、無複雜 UI。

| 版本里程碑 | 代碼證據 | 功能說明 |
|-----------|---------|---------|
| v1.0 | `App.js` | React Native 骨架 + QR code 掃描配對 + Matrix 狀態顯示 |
| v1.1 | `src/security/encryption.js` | AES-256-CBC 加密通訊 + HMAC-SHA256 簽名 + Key B 整合 |
| **v1.2** | `src/api/client.js` | **API 客戶端 (healthCheck, getSystemStatus, connectWebSocket)** |

**為什麼這麼低？** 對比 desktop (37 JS 模塊, 完整 Live2D, WebSocket, system tray, IPC security)，mobile 只有 3 個源文件，功能密度差了一個數量級。標記為 6.5.0-dev 是**整個代碼庫最嚴重的版本號通貨膨脹**。

**當前錯誤標記**: `package.json` → `6.5.0-dev` ❌ — MAJOR 虛高 5、MINOR 虛高 3。

---

#### ④ packages/cli (Python CLI) → **1.1.0** ✅ (保持當前)

獨立工具，有自己的生命週期。8 個 Python 模塊。

| 版本 | 代碼證據 | 功能 |
|------|---------|------|
| v1.0 | `cli/main.py`, `cli/unified_cli.py` | 基礎 CLI: health check, chat, analyze |
| **v1.1** | HSP 整合, `port_manager.py`, error handling | **HSP protocol CLI + port conflict resolution** |

**當前錯誤標記**: `package.json` → `1.0.0` ❌ 與 `__init__.py` (`1.1.0`) 自身不一致。CLI package.json 應更新為 `1.1.0`。

---

#### ⑤ packages/biology-core (Voxel DNA) → **1.0.0** ✅ (保持當前)

| 版本 | 代碼證據 | 功能 |
|------|---------|------|
| **v1.0** | `src/dna_body.py` (285 行) | AngelaDNA 體素引擎: 2.5D 128×384×6×5 軀體矩陣, 9 段脊椎, 五指獨立指節, 慣性布料物理 |

單一文件但功能穩定。1.0.0 合理。

---

#### 總版本 vs 子版本關係圖

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Unified AI Project                                │
│                    總版本: 7.5.0-dev                                 │
│  (定義: 整個專案的完整功能集合, 由 backend 主版本驅動)               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │ apps/backend      7.5.0-dev  ▲ 主產品, 驅動總版本             │   │
│  │ (FastAPI+AI Engine)          │ 總版本 = backend 版本           │   │
│  └──────────────────────────────┘                                  │   │
│                                                                     │
│  ┌────────────────────────┐   ┌────────────────────────┐           │   │
│  │ apps/desktop-app       │   │ apps/mobile-app        │           │   │
│  │ 4.1.0-dev              │   │ 1.2.0-dev              │           │   │
│  │ (Electron + Live2D)    │   │ (React Native)         │           │   │
│  │ ↑ 版本反映自身渲染層    │   │ ↑ 獨立版本, 成熟度低    │           │   │
│  │   和安全層的成熟度      │   │   不應跟隨 backend      │           │   │
│  └────────────────────────┘   └────────────────────────┘           │   │
│                                                                     │
│  ┌────────────────────────┐   ┌────────────────────────┐           │   │
│  │ packages/cli           │   │ packages/biology-core  │           │   │
│  │ 1.1.0 ✅               │   │ 1.0.0 ✅               │           │   │
│  │ (Python CLI, 獨立工具)  │   │ (Voxel DNA, 獨立包)    │           │   │
│  └────────────────────────┘   └────────────────────────┘           │   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

#### 子版本號錯誤修正行動清單

| 文件 | 當前值 | 正確值 | 操作 | 緊急性 |
|------|--------|--------|------|--------|
| `apps/backend/pyproject.toml` | 0.1.0 | 7.5.0-dev | 修改 version 字段 | 🔴 High |
| `apps/backend/setup.py` | 0.1.0 | 7.5.0-dev | 修改 version 字段 | 🔴 High |
| `apps/backend/package.json` | 1.0.0 | 7.5.0-dev | 修改 version 字段 | 🔴 High |
| `apps/backend/src/core/version.py` | 6.5.0-dev | **7.5.0-dev** | MAJOR +1 | 🔴 High |
| `apps/backend/src/core/__init__.py` | 6.2.0 | 7.5.0-dev | 更新 docstring | 🟡 Medium |
| `apps/desktop-app/electron_app/package.json` | 6.5.0-dev | **4.1.0-dev** | MAJOR -2, MINOR -4 | 🟡 Medium |
| `apps/mobile-app/package.json` | 6.5.0-dev | **1.2.0-dev** | MAJOR -5, MINOR -3 | 🟡 Medium |
| `packages/cli/package.json` | 1.0.0 | **1.1.0** | PATCH +1 (與 __init__.py 統一) | 🟢 Low |
| `VERSION` | 6.2.0 | **7.5.0-dev** | 與 backend 同步 | 🔴 High |
| `config/angela_config.json` | 6.1.0 | **7.5.0-dev** | 與 backend 同步 | 🔴 High |

---

## 2. 全量架構文字設計圖

### 2.1 總體系統架構 (六層全景)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         ANGELA AI — 完整系統架構                               │
│                     Unified AI Project v6.5.0-dev                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 6 — EXECUTION / PRESENTATION (執行與展示層)                    │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│  │  │  Desktop App  │  │  Mobile App  │  │  CLI / REPL  │               │   │
│  │  │  (Electron)   │  │ (ReactNative)│  │  (Python)    │               │   │
│  │  │  Live2D + WS  │  │  QR + AES    │  │  HSP + HTTP  │               │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘               │   │
│  │         │                 │                  │                       │   │
│  │         └─────────────────┼──────────────────┘                       │   │
│  │                    HTTP / WebSocket                                    │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 5 — API / TRANSPORT (API 與傳輸層)                           │   │
│  │                                                                      │   │
│  │  FastAPI (uvicorn) — main_api_server.py (1668 lines)                │   │
│  │  ┌──────────────────────────────────────────────────────────────┐   │   │
│  │  │  Middleware: CORSMiddleware → SignedCommunicationMiddleware   │   │   │
│  │  │  Routes: /api/v1/* (health, status, chat, session, actions)  │   │   │
│  │  │  WebSocket: /ws/* (state sync, heartbeat, messaging)         │   │   │
│  │  │  Session: TTLSessionManager (1h TTL, LRU, max 1000)          │   │   │
│  │  └──────────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 4 — APPLICATION SERVICES (應用服務層)                        │   │
│  │                                                                      │   │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────┐ ┌──────────────────┐   │   │
│  │  │ChatService │ │LLMService  │ │Vision/   │ │EconomyManager    │   │   │
│  │  │(state混成)  │ │(Multi-LLM) │ │Audio/    │ │(Angela經濟系統)   │   │   │
│  │  │            │ │Ollama/GPT/ │ │Tactile   │ │                  │   │   │
│  │  │            │ │Gemini      │ │Services  │ │                  │   │   │
│  │  └────────────┘ └────────────┘ └──────────┘ └──────────────────┘   │   │
│  │                                                                      │   │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────┐ ┌──────────────────┐   │   │
│  │  │Wiring      │ │AngelaTypes │ │Math      │ │BrainBridge       │   │   │
│  │  │(DI注入)     │ │(Pydantic)  │ │Verifier  │ │Service           │   │   │
│  │  └────────────┘ └────────────┘ └──────────┘ └──────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 3 — CORE INFRASTRUCTURE (核心基礎設施層)                      │   │
│  │                                                                      │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │   │
│  │  │ HAM Memory   │ │ Digital Life │ │ HSP Protocol │                 │   │
│  │  │ Manager      │ │ Integrator   │ │ MQTT Bridge  │                 │   │
│  │  │ (ChromaDB)   │ │ (代謝心跳)    │ │ Pub/Sub      │                 │   │
│  │  ├──────────────┤ ├──────────────┤ ├──────────────┤                 │   │
│  │  │State Matrix  │ │ ConfigLoader │ │ Security     │                 │   │
│  │  │4D (αβγδ)     │ │ (YAML三層)   │ │ A/B/C Keys   │                 │   │
│  │  │→ 8D (εθζη)   │ │              │ │ Encryption   │                 │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                 │   │
│  │                                                                      │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │   │
│  │  │Neuroplasticity│ │Endocrine     │ │Metamorphosis │                 │   │
│  │  │(記憶強化)     │ │System (內分泌)│ │ (靈魂核心)    │                 │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 2 — AI ENGINE (人工智慧引擎層)                                │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────┐    │   │
│  │  │  AGENT SYSTEM (10+ Agents)                                   │    │   │
│  │  │  CreativeWriting / CodeUnderstanding / DataAnalysis           │    │   │
│  │  │  KnowledgeGraph / ImageGeneration / Planning / WebSearch     │    │   │
│  │  │  NLPProcessing / Vision / FantasyDM / Audio                 │    │   │
│  │  └─────────────────────────────────────────────────────────────┘    │   │
│  │                                                                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │   │
│  │  │Alignment │ │Learning  │ │Reasoning │ │LIS (免疫系統)        │  │   │
│  │  │(ASI對齊)  │ │(經驗回放) │ │(因果推理) │ │ErrIntrospector      │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘  │   │
│  │                                                                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │   │
│  │  │RAG       │ │Personality│ │Response  │ │Formula Engine        │  │   │
│  │  │Manager   │ │Manager   │ │Generator │ │(Meta Formulas)       │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  LAYER 1 — THEORETICAL FOUNDATION (理論基礎層)                       │   │
│  │                                                                      │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐   │   │
│  │  │HSM Formula │ │CDM Dividend│ │Life        │ │Active Cognition│   │   │
│  │  │(時空映射)   │ │(認知紅利)   │ │Intensity   │ │(主動認知)      │   │   │
│  │  ├────────────┤ ├────────────┤ ├────────────┤ ├────────────────┤   │   │
│  │  │Non-Paradox │ │Precision   │ │Maturity    │ │Angela DNA     │   │   │
│  │  │(非悖論)     │ │(精度管理)   │ │L0-L11      │ │(體素骨架)      │   │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │  CROSS-CUTTING — INTEGRATIONS (橫切集成層)                           │   │
│  │                                                                      │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │   │
│  │  │Atlassian     │ │Google Drive  │ │Rovo Dev      │                 │   │
│  │  │(Confluence+  │ │(File Ops)    │ │Agent         │                 │   │
│  │  │ Jira)        │ │              │ │              │                 │   │
│  │  ├──────────────┤ ├──────────────┤ ├──────────────┤                 │   │
│  │  │MCP Protocol  │ │OS Bridge     │ │Firebase      │                 │   │
│  │  │(Context7)    │ │(OS操作)      │ │(Cloud)       │                 │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘                 │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 桌面端內部架構 (Electron)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Angela Desktop App (Electron)                     │
├─────────────────────────────────────────────────────────────────────┤
│  Main Process (main.js — 1566 lines)                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Window: frameless, transparent, always-on-top, 1280x720     │   │
│  │  Lifecycle: single-instance, tray hide (no quit on close)    │   │
│  │  Security: contextIsolation=true, nodeIntegration=false       │   │
│  │  GPU: WebGL2 enabled (for Live2D Cubism SDK 5 R5)           │   │
│  │  WebSocket: Node ws client → IPC bridge to renderer          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  Preload (preload.js — 142 lines)                                  │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  contextBridge.exposeInMainWorld('electronAPI', {            │   │
│  │    window: {minimize, maximize, close, resize, ...}          │   │
│  │    live2d: {loadModel, getModels}                            │   │
│  │    backend: {get/set IP}                                     │   │
│  │    security: {init, encrypt, decrypt}                        │   │
│  │    websocket: {connect, disconnect, send, getStatus}         │   │
│  │    ... 15+ namespaces                                        │   │
│  │  })                                                          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  Renderer Process (Vanilla JS — 30+ modules)                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  app.js (1312 lines)  — Main orchestrator                    │   │
│  │  api-client.js (506)  — REST fetch() to backend              │   │
│  │  backend-websocket.js (1264)  — WS via IPC bridge           │   │
│  │  live2d-manager.js (1219)  — Character controller            │   │
│  │  live2d-cubism-wrapper.js (1426)  — Cubism SDK 5 wrapper    │   │
│  │  unified-display-matrix.js (1359)  — Coordinate/scaling     │   │
│  │  state-matrix.js  — 4D emotion (αβγδ)                       │   │
│  │  security-manager.js  — Key C encryption                    │   │
│  │  tray-manager.js  — System tray                              │   │
│  │  ... 20+ additional modules                                  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  Live2D Rendering Stack                                           │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Cubism SDK 5 R5 (Core + Framework bundled)                  │   │
│  │  ├── canvas#live2d-canvas (WebGL) — Primary rendering       │   │
│  │  ├── canvas#fallback-canvas (2D) — Fallback sprites         │   │
│  │  ├── div#click-layer — Hit detection                        │   │
│  │  └── Model: miara_pro_en (resources/models/)                │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 後端內部模塊依賴圖

```
┌──────────┐     HTTP/WS     ┌──────────────────┐
│  Desktop  │◄──────────────►│  main_api_server  │
│  /Mobile  │                │  (FastAPI)         │
│  /CLI     │                │  1668 lines        │
└──────────┘                 └─────────┬──────────┘
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                   ┌──────────┐ ┌──────────┐ ┌──────────┐
                   │api/router │ │services/ │ │wiring.py │
                   │ (v1/*)   │ │ (chat,   │ │ (DI)     │
                   └────┬─────┘ │  llm,   │ └──────────┘
                        │       │  vision) │
                        │       └────┬─────┘
                        ▼            ▼
                   ┌─────────────────────────┐
                   │       core/              │
                   │  (基礎設施 + 領域邏輯)    │
                   │                         │
                   │ ┌─────────┐ ┌─────────┐ │
                   │ │autonomous│ │   hsp   │ │
                   │ │(數位生命) │ │ (MQTT)  │ │
                   │ ├─────────┤ ├─────────┤ │
                   │ │config   │ │security │ │
                   │ │(YAML)   │ │(A/B/C)  │ │
                   │ ├─────────┤ ├─────────┤ │
                   │ │state    │ │hardware  │ │
                   │ │(αβγδ+εθζη)│ │(GPU/ACC)│ │
                   │ └─────────┘ └─────────┘ │
                   └───────────┬─────────────┘
                               │
                               ▼
                   ┌─────────────────────────┐
                   │        ai/               │
                   │  (AGI/ASI 引擎)          │
                   │                         │
                   │ ┌─────────┐ ┌─────────┐ │
                   │ │  memory  │ │ agents  │ │
                   │ │  (HAM)   │ │ (x10)   │ │
                   │ ├─────────┤ ├─────────┤ │
                   │ │learning │ │lis      │ │
                   │ │(經驗回放)│ │(免疫)   │ │
                   │ ├─────────┤ ├─────────┤ │
                   │ │response │ │context  │ │
                   │ │(生成器)  │ │(對話)    │ │
                   │ └─────────┘ └─────────┘ │
                   └─────────────────────────┘
```

### 2.4 數據流圖 (一次 Chat 請求的完整路徑)

```
User Input
    │
    ▼
Desktop App (Electron)
    │ POST /api/v1/chat/unified  (JSON)
    ▼
FastAPI Router (CORSMiddleware → SignedCommunicationMiddleware)
    │
    ▼
AngelaChatService
    │
    ├──→ StateMatrix4D.update()   (更新 αβγδεθζη 八維)
    ├──→ IntentRouter
    │       ├── MathIntent  → MathVerifier (ε axis drive)
    │       ├── CodeIntent  → CodeInspectorBridge (β axis drive)
    │       └── General     → LLMService
    ├──→ ThetaRouter (meta-cognitive routing)
    │       ├── Port→Axis mapping
    │       ├── Cascade (ripple through axes)
    │       └── Merge results
    ├──→ HAMMemoryManager.store()  (記憶本次互動)
    ├──→ LIS (ErrIntrospector)     (檢測偏差)
    ├──→ AngelaLLMService         (LLM 推理)
    │       ├──  pack 8D state → _construct_angela_prompt()
    │       ├──  LLM call (Ollama/GPT/Gemini)
    │       └──  unpack response
    ├──→ ResponseComposer (merge LLM + formula + state)
    ├──→ NeuroplasticityBridge (強化相關記憶)
    └──→ MetabolicHeartbeat.tick() (30s cycle)
    │
    ▼
WebSocket Push → Desktop App Renderer
    │
    ├──→ Live2DManager.updateExpression(emotion)
    ├──→ StateMatrixDisplay (αβγδ visualization)
    └──→ ChatPanel.showResponse(text)
```

---

## 3. 淺層檢查 — 目錄結構與模塊邊界

### 3.1 Monorepo 結構完整性

```
unified-ai-project/
├── apps/           # 應用程式 (backend / desktop-app / mobile-app / ...)
│   ├── backend/        Python FastAPI — 主要後端
│   ├── desktop-app/    Electron — 桌面客戶端
│   ├── mobile-app/     React Native — 移動端
│   ├── pixel-angela/   PyQt — 解剖學實驗前端
│   ├── web-live2d-viewer/  Web — Live2D 預覽
│   ├── gemini-os-bridge/   OS 自動化微服務
│   └── training/      模型訓練目錄
├── packages/       # 共享包
│   ├── cli/            Python CLI 工具
│   └── biology-core/   Python 體素 DNA 核心
├── tests/          # 測試套件 (24 子目錄)
├── config/         # 運行時配置
├── docs/           # 文檔 (179+ 文件)
├── scripts/        # 工具腳本 (42+)
├── configs/        # 系統/標準/MOD 配置
└── 根配置          # package.json, pyproject.toml, docker-compose.yml, ...
```

**淺層一致性評分**: ✅ 8/10

| 檢查項 | 結果 | 備註 |
|-------|------|------|
| pnpm workspace 正確 | ✅ | `pnpm-workspace.yaml` 包含 `packages/*`, `apps/*`, `apps/*/electron_app` |
| 各包有 package.json | ✅ | backend/pyproject.toml + package.json, desktop-app/package.json x2 |
| 結構層次一致 | ⚠️ | `electron_app/` 嵌套在 `desktop-app/` 下但 pnpm 直接引用 |
| 無冗餘目錄 | ❌ | `config/` vs `configs/` 並存且含義不明確 |
| 文檔目錄整潔 | ❌ | `docs/` 有 179 個文件，缺乏子目錄層級管理 |

### 3.2 頂層配置完整性

| 配置文件 | 狀態 | 評語 |
|---------|------|------|
| `package.json` | ✅ | 完整的 npm scripts, workspaces, devDependencies |
| `pyproject.toml` | ✅ | Black/isort/flake8/mypy/pytest/coverage 全配置 |
| `.pre-commit-config.yaml` | ✅ | 9 個 hooks + bandit + gitleaks + eslint |
| `.editorconfig` | ✅ | Python 4 spaces, JS 2 spaces |
| `.env.example` | ✅ | 130 行完整模板 |
| `.gitignore` | ✅ | 127 行全面規則 |
| `eslint.config.mjs` | ✅ | Flat config with globals |
| `.prettierrc` | ✅ | No semi, single quote, 100 width |
| `docker-compose.yml` | ✅ | Redis 7 Alpine |
| `.flake8` | ⚠️ | 與 pyproject.toml 中的 flake8 配置重複 |

**淺層發現**: 根目錄有 143 個條目，過多零散文件缺乏目錄整理。`config/` 與 `configs/` 並存造成混淆。

---

## 4. 中層檢查 — 模塊間依賴與數據流

### 4.1 依賴方向與循環依賴

```
正確方向 (Dependency Rule):
    Desktop/Mobile/CLI  →  API/Transport  →  Services  →  Core  →  AI Engine
        (L6)                 (L5)              (L4)        (L3)       (L2)

實際依賴掃描:
    services/main_api_server.py  →  core/autonomous/     ✅ 正確
    services/main_api_server.py  →  ai/memory/           ✅ 正確
    services/angela_llm_service.py  →  ai/agents/        ✅ 正確
    ai/memory/ham_memory/  →  core/config_loader.py     ✅ 正確
    core/autonomous/  →  core/hsp/                      ✅ 正確
    
但發現:
    core/ 中某些模塊直接 import ai/ (違反依賴方向)        ⚠️ 警告
    ai/agents/ 直接 import api/models/                    ⚠️ 警告
```

### 4.2 服務層 (services/) 分析

| 服務 | 文件大小 | 職責 | 是否鬆耦合 |
|------|---------|------|-----------|
| `main_api_server.py` | 1668 行 | API 入口 + WebSocket + 生命週期 | ⚠️ 職責過重 (應分拆) |
| `angela_llm_service.py` | 2196 行 | LLM 路由 + 多後端 + Prompt 構建 | ⚠️ 過大，混合了路由與格式 |
| `chat_service.py` | 中 | 聊天協調 + 狀態矩陣整合 | ✅ |
| `wiring.py` | 中 | DI 注入，連結各服務回調 | ✅ |
| `connection_session.py` | 中 | WebSocket 會話管理 | ✅ |

### 4.3 核心層 (core/) 分析 — 30+ 子包

| 子包 | 文件數 | 關鍵類 | 狀態 |
|------|-------|--------|------|
| `autonomous/` | 60+ | `DigitalLifeIntegrator`, `EndocrineSystem`, `Neuroplasticity`, `CerebellumEngine` | ✅ 核心完整 |
| `hsp/` | 8+ | `HSPConnector`, `MQTTSubscriptionManager`, `HSPFallbackManager` | ✅ 完整 |
| `state/` | 10+ | `StateMatrix4D`, `DimensionState`, `Axis`, `AxisField` | ✅ 完整 |
| `security/` | 8+ | `AuthMiddleware`, `KeyGenerator/Validator`, `SecureEval` | ✅ 完整 |
| `config/` | 5+ | `ConfigLoader`, `AngelaConfigManager`, `TieredConfigLoader` | ✅ 完整 |
| `precision/` | 3 | `PrecisionManager`, `DecimalMemoryBank`, `HierarchicalRouter` | ✅ 完整 |
| `metamorphosis/` | 4 | `SoulCore`, `BodyAdapter`, `TransitionAnim` | ✅ 完整 |
| `maturity/` | 2 | `MaturityManager`, `ExperienceTracker` | ✅ 完整 |
| `system/` | 5+ | `BootstrapManager`, `TieredConfigLoader`, `StateStore` | ✅ 完整 |
| `art/` | 6 | `RealComfyUIAPI`, `RealEdgeTTS`, `RealPlaywrightBrowser` | ✅ 完整 |
| `tracing/` | 3 | `CausalChain`, `CausalTracer`, `ChainValidator` | ⚠️ 新加 |
| `ripple/` | 2 | `RippleNodeSystem` | ⚠️ 迭代中 |
| `metacognition/` | 2 | `MetacognitiveCapabilitiesEngine` | ⚠️ 迭代中 |
| `influence/` | 1 | `InfluenceSpace` | ⚠️ 新加 |

### 4.4 AI 引擎 (ai/) 分析

| 子系統 | 子包數 | 關鍵能力 | 狀態 |
|--------|-------|---------|------|
| **HAM Memory** | 8+ | HAMMemoryManager, ChromaDB, FAISS, AttractorField | ✅ 核心 |
| **Agent System** | 10 agents | CreativeWriting, CodeUnderstanding, DataAnalysis, etc. | ✅ 完整 |
| **Alignment** | 6 | EmotionSystem, ValueSystem, AdversarialGen, Ontology | ⚠️ 部分實現 |
| **Learning** | 5 | ExperienceReplay, KnowledgeDistillation, FactExtraction | ✅ 完整 |
| **LIS** | 4 | ErrIntrospector, HAMLISCache, Antibody Management | ⚠️ 迭代中 |
| **Response** | 5 | Composer, DeviationTracker, NeuroAutoSelector | ✅ 完整 |
| **Context** | 5 | DialogueContext, MemoryContext, Storage backends | ✅ 完整 |
| **Reasoning** | 2 | CausalReasoningEngine | ⚠️ 基礎實現 |
| **Personality** | 2 | PersonalityManager, JSON templates | ✅ 完整 |

### 4.5 中層一致性發現

| 檢查項 | 結果 | 說明 |
|-------|------|------|
| 模塊邊界清晰 | ⚠️ 7/10 | core/autonomous 有 60+ 文件，職責過廣 |
| 依賴方向正確 | ⚠️ 6/10 | 存在少量反向依賴 |
| 服務粒度適當 | ❌ 4/10 | main_api_server.py 1668行, angela_llm_service.py 2196行 過大 |
| 配置分層正確 | ✅ 8/10 | TCS 三層配置 (S/A/M) 設計合理 |
| 錯誤處理統一 | ✅ 8/10 | AngelaError 層次清晰, ErrorHandler 統一 |
| API 設計 RESTful | ⚠️ 6/10 | 部分端點 (如 /system/emergency) 風格不一致 |

---

## 5. 深層檢查 — 核心算法與理論公式

### 5.1 8D 狀態矩陣算法 (StateMatrix4D)

```
維度空間: αβγδεθζη (8 維)
每個維度: { coordinate: (x, y, z), intent_vector: (x, y, z), fields: {...} }

核心算法:
  1. update() → compute_coordinate() → apply_intent_gravity() → apply_inter_dimensional_drag()
  
  2. compute_coordinate()  (動態坐標計算)
     α: x = comfort - tension
        y = (energy - rest_need) × 10
        z = arousal - 0.5
  
  3. apply_intent_gravity()  (意圖重力吸引)
     每 cycle: coordinate += (intent_vector - coordinate) × gravity_strength
  
  4. apply_inter_dimensional_drag()  (維度連動拖拽)
     Δ 在一個維度的變化按權重矩陣傳播到其他維度
  
  5. export_for_llm() → 打包全部 8D + θ + η 狀態供 LLM Prompt
```

**一致性檢查**: `ANGELA_STATUS.md` 中的 8D 定義與 `state_matrix.py` 實際代碼一致。但 `ANGELA_MATRIX_ANNOTATION_GUIDE.md` 只定義了 4D (αβγδ)，缺少 εθζη 四維，存在**文檔滯後**。

### 5.2 HAM Memory 層次算法

```
HAM 記憶層次:
  L1 — Raw Memory (原始記憶):  sensor input, chat history
  L2 — Abstract Memory (抽象記憶):  pattern, concept, relation
  L3 — Symbolic Memory (符號記憶):  symbolic representation, formula

AttractorField 算法:
  1. 每個記憶點在向量空間中有一個位置
  2. Attractor (吸引子) 是穩定點，附近的記憶被"吸引"強化
  3. Gradient descent 導航:
     新記憶位置 = 舊位置 - learning_rate × gradient(fields)
  4. 重要性評分:  relevance = cosine_similarity(query_vector, memory_vector) × importance_weight

向量存儲:
  - ChromaDB: 持久化向量存儲
  - FAISS: 快速相似性搜索
  - JSON: 本地文件備份
```

**一致性檢查**: HAM 的三層記憶模型與 `ANGELA_MATRIX_ANNOTATION_GUIDE.md` 中的 L2 生命層匹配。但相關文檔缺乏對 AttractorField 梯度下降算法的詳細記載。

### 5.3 HSP 協議算法

```
HSP (Hierarchical State Protocol):
  傳輸層: MQTT (paho-mqtt / gmqtt)
  安全層: HMAC-SHA256 簽名 + 時間戳防止重放
  消息格式:
    {
      "type": "fact" | "command" | "query" | "response",
      "payload_schema_uri": "hsp://schema/...",
      "payload": {...},
      "signature": "hmac...",
      "timestamp": 1234567890
    }
  
  服務發現: ServiceDiscoveryModule (UDP multicast + MQTT topics)
  容錯: HSPFallbackManager (file:// → in-memory → http:// → mqtt://)
  ACK 機制: 每個發布消息等待 ACK，超時重試
```

**一致性檢查**: `docs/HSP.md` 與實際 `core/hsp/` 代碼基本一致。但 `payload_schema_uri` 的 `hsp://` URI 格式在代碼中部分為硬編碼，不符合文檔中描述的動態 schema 註冊。

### 5.4 理論公式系統

| 公式 | 數學基礎 | 代碼實現 | 文檔覆蓋 |
|------|---------|---------|---------|
| **HSM Formula** (時空映射) | CognitiveGap + ExplorationEvent → GovernanceBlueprint | `core/hsm_formula_system.py` (393 行) | ✅ 完整 |
| **CDM Dividend** (認知紅利) | CognitiveInvestment → LifeSenseOutput → DividendDistribution | `core/cdm_dividend_model.py` | ✅ 完整 |
| **Life Intensity** (生命強度) | KnowledgeState × ConstraintState × ObserverPresence | `core/life_intensity_formula.py` | ✅ 完整 |
| **Active Cognition** (主動認知) | StressVector + OrderBaseline → ActiveConstruction | `core/active_cognition_formula.py` | ✅ 完整 |
| **Non-Paradox** (非悖論) | GrayZoneVariable × PossibilityState → CoexistenceField | `core/non_paradox_existence.py` | ✅ 完整 |

**一致性檢查**: 這五大公式系統在 `core/__init__.py` 中正確導出，代碼實現完整。但這些公式在實際 chat 流程中的使用程度不一致——部分公式的計算結果並未真正流入 LLM Prompt，屬於「定義完整但集成不完整」。

### 5.5 數位生命算法 (DigitalLifeIntegrator)

```
代謝心跳 (MetabolicHeartbeat):
  週期: 30 秒
  每 tick:
    1. BiologicalIntegrator.update()
       → EndocrineSystem: hormone level adjustment
       → AutonomicNervousSystem: arousal/homeostasis
       → Neuroplasticity: memory reinforcement
    2. StateMatrix4D._post_update()
       → apply_intent_gravity()
       → apply_inter_dimensional_drag()
    3. DigitalLifeIntegrator.check_state_transitions()
       → Lifecycle state: BORN → GROWING → MATURE → AGING → TRANSCEND

神經可塑性 (Neuroplasticity):
  Hebbian 學習: "Fire together, wire together"
  長期增強 (LTP): 高頻刺激 → 突觸連接增強
  長期抑制 (LTD): 低頻刺激 → 突觸連接減弱
  記憶固化: 短期記憶 → 睡眠/休息時 → 長期記憶
```

---

## 6. 一致性綜合評分表

### 6.1 版本一致性 (13 位置全面校驗)

| # | 文件位置 | 聲明版本 | Git 最後更新 | 滯後天數 | 與基準一致? |
|---|---------|---------|-------------|---------|-----------|
| 1 | `package.json` | **6.5.0-dev** | 2026-05-25 (HEAD) | 0 | ✅ 基準 |
| 2 | `core/version.py` | **6.5.0-dev** | 2026-05-24 | 1 | ✅ |
| 3 | `desktop-app/package.json` | **6.5.0-dev** | 2026-05-24 | 1 | ✅ |
| 4 | `mobile-app/package.json` | **6.5.0-dev** | 2026-05-24 | 1 | ✅ |
| 5 | `VERSION` | **6.2.0** | 2026-02-07 | **107** | ❌ 落後 3 minor + 1 phase |
| 6 | `config/angela_config.json` | **6.1.0** | 2026-02-07 | **107** | ❌ 落後 4 minor + 1 phase |
| 7 | `core/__init__.py` | **6.2.0** | 2026-02-22 | **92** | ❌ 落後 3 minor + 1 phase |
| 8 | `CHANGELOG.md` (v6.2.2) | **6.2.2** | 2026-05-16 | 9 | ❌ 落後 3 minor |
| 9 | `CHANGELOG.md` (v7.2-7.4) | **7.x** | 2026-05-09 | 16 | ❌ 超前 1 major (虛擬版本) |
| 10 | `ANGELA_STATUS.md` | **v6.3** | — | — | ❌ 格式混亂 |
| 11 | `packages/cli/__init__.py` | **1.1.0** | — | — | ✅ 獨立版本 (不同產品) |
| 12 | `packages/biology-core/package.json` | **1.0.0** | — | — | ✅ 獨立版本 (不同產品) |
| 13 | `reports/*.md` (~20 files) | **v6.2.0~v6.2.3** | 各種日期 | 各種 | ⚠️ 歷史文檔快照 |

**版本一致性統計**: 13 個位置中只有 **4 個** (31%) 與當前基準 `6.5.0-dev` 一致。
3 個核心文件 (`VERSION`, `config`, `core/__init__`) 已超過 90 天未更新。
CHANGELOG 中存在 v7.x 虛擬版本號，與實際代碼 v6.x 不符。

> **版本分數**: 4/13 一致 = **31%** (比之前 22% 略高，因為包含了更多位置的完整校驗)

#### 版本根源追溯結論

| 追問 | 答案 |
|------|------|
| 第一個版本的版本號正確嗎? | `ddb266946` 中 `0.1.0` 是正確的初始標記 |
| 版本號變更的理由是? | 從無理由變更。每次變更都是 AI agent 自動操作，"Fix and update" 是最常見的提交信息，從未解釋版本號變更原因 |
| v1.0~v6.0 真的存在過嗎? | **不存在**。這些版本號只存在於回溯性 CHANGELOG 中，Git 歷史中從未有任何文件被標記為這些版本 |
| v7.x 是真實發布嗎? | **不是**。v7.x 是 AI agent 在 2026-05-09 創建 CHANGELOG 時自行分配的版本號，代碼庫從未正式採用 |
| 6.5.0-dev 從何而來? | 2026-05-24 由 AI agent 直接從 6.2.1 跳至 6.5.0-dev，無對應的 minor 版本遞增過程 |

### 6.2 淺層一致性 (目錄結構)

| 檢查項 | 分數 | 說明 |
|-------|------|------|
| monorepo 結構 | 8/10 | 基本正確，嵌套略亂 |
| 配置完整性 | 9/10 | 幾乎所有工具都有配置 |
| 根目錄整潔 | 5/10 | 143 個條目，文件散落 |
| config/ vs configs/ 混淆 | 4/10 | 兩個配置目錄含義不明 |

> **淺層分數**: 26/40 = **65%**

### 6.3 中層一致性 (模塊依賴)

| 檢查項 | 分數 | 說明 |
|-------|------|------|
| 模塊邊界清晰 | 7/10 | 大部分清晰，部分包過大 |
| 依賴方向正確 | 6/10 | 少量反向依賴 |
| 服務粒度 | 4/10 | 關鍵服務文件過大 |
| 配置分層 | 8/10 | TCS 設計合理 |
| 錯誤處理 | 8/10 | AngelaError 統一 |
| API 設計 | 6/10 | 部分不一致 |
| 橫切關注點 | 7/10 | Security/Logging 良好, Monitoring 一般 |

> **中層分數**: 46/70 = **66%**

### 6.4 深層一致性 (算法與理論)

| 檢查項 | 分數 | 說明 |
|-------|------|------|
| 8D State Matrix 代碼 vs 文檔 | 9/10 | 高度一致 (εθζη 文檔缺) |
| HAM Memory 理論 vs 實現 | 8/10 | AttractorField 缺文檔 |
| HSP Protocol 規範 vs 代碼 | 7/10 | Schema URI 硬編碼問題 |
| 五大公式理論 vs 實現 | 8/10 | 定義完整，集成不完整 |
| 數位生命 vs 文檔 | 8/10 | 大部分一致 |
| LIS 設計 vs 實現 | 6/10 | 部分 LIS 功能未完全實現 |
| Agent System 設計 vs 實現 | 8/10 | AgentManager 完整 |
| Matrix Annotation vs 實際代碼 | 5/10 | 部分模塊缺少註解 |

> **深層分數**: 59/80 = **74%**

### 6.5 總體一致性評分

| 層級 | 分數 | 權重 | 加權分 |
|------|------|------|--------|
| 版本一致性 | 31% (13中4) | 15% | 4.7% |
| 淺層 (結構) | 65% | 25% | 16.3% |
| 中層 (模塊) | 66% | 35% | 23.1% |
| 深層 (算法) | 74% | 25% | 18.5% |
| **總分** | | **100%** | **62.6%** |

> **整體架構一致性評分**: 62.6% — **中等偏下，需要系統性改善**
>
> 相比初版 61.2% 微升 1.4%，原因僅是納入了更多版本位置的校驗，暴露了更多不一致（13 個位置僅 4 個一致），但版本一致性權重僅 15%，對總分影響有限。

---

## 7. 關鍵發現與矛盾點

### 7.1 嚴重問題 (Critical)

| # | 問題 | 影響 | 涉及文件 | Git 根源 |
|---|------|------|---------|---------|
| C1 | **版本號散亂**: 13 個位置僅 4 個一致。`VERSION` 和 `config/angela_config.json` 已 **107 天未更新** | 混淆開發者、CI/CD 可能誤判、無法確定發布版本 | VERSION, config/*, core/*, docs/* | `b29441e74` 創建時就不一致；之後無人維護 |
| C2 | **CHANGELOG v7.x 是 AI agent 虛構的版本號**: v7.2.0~v7.4.0 描述的功能存在於代碼，但版本號從未被寫入任何源代碼文件。Git 中**無對應 tag、無對應 package.json 版本** | 版本追溯混亂，新開發者無法理解版本譜系 | CHANGELOG.md | `0e803d64` agent 首次創建 CHANGELOG 時自行分配 |
| C3 | **無版本管理流程**: 所有版本變更均由 AI agent 在 "Fix and update" 提交中自動完成，從無人工審核、無版本發布規範 | 版本號失去語義，無法作為發布依據 | 全局 | 項目從第一天起就沒有版本管理約定 |
| C4 | **config/ vs configs/** 雙目錄 | 配置不統一，可能覆蓋錯誤 | config/, configs/ | 目錄重構未完成 |

### 7.2 中度問題 (Major)

| # | 問題 | 影響 | 涉及文件 |
|---|------|------|---------|
| M1 | **main_api_server.py 1668 行**: 職責過重 | 維護困難，測試覆蓋低 | services/main_api_server.py |
| M2 | **angela_llm_service.py 2196 行**: 混合路由/格式/調用 | 違反單一職責 | services/angela_llm_service.py |
| M3 | **core/autonomous/ 60+ 文件**: 包過大 | 邊界模糊，應拆分 | core/autonomous/ |
| M4 | **Matrix Annotation 覆蓋不全**: 部分模塊無注解 | 違反 AGENTS.md 規範 | 多個 ai/ 子包 |
| M5 | **8D 文檔滯後**: ANGELA_MATRIX_GUIDE 只定義了 4D | 文檔與代碼不同步 | ANGELA_MATRIX_ANNOTATION_GUIDE.md |
| M6 | **五大公式集成不完整**: 定義有但未實際用於推理 | 浪費計算資源 | core/*_formula_*.py |

### 7.3 輕微問題 (Minor)

| # | 問題 | 涉及 |
|---|------|------|
| m1 | 根目錄 143 個條目過多 | 需要整理到子目錄 |
| m2 | docs/ 179 個文件無子目錄管理 | docs/ |
| m3 | HSP payload_schema_uri 硬編碼 | core/hsp/ |
| m4 | 缺少 docs/ARCHITECTURE.md 作為權威架構文檔 | — |
| m5 | 測試覆蓋率目標 80% 但實際約 60%-70% | tests/ |

---

## 8. 改進建議

### 8.1 立即行動 (Priority High)

1. **統一版本號 — 解決 107 天未更新的文件**:
   - 更新 `VERSION` 文件: `6.2.0` → `6.5.0-dev`
   - 更新 `config/angela_config.json`: `6.1.0` → `6.5.0-dev`
   - 更新 `core/__init__.py` docstring: `6.2.0` → `6.5.0-dev`
   - **建立 CI 檢查**: 在 `ci.yml` 中加入版本一致性檢查，確保所有版本位置一致

2. **解決 CHANGELOG v7.x 分歧**:
   - 方案 A (推薦): 將 v7.x 條目標註為 `[7.2.0] → Internal/Unreleased`，明確標記這些是非正式內部版本
   - 方案 B: 將 CHANGELOG 全部重寫為線性 v6.x 譜系，v7.x 的功能歸入對應的 v6.x 版本
   - **根本原因**: 防止 AI agent 未來再次自行分配版本號，應在 `AGENTS.md` 中增加"禁止 AI 自行分配主版本號"的規則

3. **建立版本發布流程**:
   - 定義 `CONTRIBUTING.md` 中的版本變更規則:
     - MAJOR: 架構重大重構或打破向後兼容
     - MINOR: 新功能 (必須有對應 CHANGELOG 條目)
     - PATCH: 修復 (必須有對應 commit message)
   - 創建 `RELEASE_CHECKLIST.md` 模板
   - **禁止裸 "Fix and update" 提交** — 要求每個版本變更必須明確說明理由

4. **整理 config 目錄**: 合併 `config/` 和 `configs/` 為單一 `config/` 目錄

### 8.2 短期 (Priority Medium)

4. **拆分大型服務文件**: 
   - `main_api_server.py` → `api/lifespan.py` + `api/routes/*.py` + `services/websocket_manager.py`
   - `angela_llm_service.py` → `services/llm/router.py` + `services/llm/providers/*.py`
5. **重構 `core/autonomous/`**: 按領域拆分為 `life/`, `bio/`, `engine/`
6. **更新 Matrix Annotation**: 補全缺失的 εθζη 維度到指南和代碼註解
7. **集成理論公式**: 將五大公式計算結果實際注入 LLM Prompt

### 8.3 長期 (Priority Low)

8. **建立架構治理**: 建立 `docs/ARCHITECTURE.md` 為單一事實來源 (SSOT)
9. **根目錄清理**: 將零散文件歸類到 `docs/`, `tools/`, `scripts/`
10. **提升測試覆蓋率**: 從 ~70% 提升到 85%+
11. **自動化一致性檢查**: 在 CI 中增加版本號一致性、依賴方向檢查

---

## 附錄 A: 文件計數統計

| 類別 | 數量 | 說明 |
|------|------|------|
| Python 文件 | ~1,001 | 主要後端邏輯 |
| JS/TS 文件 | ~140 | Electron + 工具 |
| MD 文檔 | ~805 | 包含大量生成文檔 |
| 配置文件 | ~577 | YAML/JSON/TOML/INI |
| 測試文件 | ~238 | 24 個測試子目錄 |
| **總計** | **~2,761** | |

## 附錄 B: 分支拓撲 (關鍵分支)

| 分支 | 基於 | 狀態 | 用途 |
|------|------|------|------|
| `main` | — | Active | 主開發分支 |
| `master` | 初始 | ⏸️ 停滯 | Git 初始分支 (與 main 分離) |
| `v6.0-clean` | main | ⏸️ | v6.0 清理版本 |
| `infra/backups` | main | Active | 每週配置備份 |
| `fix/*` | main | Merged | 各類修復分支 |
| `feature/*` | main | Merged | 各類功能分支 |
| `dependabot/*` | main | Auto | 自動依賴更新 |

## 附錄 C: 術語對照表

| 術語 | 全稱 | 說明 |
|------|------|------|
| HAM | Hierarchical Associative Memory | 分層關聯記憶 |
| HSP | Hierarchical State Protocol | 分層狀態協議 (MQTT 基礎) |
| LIS | Linguistic Immune System | 語言免疫系統 |
| AVIS | AI Virtual Input System | AI 虛擬輸入系統 |
| HSM | Hierarchical Space-time Map | 分層時空映射 |
| CDM | Cognitive Dividend Model | 認知紅利模型 |
| MCP | Model Context Protocol | 模型上下文協議 |
| TCS | Tiered Configuration System | 分層配置系統 |
| UDM | Unified Display Matrix | 統一顯示矩陣 (桌面坐標) |

---

> **文檔信息**:  
> 生成方式: 基於 100% 實際代碼分析 (Git 歷史、文件結構、配置、算法源碼)  
> 分析深度: 淺層(目錄) → 中層(模塊依賴) → 深層(算法數學)  
> 生成日期: 2026-05-25  
> 分析工具: 手動代碼審查 + 靜態分析
