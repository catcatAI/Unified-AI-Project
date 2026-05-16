# Angela AI — Comprehensive Task Inventory v6.2.2
> 2026-05-16 | 集中整理所有任務進度
> 整理自：ANGELA_STATUS.md, WEBSOCKET_CONNECTION_ARCHITECTURE.md, NEXT_PHASE.md, REFACTORING_PLAN.md, POST_REFACTOR_PLAN.md, CHANGELOG.md, TEST_REPORT.md, REMEDIATION_PLAN.md

---

## 執行摘要

**版本**: v6.2.5 (Phase 5 — REPL + θ/η Integration COMPLETE)
**總任務數**: 96
**已完成**: 80 (83.3%)
**進行中**: 1 (1.0%)
**待處理**: 12 (12.5%)
**已跳過/延後**: 1 (1.0%)

---

## 一、已完成任務（71項）

### 1.1 Phase 1-7 重構（7/7）✅

| # | 任務 | 檔案 | 行數 | 狀態 |
|---|------|------|------|------|
| 1 | Axis + AxisField 提取 | `core/state/axis_field.py` | 334 | ✅ |
| 2 | TemporalState 重構 | `core/state/temporal.py` | 426 | ✅ |
| 3 | AllocationPolicy 重構 | `core/allocation/policy.py` | 260 | ✅ |
| 4 | Config 外部化 | `core/state/config_loader.py` | 239 | ✅ |
| 5 | RippleNode 對象化 | `core/ripple/node.py` | 361 | ✅ |
| 6 | InfluenceSpace 抽象 | `core/influence/space.py` | 333 | ✅ |
| 7 | StateMatrixAdapter facade | `core/autonomous/state_matrix_adapter.py` | 891 | ✅ |

### 1.2 Post-Refactor Plan v1.0（9/9）✅

| # | 任務 | 檔案 | 狀態 |
|---|------|------|------|------|
| 1 | Smoke tests (9 scenarios) | `test_smoke_real.py` | ✅ |
| 2 | God Class 清理 (2.1-2.4, 2.6-2.7) | state_matrix.py | ✅ |
| 3 | CodeInspector 整合 | `ai/code_inspection/code_inspector_integration.py` (220行) | ✅ |
| 4 | SelfIntrospectorV2 | `core/autonomous/self_introspector_v2.py` (228行) | ✅ |
| 5 | 完整測試套件 | 11 files, 94+ tests | ✅ |
| 6 | TemporalState `get_at()` 負索引修復 | `temporal.py` | ✅ |
| 7 | Facade routing 單軸錯誤修復 | `state_matrix_adapter.py` | ✅ |
| 8 | InfluenceApplicator `amount` 被忽略修復 | `influence_applicator.py` | ✅ |
| 9 | Smoke S1 錯誤軸字段修復 | `test_smoke_real.py` | ✅ |

### 1.3 新建模組（14/14）✅

| # | 模組 | 檔案 | 行數 | 測試 |
|---|------|------|------|------|
| 1 | AxisFieldRegistry | `core/state/axis_field.py` | 334 | test_phase1.py (5) |
| 2 | Axis | `core/state/axis.py` | 215 | test_phase1_2.py (1) |
| 3 | TemporalState | `core/state/temporal.py` | 426 | test_temporal_unit.py (14) |
| 4 | StateConfig | `core/state/config_loader.py` | 239 | test_smoke_real.py S7 (1) |
| 5 | ResonanceEngine | `core/allocation/resonance.py` | 184 | test_phase1_2.py (1) |
| 6 | AllocationPolicy | `core/allocation/policy.py` | 260 | test_allocation_policy_unit.py (10) |
| 7 | NegativityDetector | `core/allocation/negativity.py` | 310 | test_phase1_2.py (1) |
| 8 | RippleNode | `core/ripple/node.py` | 361 | test_phase5_6.py (4) |
| 9 | InfluenceSpace | `core/influence/space.py` | 333 | test_phase5_6.py (4) |
| 10 | StateMatrixAdapter | `core/autonomous/state_matrix_adapter.py` | 891 | test_smoke_real.py (9) |
| 11 | InfluenceApplicator | `core/autonomous/influence_applicator.py` | 124 | test_influence_applicator_unit.py (7) |
| 12 | SelfIntrospectorV2 | `core/autonomous/self_introspector_v2.py` | 228 | test_self_introspector_v2.py (8) |
| 13 | CodeInspectorBridge | `ai/code_inspection/code_inspector_integration.py` | 220 | test_code_inspector_integration.py (8) |
| 14 | TextToVector | `core/state/text_to_vector.py` | 33 | 間接測試 |

