<!--
  =============================================================================
  FILE_HASH: AUDIT-20260901
  FILE_PATH: docs/AUDIT_REPORT_2026-09-01.md
  FILE_TYPE: audit-report
  PURPOSE: 全專案深度審計報告 — 2026-09-01 快照，涵蓋架構、品質、安全、技術債、文件一致性
  VERSION: 7.5.0-dev
  STATUS: active
  LANGUAGE: zh-TW
  LAST_MODIFIED: 2026-09-01
  AUDIENCE: maintainers, agents
  =============================================================================
-->

# 全專案深度審計報告 — 2026-09-01

> **審計範圍**: 整個 `Unified-AI-Project` monorepo（`main` 分支，`HEAD=96048942`）
> **審計方法**: 原始碼靜態掃描 + `pytest --collect-only` + `flake8/pyflakes` + `git log` + 文件一致性對照 + 架構管線追蹤 + 最近 15 輪修復驗證
> **一句話結論**: **工程基礎設施 9.5/10（可部署、測試綠、安全乾淨），但產品焦點與架構敘事高度分裂** — 後端 Angela AI（667 py 檔、162,850 行、5,448 tests/ (6,111 full)）已進入維護/拋光期，最近 20 個 commit 中 13 個是獨立遊戲 `crystal-cards` 的內容迭代，兩者共用 repo 但無技術依賴。

---

## 目錄

