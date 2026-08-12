# 專案全面分析報告 — 2026-08-08

<!--
  =============================================================================
  FILE_HASH: TBD
  FILE_PATH: docs/COMPREHENSIVE_PROJECT_ANALYSIS_2026-08-08.md
  FILE_TYPE: documentation
  PURPOSE: 全專案檢查/分析紀錄（測試收集、原始碼缺陷、環境依賴、前端資源、雜物清理）
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-08-08
  AUDIENCE: developers, agents
  =============================================================================
-->

## 1. 摘要

針對整個 Unified-AI-Project (Angela AI v7.5.0-dev) 進行的一次全面檢查與分析。
所有項目皆已**逐項實測驗證**（非僅靜態閱讀），確認**無誤報**。

- 測試收集：**5,378 tests collected, 13 errors**（因錯誤中斷，無法完整執行）
- 原始碼缺陷（阻斷測試收集）：**2 處**
- 環境缺少依賴（阻斷測試收集）：**3 個套件**
- 前端資源缺失：**2 類**
- 後端 CLI 缺陷：**1 處**
- web-dashboard 假資料：**3 個 API route**
- 孤兒/垃圾檔案：**多個**

## 2. 專案概況

| 領域 | 規模 |
|---|---|
| Python 後端 (`apps/backend/src`) | 629 檔 / 146,601 行 |
| 全專案 Python | 1,269 檔 / 263,867 行 |
| JS | 73 檔 |
| TS | 169 檔 |
| 測試檔案 | 356 檔（`tests/` 321 + `apps/backend/tests/` 35） |
| 測試函式 | ~5,314 個 `def test_*` |

主要子系統：ED3N 引擎、GARDEN 引擎、HAM 記憶、多模態編解碼、
LLM 路由（9 providers）、HSP 協定、CNS 事件匯流排、卡片遊戲子系統
（`apps/backend/src/game/`）、根目錄 CLI 文字冒險遊戲（`game.py`/`run_game.py`）。

## 3. 測試收集錯誤（13 errors）— 阻斷套件執行

`python3 -m pytest --collect-only -q` → `5378 tests collected, 13 errors in 45.75s`

### 3.1 🔴 原始碼缺陷（必須修復）

#### 3.1.1 `key_validator.py` 缺少 `Any` import

- **檔案**：`apps/backend/src/core/security/key_validator.py`
- **行號**：line 21（import）、line 172（使用 `Dict[str, Any]`）
- **現象**：`NameError: name 'Any' is not defined`
- **根因**：`from typing import Dict, List, Optional, Tuple` 漏匯入 `Any`
- **受影響測試（3 檔）**：
  - `tests/core/security/test_key_generator.py`
  - `tests/core/security/test_key_validator.py`
  - `tests/core/test_secure_eval.py`
- **驗證**：`from core.security.key_validator import KeyValidator` → NameError 可重現
- **修復**：`from typing import Dict, List, Optional, Tuple, Any`

#### 3.1.2 `token_effects.py` 不存在但被 import

- **檔案**：`apps/backend/src/game/token_effects.py`（**不存在**）
- **引用處**：`apps/backend/src/game/engine.py:13`、`apps/backend/src/game/screens.py:10`
- **現象**：`ModuleNotFoundError: No module named 'apps.backend.src.game.token_effects'`
- **根因**：`.gitignore:72` 的 `*token*` 規則遮蔽了此檔（僅例外排除 `!**/token_stream.py`）。
  全 git 歷史 `git rev-list --all | grep token_effects` 皆查無此檔 → 從未被提交過，
  導致整個 game 子系統無法 import（`game/__init__.py` → `engine.py` → `token_effects` 斷裂）。
- **受影響測試（1 檔）**：`tests/game/test_game_subsystem.py`（13 個 test 全被阻斷）
- **驗證**：`git check-ignore -v` → `.gitignore:72:*token*`；實測 import 可重現
- **修復**：需 (a) `.gitignore` 加 `!**/token_effects.py`；或 (b) 依 `engine.py`/`screens.py`
  的 import 契約補寫 `token_effects.py`（函式：`apply_token_hp`、`apply_token_spirit`、
  `apply_token_skill_bonus`、`get_combat_dice_bonus`、`get_damage_resistance`、
  `get_token_descriptions`、`compute_token_effects`，並含 `TokenEffect` 型別）

### 3.2 🟡 環境缺少依賴（`pip install` 可解）

| 缺失套件 | 宣告位置 | 受影響測試 |
|---|---|---|
| `python-multipart` | `apps/backend/pyproject.toml:53`（BASE 層） | 7 檔（Form data 需要） |
| `paho-mqtt` | `apps/backend/pyproject.toml:40`（BASE 層） | `tests/mcp/test_mcp_fallback_protocols.py` |
| `google-auth` | `apps/backend/pyproject.toml:97`（`google` extra） | `apps/backend/tests/api/v1/endpoints/test_drive_integration.py` |

- **現象**：`RuntimeError: Form data requires "python-multipart"`（7 處）、
  `ModuleNotFoundError: No module named 'paho'`、`No module named 'google.auth'`
- **驗證**：`pip3 list | grep -iE "paho|google|multipart"` → 皆未安裝；對應 pyproject 均有宣告
- **受影響測試總計（9 檔）**：
  - `tests/api/test_api_endpoints.py`
  - `tests/api/test_chat_session_memory.py`
  - `tests/unit/test_causal_session_buffer.py`
  - `apps/backend/tests/api/test_audio_endpoints.py`
  - `apps/backend/tests/api/test_openapi_schema.py`
  - `apps/backend/tests/api/test_router_health_and_root.py`
  - `apps/backend/tests/api/test_vision_endpoints.py`
  - `tests/mcp/test_mcp_fallback_protocols.py`
  - `apps/backend/tests/api/v1/endpoints/test_drive_integration.py`

