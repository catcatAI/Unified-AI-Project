# PRD: 全面程式碼審視與開發任務盤點（Unified-AI-Project）

## 1) 背景與目標
- 本專案為 Angela AI v6.2.0 的 monorepo，包含 Python 後端、Electron 桌面端、行動端橋接與 Live2D 相關前端/工具。
- 任務目標：深入審視整個代碼庫，系統化找出所有工程問題、風險與技術債，並產出可執行的開發任務清單與優先序。

## 2) 範圍（In Scope）
- Monorepo 管理與工作流：pnpm workspaces、pre-commit、測試/格式化/lint 指令一致性
- 後端（Python）：FastAPI/服務框架、依賴管理、測試與覆蓋率、型別/靜態分析、結構與封裝
- 桌面端（Electron）：native modules、打包/啟動流程、與後端通訊、Live2D 整合
- 行動端（React Native）：現況盤點與最小可運作路徑
- Web/Live2D viewer：libs 與打包策略、第三方依賴同步
- 測試系統（tests/）：現況、穩定性、覆蓋率、標記與分類
- 安全與配置：金鑰管理、憑證/密碼外洩風險、跨平台相容

不在範圍（Out of Scope）：產品 UI/UX 大改版、非工程面市場/商業策略。

## 3) 目標使用者/利害關係人
- 開發者、維運與測試工程師
- PM/技術負責人（需要清楚的風險/里程碑與可追蹤交付）

## 4) 主要成功指標（Acceptance Criteria）
- 交付一份覆蓋整個代碼庫的「問題清單與開發任務」並含優先級與風險等級
- 指令可在乾淨環境穩定執行：
  - JS/TS：`pnpm lint`、`pnpm format`、`pnpm test`
  - Python：`flake8 apps/backend/src tests/`、`black apps/backend/src tests/`、`isort apps/backend/src tests/`、`mypy apps/backend/src`、`pytest tests/`
- 能在本地成功啟動後端與桌面端最小路徑（README/腳本與現況一致）
- 明確列出開放問題（Open Questions）並得到決策或假設

## 5) 既有結構與技術概況（初步盤點）
- Monorepo
  - [./pnpm-workspace.yaml](./pnpm-workspace.yaml)：workspaces = `packages/*`、`apps/*`、`apps/desktop-app/electron_app`
  - Root [./package.json](./package.json)：提供 `dev`, `test`, `lint`, `format`, `check`, `setup`, `build` 等腳本
  - Root [./pyproject.toml](./pyproject.toml)：Black/isort/flake8/mypy/pytest/coverage 統一配置（Python 3.8+）
  - Pre-commit：存在 root 與 apps/backend 兩份 [.pre-commit-config.yaml]
- 後端（Python）
  - [./apps/backend/README.md](./apps/backend/README.md) 宣稱 FastAPI + Uvicorn，提供 `pnpm --filter backend dev` 執行方式
  - [./apps/backend/package.json](./apps/backend/package.json) 內含多個 Python 腳本橋接、`dev:api` 指向 `uvicorn src.services.main_api_server:app`
  - 依賴管理分散：`apps/backend/pyproject.toml`、`apps/backend/requirements.txt`、`apps/backend/requirements-dev.txt`、root `requirements.txt`
  - `apps/backend/pyproject.toml` 的 metadata 與依賴列表出現 Flask 與 sampleproject 連結，與 README/FastAPI 敘述不一致
- 桌面端（Electron）
  - [./apps/desktop-app/README.md](./apps/desktop-app/README.md) 標示「Temporarily Unavailable」
  - [./apps/desktop-app/electron_app/README.md](./apps/desktop-app/electron_app/README.md) 提供完整啟動/打包/功能 API 與 Node 18+ 要求
  - 原生音訊模組位於 `apps/desktop-app/native_modules/*`（Windows/macOS/Linux），需各自編譯
- 行動端（Mobile）
  - 存在 `apps/mobile-app`（含 React Native 設定與 API 客戶端等檔）
- Live2D / Web viewer
  - `apps/web-live2d-viewer` 與嵌入的 `libs/live2dframework` TypeScript/JS 原始碼與建置設定
