<!--
  =============================================================================
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: zh-tw/en
  LAST_MODIFIED: 2026-09-21 (R75: 薄索引化 — 狀態/結構/調用細節改由工具生成，本檔只留核心)
  =============================================================================
-->

# Angela AI v7.5.0-dev — Cross-Platform Digital Life System

[English](#english-version) | [繁體中文](#繁體中文版)

跨平台數位生命系統：多模型路由（Ollama / llama.cpp / OpenAI / Anthropic / Gemini
/
unified-1g 本地引擎）、記憶、情緒、安全閘門、11 專業 Agent、Live2D 桌面具身化、Luanti 遊戲代理（識別／記憶／自主探索／行為訓練）。

**本 README 只回答「這是什麼、怎麼啟動、去哪查」。**
狀態、結構、調用細節全部由工具實時生成——不會過期：

| 問題                       | 去哪查                                                                                             | 性質                         |
| -------------------------- | -------------------------------------------------------------------------------------------------- | ---------------------------- |
| 現在能幹嘛？多成熟？       | [STATUS_MATRIX.md](docs/STATUS_MATRIX.md)（真相源：[status_matrix.yaml](docs/status_matrix.yaml)） | 生成（手改會被覆蓋）         |
| 專案全貌／模組樹／路由表   | [PROJECT_MAP_GENERATED.md](docs/PROJECT_MAP_GENERATED.md) 或 `--module` 查詢                       | 生成（永不過期）             |
| 怎麼用？配什麼？怎麼驗證？ | [INVOCATION_MATRIX.md](docs/INVOCATION_MATRIX.md)                                                  | 手寫（照表調用失敗不許過夜） |
| 明確不支援什麼？           | [unsupported.md](docs/user_guide/unsupported.md)                                                   | 手寫                         |
| 其他所有文檔               | [docs/INDEX.md](docs/INDEX.md)                                                                     | 索引                         |

<a name="english-version"></a>

## Quick Start

```bash
# Clone
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# (Recommended) Setup and activate Python virtual environment (.venv)
python -m venv .venv
# On Windows PowerShell:
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install Python backend dependencies (run from repo root). Pick ONE tier:
pip install -e "apps/backend"            # Quick start: lightweight (numpy backend, no torch/vector DB)
# pip install -e "apps/backend[standard]"  # Full features: torch embeddings + ChromaDB + media + GPU + cache
# pip install -e "apps/backend[dev]"       # Developer: standard + pytest/black/mypy/pre-commit toolchain

# Install JS workspace dependencies using pnpm (use npx if pnpm is not installed globally)
npx pnpm install --no-frozen-lockfile
npx pnpm approve-builds --all

# Option 1: Use unified launcher (Recommended)
python scripts/run_angela.py              # Start all (backend + desktop)
python scripts/run_angela.py --api-only   # Backend only
python scripts/run_angela.py --health-check  # Health check

# Option 2: Start backend directly
python apps/backend/start_server.py

# Option 3: Start desktop app (separate terminal)
npx pnpm dev:desktop

# Option 4: Play the text adventure game (no LLM needed)
pip install -e "apps/backend[tui]"   # Install TUI dependencies (textual + rich)

# Textual TUI (apps/backend/src/game)
cd apps/backend && python -m src.game.app

# CLI RPG (apps/game-rpg)
python apps/game-rpg/run_game.py
```

**Prerequisites**: Python 3.10+, Node.js 16+, Ollama (LLM backend).

> **New to the project?** See [QUICK_START.md](docs/usage/QUICK_START.md) for a
> step-by-step walkthrough, troubleshooting tips, and expected behavior. For
> optional training or custom configuration, see
> [SCENARIOS.md](docs/usage/SCENARIOS.md).

## Project Map — 官方導航方式（AI/人皆適用）

全倉結構事實由 `scripts/gen_project_map.py`（stdlib-only，AST 掃描）實時提供：

```bash
# 生成全圖（含入口點/API 路由表/模組樹/callers/測試映射/孤兒診斷/預算門）
python scripts/gen_project_map.py --budget 10000

# 查詢模式：一個模組的實時情報（imports/callers/tests/top-level defs）
python scripts/gen_project_map.py --module game_agent
python scripts/gen_project_map.py --module execution_gate --limit 3
```

生成圖四區塊：依賴排錯（第三方/倉內分開）→ 碰撞索引（同名檔深→淺）→實時結構（入口點、123 條 FastAPI 路由、模組樹、被引用 Top、測試映射、STATUS_MATRIX 宣稱 vs 實體核對）→ 行為核心（驗收門/配置鍵/大檔/未用 import）。

## Status — 對內外宣稱的唯一出口

- **[STATUS_MATRIX.md](docs/STATUS_MATRIX.md)**：23 條功能 × 五級狀態（`claimed`
  → `implemented` → `wired` → `verified` →
  `production`），每列附驗證指令與日期。**改狀態只改 YAML，重跑生成器**：

  ```bash
  python scripts/gen_status_matrix.py            # YAML → STATUS_MATRIX.md
  python scripts/gen_status_matrix.py check      # 三層核對（結構/實體/語意）
  ```

- 交叉核對自動化：`gen_project_map.py`
  會驗證 YAML 宣稱的每個 implementation/tests 路徑真實存在；違規即 CI 紅。
- 誠實缺口（mypy
  432 棘輪門、angela_bench 已建仍有跨 AI 對比待接入、live 訓練樣本等）見 STATUS_MATRIX。

## What Does NOT Work — 防重實作清單（手寫保護區）

以下已刪除，**請勿重新實作**（歷史脈絡見 `docs/` 歸檔）：

- **Mobile app**（Phase 11 🗑️）、**TactileService**（無硬體，Phase 11 🗑️）
- **ImageGenerationAgent / ComfyUIClient / AngelaRealPainter**（stub，Phase 9-10
  🗑️）
- **`services/wiring.py`**（死碼，Phase 11 🗑️）
- **11 dead
  subsystems**（learning/ops/dialogue/evaluation/execution/code_inspection/
  compression/lis/language_models/integration/symbolic_space，Phase 11b 🗑️）
- **5 dead
  modules**（code_understanding/personality/time/translation/distributed，Phase
  12 🗑️）
- **Trust module**（Phase 12b 🗑️）、**`ai/security/`**（空模組，Phase 9 🗑️）
- **`comic_composer.py`**（佔位 URL，Phase 9 🗑️）

## CI Gates（提交前自查）

```bash
python scripts/gen_project_map.py --budget 10000   # 地圖預算門（超標=專案有病）
python scripts/gen_status_matrix.py check          # 狀態宣稱核對
python scripts/mypy_budget_gate.py                 # mypy 棘輪門（基線 391，只降不升；--top N 附按檔案分布報告）
python -m pytest tests/                            # 全倉測試
python -m flake8 && python -m black --check . && python -m isort --check-only .
npx prettier --check .                             # 全倉格式（豁免見 .prettierignore）
```

隨機三目錄組合測試在 CI 每次探索一種組合（防 sys.path 類跨套件汙染回歸）。

## Documentation Index

- [docs/INDEX.md](docs/INDEX.md) — 全部文檔索引
- [INVOCATION_MATRIX.md](docs/INVOCATION_MATRIX.md)
  — 啟動入口 9 種／核心 API／配置 5 層／模組重複度結論
- [RELEASE_CRITERIA.md](docs/06-project-management/RELEASE_CRITERIA.md)
  — 發佈六維度門檻
- [QUICK_START.md](docs/usage/QUICK_START.md) /
  [SCENARIOS.md](docs/usage/SCENARIOS.md)

<a name="繁體中文版"></a>

## 繁體中文版

**本檔只回答「這是什麼、怎麼啟動、去哪查」。** 狀態看
[STATUS_MATRIX.md](docs/STATUS_MATRIX.md)（真相源
[status_matrix.yaml](docs/status_matrix.yaml)，改狀態只改 YAML）、結構看
[PROJECT_MAP_GENERATED.md](docs/PROJECT_MAP_GENERATED.md) 或
`python scripts/gen_project_map.py --module <片段>` 查詢、調用看
[INVOCATION_MATRIX.md](docs/INVOCATION_MATRIX.md)、不支援項看
[unsupported.md](docs/user_guide/unsupported.md)。

### 快速啟動

```bash
# 克隆專案
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# (推薦) 建立並啟用 Python 虛擬環境
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# 安裝後端 Python 依賴（於 repo 根目錄執行）。三選一：
pip install -e "apps/backend"            # 快速啟動：輕量（numpy 後端，無 torch/向量庫）
# pip install -e "apps/backend[standard]"  # 完整功能：torch 嵌入 + ChromaDB + 媒體 + GPU + 快取
# pip install -e "apps/backend[dev]"       # 開發者：standard + pytest/black/mypy/pre-commit 工具鏈

# 使用 pnpm 安裝工作區 JS 依賴
npx pnpm install --no-frozen-lockfile
npx pnpm approve-builds --all

# 方式一：使用統一啟動器（推薦）
python scripts/run_angela.py              # 全部啟動（backend + desktop）
python scripts/run_angela.py --api-only   # 僅後端
python scripts/run_angela.py --health-check  # 健康檢查

# 方式二：直接啟動後端
python apps/backend/start_server.py

# 方式三：手動啟動桌面端（另開終端機）
npx pnpm dev:desktop

# 方式四：文字冒險遊戲（無需 LLM）
pip install -e "apps/backend[tui]"
cd apps/backend && python -m src.game.app
```

**前置需求**：Python 3.10+、Node.js 16+、Ollama（LLM 後端）。

> 初次接觸請看[快速開始指南](docs/usage/QUICK_START.zh.md)（逐步解說、疑難排解）。

### 文檔索引

- [docs/INDEX.md](docs/INDEX.md) — 全部文檔索引
- [STATUS_MATRIX.md](docs/STATUS_MATRIX.md) — 功能成熟度唯一總表（生成視圖）
- [INVOCATION_MATRIX.md](docs/INVOCATION_MATRIX.md)
  — 調用矩陣（怎麼用、配什麼、怎麼驗證）