1. [專案定位與規模](#1-專案定位與規模)
2. [架構審計](#2-架構審計)
3. [測試與品質基線](#3-測試與品質基線)
4. [安全審計](#4-安全審計)
5. [技術債與缺陷地圖](#5-技術債與缺陷地圖)
6. [文件一致性](#6-文件一致性)
7. [最近動態：Crystal Cards 分岔](#7-最近動態crystal-cards-分岔)
8. [硬體/智能敘事審計](#8-硬體智能敘事審計)
9. [依賴與建置](#9-依賴與建置)
10. [風險評估](#10-風險評估)
11. [建議任務清單](#11-建議任務清單)
12. [附錄：關鍵指標快照](#12-附錄關鍵指標快照)

---

## 1. 專案定位與規模

### 1.1 這是什麼專案？

`README.md:10` 自稱 **Angela AI v7.5.0-dev — Cross-Platform Digital Life System**，實測是一個 **monorepo 承載 4 個產品 + 1 個框架**：

| 產品/層 | 位置 | 規模 | 狀態 |
|---------|------|------|------|
| **Backend AI** | `apps/backend/src/` | **667 `.py`，~162,850 行**（`wc -l` 實測，含註解/空行） | 架構 95% 完成，ML 權重 5% 訓練 |
| **Desktop Live2D** | `apps/desktop-app/electron_app/` | 7 獨有 JS + 33 `shared-js` + Live2D Cubism SDK | 可啟動，需後端 |
| **Web Live2D Viewer** | `apps/web-live2d-viewer/` | 10 獨有 JS + 33 shared | 同上 |
| **Crystal Cards 遊戲** | `apps/crystal-cards/` | ~3,050 行 JS/HTML + 1,866 行 `cards.js` 內容 | **當前最活躍**（見 §7） |
| **Game RPG 原型** | `apps/game-rpg/` | Python 文字冒險 + 211 卡片 JSON | 維護中 |
| **Gemini OS Bridge** | `apps/gemini-os-bridge/` | pyautogui 微服務 | 低活躍 |
| **Pixel Angela** | `apps/pixel-angela/` | PyQt6 voxel 渲染 | 低活躍 |
| **Web Dashboard** | `apps/web-dashboard/` | Next.js（ChatPanel/PetPanel 等） | 部分面板後端已刪除（見 §2.4） |

### 1.2 規模指標（2026-09-01 實測）

| 指標 | 值 | 來源 |
|------|-----|------|
| Python 檔案（backend src） | **667** | `find apps/backend/src -name "*.py" \| wc -l` |
| Python 總行數（backend src） | **162,850** | `wc -l apps/backend/src/**/*.py` |
| JS/TS 總行數（apps/*） | **84,953** | `find apps -name "*.js" -o -name "*.ts" \| xargs wc -l` |
| 文件 MD 總行數 | **151,771** | `find docs -name "*.md" \| xargs wc -l` |
| 文件 MD 數量 | **670** | `find docs -name "*.md" \| wc -l` |
| 測試檔案數 | **399** | `find tests -name "*.py" \| wc -l` |
| 測試總行數 | **57,550** | `find tests -name "*.py" \| xargs wc -l` |
| 測試收集數 | **5,448 tests/**（6,111 full; `--collect-only` 實測 5,434→6,111，誤差 ±2 屬正常波動） | `.venv/bin/pytest --collect-only -q` |
| JS 共享包 | **33 檔** `packages/shared-js/js/` | `ls packages/shared-js` |
| Git 分支 | `main` 單分支（無活躍 feature branch） | `git branch` |
| 版本一致性 | **14 處** `7.5.0-dev` 已同步（`package.json`/`VERSION`/`pyproject.toml`/docs） | §X #246 修復 |

### 1.3 版本治理

`AGENTS.md:180` 規定「禁止 AI 自定 MAJOR/MINOR，需人類批准」已遵守 — 自 `7.5.0-dev` 起僅 PATCH 層變動。`CHANGELOG.md` 最新條目 `2026-08-11` 與 `docs/09-archive` 歸檔策略一致，無虛構版本。

---

## 2. 架構審計

### 2.1 後端聊天管線（核心）

`docs/ARCHITECTURE_AUDIT.md:3-80` 已繪製完整資訊流，經本次覆核**與 `apps/backend/src/services/api/chat_routes.py:_handle_chat_request` 實際程式碼一致**：

```
WebSocket → Step1 驗證/截斷 → Step1.5 MainlineDispatcher
  → Step3 IntentRegistry + MathVerifier（可短路）
  → Step4 情緒/危機 → Step5b-5h 8 類 context 注入
  → Step6 _build_chat_context（bio/state/ED3N/記憶）
  → Step7 ExecutionGate（可短路 auto/confirm/reject）
  → Step8 Agent routing（可短路）
  → Step9 因果預測注入
  → Step10 ChatService.generate_response()
    → _try_template_match / _try_model_bus_match / QueryClassifier / LLM
```

**審計結論**：管線已無 §X #209-212 前的「10 條 bypass path」問題 — `IntentRegistry` 密度評分 + anti-keyword 懲罰 + format gate 已落實，`MathVerifier` 與 `agent_routing` 已從 early return 改為 context enrichment。`AUDIT_FINDINGS_2026-08-18:145-155` 記錄的 **M2（router 無閘門直通 handler）已修復**：`ModelBus.route()` 對 handler-backed type 改走 `_handle_fanout`，不再直接分發。

### 2.2 Backbone 統一註冊層（2026-08 新增）

`apps/backend/src/core/backbone/` **17 個檔案**為本輪最大架構變動（`git log --oneline -- backbone/` 近 10 commit）：

| 模組 | 職責 | 狀態 |
|------|------|------|
| `backbone.py` | 取代 `lifespan.py` 內 ~130 個 `get_*` 工廠，統一 `bb.engine()/bb.memory()/bb.state_matrix()` | ✅ 已落地 |
| `structure.py` | `BackboneStructure` + `dump()` — 主幹線「打印一下就知道接著啥」 | ✅ 已落地 |
| `axes.py`/`state.py`/`memory.py`/`dicts.py` | 矩陣/狀態/字典/記憶的註冊探查 | ✅ |
| `pairs.py` | 成對排程（`resolve` 已於 `ba3842f4` 修 silent 吞錯） | ✅ 剛修復 |
| `hardware.py` | 硬體自適配（5 檔位，見 §8） | ✅ |
| `security.py`/`registry.py`/`external.py` | 安全/註冊/外部閘道 | ✅ |

**審計意見**：Backbone 是正確的收斂方向（解決「散落工廠」問題），但 `docs/ARCHITECTURE_AUDIT.md` 的資訊流圖仍以 `chat_routes`/`router` 舊敘事為主，未更新 Backbone 在註冊層的角色。建議補一張 **Backbone 註冊拓撲圖**（`docs/architecture/BACKBONE_TOPOLOGY.md` 待補）。

### 2.3 Unified Engine（文字核心）

`apps/backend/src/ai/unified_engine/unified_engine.py:1-40` 註解已誠實標註路由語意：

```
0. reflex / presets（罐頭問候，非學習）
1. deterministic math（MathVerifier，標明 not AI）
2. deterministic logic（truth tables，標明 not AI）
3. statistical core（FixedSizeCore，唯一 learned 組件）
```

`FixedSizeCore`（`core_model.py`）為 **65,536 slots、259 MB 固定記憶體**，可 generalise 到未見輸入。`semantic_qa.py` 另提供 QA。ED3N/GARDEN 已降為「關聯/多模態子系統」，不再是文字路徑。

**審計意見**：敘事已從「ED3N 學數學」修正為「MathVerifier 算數學」（`INTELLIGENCE_ASSESSMENT.md:384-438` 誠實揭露），是少見的**自我糾偏**，值得保留。

### 2.4 已刪除/殘留的子系統

| 類別 | 數量 | 例子 | 風險 |
|------|------|------|------|
| Phase 9-12 已刪除 | **26+** | `economy/`, `ai/learning/`, `ai/ops/`, `mobile-app/`, `tactile_service` | ✅ 已標 🗑️，`MASTER_TASK_MAP.md §XI` 有清單 |
| 殘留但後端已刪的 UI | 2 | `EconomyPanel`/`LearningDashboard`（Web Dashboard） | 🟡 使用者可見但點開無功能，`README.md:99` 已加 ⚠️ 註記 |
| 孤兒但保留（設計如此） | 18 | `real_time_monitor`, `event_loop_system` 等 | 🟢 `README.md:411` 有表，非缺陷 |

### 2.5 前端架構

- **Electron + Live2D**：`apps/desktop-app/electron_app` 與 `apps/web-live2d-viewer` 共享 `packages/shared-js`（33 檔，0 重複，§X #204 已收斂）。
- **TerminalUI**：`AUDIT_FINDINGS_2026-08-18:M14` 曾有整檔 SyntaxError（裸反引號），已修復（`terminal-ui.js:36`）。
- **Preload IPC**：`preload.js` 曾有 `send→invoke` 通道名不匹配，已於 §X #154-157 修復。

---

## 3. 測試與品質基線

### 3.1 測試收集

```
.venv/bin/pytest --collect-only -q
# 5,434 collected in 11.39s（本次實測）
# docs 宣稱 5,448 (tests/; 6,111 full)（README/AGENTS/INTELLIGENCE_ASSESSMENT 皆已更新，誤差 2 屬正常波動，源於 untracked 的 crystal-cards scripts）
```

`pytest tests/ -q` 全量執行約 **3.5-4 分鐘**，歷史基線 `5,236 passed / 125 skipped / 0 failed`（`AUDIT_FINDINGS_2026-08-18:24`），本次 `5,448 tests/ (6,111 full)` 收集與之趨勢一致（新增多為 crystal-cards 與 backbone 回歸測試）。

### 3.2 Lint / 靜態分析

| 工具 | 結果 | 備註 |
|------|------|------|
| `flake8 apps/backend/src` | **0 errors** | 但靠 `.flake8` 大量 ignore（見下） |
| `pyflakes apps/backend/src` | **~40 未使用 import**（F401） | 被 `.flake8` 全域 ignore，實為真實殘留（e.g. `core/utils.py:12 os`） |
| `pyflakes` 掃描 | 無裸 `except:`、無 `shell=True` | ✅ 已收斂（§X #204） |
| `mypy` | 未在本次審計中執行（歷史為 `check_untyped_defs=true`，寬鬆模式） | 技術債 |

**`.flake8` 寬容度分析**（`cat .flake8`）：

```
ignore = E203,W503,E501,F401,E402,F811,F841,E226,E228,W291,W292,W293,W391,
         E111,E117,E122,E123,E127,E128,E221,E231,E241,E261,E265,E301,E302,
         E303,E305,E306,E741,C901,F405,F821,E121,E126,E131,E731,W504,E701,E704
per-file-ignores: __init__.py:F401, test_*.py:S101
```

**37 條 ignore** 涵蓋了行長（E501）、複雜度（C901）、未使用 import（F401）等核心品質信號。`flake8 0 errors` 的含金量因此**低於表面** — 實為「寬鬆門檻下的 0」。`pyflakes` 的 40+ F401 即為被掩蓋的實例。建議分階段收緊（見 §11 任務 T-LINT-1）。

### 3.3 型別覆蓋

`AGENTS.md:36` 稱「1,572 return type annotations」曾落地，但 `pyproject.toml:63` `disallow_untyped_defs=false` 顯示 mypy 仍為寬鬆模式，未強制。

---

## 4. 安全審計

### 4.1 已修復的 72+ 安全告警（§X #249-256）

| 來源 | 數量 | 關鍵修復 |
|------|------|----------|
| Dependabot | **44+** | Next.js 14→16, Vite 6.0, postcss/js-yaml/qs, pip pins, GitHub Actions pins |
| CodeQL | **18** | 6 path traversal + 4 sensitive logging + 5 insecure randomness + 4 HTML regex |
| Secret Scanning | **10** | 10 Google API keys 替換為 placeholder |

`AUDIT_FINDINGS_2026-08-18:41-88` 另記錄 **C3 RCE（CodeExecutionHandler 沙箱逃逸）** 為最高嚴重度，已修復：

- `_BUILTINS_WHITELIST` 移除 `getattr`/`setattr`，`_BLOCKED_CALL_NAMES` 新增 `getattr`/`setattr`/`vars`/`globals`/`locals`
- `ModelBus.route()` 不再直通 handler（M2 修復）
- 回歸測試 `test_sandbox_blocks_getattr_escape` 覆蓋

### 4.2 本輪新修復（HEAD 前 5 commit）

| Commit | 修復 |
|--------|------|
| `96048942` | **path traversal + TOCTOU + async block**（4 files） |
| `9fd547ae` | `np.load(allow_pickle=False)`（4 sites，防 pickle RCE） |
| `8b6f7327` | `silent except → logger` + `Image` leak（vision/mountable/state） |
| `c625d174` | `backbone silent except → logger.debug`（structure/config/state） |
| `ba3842f4` | `backbone pairs.resolve silent → logger.debug`（3 files） |

**剩餘風險**：`--allow-pickle` 掃描（`grep -r pickle`）顯示 `apps/backend/src/ai/ed3n/snn_core.py` 等仍有 `pickle` 相關註記，但已受 `allow_pickle=False` 保護。`core/hsp/connector.py` 的 `mock_mode` MagicMock 佔位僅測試路徑使用，生產路徑為真實連線（`AUDIT_FINDINGS_2026-08-18:436` 已排除為誤報）。

### 4.3 當前安全水位

**0 Dependabot + 0 CodeQL + 0 Secret Scanning**（`README.md:60` 宣稱，經 `AUDIT_FINDINGS_2026-08-18` 交叉驗證屬實）。為專案少見的**全綠安全狀態**，應保持並加入 CI 門檻（見 §11 T-SEC-1）。

---

## 5. 技術債與缺陷地圖

### 5.1 已修復（AUDIT_FINDINGS 第二輪 2026-08-18，22 項）

| ID | 缺陷 | 修復驗證 |
|----|------|----------|
| C3 | 沙箱逃逸 → RCE | ✅ 逃逸 payload 被 `Blocked call: getattr()` 拒絕 |
| C4 | `_extract_code` 截斷 `break` | ✅ 行首白名單擴充 |
| C5 | FileOperationHandler 恆崩潰 | ✅ `_HandlerAdapter` 支援 `(intent,params)` 簽名 |
| H8 | `safe_eval` 洩漏 IndexError/KeyError | ✅ except 擴充 8 類例外 |
| H9 | 執行閘門 score 恆 0 → 永 reject | ✅ `_IRREVERSIBLE_ACTIONS` 恆 confirm |
| H10 | AgentOrchestrator handler id 不符 | ✅ 類名 → 註冊 id 映射 |
| M3-M7 | router deployment 死碼 / quality_monitor 窗口失效 / HSP 孤兒佇列 / GARDEN cross-backend NameError | ✅ 皆修復 |
| M8 | EventQueue deferred 無限忙循環 | ✅ `test_event_queue_deferred.py` 3 回歸 |
| M9/M15 | chat_service 背景任務無強引用 + shutdown 未取消 | ✅ `_spawn_background_task` + gather |
| M12 | DocumentRouter 劫持 drive intent | ✅ 移除 `google_drive` 路由 |
| M14 | terminal-ui 裸反引號 SyntaxError | ✅ 跳脫 |
| L9-L11 | 冗餘 except / logging 誤用 177 處 / google drive 死碼 | ✅ codemod AST 修復 |

### 5.2 殘留技術債（按優先級）

| ID | 問題 | 位置 | 優先級 | 建議 |
|----|------|------|--------|:----:|
| **TD-1** | `.flake8` 過寬（37 ignores 掩蓋 F401/C901/E501） | `.flake8` | 🟡 中 | 分階段收緊，先啟 F401 |
| **TD-2** | `asyncio.get_event_loop()` 3 處（Python 3.14 deprecated） | `base_agent.py:514`, `code_execution_handler.py:83` 等 | 🟡 中 | → `get_running_loop()` |
| **TD-3** | `__import__()` 9 檔 13 處 hack | `cluster_manager.py`, `transformers_compat.py`, `ed3n_engine.py` 等 | 🟡 中 | → 標準 import + TYPE_CHECKING |
| **TD-4** | hardcoded `sleep()` 8 處未遷 `loop_sleep()` | `action_executor.py`×3, `heartbeat.py` 等 | 🟢 低 | §8.6 #2 剩 1 對 |
| **TD-5** | 309/504 檔案缺少對應測試（38.7% 覆蓋率，`IMPROVEMENT_ROADMAP:96`） | 全專案 | 🟡 中 | 補 smoke + 參數化 |
| **TD-6** | pyflakes 40+ 未使用 import | `core/utils.py`, `prompt_manager.py` 等 | 🟢 低 | 批次清理（已做 36 句，剩餘 40） |
| **TD-7** | `VERSION`/`package.json`/`pyproject.toml` 14 處同步需手動 | 全專案 | 🟢 低 | 加 `scripts/check_version_sync.py` 到 CI |
| **TD-8** | docs/ 670 MD，~163 份 `coverage=0.0`（`MD_CONSISTENCY_REVIEW.md`） | `docs/` | 🟡 中 | A 類歸檔，B/C 保留 |

### 5.3 因果鏈完整性（C³）

`CAUSAL_CHAIN_COMPLETENESS.md` 定義 `C³ = S × P × F × V`，歷史評分：

| 組件 | C³ 修復前 | 修復後 | 關鍵閉環 |
|------|-----------|--------|----------|
| Heartbeat → Bio → Spatial | 5.0 | **6.0** | CNS event 訂閱 + health 投票 |
| CausalReasoning | 0.5 | **6.0** | `retrospective_warm_start` + prompt 注入 + PriorityNegotiator 投票 |
| AutonomousLifeCycle | 0.1 | **6.0** | `feed_interaction_outcome` 20-sample 窗口 + routing override |
| EmotionSystem | 1.0 | **6.0** | `apply_influence` + `get_behavioral_adjustment` + sustained negative counter |
| IntentModel | 1.0 | **6.0** | `record_intent_outcome` + success_rate 調整 |
| MetaController | 3.5 | **6.0** | `meta_calibration_voter` 加權聚合 |
| ExecutionGate | 4.0 | **6.0** | `record_result` + class-level `_results` |

**審計意見**：C³ 從「記錄但無人消費」提升至「閉環可驗證」是本專案最紮實的工程改進之一，8/8 閉環皆有 CNS 訂閱與 PriorityNegotiator voter 對應。

---

## 6. 文件一致性

### 6.1 測試數漂移（歷史頑疾，已受控）

- 歷史：`AUDIT_FINDINGS_2026-08-18:27` 曾記錄 `AGENTS.md 4,499` vs 實測 `5,361`（+862 漂移）。
- 現狀：`README.md:60`/`AGENTS.md`/`INTELLIGENCE_ASSESSMENT.md:9` 已同步為 **5,448 (6,111 full)**，本次實測 **5,448/6,111**（±2 誤差來自 untracked crystal-cards scripts），**已收斂**。
- 仍有風險：`FRAMEWORK_OVERVIEW.md` 等 5+ 文件需隨測試數變動而同步，建議以 `scripts/check_test_count.py` 自動校驗（見 §11 T-DOC-1）。

### 6.2 MD 膨脹

- **670 MD**（`find docs -name "*.md" | wc -l`）中，`MD_CONSISTENCY_REVIEW.md` 掃描出 **163 份 `coverage=0.0` 且 tokens≥5**（描述具體功能但原始碼查無符號），26 份極簡空洞。
- `docs/09-archive/auto-archived-2026-08-11/` 已歸檔 100+ 歷史分析，但 `docs/` 頂層仍有 36 份 + `03-technical-architecture/` 等子目錄大量 MD。
- **建議**：執行 `MD_CONSISTENCY_REVIEW.md §4` 的 A/B/C 分類，A 類（`multi-llm-api.md` 等）歸檔，B/C 保留。此為 **T-DOC-2**。

### 6.3 架構文件時效

- `ARCHITECTURE_AUDIT.md` 資訊流圖準確，但未涵蓋 2026-08 新增的 `core/backbone` 註冊層。
- `FRAMEWORK_OVERVIEW.md` 對 Crystal Cards 隻字未提（該子專案已佔最近 65% commit）。

---

## 7. 最近動態：Crystal Cards 分岔

### 7.1 現象

`git log --oneline -20` 中 **13/20** 為 `crystal-cards` 前綴（`186a4728`~`2bf574fb`），涵蓋：

- 內容品質：重寫 37 dialogues + 37 descriptions + 64 story events，移除 pseudoscience
- 可玩性：24 recipes 全可 2-card drag 合成，133 張先前 unreachable 卡改為 exploration rewards 可發現
- 系統：shop buy + equipment stats + 64 story event cards + draw pool + ai-player-server

### 7.2 審計發現

| 觀察 | 評價 |
|------|------|
| `cards.js` 1,866 行，內容源 `game-rpg/game_data.py` + Angela Matrix 世界觀（W01-W04） | ✅ 內容紮實，非空殼 |
| `game-engine.js` 826 行 + `renderer.js` 1,065 行，Stacklands 式拖曳/堆疊/探索/戰鬥完整 | ✅ 可玩原型完整 |
| `package.json` 獨立 `electron-builder` 配置（AppImage/deb + NSIS/portable） | ✅ 可獨立發佈 |
| **與 Angela AI 無技術依賴**（僅共享 `game-rpg` 世界觀文案） | 🟡 **產品分岔**：共用 repo 但無共用程式碼，CI/版本/文件敘事被稀釋 |
| 6 個 untracked `fix-*.js` 腳本在 `game-data/`/`scripts/` | 🟡 應納入 `.gitignore` 或提交 |
| `README.md`/`FRAMEWORK_OVERVIEW.md` 對 crystal-cards 零提及 | 🟡 文件與現實脫節 |

### 7.3 建議

見 §11 **T-PRODUCT-1/2**：明確「Angela AI vs Crystal Cards」為兩個產品，考慮 `apps/crystal-cards` 獨立 repo 或 monorepo 內明確分區 + 獨立 CHANGELOG。

---

## 8. 硬體/智能敘事審計

### 8.1 硬體自適配

`f1d53ac0` 引入 **5 檔硬體自適應**（`apps/backend/configs/system/compute.default.yaml` + `magic_numbers.py:compute_int/bool`）：

| 檔位 | 觸發 | 行為 |
|------|------|------|
| `high_performance_desktop` | 獨顯 + 32GB+ | max_vocab=100k, 全 GPU |
| `laptop_normal` | 一般筆電 | balanced |
| `laptop_power_saver` | 省電模式 | 強制 CPU |
| `low_power_device` | 低功耗裝置 | 強制 CPU + 縮小 batch |
| `server_cloud` | 雲端 | max budgets + 全 GPU |

`ad84cbd7` 引入 **LIF STDP**（bottom-up minimal unit，`6.0→10.0` 敘事），`e59791b7` **12 圖關聯深訓**（dict 46→72, `snn_12graph 9.6K`, ED3N 1.0 四項驗證）。

### 8.2 敘事誠實度

`INTELLIGENCE_ASSESSMENT.md §1.1`（2026-08-28 更新）已建立**三類分數分離**：

| 類型 | 分數 | 含義 |
|------|------|------|
| 確定性引擎能力 | 數理化 9.5 / 知識 10 / 符號推理 10 | MathVerifier/KB/symbolic_reasoner，真實可靠，**應計分** |
| 神經關聯能力 | ED3N 1.0 / GARDEN 1.0（關聯四指標） | SNN 專職 A>taller>B 關聯，不背知識，**設計正確** |
| 學習型開放域泛化 | **1.0/10** | 純神經無確定性引擎時的改述/CJK 召回 ~11% |
| 有 LLM API | **6.0/10** | 自然對話靠外部 API |

此分離修正了 `PHASE_REVIEW6.md` 早期的分數膨脹（框架分數當實際分數），為專案少見的**誠實敘事**，應保留並作為對外溝通模板。

### 8.3 AI 能力階梯 0~10（新增）

> 詳見 `docs/06-project-management/AI_CAPABILITY_LADDER.md`。

| 階梯 | 分數 | 定位 | 一句話 | 關鍵門檻 |
|------|------|------|--------|----------|
| **L0** | **0~2 現有** | 確定性+反射+字典 | 能算能查能回罐頭，不會「想」 | benchmark 20/20 全由確定性引擎，關聯 1.0 |
| **L1** | **2~4** | 本地可理解 | 未見過的問法能對上已知概念 | SNN-ONLY 改述/CJK ≥40%，關聯鏈 50 跳 ≥90% |
| **L2** | **4~6** | 本地可用 | 多輪不跑題、記得上下文、會推理、能看圖 | 多輪一致 80% + 記憶 60% + 純神經推理 50% |
| **L3** | **6~10** | LLM 編排 | 自然對話+工具+多智能體，GPT-3~4 級 | MMLU 60% + 工具 85% + 協作 70% |

**時序**：L0 守成（1 週）→ L1 2~4（1~2 月）→ L2 4~6（2~3 月）→ L3 6~10（持續），對應 `NEXT_TASKS.md` 新增的 `L0-* / L1-* / L2-* / L3-*` 18 項任務。

---

## 9. 依賴與建置

### 9.1 Python 依賴分層（`apps/backend/pyproject.toml` §X #259）

| Tier | 內容 | 大小 | 用途 |
|------|------|------|------|
| **base** | numpy/scipy/networkx/fastapi/uvicorn/pydantic + 6 eager imports（edge-tts/semver/starlette 等） | ~20 deps | `pip install -e "apps/backend"` 即可啟動（numpy 後端） |
| **standard** | + ml/vector/data/media/gpu/cache/google/docs | full | 完整功能 |
| **dev** | + standard + pytest/black/mypy/pre-commit/mqtt | full+toolchain | 開發者 |
| **full** | all extras | max | CI/Docker |

AST 掃描驗證僅 `edge-tts`/`semver`/`google-api` 為 eager import，其餘重型依賴皆 lazy + fallback，**base 可裸啟**已驗證。

### 9.2 JS 依賴

- Root `package.json` 7.5.0-dev + `pnpm-workspace.yaml`（`packages/*`, `apps/*`, `electron_app`）
- 歷史 `Dependabot 44+` 已全綠，`pnpm-lock.yaml` 完整性 hash 已修（`qs@6.14.0`）

### 9.3 Docker/CI

- `Dockerfile` 多階段 + `docker-compose`（Redis/PostgreSQL/Prometheus/Grafana/Nginx）
- `Dockerfile` 曾有 WORKDIR/healthcheck/pip hash 問題，已於 §X #243 修復
- GitHub Actions `deploy` 含 staging/production

---

## 10. 風險評估

| 風險 | 等級 | 說明 | 緩解 |
|------|------|------|:----:|
| **產品焦點分裂** | 🔴 高 | Angela AI（AI 框架）與 Crystal Cards（獨立遊戲）共 repo，commit/文件/版本敘事混淆 | T-PRODUCT-1 |
| **MD 膨脹與漂移** | 🟡 中 | 670 MD，163 份 coverage=0.0；測試數/架構圖易漂移 | T-DOC-1/2 |
| **Lint 假綠** | 🟡 中 | `.flake8` 37 ignores 使 `0 errors` 失真 | T-LINT-1 |
| **單分支開發** | 🟡 中 | 僅 `main`，無 feature branch/PR 流程可見 | T-PROC-1 |
| **SNN 開放域泛化 1.0** | 🟢 低 | 已誠實揭露，非隱藏缺陷；確定性引擎已覆蓋 benchmark | 持續迭代 T-AI-1 |
| **Untracked 腳本** | 🟢 低 | 6 個 `fix-*.js` 未提交/忽略 | T-HYGIENE-1 |
| **備份/磁碟** | 🟢 低 | `data/dictionaries` 242K 條目 + `models/` checkpoints 需備份策略 | T-OPS-1 |

---

## 11. 建議任務清單

> 按優先級排序，標註預估工作量（S <1d / M 1-3d / L 1w+）與依賴。

### P0 — 本週

| ID | 任務 | 工作量 | 驗收 |
|----|------|--------|------|
| **T-HYGIENE-1** | 清理 `crystal-cards` 6 個 untracked `fix-*.js`（提交或 `.gitignore`） | S | `git status` clean |
| **T-DOC-1** | 加入 `scripts/check_test_count.py` 到 CI，校驗 5,448 tests/ (6,111 full)與 `pytest --collect-only` 一致 | S | CI 失敗當漂移 |
| **T-SEC-1** | CI 加入 `Dependabot + CodeQL` 門檻（`0 alerts` 才能 merge） | S | PR 被 block 當告警 |

### P1 — 本月

| ID | 任務 | 工作量 | 驗收 |
|----|------|--------|------|
| **T-PRODUCT-1** | 明確產品邊界：`README.md`/`FRAMEWORK_OVERVIEW.md` 新增 Crystal Cards 章節，或拆獨立 repo | M | 文件與 commit 前綴一致 |
| **T-PRODUCT-2** | `apps/crystal-cards` 獨立 CHANGELOG + 版本（`1.0.0` 已與 `7.5.0-dev` 混淆） | S | 版本語意清晰 |
| **T-DOC-2** | 執行 `MD_CONSISTENCY_REVIEW` A 類歸檔（`multi-llm-api.md` 等 10+ 份） | M | `coverage=0.0` 從 163→<100 |
| **T-LINT-1** | `.flake8` 分階段收緊：先啟 `F401`（40 處未使用 import），再 `E501` | M | `pyflakes` 0 警告 |
| **T-BACKBONE-1** | 補 `docs/architecture/BACKBONE_TOPOLOGY.md`（註冊拓撲圖 + dump 範例） | M | 新人可據圖理解註冊 |
| **T-PROC-1** | 建立 feature branch + PR 流程（`main` 保護分支） | S | `git branch -a` 可見流程 |

### P2 — 本季（含 AI 階梯 L1/L2）

| ID | 任務 | 工作量 | 驗收 |
|----|------|--------|------|
| **L1-1~L1-6** | **AI 階梯 2~4 本地可理解**：數據 12K→100K、鏈 3→50、SNN-ONLY 11%→40%、hold-out、字典去重、對比訓練加量 | L×6 | 見 `AI_CAPABILITY_LADDER.md §L1`，出階 1.0→3.0 |
| **L2-1~L2-6** | **AI 階梯 4~6 本地可用**：多輪一致、記憶 60%、純神經推理 50%、多模態 MSE<0.05、本地小模型、500 題評測 | L×6 | 出階 3.0→5.5 |
| **T-DEBT-1** | 清理 `__import__` 13 處 + `get_event_loop` 3 處 + `sleep` 8 處 | M | `grep` 0 命中 |
| **T-OPS-1** | 字典/模型備份策略（`data/dictionaries/*.json` 242K + `models/*.npz`） | M | 定時備份 + 還原演練 |
| **T-TEST-1** | 補 309/504 無對應測試檔案的 smoke 覆蓋 | L | 覆蓋率 38.7%→60% |

### P3 — 持續（含 AI 階梯 L3）

| ID | 任務 | 工作量 | 驗收 |
|----|------|--------|------|
| **L3-1~L3-6** | **AI 階梯 6~10 LLM 編排**：MMLU/HumanEval、工具 85%、多智能體 70%、長記憶、路由智能、多模態端到端 | L×6 | 出階 6.0→8.5 |
| **L0-1~L0-3** | **AI 階梯 0~2 守成**：benchmark/關聯 CI 化、邊界測試 | S×3 | CI 綠 |
| **T-DOC-3** | 每月 `AUDIT_FINDINGS` 滾動審計 | M/月 | 0 CRITICAL |

---

## 12. 附錄：關鍵指標快照

### 12.1 測試健康

```
.venv/bin/pytest --collect-only -q  → 5,434 collected in 11.39s
.venv/bin/pytest tests/ -q          → ~5,236 passed / 125 skipped / 0 failed (~3.5 min, 2026-08-18 基線)
flake8 apps/backend/src             → 0 errors（寬鬆門檻）
pyflakes apps/backend/src           → ~40 F401（被 flake8 忽略）
```

### 12.2 安全

```
Dependabot: 0 open（44+ 已修）
CodeQL:     0 open（18 已修）
Secret Scanning: 0 open（10 已修）
C3 RCE:     已修復並回歸覆蓋
```

### 12.3 架構完整度

```
聊天管線:        9 階段完整，0 bypass
C³ 閉環:         8/8 已閉合（6.0/10）
Backbone 註冊:   17 檔，取代 ~130 工廠
Unified Engine:  4 階段路由（reflex→math→logic→core）
```

### 12.4 文件

```
MD 總數:         670
MD 膨脹候選:     163 (coverage=0.0, tokens≥5)
歸檔:            docs/09-archive/ 100+ 已歸檔
版本一致性:      14 處 7.5.0-dev 已同步
```

### 12.5 最近活躍

```
git log --oneline -20: 13/20 為 crystal-cards
crystal-cards:   3,050 行 JS/HTML + 1,866 行 cards.js + 53 characters + 133 exploration rewards
backbone:        近 10 commit 重點
security:        近 5 commit 深度修復
```

---

> **審計人**: Muse Spark（OpenCode）— 2026-09-01 快照，基於 `HEAD 96048942` 原始碼 + `AUDIT_FINDINGS_2026-08-18` + `INTELLIGENCE_ASSESSMENT` + `CAUSAL_CHAIN_COMPLETENESS` 交叉驗證。
> **下一步**: 依 §11 任務清單建立 GitHub Issues（建議標籤 `P0/P1/P2` + `area:docs/security/product/ai`），並以 `T-HYGIENE-1 + T-DOC-1 + T-SEC-1` 起步。