## 4. 前端資源缺失

### 4.1 Live2D 模型清單指向不存在的 `.model3.json`

- **檔案**：
  - `apps/desktop-app/electron_app/models/models.json`
  - `apps/web-live2d-viewer/models/models.json`
- **現象**：兩檔皆指向 `models/miara_pro_en/runtime/miara_pro_t03.model3.json`，
  且 `packages/shared-js/js/angela-character-config.js:12` 亦指向
  `models/Epsilon_free/runtime/Epsilon_free.model3.json`
- **驗證**：`find ... -name "*.model3.json"` → **0 個**。實際只有 `.moc3`/`.cdi3.json`/
  `.physics3.json`/`.motion3.json`/紋理，缺少 Live2D 必需的 model3 清單檔
- **影響**：Live2D 模型無法載入，會降級為 2D fallback（`isFallback=true`）

### 4.2 Cubism Framework bundle 路徑不存在

- **檔案**：`apps/desktop-app/electron_app/index.html:846`
- **現象**：`libs/live2dframework/dist/live2dcubismframework.bundle.js` 不存在
- **驗證**：`libs/live2dframework/dist/` 目錄不存在（無 build 腳本在
  `live2dframework/package.json`，tsc/webpack 鏈未建立）
- **影響**：桌面端 Live2D 會記錄 "Cubism Core not found" 並用 fallback

## 5. 後端 CLI 缺陷

- **檔案**：`packages/cli/cli/__main__.py`
- **現象**：`from .cli_runner import main`，但 `cli_runner.py` 位於
  `packages/cli/cli_runner.py`（上一層），`packages/cli/cli/cli_runner.py` 不存在
- **驗證**：實測 `ls` → `cli/cli_runner.py` 不存在
- **影響**：`python -m cli`（或 `python -m cli.cli`）會 `ModuleNotFoundError`；
  pnpm scripts 改用 `python -m cli.unified_cli`（可用）繞過

## 6. web-dashboard 假資料與未使用元件

- **假資料 API（3 檔）**：`apps/web-dashboard/src/pages/api/pet.ts`、
  `pet/interact.ts`、`system/metrics.ts` → 回傳硬編碼/隨機值，未連後端
- **未使用元件（3 檔）**：`EconomyPanel`、`LearningDashboard`、`MemoryViewer`
  已定義但未被 `src/pages/index.tsx` import/渲染（只用了 ChatPanel、PetPanel、SystemMonitor）
- **驗證**：`grep` index.tsx imports → 僅 3 個 component

## 7. 孤兒/垃圾檔案

| 項目 | 說明 |
|---|---|
| 根目錄 `0` | UTF-16 (BOM) + CRLF 的 8-byte 垃圾檔（內容 `0\r\n`），疑似誤輸出 |
| `apps/backend/collect_output.txt` | 115KB 分析產物 |
| `apps/backend/import_timing.txt` | 210KB import 效能分析產物 |
| `apps/backend/import_analysis.json` | 13KB 分析產物 |
| `apps/backend/PLACEHOLDER_REPORT.md` | 100-byte 佔位符報告 |
| `apps/backend/import_all_lines.txt` | 0-byte 空檔 |
| `packages/shared-js/js/live-logger.js` | 孤兒模組（無任何 index.html/JS 引用） |
| `tests/fragmenta/`、`tests/tools/`、`tests/desktop-app/agents/` | 僅含 `__init__.py` 的空目錄 |
| `scripts/train_*.py`（24 檔） | 大部分為實驗腳本，僅少數被 docs/測試引用 |

## 8. 錯誤分類統計

| 分類 | 數量 |
|---|---|
| 🔴 原始碼缺陷（阻斷測試） | 2 |
| 🟡 環境缺依賴（阻斷測試） | 3 套件 / 9 測試檔 |
| 🟠 前端資源缺失 | 2 |
| 🟠 CLI 缺陷 | 1 |
| 🟠 假資料/未用元件 | 3 API / 3 元件 |
| ⚪ 孤兒/垃圾檔案 | ~9 |

## 9. 建議修復優先序

1. **P0**：`key_validator.py` 補 `Any` import（2 行）— 解鎖 3 檔測試
2. **P0**：修復 `.gitignore` + 補寫 `token_effects.py` — 解鎖遊戲子系統（13 test）
3. **P0**：`pip install python-multipart paho-mqtt "google-auth"` — 解鎖 9 檔測試
4. **P1**：補 `.model3.json` 清單檔或改指向既有資源 — 恢復 Live2D
5. **P1**：修 `packages/cli/cli/__main__.py` import 路徑
6. **P2**：清理根目錄 `0` 檔與 `apps/backend/` 分析產物
7. **P2**：web-dashboard 接真實後端或移除 mock/未用元件

## 10. 驗證方法附註

- 測試收集：`timeout 300 python3 -m pytest --collect-only -q`
- 個別 import 驗證：`python3 -c "import sys; sys.path.insert(0,'apps/backend/src'); ..."`
- git 歷史：`git rev-list --all | xargs git ls-tree -r --name-only | grep token_effects`
- gitignore 遮蔽：`git check-ignore -v <path>`
- 環境套件：`pip3 list | grep -iE "paho|google|multipart"`
- flake8 未安裝於目前環境（`No module named flake8`），lint 驗證未能執行