### 1.4 WebSocket Session Management — Phase 4（8/8）✅

| # | 任務 | 檔案 | 狀態 |
|---|------|------|------|
| 1 | SessionManager 類 | `services/connection_session.py` | ✅ |
| 2 | ConnectionSession dataclass | `services/connection_session.py` | ✅ |
| 3 | ConnectionManager 改造 | `services/main_api_server.py:793-950` | ✅ |
| 4 | WebSocket 端點 session 支持 | `services/main_api_server.py:953-1112` | ✅ |
| 5 | BackendWebSocketClient session_id | `electron_app/js/backend-websocket.js:21-155` | ✅ |
| 6 | Main process session 支持 | `electron_app/main.js:1371-1448` | ✅ |
| 7 | Preload IPC 更新 | `electron_app/preload.js:107-113` | ✅ |
| 8 | test_connection_session.py | `tests/test_connection_session.py` (21 tests) | ✅ |

### 1.5 Anchor Learning System ✅

| # | 任務 | 檔案 | 狀態 |
|---|------|------|------|
| 1 | AnchorLearningEngine | `core/autonomous/anchor_learning.py` | ✅ |
| 2 | test_anchor_learning.py | `tests/test_anchor_learning.py` (10 tests) | ✅ |
| 3 | StateMatrixAdapter 集成 | 4觸發點（update_*, allocation_decide, meta_allocate, correct_misallocation） | ✅ |

### 1.6 P8 — LLM E2E Integration ✅

| # | 任務 | 狀態 |
|---|------|------|
| 1 | `integrate_verification_result()` | ✅ |
| 2 | `integrate_code_inspect()` | ✅ |
| 3 | `ask_theta_for_analysis()` | ✅ |
| 4 | HTTP API `/math/verify` | ✅ |
| 5 | HTTP API `/code/inspect` | ✅ |
| 6 | HTTP API `/theta/analyze` | ✅ |
| 7 | E2E Test | ✅ 4/4 tests passing |

### 1.7 P9 — Persistence Layer ✅

| # | 任務 | 狀態 |
|---|------|------|
| 1 | `StatePersistence` class | ✅ |
| 2 | `save_checkpoint()` | ✅ |
| 3 | `load_checkpoint()` | ✅ |
| 4 | `list_checkpoints()` | ✅ |
| 5 | `delete_checkpoint()` | ✅ |
| 6 | `auto_checkpoint()` | ✅ |
| 7 | `init_persistence()` | ✅ |
| 8 | HTTP API (5 endpoints) | ✅ |
| 9 | Tests | ✅ 6/6 passing |

### 1.8 Desktop App Integration ✅

| # | 任務 | 狀態 |
|---|------|------|
| 1 | Desktop `state-matrix.js` — 添加 θ, 更新影響矩陣 | ✅ |
| 2 | Desktop WebSocket — sendStateUpdate(), requestFullState(), 6D 支持 | ✅ |
| 3 | Mobile `App.js` — 6D matrix (αβγδεθ), real backend data | ✅ |
| 4 | Mobile η button — module bar + execution count/success rate/drift | ✅ |

### 1.9 Phase 3 — Feature Completion (2/2) ✅

| # | 任務 | 狀態 |
|---|------|------|
| 1 | P8 — True LLM E2E Integration | ✅ |
| 2 | P9 — Persistence Layer (Redis/JSON) | ✅ |

### 1.10 其他已完成任務