- 測試系統
  - [./tests/README.md](./tests/README.md) 說明測試目錄結構與改進計畫，指出部分模組覆蓋率不足
  - 專案根目錄存在大量 `tests/` 測試與 `tests_backup/` 歷史測試

## 6) 初步發現的問題與風險（待驗證/落地任務來源）
- 依賴與建置一致性
  - Python 依賴定義分散且不一致：root `requirements.txt` vs `apps/backend/requirements*.txt` vs `apps/backend/pyproject.toml` vs root `pyproject.toml`
  - `apps/backend/pyproject.toml` 指向 Flask 與 sampleproject URLs，需與實際 FastAPI/專案資訊對齊
  - Node 版本要求不一致：root engines `node >=16`，electron_app README 要求 Node 18+
  - pnpm workspace 與 `apps/desktop-app/electron_app` 的套件安裝/打包流程需對齊 root 腳本
- 架構與程式碼健康
  - 後端框架敘述與實作需統一（FastAPI 為主？是否仍兼容 Flask？）
  - 後端模組邊界、服務劃分、測試隔離與資料夾結構需審視（`src/services`, `src/core`, `src/ai` 等）
  - Live2D libs 原始碼嵌入與版本升級策略（安全/授權/同步風險）
  - `tests_backup/` 與現行 `tests/` 的責任邊界與冗餘
- 測試與品質
  - 覆蓋率目標（root pyproject 指向 apps/backend/src）與實際報告需對齊
  - 測試標記（unit/integration/slow 等）是否貫徹並穩定
  - pre-commit 與 lint/format/type-check 是否在 CI 中強制執行
- 安全與設定
  - A/B/C 金鑰與敏感設定之管理策略（檔案忽略、運行時注入、範例樣板）
  - 原生模組與跨平台打包簽章/權限
  - 依賴安全掃描與定期升級策略

## 7) 交付物
- 全域工程審視報告（本 PRD + 後續技術規格/規劃）
- 「問題清單與開發任務」：分區域（後端/桌面端/行動端/Live2D/測試/Infra），每項含：
  - 說明、衝擊面、風險等級（High/Med/Low）、建議方案、預估工時、驗證方式
- 執行與驗證路徑：
  - JS/TS：`pnpm lint`、`pnpm format`、`pnpm test`
  - Python：`flake8`、`black`、`isort`、`mypy`、`pytest`（參見 root `pyproject.toml` 與 [./agents.md](./agents.md) 的指令約定）

## 8) 里程碑（建議）
1. 現況驗證與一致性修正（依賴/指令/README 與實作對齊）
2. 後端框架與封裝統一、測試基準建立（coverage gate）
3. 桌面端最小可運作路徑（Node 版本、打包、與後端通訊）
4. 安全/金鑰/機密治理與 CI 內化（secret scan / dep audit）
5. Live2D/前端建置與版本升級策略定稿
6. 中長期優化（性能、Observability、開發者體驗）

## 9) 開放問題（需產品/技術決策）
- 後端最終框架標準：完全 FastAPI？是否保留 Flask 相容層？
- Python 依賴單一真實來源（single source of truth）選擇：`pyproject.toml` 還是 `requirements*.txt`？
- Node 版本策略：是否全倉統一為 Node 18+（或 LTS）？
- 桌面端目前狀態：短期目標是 Demo 還是產品級可發佈？
- 測試覆蓋率門檻與必過範圍（>80%？後端為主或全倉？）
- 機密/金鑰治理：目標方案（.env 樣板、Vault、或 CI secret）
- 是否需要正式支援多平台打包（Win/macOS/Linux）與自動化流程？

## 10) 驗證方式
- 在乾淨環境執行：
  - `pnpm install` 與 workspace 範圍安裝是否正常
  - 後端：`pnpm --filter backend dev` 或 `python -m uvicorn src.services.main_api_server:app --reload`
  - 桌面端：`cd apps/desktop-app/electron_app && pnpm start`
- Lint/Format/Type/Test 全綠（參見 root scripts 與 agents.md 指南）

——
以上為「深入審視與任務盤點」之 PRD，後續將在 Technical Specification 與 Planning 中細化執行步驟與具體任務列表（含驗證條件與風險等級）。