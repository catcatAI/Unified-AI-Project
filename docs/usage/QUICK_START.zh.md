<!--
  =============================================================================
  ANGELA-MATRIX: L3 [β] [B] [L4]
  FILE_HASH: Initial
  FILE_PATH: docs/usage/QUICK_START.zh.md
  FILE_TYPE: documentation
  PURPOSE: 快速開始指南 — 從複製專案到啟動系統的直接路徑
  VERSION: 1.0.0
  STATUS: active
  LANGUAGE: zh-tw
  AUDIENCE: users, developers
  LAST_MODIFIED: 2026-07-07
  =============================================================================
-->

# 快速開始指南

> **目標**：在 10 分鐘內讓 Angela AI 系統啟動運行。

## 環境需求

| 需求 | 版本 | 說明 |
|------|------|------|
| Python | 3.10+ | 已測試 3.10–3.14 |
| Node.js | 16+ | 前端所需 |
| pnpm | 最新 | JS 工作區管理器（可用 `npx pnpm`） |
| Ollama | 最新 | 本地 LLM 後端（可選但推薦） |

## 我該裝哪個層級？

後端依賴已依需求拆分成數個層級，只裝你需要的即可。

| 我是…​ | 指令 | 得到什麼 | 大致體積 |
| --- | --- | --- | --- |
| **只想快速試用** | `pip install -e "apps/backend"` | 伺服器 + 核心 AI（GARDEN/ED3N，純 numpy 後端）。不含 torch、不含向量庫。 | 最小 / 最快 |
| **有需求、要完整功能** | `pip install -e "apps/backend[standard]"` | 以上全部 **＋ 真實神經嵌入（torch）、ChromaDB 向量庫、媒體（TTS/OCR/螢幕）、GPU 遙測、Redis 快取**。 | 大（含 torch 約 120MB） |
| **開發者 / 貢獻者** | `pip install -e "apps/backend[dev]"` | *standard* 全部 **＋ 測試與品質工具鏈**（pytest、black、isort、flake8、mypy、pre-commit、MQTT 測試 broker）。 | 最大 |

也可自由組合更細的群組，例如 `pip install -e "apps/backend[ml,vector]"`。
可用群組：`ml`、`vector`、`data`、`media`、`gpu`、`cache`、`google`、`docs`、`nlp`、`installer`、`game`。`full` 會裝上全部。

## 第一步：複製並設定

```powershell
git clone https://github.com/catcatAI/Unified-AI-Project.git
cd Unified-AI-Project

# Python 虛擬環境
python -m venv .venv
.venv\Scripts\Activate.ps1

# 安裝後端依賴（於 repo 根目錄執行）。三選一：
#
#   快速體驗  — 輕量，只啟動伺服器 + 核心 AI（numpy 後端，無 torch/向量庫），
#              安裝最快：
pip install -e "apps/backend"
#
#   完整功能  — 有需求的用戶：真實嵌入（torch）、向量資料庫、媒體、GPU、快取：
# pip install -e "apps/backend[standard]"
#
#   開發者    — 完整功能 + 測試/檢查/型別工具鏈（pytest、black、mypy…）：
# pip install -e "apps/backend[dev]"

# 安裝 JS 依賴
npx pnpm install --no-frozen-lockfile
npx pnpm approve-builds --all
```

## 第二步：設定

複製環境模板並依需求編輯：

```powershell
copy .env.example .env
```

直接啟動的最低 `.env` 設定：

```ini
# LLM 後端（至少需要一個）
OLLAMA_HOST=http://localhost:11434
OPENAI_API_KEY=

# 系統
LOG_LEVEL=INFO
```

**沒有 LLM？** 系統會自動降級至 ED3N+GARDEN 內建推論模型。功能會受限（詳見 [SCENARIOS.zh.md](SCENARIOS.zh.md#不使用-llm)）。

## 第三步：啟動

```powershell
# 方式 A：統一啟動器（推薦）
python scripts/run_angela.py

# 方式 B：僅啟動後端
python scripts/run_angela.py --api-only

# 方式 C：先執行健康檢查
python scripts/run_angela.py --health-check
```

後端啟動於 `http://localhost:8000`。API 文檔位於 `http://localhost:8000/docs`。

## 直接可用功能

| 功能 | 狀態 | 預期行為 |
|------|------|----------|
| **聊天 API** | ✅ | `POST /api/v1/chat` — 基礎對話，情緒感知回應 |
| **情緒系統** | ✅ | 人格根據對話上下文動態調整 |
| **記憶系統** | ✅ | HAM + VectorStore，跨會話持久化 |
| **圖片理解** | ✅ | `POST /api/v1/chat` 附圖片附件 |
| **TTL 模型** | ✅ | 三層視覺解碼器，已預先訓練 |
| **訓練管線** | ✅ | `python scripts/train_pipeline.py` |
| **Live2D 桌面** | ✅ | `npx pnpm dev:desktop`（另開終端機） |
| **Web 檢視器** | ✅ | `npx pnpm dev:web` |

## 需要 LLM 的功能

若跳過 Ollama 設定，以下功能會降級至 ED3N/GARDEN（品質下降）：

- 複雜對話推理
- 程式碼生成
- 多輪規劃
- 知識問答

## 故障排除

### 「Module not found」錯誤
```powershell
# 重裝你原本使用的層級（範例：standard）
pip install -e "apps/backend[standard]" --force-reinstall
```

### 連接埠 8000 已被佔用
```powershell
# 檢查誰在用
netstat -ano | findstr :8000
# 或修改 .env 中的連接埠：
API_PORT=8001
```

### Live2D 桌面無法開啟
改用 Web 檢視器：
```powershell
npx pnpm dev:web
```
然後在瀏覽器中開啟 `http://localhost:5173`。

### Ghostscript/GPL Ghostscript 警告
這些是無害的，可以忽略。來自 PDF/圖片處理管線。

### 長時間運行記憶體持續增長（記憶體洩漏預防）
若發現長時間運行後記憶體持續增加，系統現在會自動限制內部歷史緩衝區。所有無限制陣列已在第3輪審計中修復：
- **聊天會話**：TTL 快取每60秒清理一次，最多1000個會話
- **向量存儲**：上限10,000條（FIFO 淘汰）
- **情緒歷史**：上限1,000個狀態
- **所有 JS 監聽器陣列**：已去重，`destroy()`時清理
- **Live2D 管理器**：`_stopAnimation` → `stop()`（原拋出 TypeError，導致 rAF/定時器永久洩漏）

### 「No module named 'ai.*'」
確保你在專案根目錄（`Unified-AI-Project/`）執行，而非 `apps/backend/` 內。

## 下一步

- [使用場景](SCENARIOS.zh.md) — 先訓練、先設定、自定義 LLM
- [腳本參考](../scripts/ACTIVE_SCRIPTS.md) — 完整命令目錄
- [架構總覽](../architecture/ANGELA_FULL_ARCHITECTURE.md) — 系統設計