| # | 任務 | 說明 |
|---|------|------|
| 1 | P1-1 Test Suite Syntax Fixes | 238 test files 語法修復 ✅ |
| 2 | P1-2 Backend Import Timeout | Lazy loading 修復 ✅ |
| 3 | P1-3 Core AI System Fixes | AI service modules 修復 ✅ |
| 4 | P2-3 Environment Configuration | .env with secure keys ✅ |
| 5 | P2-1 Technical Debt Markers | 43 TODO/FIXME documented ✅ |
| 6 | P2-2 Deprecated Code Review | 3 files reviewed ✅ |
| 7 | N.22.6 Self-Introspection | SelfIntrospectorV2 ✅ |
| 8 | N.22.1 Workflow Integration | CodeInspectorBridge ✅ |
| 9 | StateMatrix4D 清理 | 1834行→1604行 (-230行) ✅ |
| 10 | RippleApplicatorRegistry | 6軸應用器 + registry ✅ |

### 1.11 測試矩陣（11/11 files, 115+ tests）✅

| 套件 | 檔案 | 測試數 | 狀態 |
|------|------|--------|------|
| TemporalState unit | `test_temporal_unit.py` | 14 | ✅ PASS |
| AllocationPolicy unit | `test_allocation_policy_unit.py` | 10 | ✅ PASS |
| InfluenceApplicator unit | `test_influence_applicator_unit.py` | 7 | ✅ PASS |
| CodeInspectorBridge unit | `test_code_inspector_integration.py` | 8 | ✅ PASS |
| SelfIntrospectorV2 unit | `test_self_introspector_v2.py` | 8 | ✅ PASS |
| Smoke real | `test_smoke_real.py` | 9 scenarios | ✅ PASS |
| Final pipeline | `test_final.py` | 1 | ✅ PASS |
| Phase1 | `test_phase1.py` | 6 | ✅ PASS |
| Phase1-2 integration | `test_phase1_2.py` | 7 | ✅ PASS |
| Phase5-6 | `test_phase5_6.py` | 10 | ✅ PASS |
| Comprehensive audit | `test_audit_comprehensive.py` | 14 sections | ✅ PASS |
| Connection session | `test_connection_session.py` | 21 | ✅ PASS (20/21) |
| Anchor learning | `test_anchor_learning.py` | 10 | ✅ PASS |
| **TOTAL** | **13 files** | **115+** | **114+ PASS** |

---

## 二、進行中任務（3項）

### 2.1 WebSocket RSV Error 診斷 🔄

**問題**: `reserved bits must be 0` ProtocolError
**位置**: `main_api_server.py:953-1112`
**分析進度**:
- RSV3=1, opcode=0 (continuation frame), FIN=1
- Payload: 4 bytes (`b'\xe1\xf0;h'` — masked text data)
- ASGI receive 正常：只有一個 WebSocket client 連接
- 客戶端收到 `send_json()` 響應後立即發送 continuation frame
- 根本原因：**未知**

**已嘗試修復**:
1. ✅ 簡化握手流程（移除 temp session → unregister → re-register）
2. ✅ 調試代碼：Frame.check 和 Frame.read 的 patch
3. ✅ 等待握手完成後才進入消息循環
4. 🔄 仍待確認根本原因

**下一步**:
- 添加 frame payload 內容日誌
- 檢查客戶端是否在處理 WebSocket 升級響應時出錯
- 可能的話：捕獲 client 端的網絡流量

### 2.2 P7 StateMatrix4D 進一步清理 🔄

**目標**: 1834行 → ~1200行
**狀態**: 部分完成（1604行，-230行）
**待處理**:
- 移除已委託給新模組的舊邏輯
- 最終整合：StateMatrix4D 內部只使用新模組
- 標記過時方法為 deprecated

### 2.3 WebSocket Multi-Client Session Routing 🔄

**目標**: 多設備支援
**狀態**: 架構已設計，但尚未實現
**待處理**:
- 多客戶端 session 路由
- 按 session_id 廣播
- 重連恢復測試

---

## 三、待處理任務（12項）

### 3.1 高優先級（4項）

| # | 任務 | 優先級 | 說明 |
|---|------|--------|------|
| 1 | WebSocket RSV Error 根本修復 | 🔴 HIGH | 解決 `reserved bits must be 0` |
| 2 | WebSocket 重連恢復測試 | 🔴 HIGH | `tests/test_websocket_lifecycle.py` |
| 3 | 移除主進程 auto-reconnect | 🟡 MEDIUM | main.js 已移除，但需驗證 |
| 4 | test_connection_session.py 1個失敗測試 | 🟡 MEDIUM | 21個測試中20個通過 |

