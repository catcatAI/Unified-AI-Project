# 測試超時策略與實測指南

本文檔描述了專案的測試超時策略、實測（Practical Testing）方法，以及前端終端對話測試流程。

## 當前測試狀態

| 指標 | 數值 |
|:-----|:----:|
| **測試總數** | **4,387** (2026-07-09) |
| 收集時間 | ~26 秒 |
| 0 errors | ✅ |
| pytest-timeout | 已安裝 |
| pytest-asyncio | 已安裝 |

## 超時設置原則

1. **基本單元測試**：5秒超時
   - 簡單的功能測試
   - 無外部依賴的測試
   - 同步測試

2. **集成測試**：10秒超時
   - 涉及多個模組的測試
   - 有外部依賴的測試
   - 異步測試
   - 數據庫操作測試
   - 網絡請求測試

3. **性能測試**：30秒或更長
   - 壓力測試
   - 負載測試
   - 長時間運行的測試
   - 大數據量處理測試

## 自動化超時設置

專案中提供了自動化腳本 `scripts/add_pytest_timeouts.py`
來為測試文件添加超時設置：

```bash
# 為所有測試文件添加超時設置
python scripts/add_pytest_timeouts.py
```

腳本會根據文件路徑和名稱自動設置適當的超時時間：

- 位於 `integration` 目錄下的測試：10秒
- 位於 `performance` 目錄下的測試：30秒
- 其他測試：5秒

特殊文件的超時設置可以在腳本的 `SPECIAL_TIMEOUTS` 字典中配置。

## 運行測試（含超時）

### 基本命令

```bash
# 運行所有測試，啟用超時檢測（建議 CI 使用 30s）
pytest tests/ --timeout=30 --timeout_method=thread -q

# 運行所有測試（使用預設，無強制超時）
pytest tests/

# 運行特定測試文件
pytest tests/path/to/test_file.py --timeout=10 -v

# 運行特定測試類或方法
pytest tests/path/to/test_file.py::TestClassName::test_method --timeout=5 -v
```

### 快速驗證（僅收集）

```bash
# 確認測試收集數與 0 errors
pytest tests/ --collect-only -q 2>&1 | tail -5
```

### 執行特定領域測試

```bash
# 安全測試
pytest tests/security/ --timeout=10 -v

# AI 核心測試
pytest tests/ai/ --timeout=15 -v

# API 測試
pytest tests/api/ --timeout=10 -v

# CLI 測試
pytest tests/cli/ --timeout=10 -v
```

## 前端終端對話實測（Frontend Terminal Testing）

所有 3 個前端（web-live2d-viewer、Electron、Electron MVP）均配備**浮動終端覆蓋層**（Ctrl+` 切換），可直接測試對話流程。

### 實測步驟

1. **啟動後端**：
   ```bash
   python run_angela.py --api-only
   ```
   或
   ```bash
   pnpm dev:backend
   ```

2. **開啟前端**：
   - Web: 瀏覽器打開 `apps/web-live2d-viewer/index.html`
   - Electron: `pnpm dev:desktop`

3. **測試對話管線**：
   - 按下 Ctrl+` 開啟終端
   - 輸入訊息後按 Enter
   - 觀察 `route` 和 `hit_source` 欄位

4. **測試模式**：
   | 模式 | 輸入 | 預期 route |
   |------|------|-----------|
   | 一般問候 | "你好" | llm |
   | 數學 | "2+2" | dual_rail |
   | 檔案操作 | "幫我建立一個筆記" | gate_confirm → agent |
   | 情感 | "我今天心情不好" | llm（含 emotion） |
   | 緊急 | "救命" | llm（含 crisis_level） |

### 自動化實測建議

對於前端終端，可使用以下進行自動化測試：

```bash
# 測試 API 端點
curl -X POST http://localhost:8000/api/v1/chat/unified \
  -H "Content-Type: application/json" \
  -d '{"message": "你好", "session_id": "test-001"}' | python -m json.tool

# 測試數學推理
curl -X POST http://localhost:8000/api/v1/chat/unified \
  -H "Content-Type: application/json" \
  -d '{"message": "2+2=?", "session_id": "test-math"}' | python -m json.tool
```

## 實測範疇與智能分層驗證

### 三層智能驗證

專案的 AI 回應管線支援三種智能層級，實測應涵蓋：

| 層級 | 名稱 | 實測重點 |
|:----:|:-----|:---------|
| L1 | **預設組合式硬編** (ED3N Reflex) | 基本問候、數學、時事回應是否合理 |
| L2 | **本地訓練模型** (ED3N/GARDEN) | 訓練後是否提升準確率、記憶是否正確 |
| L3 | **LLM** (外部 API) | 複雜對話、創意、情感回應是否自然 |

### 安全驗證

實測中需確認：

- ✅ **檔案操作安全**：`DesktopInteraction._is_safe_path()` 限制操作範圍在 `_ALLOWED_ROOTS` 內
- ✅ **自主行為追蹤**：`AutonomousLifeCycle` 所有決策均透過 `BehaviorExecutor` 記錄成功/失敗
- ✅ **非同步一致性**：`ExecutionGate` 透過 `confirm_then_execute` 要求用戶確認後才執行
- ✅ **表達式安全**：`safe_eval` 使用 AST 白名單，禁止任意程式碼執行
- ❌ **無幻覺漏洞**：不存在「對話說新增→執行刪除」這類非同步不一致

### 硬件資源消耗驗證

| 場景 | 預期行為 |
|:-----|:---------|
| 低配備硬體 | 自動降級至 ED3N Reflex（L1），關閉 Live2D/GPU |
| 高配備硬體 | 啟用 LLM（L3）+ Live2D + 多模態 |
| 自動調整 | `PerformanceManager` + `HardwareDetection` 自動偵測並調整 |

## 常見問題排查

### 測試超時

1. **問題**：測試經常超時
   **解決方案**：
   - 檢查是否有無限循環
   - 優化數據庫查詢
   - 增加超時時間（僅在必要時）

2. **問題**：異步測試卡住
   **解決方案**：
   - 確保所有異步操作都有適當的 `await`
   - 使用 `asyncio.wait_for` 設置超時
   - 檢查是否有未完成的協程

3. **問題**：CI 環境中超時
   **解決方案**：
   - 在 CI 配置中增加超時時間
   - 考慮將長時間運行的測試標記為 `@pytest.mark.slow` 並單獨運行
   - 優化測試數據和環境設置

## 維護與更新

1. **定期審查**：
   - 定期檢查測試的超時設置
   - 移除不必要的長時間超時
   - 更新過時的測試

2. **文檔**：
   - 在測試文件中添加註釋說明超時設置的原因
   - 記錄特殊的測試環境要求
   - 更新本文檔以反映當前的測試策略

3. **工具支持**：
   - 使用 `pytest-timeout` 插件管理超時
   - 考慮使用 `pytest-xdist` 進行並行測試
   - 使用 `pytest-cov` 檢查測試覆蓋率

## 參考資源

- [pytest-timeout 文檔](https://pypi.org/project/pytest-timeout/)
- [pytest-asyncio 文檔](https://pypi.org/project/pytest-asyncio/)
- [Python 測試最佳實踐](https://docs.pytest.org/en/stable/goodpractices.html)
- [異步測試指南](https://docs.pytest.org/en/stable/asyncio.html)
- [tests/README.md](../../../tests/README.md) — 測試目錄結構與運行方式