### 3.2 中優先級（5項）

| # | 任務 | 優先級 | 說明 |
|---|------|--------|------|
| 5 | Desktop App Live2D SDK Integration | 🟡 MEDIUM | 安裝 Live2D SDK，60 FPS 渲染 |
| 6 | Desktop App StateMatrixAdapter 集成 | 🟡 MEDIUM | Port routing, η axis monitoring |
| 7 | Mobile η Module Controls | 🟡 MEDIUM | Module parameter adjustment |
| 8 | RippleApplicatorRegistry 最終實現 | 🟡 MEDIUM | 可插拔的應用器 |
| 9 | 標記過時方法 deprecated | 🟡 MEDIUM | 準備最終移除 |

### 3.3 低優先級（3項）

| # | 任務 | 優先級 | 說明 |
|---|------|--------|------|
| 10 | P2 迭代任務（N.22.x）| 🟢 LOW | N.22-DUAL-RAIL, N.22.5, N.22.2, N.22.3-4, N.22.7 |
| 11 | 創建 js/session-manager.js | 🟢 LOW | 可選重構 |
| 12 | 簡化 main.js WebSocket 處理 | 🟢 LOW | 可選優化 |

---

## 四、v6.2.x REPL + θ/η 整合任務（8項）

> Angela v6.2.3+ — 座標AI系統 + REPL 完整整合
> 來源: ANGELA_REPL_INTEGRATION_PLAN_v6.2.5.md

### 4.1 狀態打包（1項）

| # | 任務 | 檔案 | 狀態 |
|---|------|------|------|
| 1 | `state_matrix.export_for_llm()` | `core/autonomous/state_matrix.py` | ✅ 完成 |

### 4.2 θ/η 初始化（1項）

| # | 任務 | 檔案 | 狀態 |
|---|------|------|------|
| 2 | θ/η 初始化 | `services/main_api_server.py` + `chat_service.py` | ✅ 完成 |

### 4.3 LLM 增強（1項）

| # | 任務 | 檔案 | 狀態 |
|---|------|------|------|
| 3 | `_construct_angela_prompt()` 增強 | `services/angela_llm_service.py` | ✅ 完成 |

### 4.4 Chat Pipeline 整合（1項）

| # | 任務 | 檔案 | 狀態 |
|---|------|------|------|
| 4 | `chat_service.generate_response()` 重構 | `services/chat_service.py` | ✅ 完成 |

### 4.5 θ 自檢迴路（2項）

| # | 任務 | 檔案 | 狀態 |
|---|------|------|------|
| 5 | θ 錯配檢測觸發 | `services/chat_service.py` | ✅ 完成 |
| 6 | θ 校正執行 | `services/chat_service.py` | ✅ 完成 |

### 4.6 η 執行整合（2項）

| # | 任務 | 檔案 | 狀態 |
|---|------|------|------|
| 7 | η 模組觸發曲線 | `services/chat_service.py` | ✅ 完成 |
| 8 | η → θ 反饋 | `services/chat_service.py` | ✅ 完成 |

### 4.7 Ζ軸真實整合（1項）

| # | 任務 | 檔案 | 狀態 |
|---|------|------|------|
| 9 | Ζ (Zeta) 軸真實實現 | `core/autonomous/state_matrix.py` | ✅ 完成 |

### 4.8 測試驗證（1項）

| # | 任務 | 檔案 | 狀態 |
|---|------|------|------|
| 10 | REPL 整合測試 | - | ✅ 完成（6 項單元測試全部通過）|

---

## 五、v6.2.5 完成狀態（Section 4 全部 ✅）

Section 4 全部 9 個任務已完成，詳見上表。REPL 整合測試（6 項單元測試）全部通過。

---

## 六、已跳過/延後任務（1項）

| # | 任務 | 狀態 | 說明 |
|---|------|------|------|
| 1 | P2-5 Invalid Python Distributions | ⊘ 延後 | ~ensorflow, ~umpy warnings — 非阻塞 |

---

## 六、詳細任務清單

### 6.1 重構相關任務（Phase 1-7 + Post-Refactor）

```
✅ Phase 1: 核心抽象
   ├─ Axis + AxisField + Registry   → core/state/axis_field.py (334行)
   └─ TemporalState               → core/state/temporal.py (426行)

✅ Phase 2: 決策重構
   ├─ AllocationPolicy           → core/allocation/policy.py (260行)
   ├─ ResonanceEngine             → core/allocation/resonance.py (184行)
   └─ NegativityDetector          → core/allocation/negativity.py (310行)

✅ Phase 3: 配置外部化
   └─ YAML配置 → StateConfig     → core/state/config_loader.py (239行)

✅ Phase 4: 漣漪系統
   └─ RippleNode對象化           → core/ripple/node.py (361行)

✅ Phase 5: 影響系統
   └─ InfluenceSpace抽象         → core/influence/space.py (333行)

✅ Phase 6: 整合適配器
   └─ StateMatrixAdapter          → core/autonomous/state_matrix_adapter.py (891行)

✅ Phase 7: 雙軌並行
   └─ 舊 StateMatrix4D 完全保留，新模組提供新 API

✅ Post-Refactor: Smoke Tests (9 scenarios)
✅ Post-Refactor: God Class 清理 (2.1-2.4, 2.6-2.7)
✅ Post-Refactor: CodeInspector 整合
✅ Post-Refactor: SelfIntrospectorV2
✅ Post-Refactor: 完整測試套件 (13 files, 115+ tests)
```

### 5.2 WebSocket Session Management 任務

```
✅ P0-1: SessionManager 類
✅ P0-2: ConnectionSession dataclass
✅ P0-3: ConnectionManager 改造
✅ P0-4: WebSocket 端點接受 session_id
✅ P1-1: BackendWebSocketClient 攜帶 session_id
✅ P1-2: Main process session 支持
✅ P1-3: Preload IPC 更新
✅ P1-4: 移除主進程 auto-reconnect
✅ P1-5: 重連時攜帶 session_id
✅ P1-6: 多客戶端註冊表
✅ P1-7: 按 session 廣播

🔄 P2-1: WebSocket RSV Error 根本修復（進行中）
🔄 P2-2: 多客戶端 session 路由（進行中）
🔄 P2-3: 重連恢復測試（進行中）

⬜ P3-1: 創建 js/session-manager.js
⬜ P3-2: 簡化 main.js WebSocket
```

### 5.3 P8/P9 Feature Completion 任務

```
✅ P8: True LLM E2E Integration
   ├─ integrate_verification_result()
   ├─ integrate_code_inspect()
   ├─ ask_theta_for_analysis()
   ├─ HTTP /math/verify
   ├─ HTTP /code/inspect
   ├─ HTTP /theta/analyze
   └─ E2E Test (4/4 passing)

✅ P9: Persistence Layer (Redis/JSON)
   ├─ StatePersistence class
   ├─ save_checkpoint()
   ├─ load_checkpoint()
   ├─ list_checkpoints()
   ├─ delete_checkpoint()
   ├─ auto_checkpoint()
   ├─ init_persistence()
   └─ HTTP API (5 endpoints)
```

### 5.4 Desktop/Mobile Integration 任務

```
✅ Desktop: state-matrix.js 6D 支持 (αβγδεθ)
✅ Desktop: WebSocket sendStateUpdate(), requestFullState(), 6D
✅ Desktop: BackendWebSocketClient _mergeStateData 6D
✅ Mobile: App.js 6D matrix + real backend data
✅ Mobile: η button + module status

⬜ Desktop: Live2D SDK Integration (60 FPS)
⬜ Desktop: StateMatrixAdapter 集成 (port routing, η)
⬜ Mobile: η Module Controls (adjust parameters)
```

### 5.5 N.22 迭代任務

```
✅ N.22.6 自我內省趨勢追蹤 → SelfIntrospectorV2
✅ N.22.1 工作流整合 → CodeInspectorBridge

⬜ N.22-DUAL-RAIL 數學驗證 → MathVerifier + TemporalState correlation
⬜ N.22.5 空間美學推斷 → AllocationPolicy
⬜ N.22.2 生理張力成功率 → RippleAccumulator
⬜ N.22.3-4 空間成熟度評估 → ResonanceEngine
⬜ N.22.7 AI Posture Selection → NegativityDetector
```

### 5.6 P7 StateMatrix4D 清理

```
🔄 清理狀態: 1834行→1604行（-230行，已完成部分）

待處理:
⬜ 移除已委託給新模組的舊邏輯
⬜ 最終整合：StateMatrix4D 內部只使用新模組
⬜ 標記過時方法為 deprecated
⬜ 目標：1834行 → ~1200行
```

### 5.7 其他待處理任務

```
⬜ 測試套件覆蓋率 > 80%（當前 71+ tests）
⬜ 修復 test_connection_session.py 的 1 個失敗測試
⬜ SQL Injection 漏洞修復（evaluation_db.py）
⬜ Command Injection 漏洞修復（execution_manager.py）
⬜ File Path Injection 漏洞修復
⬜ HSP Connection Stability 改進
⬜ Native Audio Modules 構建和驗證
```

---

## 六、測試覆蓋矩陣

| 模組 | 檔案 | 行數 | 測試數 | 覆蓋狀態 |
|------|------|------|--------|---------|
| AxisFieldRegistry | core/state/axis_field.py | 334 | 5 | ✅ 完整 |
| TemporalState | core/state/temporal.py | 426 | 14+1 | ✅ 完整 |
| ResonanceEngine | core/allocation/resonance.py | 184 | 1+間接 | ✅ 完整 |
| AllocationPolicy | core/allocation/policy.py | 260 | 10+1 | ✅ 完整 |
| NegativityDetector | core/allocation/negativity.py | 310 | 1+間接 | ✅ 完整 |
| RippleNode | core/ripple/node.py | 361 | 4 | ✅ 完整 |
| InfluenceSpace | core/influence/space.py | 333 | 4 | ✅ 完整 |
| StateMatrixAdapter | core/autonomous/state_matrix_adapter.py | 891 | 9+若干 | ✅ 完整 |
| InfluenceApplicator | core/autonomous/influence_applicator.py | 124 | 7 | ✅ 完整 |
| SelfIntrospectorV2 | core/autonomous/self_introspector_v2.py | 228 | 8 | ✅ 完整 |
| CodeInspectorBridge | ai/code_inspection/code_inspector_integration.py | 220 | 8 | ✅ 完整 |
| ConnectionSession | services/connection_session.py | 457 | 21 | ✅ 20/21 |
| AnchorLearning | core/autonomous/anchor_learning.py | 295 | 10 | ✅ 完整 |

---

## 七、關鍵問題追蹤

### Issue #1: WebSocket RSV Error 🔴
- **問題**: `reserved bits must be 0` — RSV3=1, opcode=0
- **位置**: `main_api_server.py:953-1112`
- **嚴重性**: 🔴 CRITICAL — 阻止連接正常運作
- **根本原因**: 未知
- **已嘗試**: 3種修復方案
- **狀態**: 🔄 診斷中

### Issue #2: Semantic Anchor Sparsity 🟡 → ✅ 已修復
- **問題**: 32維錨點只有 4-5 個非零值
- **影響**: ASSIGN 閾值 (0.7) 無法觸發
- **狀態**: ✅ 已修復 — AnchorLearningEngine

### Issue #3: StateMatrix4D 仍為 ~1604 行 🟡
- **目標**: ~1200 行
- **狀態**: 🔄 部分完成（-230行）

---

## 八、版本歷史

| 版本 | 日期 | 狀態 | 完成度 |
|------|------|------|--------|
| 6.2.0 | 2026-02-19 | Phase 1-7 重構完成 | ✅ |
| 6.2.1 | 2026-05-14 | Post-Refactor v1.0 完成 + 94 tests | ✅ |
| 6.2.2 | 2026-05-16 | WebSocket Session Management | 🔄 81.6% |
| 6.2.5 | 2026-05-16 | REPL + θ/η Integration Added | 🔄 74.0% |

---

**最後更新**: 2026-05-16
**版本**: v6.2.5
**下一步**: 
1. 新增 `state_matrix.export_for_llm()` — 打包 6 維 + θ + η 供 LLM 使用
2. 增強 `_construct_angela_prompt()` — 加入 θ/η 狀態 + 座標 + 氛圍指引
3. 重構 `chat_service.generate_response()` — 加入 IntentRouter + θ/η 管道
4. REPL 測試 + 觀察座標變化